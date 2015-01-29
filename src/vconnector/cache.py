# Copyright (c) 2015 Marin Atanasov Nikolov <dnaeon@gmail.com>
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
The vConnector caching module

"""

import logging

from time import time
from collections import OrderedDict

from pyVmomi import vim
from vconnector.exceptions import CacheException

__all__ = ['CachedObject', 'CacheInventory']


class CachedObject(object):
    def __init__(self, name, obj, ttl=300):
        """
        Initializes a new cached object

        Args:
            name               (str): Human readable name for the cached entry
            obj  (vim.ManagedEntity): A managed object to store in the cache
            ttl                (int): The TTL in seconds for the cached object

        Raises:
            CacheException

        """
        if not isinstance(obj, vim.ManagedEntity):
            raise CacheException('Need a vim.ManagedEntity instance to cache')

        self.name = name
        self.obj = obj
        self.ttl = ttl
        self.timestamp = time()

class CacheInventory(object):
    """
    Inventory for cached objects

    """
    def __init__(self, maxsize=0):
        """
        Initializes a new cache inventory

        Args:
            maxsize (int): Upperbound limit on the number of items that
                           will be stored in the cache inventory

        """
        if maxsize < 0:
            raise CacheException('Cache inventory size cannot be negative')

        self._cache = OrderedDict()
        self.maxsize = maxsize

    def __len__(self):
        return len(self._cache)

    def __contains__(self, key):
        if key not in self._cache:
            return False

        item = self._cache[key]
        if self._has_expired(item):
            return False
        return True

    def _has_expired(self, item):
        """
        Checks if a cached item has expired and removes it if needed

        If the upperbound limit has been reached then the last item
        is being removed from the inventory.

        Args:
            item (CachedObject): A cached object to lookup

        """
        if time() > item.timestamp + item.ttl:
            logging.debug(
                'Object %s has expired and will be removed from cache',
                item.name
            )
            self._cache.pop(item.name)
            return True
        return False

    def add(self, obj):
        """
        Add an item to the cache inventory

        Args:
            obj (CachedObject): A CachedObject instance to be added

        Raises:
            CacheException

        """
        if not isinstance(obj, CachedObject):
            raise Exception('Need a CachedObject instance to put in the cache')

        if self.maxsize > 0 and len(self._cache) == self.maxsize:
            popped = self._cache.popitem(last=False)
            logging.debug('Cache maxsize reached, removing %s', popped.name)

        logging.debug('Caching object %s [ttl: %d seconds]', obj.name, obj.ttl)
        self._cache[obj.name] = obj

    def get(self, key):
        """
        Retrieve an object from the cache inventory

        Args:
            key (str): Name of the cache item to retrieve

        Returns:
            The cached object if found, None otherwise

        """
        if key not in self._cache:
            return None

        item = self._cache[key]
        if self._has_expired(item):
            return None
        return item.obj

