# Copyright (c) 2013-2015 Marin Atanasov Nikolov <dnaeon@gmail.com>
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
VMware vSphere Connector Module for Python

This module provides classes and methods for managing 
connections to VMware vSphere hosts and retrieving of
object properties.

"""

import ssl
import logging
import sqlite3

import pyVmomi
import pyVim.connect

from vconnector.cache import CachedObject
from vconnector.cache import CacheInventory
from vconnector.exceptions import VConnectorException

__all__ = ['VConnector', 'VConnectorDatabase']


class VConnector(object):
    """
    VConnector class

    The VConnector class defines methods for connecting,
    disconnecting and retrieving of objects from a
    VMware vSphere host.

    Returns:
        VConnector object
    
    Raises:
        VConnectorException

    """
    def __init__(self,
                 user,
                 pwd,
                 host,
                 ssl_context=None,
                 cache_maxsize=0,
                 cache_enabled=False,
                 cache_ttl=300,
                 cache_housekeeping=0
    ):
        """
        Initializes a new VConnector object

        Args:
            user                     (str): Username to use when connecting
            pwd                      (str): Password to use when connecting
            host                     (str): VMware vSphere host to connect to
            ssl_context   (ssl.SSLContext): SSL context to use for the connection
            cache_maxsize            (int): Upperbound limit on the number of
                                            items that will be stored in the cache
            cache_enabled           (bool): If True use an expiring cache for the
                                            managed objects
            cache_ttl                (int): Time in seconds after which a
                                            cached object is considered as expired
            cache_housekeeping       (int): Time in minutes to perform periodic
                                            cache housekeeping

        """
        self.user = user
        self.pwd  = pwd
        self.host = host

        self.ssl_context = None
        if not ssl_context:
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                # Legacy Python that doesn't verify HTTPS certificates by default
                pass
            else:
                # Handle target environment that doesn't support HTTPS verification
                self.ssl_context = _create_unverified_https_context()
        else:
            self.ssl_context = ssl_context

        self._si  = None
        self._perf_counter = None
        self._perf_interval = None
        self.cache_maxsize = cache_maxsize
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.cache_housekeeping = cache_housekeeping
        self.cache = CacheInventory(
            maxsize=self.cache_maxsize,
            housekeeping=self.cache_housekeeping
        )

    @property
    def si(self):
        if not self._si:
            self.connect()
        if not self._si.content.sessionManager.currentSession:
            logging.warning(
                '[%s] Lost connection to vSphere host, trying to reconnect',
                self.host
            )
            self.connect()
        return self._si

    @property
    def perf_counter(self):
        if not self._perf_counter:
            self._perf_counter = self.si.content.perfManager.perfCounter
        return self._perf_counter

    @property
    def perf_interval(self):
        if not self._perf_interval:
            self._perf_interval = self.si.content.perfManager.historicalInterval
        return self._perf_interval

    def connect(self):
        """
        Connect to the VMware vSphere host

        Raises:
             VConnectorException
        
        """
        logging.info('Connecting vSphere Agent to %s', self.host)
        
        try:
            self._si = pyVim.connect.SmartConnect(
                host=self.host,
                user=self.user,
                pwd=self.pwd,
                sslContext=self.ssl_context,
            )
        except Exception as e:
            # TODO: Maybe retry connection after some time
            # before we finally give up on this vSphere host
            logging.error('Cannot connect to %s: %s', self.host, e)
            raise

    def disconnect(self):
        """
        Disconnect from the VMware vSphere host

        """
        if not self._si:
            return

        logging.info('Disconnecting vSphere Agent from %s', self.host)
        pyVim.connect.Disconnect(self.si)

    def reconnect(self):
        """
        Reconnect to the VMware vSphere host

        """
        self.disconnect()
        self.connect()

    def get_datacenter_view(self):
        """
        Get a view ref to all vim.Datacenter managed objects

        """
        return self.get_container_view(
            obj_type=[pyVmomi.vim.Datacenter]
        )

    def get_cluster_view(self):
        """
        Get a view ref to all vim.ClusterComputeResource managed objects

        """
        return self.get_container_view(
            obj_type=[pyVmomi.vim.ClusterComputeResource]
        )

    def get_host_view(self):
        """
        Get a view ref to all vim.HostSystem managed objects

        """
        return self.get_container_view(
            obj_type=[pyVmomi.vim.HostSystem]
        )

    def get_vm_view(self):
        """
        Get a view ref to all vim.VirtualMachine managed objects

        """
        return self.get_container_view(
            obj_type=[pyVmomi.vim.VirtualMachine]
        )

    def get_datastore_view(self):
        """
        Get a view ref to all vim.Datastore managed objects

        """
        return self.get_container_view(
            obj_type=[pyVmomi.vim.Datastore]
        )

    def get_resource_pool_view(self):
        """
        Get a view ref to all vim.ResourcePool managed objects

        """
        return self.get_container_view(
            obj_type=[pyVmomi.vim.ResourcePool]
        )

    def get_distributed_vswitch_view(self):
        """
        Get a view ref to all vim.DistributedVirtualSwitch managed objects

        """
        return self.get_container_view(
            obj_type=[pyVmomi.vim.DistributedVirtualSwitch]
        )

    def collect_properties(self,
                           view_ref,
                           obj_type,
                           path_set=[],
                           include_mors=False):
        """
        Collect properties for managed objects from a view ref

        Check the vSphere API documentation for example on
        retrieving object properties:
    
            - http://pubs.vmware.com/vsphere-50/index.jsp#com.vmware.wssdk.pg.doc_50/PG_Ch5_PropertyCollector.7.2.html

        Args:
            view_ref (pyVmomi.vim.view.*): Starting point of inventory navigation
            obj_type      (pyVmomi.vim.*): Type of managed object
            path_set               (list): List of properties to retrieve
            include_mors           (bool): If True include the managed objects refs in the result

        Returns:
            A list of properties for the managed objects

        """
        collector = self.si.content.propertyCollector

        logging.debug(
            '[%s] Collecting properties for %s managed objects',
            self.host,
            obj_type.__name__
        )

        # Create object specification to define the starting point of
        # inventory navigation
        obj_spec = pyVmomi.vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.obj = view_ref
        obj_spec.skip = True

        # Create a traversal specification to identify the
        # path for collection
        traversal_spec = pyVmomi.vmodl.query.PropertyCollector.TraversalSpec()
        traversal_spec.name = 'traverseEntities'
        traversal_spec.path = 'view'
        traversal_spec.skip = False
        traversal_spec.type = view_ref.__class__
        obj_spec.selectSet = [traversal_spec]

        # Identify the properties to the retrieved
        property_spec = pyVmomi.vmodl.query.PropertyCollector.PropertySpec()
        property_spec.type = obj_type
                
        if not path_set:
            logging.warning(
                '[%s] Retrieving all properties for objects, this might take a while...',
                self.host
            )
            property_spec.all = True
            
        property_spec.pathSet = path_set

        # Add the object and property specification to the
        # property filter specification
        filter_spec = pyVmomi.vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = [obj_spec]
        filter_spec.propSet = [property_spec]

        # Retrieve properties
        props = collector.RetrieveContents([filter_spec])

        data = []
        for obj in props:
            properties = {}
            for prop in obj.propSet:
                properties[prop.name] = prop.val

            if include_mors:
                properties['obj'] = obj.obj

            data.append(properties)

        return data

    def get_container_view(self, obj_type, container=None):
        """
        Get a vSphere Container View reference to all
        objects of type 'obj_type'

        It is up to the caller to take care of destroying the View
        when no longer needed.

        Args:
            obj_type               (list): A list of managed object types
            container (vim.ManagedEntity): Starting point of inventory search

        Returns:
            A container view ref to the discovered managed objects

        """
        if not container:
            container = self.si.content.rootFolder

        logging.debug(
            '[%s] Getting container view ref to %s managed objects',
            self.host,
            [t.__name__ for t in obj_type]
        )

        view_ref = self.si.content.viewManager.CreateContainerView(
            container=container,
            type=obj_type,
            recursive=True
        )

        return view_ref

    def get_list_view(self, obj):
        """
        Get a vSphere List View reference 

        It is up to the caller to take care of destroying the View
        when no longer needed.

        Args:
            obj (list): A list of managed object to include in the View

        Returns:
            A list view ref to the managed objects
        
        """
        view_ref = self.si.content.viewManager.CreateListView(obj=obj)

        logging.debug(
            '[%s] Getting list view ref for %s objects',
            self.host,
            [o.name for o in obj]
        )

        return view_ref

    def get_object_by_property(self, property_name, property_value, obj_type):
        """
        Find a Managed Object by a propery

        If cache is enabled then we search for the managed object from the
        cache first and if present we return the object from cache.

        Args:
            property_name            (str): Name of the property to look for
            property_value           (str): Value of the property to match 
            obj_type       (pyVmomi.vim.*): Type of the Managed Object

        Returns:
            The first matching object
    
        """
        if not issubclass(obj_type, pyVmomi.vim.ManagedEntity):
            raise VConnectorException('Type should be a subclass of vim.ManagedEntity')

        if self.cache_enabled:
            cached_obj_name = '{}:{}'.format(obj_type.__name__, property_value)
            if cached_obj_name in self.cache:
                logging.debug('Using cached object %s', cached_obj_name)
                return self.cache.get(cached_obj_name)

        view_ref = self.get_container_view(obj_type=[obj_type])
        props = self.collect_properties(
            view_ref=view_ref,
            obj_type=obj_type,
            path_set=[property_name],
            include_mors=True
        )
        view_ref.DestroyView()

        obj = None
        for each_obj in props:
            if each_obj[property_name] == property_value:
                obj = each_obj['obj']
                break

        if self.cache_enabled:
            cached_obj = CachedObject(
                name=cached_obj_name,
                obj=obj,
                ttl=self.cache_ttl
            )
            self.cache.add(obj=cached_obj)

        return obj

class VConnectorDatabase(object):
    """
    VConnectorDatabase class

    Provides an SQLite database backend for storing information
    about vSphere Agents, such as hostname, username, password, etc.
    
    Returns:
        VConnectorDatabase object
    
    Raises:
        VConnectorException

    """
    def __init__(self, db):
        """
        Initializes a new VConnectorDatabase object

        Args:
            db (str): Path to the SQLite database file

        """
        self.db = db
        self.conn = sqlite3.connect(self.db)

    def init_db(self):
        """
        Initializes the vConnector Database backend

        """
        logging.info('Initializing vConnector database at %s', self.db)

        self.cursor = self.conn.cursor()

        sql = """
        CREATE TABLE hosts (
            host TEXT UNIQUE,
            user TEXT,
            pwd  TEXT,
            enabled INTEGER
        )
        """

        try:
            self.cursor.execute(sql)
        except sqlite3.OperationalError as e:
            raise VConnectorException('Cannot initialize database: {}'.format(e.message))

        self.conn.commit()
        self.cursor.close()

    def add_update_agent(self, host, user, pwd, enabled=0):
        """
        Add/update a vSphere Agent in the vConnector database

        Args:
            host    (str): Hostname of the vSphere host
            user    (str): Username to use when connecting
            pwd     (str): Password to use when connecting
            enabled (int): If True mark this vSphere Agent as enabled

        """
        logging.info(
            'Adding/updating vSphere Agent %s in database',
            host
        )

        self.cursor = self.conn.cursor()
        self.cursor.execute(
            'INSERT OR REPLACE INTO hosts VALUES (?,?,?,?)',
            (host, user, pwd, enabled)
        )
        self.conn.commit()
        self.cursor.close()

    def remove_agent(self, host):
        """
        Remove a vSphere Agent from the vConnector database

        Args:
            host (str): Hostname of the vSphere Agent to remove
        
        """
        logging.info('Removing vSphere Agent %s from database', host)

        self.cursor = self.conn.cursor()
        self.cursor.execute(
            'DELETE FROM hosts WHERE host = ?',
            (host,)
        )
        self.conn.commit()
        self.cursor.close()

    def get_agents(self, only_enabled=False):
        """
        Get the vSphere Agents from the vConnector database

        Args:
            only_enabled (bool): If True return only the Agents which are enabled

        """
        logging.debug('Getting vSphere Agents from database')

        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        if only_enabled:
            sql = 'SELECT * FROM hosts WHERE enabled = 1'
        else:
            sql = 'SELECT * FROM hosts'

        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        self.cursor.close()

        return result

    def enable_agent(self, host):
        """
        Mark a vSphere Agent as enabled

        Args:
            host (str): Hostname of the vSphere Agent to enable

        """
        logging.info('Enabling vSphere Agent %s', host)

        self.cursor = self.conn.cursor()
        self.cursor.execute(
            'UPDATE hosts SET enabled = 1 WHERE host = ?',
            (host,)
        )
        self.conn.commit()
        self.cursor.close()
        
    def disable_agent(self, host):
        """
        Mark a vSphere Agent as disabled

        Args:
            host (str): Hostname of the vSphere Agent to disable

        """
        logging.info('Disabling vSphere Agent %s', host)

        self.cursor = self.conn.cursor()
        self.cursor.execute(
            'UPDATE hosts SET enabled = 0 WHERE host = ?',
            (host,)
        )
        self.conn.commit()
        self.cursor.close()
