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
import threading

from time import time
from collections import OrderedDict, namedtuple

from vconnector.exceptions import CacheException

__all__ = ['CachedObject', 'CacheInventory']

_CachedObjectInfo = namedtuple('CachedObjectInfo', ['name', 'hits', 'ttl', 'timestamp'])


class CachedObject(object):
    def __init__(self, name, obj, ttl):
        """
        Initializes a new cached object

        Args:
            name               (str): Human readable name for the cached entry
            obj               (type): Object to be cached
            ttl                (int): The TTL in seconds for the cached object

        """
        self.hits = 0
        self.name = name
        self.obj = obj
        self.ttl = ttl
        self.timestamp = time()

class CacheInventory(object):
    """
    Inventory for cached objects

    """
    def __init__(self, maxsize=0, housekeeping=0):
        """
        Initializes a new cache inventory

        Args:
            maxsize      (int): Upperbound limit on the number of items
                                that will be stored in the cache inventory
            housekeeping (int): Time in minutes to perform periodic
                                cache housekeeping

        Raises:
            CacheException

        """
        if maxsize < 0:
            raise CacheException('Cache inventory size cannot be negative')

        if housekeeping < 0:
            raise CacheException('Cache housekeeping period cannot be negative')

        self._cache = OrderedDict()
        self.maxsize = maxsize
        self.housekeeping = housekeeping * 60.0
        self.lock = threading.RLock()
        self._schedule_housekeeper()

    def __len__(self):
        with self.lock:
            return len(self._cache)

    def __contains__(self, key):
        with self.lock:
            if key not in self._cache:
                return False

            item = self._cache[key]
            return not self._has_expired(item)

    def _has_expired(self, item):
        """
        Checks if a cached item has expired and removes it if needed

        Args:
            item (CachedObject): A cached object to lookup

        Returns:
            bool: True if the item has expired, False otherwise

        """
        with self.lock:
            if time() > item.timestamp + item.ttl:
                logging.debug(
                    'Object %s has expired and will be removed from cache',
                    self.info(item.name)
                )
                self._cache.pop(item.name)
                return True
            return False

    def _schedule_housekeeper(self):
        """
        Schedules the next run of the housekeeper

        """
        if self.housekeeping > 0:
            t = threading.Timer(
                interval=self.housekeeping,
                function=self._housekeeper
            )
            t.setDaemon(True)
            t.start()

    def _housekeeper(self):
        """
        Remove expired entries from the cache on regular basis

        """
        with self.lock:
            expired = 0
            logging.info(
                'Starting cache housekeeper [%d item(s) in cache]',
                len(self._cache)
            )

            items = list(self._cache.values())
            for item in items:
                if self._has_expired(item):
                    expired += 1

            logging.info(
                'Cache housekeeper completed [%d item(s) removed from cache]',
                expired
            )
            self._schedule_housekeeper()

    def add(self, obj):
        """
        Add an item to the cache inventory

        If the upperbound limit has been reached then the last item
        is being removed from the inventory.

        Args:
            obj (CachedObject): A CachedObject instance to be added

        Raises:
            CacheException

        """
        if not isinstance(obj, CachedObject):
            raise CacheException('Need a CachedObject instance to add in the cache')

        with self.lock:
            if 0 < self.maxsize == len(self._cache):
                popped = self._cache.popitem(last=False)
                logging.debug(
                    'Cache maxsize reached, removing %s',
                    self.info(name=popped.name)
                )

            self._cache[obj.name] = obj
            logging.debug('Adding object to cache %s', self.info(name=obj.name))

    def get(self, name):
        """
        Retrieve an object from the cache inventory

        Args:
            name (str): Name of the cache item to retrieve

        Returns:
            The cached object if found, None otherwise

        """
        with self.lock:
            if name not in self._cache:
                return None

            item = self._cache[name]
            if self._has_expired(item):
                return None

            item.hits += 1
            logging.debug(
                'Returning object from cache %s',
                self.info(name=item.name)
            )

            return item.obj

    def clear(self):
        """
        Remove all items from the cache

        """
        with self.lock:
            self._cache.clear()

    def info(self, name):
        """
        Get statistics about a cached object

        Args:
            name (str): Name of the cached object

        """
        with self.lock:
            if name not in self._cache:
                return None

            item = self._cache[name]
            return _CachedObjectInfo(item.name, item.hits, item.ttl, item.timestamp)
