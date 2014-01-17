# Copyright (c) 2013-2014 Marin Atanasov Nikolov <dnaeon@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer
#    in this position and unchanged.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR(S) ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR(S) BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
The vconnector module provides classes and methods for establishing a 
connection to VMware vSphere server instance.

"""

import os
import logging
import ConfigParser

from time import time
from pysphere import VIServer, MORTypes

class VConnectorException(Exception):
    """
    Generic VConnector exception.

    """
    pass

class VConnector(object):
    """
    VConnector class.

    The VConnector class defines methods for connecting and disconnecting from a
    VMware vSphere server instance.

    Returns:
        VConnector object
    
    Raises:
        IOError

    """
    def __init__(self, config_file, extra_attr=None, ignore_locks=False, lockdir='/var/run/vconnector', keep_alive=False):
        """
        Initializes a new VConnector object.

        Args:
            config_file (ConfigParser): The config file containing the connection details
            extra_attr  (list/tuple)  : A list or tuple of extra attributes to get from the config file
            keep_alive  (bool)        : If True then request a persistent connection with the host

        """
        if not os.path.exists(config_file):
            raise IOError, 'Config file %s does not exists' % config_file

        config = ConfigParser.ConfigParser()
        config.read(config_file)
        
        self.hostname = config.get('Default', 'hostname')
        self.username = config.get('Default', 'username')
        self.password = config.get('Default', 'password')
        self.timeout  = int(config.get('Default', 'timeout'))
        self.cachettl = int(config.get('Default', 'cachettl'))
        self.viserver = VIServer()
        self.lockdir  = lockdir
        self.lockfile = os.path.join(self.lockdir, self.hostname)
        self.ignore_locks = ignore_locks
        self.keep_alive = keep_alive

        self.mors_cache = {
            'HostSystem': {
                'objects': {},
                'last_updated': 0,
                },
            'Datastore': {
                'objects': {},
                'last_updated': 0,
                }
            }
        
        # load any extra attributes from the config file
        if extra_attr and isinstance(extra_attr, (list, tuple)):
            for eachAttr in extra_attr:
                setattr(self, eachAttr, config.get('Default', eachAttr))
        
        if not os.path.exists(self.lockdir):
            os.mkdir(self.lockdir)

    def connect(self):
        """
        Connect to a VMware vSphere server.

        Raises:
             VPollerException
        
        """
        if not self.ignore_locks:
            if os.path.exists(self.lockfile):
                logging.error('Lock file exists for vSphere host %s, aborting ...', self.hostname)
                raise VConnectorException, 'Lock file exists for %s' % self.hostname
            else:
                # create a lock file
                with open(self.lockfile, 'w') as lockfile:
                    lockfile.write(str(os.getpid()))

        logging.info('Connecting to vSphere host %s', self.hostname)
        self.viserver.connect(host=self.hostname, user=self.username, password=self.password, sock_timeout=self.timeout)

        # do we want to keep persistent connection to the host
        if self.keep_alive:
            self.viserver.keep_session_alive()
        
    def disconnect(self):
        """
        Disconnect from a VMware vSphere server.

        """
        if not self.viserver.is_connected():
            logging.info('No need to disconnect from %s, as we are not connected at all', self.hostname)
            return
        
        logging.info('Disconnecting from vSphere host %s', self.hostname)
        self.viserver.disconnect()

        if not self.ignore_locks:
            os.unlink(self.lockfile)

    def reconnect(self):
        """
        Reconnect to the VMware vSphere server
        """
        self.disconnect()
        self.connect()

    def mors_cache_needs_update(self, last_update):
        """
        Checks whether a MOR cache is out-of-date.

        Returns:
            True if the cache is out-of-date, False otherwise.

        """
        now = time()

        if (now - last_update) > (self.cachettl * 60):
            return True

        return False
        
    def update_host_mors(self):
        """
        Updates the HostSystem MORs cache

        """
        if not self.mors_cache_needs_update(self.mors_cache['HostSystem']['last_updated']):
            return

        logging.info('Updating HostSystem MORs cache')

        mors = {v:k for k, v in self.viserver.get_hosts().items()}

        self.mors_cache['HostSystem']['objects'].update(mors)
        self.mors_cache['HostSystem']['last_updated'] = time()

    def update_datastore_mors(self):
        """
        Updates the Datastore MORs cache

        """
        if not self.mors_cache_needs_update(self.mors_cache['Datastore']['last_updated']):
            return

        logging.info('Updating Datastore MORs cache')
        
        result = self.viserver._retrieve_properties_traversal(property_names=['info.url'],
                                                              obj_type=MORTypes.Datastore)
        
        mors = {p.Val:item.Obj for item in result for p in item.PropSet}

        self.mors_cache['Datastore']['objects'].update(mors)
        self.mors_cache['Datastore']['last_updated'] = time()

