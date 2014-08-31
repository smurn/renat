# Copyright (C) 2014 Stefan C. Mueller

import weakref
import datetime

import tornado.concurrent

class ASyncRecordDatabase(object):
    """
    Wrapper around a :class:`InMemoryRecordDatabase` (or a compatible object)
    that has the additional method :meth:`get_future`.
    This will only work if all put operations go through this wrapper instance;
    This will typically not work in a distributed system setup.
    """
    
    def __init__(self, db):
        self.db = db
        
        #: dict maps `(id, version)` to future (for get operations)
        #: we use a weakref here so that the entry is deleted
        #: when nobody has interest in the future anymore.
        self._get_futures = weakref.WeakValueDictionary()

        #: dict maps `(id)` to future (for oldest/jungest)
        #: we use a weakref here so that the entry is deleted
        #: when nobody has interest in the future anymore.
        self._limit_futures =  weakref.WeakValueDictionary()
        
        
    def get_future(self, record_id, record_version, now=None):
        """
        Works like the regular :meth:`get`
        but returns a future that will callback as soon as the record
        is available (which might be immediatly).
        """
        if not now:
            now = datetime.datetime.now()
        
        data = self.db.get(record_id, record_version, now)
        if data is not None:
            future = tornado.concurrent.Future()
            future.set_result(data)
        else:
            self.db.touch(record_id, record_version - 1, now)
            
            future = self._get_futures.get((record_id, record_version), None)
            if not future:
                future = tornado.concurrent.Future()
                self._get_futures[(record_id, record_version)] = future

        return future
    
    
    def oldest_version_future(self, record_id, now=None):
        if not now:
            now = datetime.datetime.now()
        record_version = self.db.oldest_version(record_id, now)
        return self._limit_future(record_id, record_version)
    
    
    def jungest_version_future(self, record_id, now=None):
        if not now:
            now = datetime.datetime.now()
        record_version = self.db.jungest_version(record_id, now)
        return self._limit_future(record_id, record_version)


    def put(self, record_id, idepo, data, now=None):
        if not now:
            now = datetime.datetime.now()
            
        record_version = self.db.put(record_id, idepo, data, now)
        
        get_future = self._get_futures.get((record_id, record_version), None)
        if get_future:
            get_future.set_result(data)
            del self._get_futures[(record_id, record_version)]
            
        limit_future = self._limit_futures.get(record_id, None)
        if limit_future:
            limit_future.set_result(record_version)
            del self._limit_futures[record_id]
            
        return record_version
    
    
    def get(self, record_id, record_version, now=None):
        return self.db.get(record_id, record_version, now)

    
    def oldest_version(self, record_id, now=None):
        return self.db.oldest_version(record_id, now)

    
    def jungest_version(self, record_id, now=None):
        return self.db.jungest_version(record_id, now)
    
    
    def touch(self, record_id, record_version, now=None):
        self.db.touch(record_id, record_version, now)
        

    def _limit_future(self, record_id, record_version):
        if record_version is not None:
            future = tornado.concurrent.Future()
            future.set_result(record_version)
        else:
            future = self._limit_futures.get(record_id, None)
            if not future:
                future = tornado.concurrent.Future()
                self._limit_futures[record_id] = future
        return future
                