# Copyright (c) 2013 Marin Atanasov Nikolov <dnaeon@gmail.com>
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

It's purpose is to provide the basic primitives and interfaces required for
connecting and disconnecting from a VMware vCenter server, thus allowing it to
serve as a base for extending it and integrating it into other tools, e.g. VMware pollers.
"""

import os
import logging
import ConfigParser
from pysphere import VIServer

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
            keep_alive  (bool)        : If True then request a persistent connection with the vCenter

        """
        if not os.path.exists(config_file):
            raise IOError, 'Config file %s does not exists' % config_file

        config = ConfigParser.ConfigParser()
        config.read(config_file)
        
        self.vcenter  = config.get('Default', 'vcenter')
        self.username = config.get('Default', 'username')
        self.password = config.get('Default', 'password')
        self.timeout  = int(config.get('Default', 'timeout'))
        self.viserver = VIServer()
        self.lockdir  = lockdir
        self.lockfile = os.path.join(self.lockdir, self.vcenter)
        self.ignore_locks = ignore_locks
        self.keep_alive = keep_alive

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
                logging.error('Lock file exists for vCenter %s, aborting ...', self.vcenter)
                raise VConnectorException, 'Lock file exists for %s' % self.vcenter
            else:
                # create a lock file
                with open(self.lockfile, 'w') as lockfile:
                    lockfile.write(str(os.getpid()))

        logging.info('Connecting to vSphere host %s', self.vcenter)
        self.viserver.connect(host=self.vcenter, user=self.username, password=self.password, sock_timeout=self.timeout)

        # do we want to keep persistent connection to the vCenter
        if self.keep_alive:
            self.viserver.keep_session_alive()
        
    def disconnect(self):
        """
        Disconnect from a VMware vSphere server.

        """
        if not self.viserver.is_connected():
            logging.info('No need to disconnect from %s, as we are not connected at all', self.vcenter)
            return
        
        logging.info('Disconnecting from vSphere host %s', self.vcenter)
        self.viserver.disconnect()

        if not self.ignore_locks:
            os.unlink(self.lockfile)

    def reconnect(self):
        """
        Reconnect to the VMware vSphere server
        """
        self.disconnect()
        self.connect()
