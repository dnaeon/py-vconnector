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
The 'vmconnector' module defines classes and methods for establishing a 
connection to VMware vCenter and/or ESX servers.

It's goal is to provide the basic primitives and interface required for
connecting and disconnecting from a VMware vCenter server, thus allowing it to
serve as a base for extending it and integrating it into other tools, e.g. VMware pollers.
"""

import os
import syslog
import ConfigParser
import pysphere

class VMConnectorException(Exception):
    """
    Generic VMConnector exception.

    """
    pass

class VMConnector(object):
    """
    VMConnector class.

    The VMConnector class defines methods connecting and disconnecting from a
    VMware vCenter and/or VMware ESX servers.

    """
    def __init__(self, config, extra_attr=None):
        """
        Initializes a new VMConnector object.

        Args:
            config     (ConfigParser): A ConfigParser object containing the connection details
            extra_attr (list/tuple)  : A list or tuple of extra attributes to get from the config file

        """
        self.vcenter  = config.get('Default', 'vcenter')
        self.username = config.get('Default', 'username')
        self.password = config.get('Default', 'password')
        self.viserver = pysphere.VIServer()
        self.lockdir  = '/var/run/vm-connector'
        self.lockfile = os.path.join(self.lockdir, self.vcenter)

        # load extra attributes from the config file
        if extra_attr and isinstance(extra_attr, (list, tuple)):
            for eachAttr in extra_attr:
                setattr(self, eachAttr, config.get('Default', eachAttr))
        
        if not os.path.exists(self.lockdir):
            os.mkdir(self.lockdir)

    def connect(self, ignore_locks=False):
        """
        Connect to a VMware vCenter server.

        Args:
            ignore_locks (bool): Whether we ignore lock files or not
        
        Raises:
             VMPollerException
        
        """
        if not ignore_locks:
            if os.path.exists(self.lockfile):
                syslog.syslog('Lock file exists for vCenter %s, aborting ...' % self.vcenter)
                raise VMConnectorException, 'Lock file exists for %s' % self.vcenter

        syslog.syslog('Connecting to vCenter %s' % self.vcenter)

        # create a lock file
        with open(self.lockfile, 'w') as lockfile:
            lockfile.write(str(os.getpid()))
        
        self.viserver.connect(host=self.vcenter, user=self.username, password=self.password)
        
    def disconnect(self):
        """
        Disconnect from a VMware vCenter server.

        """
        if not self.viserver.is_connected():
            syslog.syslog('No need to disconnect from %s, as we are not connected at all' % self.vcenter)
            return
        
        syslog.syslog('Disconnecting from vCenter %s' % self.vcenter)
        os.unlink(self.lockfile)
        self.viserver.disconnect()

def load_config(path):
    """
    Parses a configuration file containing connection details to a vCenter server.

    Args:
        path (str): Path to the configuration file to parse

    Returns:
        ConfigParser object

    """
    if not os.path.exists(path):
        raise IOError, 'Config file %s does not exists' % path

    config = ConfigParser.ConfigParser()
    config.read(path)

    return config
