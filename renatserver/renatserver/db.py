# Copyright (C) 2014 Stefan C. Mueller

import datetime

class InMemoryRecordDatabase(object):
    """
    A very simple in-memory key-value store.
    """
    
    def __init__(self, max_records=1024*1024, max_size=1024, max_id_size=64, eviction_time=None):
        """
        :param max_records: Maximal number of records that can be stored. 
          After that, the put operation will throw an exception.
          
        :param max_size: Maximal size of a single record.
          
        :param eviction_time: datetime.timedelta after which a record version is deleted
          if not accessed. Defaults to 5 minutes.
        """
        if not eviction_time:
            eviction_time = datetime.timedelta(seconds=300)
        self.eviction_time = eviction_time
        
        self.max_records = max_records
        
        self.max_size = max_size
        
        self.max_id_size = max_id_size
        
        #: dict that maps `(id,version)` to _Record
        self._records = {}
        
        #: dict that maps `(id,idepo)` to `version`
        self._idepo = {}
        
        #: dict that maps `id` to the entinel of the record's version list.
        self._versions = {}
        
        #: sentinel of the evict linked list
        self._evict_list = self._Record(None, None, None, None, None)
        self._evict_list.evict_next = self._evict_list
        self._evict_list.evict_prev = self._evict_list
        

    def get(self, record_id, record_version, now=None):
        """
        Returns the data of the requested record or `None`, if no such record is stored.
        Resets the eviction timer.
        """
        if not now:
            now = datetime.datetime.now()
        self._evict(now)
        
        key = (record_id, record_version)
        record = self._records.get(key, None)
        if record:
            self._touch(record, now)
            return record.data
        else:
            return None
        
    
    def oldest_version(self, record_id, now=None):
        """
        Returns the oldest version of the given record id, or `None` if there is none.
        Resets the eviction timer of that version.
        """
        if not now:
            now = datetime.datetime.now()
        self._evict(now)
        
        versions = self._versions.get(record_id, None)
        if versions:
            # if there is a sentinel, there is at least one version
            record = versions.version_next
            self._touch(record, now)
            return record.record_version
        else:
            return None
    
    
    def jungest_version(self, record_id, now=None):
        """
        Returns the jungest version of the given record, or `None` if there is none.
        Resets the eviction timer of that version.
        """
        if not now:
            now = datetime.datetime.now()
        self._evict(now)
        
        versions = self._versions.get(record_id, None)
        if versions:
            record = versions.version_prev
            self._touch(record, now)
            return record.record_version
        else:
            return None
    
    
    def put(self, record_id, idepo, data, now=None):
        """
        Adds a new version to the given record. Returns the version number.
        
        `idepo` must be a unique identifier for this put. If a put with
        the same idepo was made before, the version number for that entry is
        returned. This gives idepotent behaviour: Put can be called
        multiple times with the exact same arguments and the behaviour is the
        same as if it was called only once.
        """
        if not now:
            now = datetime.datetime.now()
        self._evict(now)
        
        if record_id is None:
            raise ValueError("record_id is none")
        if len(record_id) >= self.max_id_size:
            raise ValueError("record id too large.")
        
        if idepo is None:
            raise ValueError("idepo is none")
        if len(idepo) >= self.max_id_size:
            raise ValueError("data is none")
        
        if data is None:
            raise ValueError("data is none")
        if len(data) > self.max_size:
            raise ValueError("record too large.")
        
        if (record_id, idepo) in self._idepo:
            return self._idepo[(record_id, idepo)]
        
        if len(self._records) >= self.max_records:
            raise ValueError("Too many records stored. Please wait until some get evicted.")
        
        jungest_version = self.jungest_version(record_id)
        if not jungest_version:
            jungest_version = 0
        
        record_version = jungest_version + 1
        
        record = self._Record(record_id, record_version, idepo, now, data)
        self._records[(record_id, record_version)] = record
        self._idepo[(record_id, idepo)] = record_version
        
        record.evict_next = self._evict_list
        record.evict_prev = self._evict_list.evict_prev
        record.evict_prev.evict_next = record
        record.evict_next.evict_prev = record

        version_list = self._versions.get(record_id, None)
        if not version_list:
            version_list = self._Record(None, None, None, None, None)
            version_list.version_next = version_list
            version_list.version_prev = version_list
            self._versions[record_id] = version_list
            
        record.version_next = version_list
        record.version_prev = version_list.version_prev
        record.version_next.version_prev = record
        record.version_prev.version_next = record
       
        return record_version
        
    def touch(self, record_id, record_version, now=None):
        """
        Resets the eviction timer.
        """
        if not now:
            now = datetime.datetime.now()
        self._evict(now)
            
        record = self._records.get((record_id, record_version), None)
        if record:
            self._touch(record, now)
        else:
            return
    
    
    def _touch(self, record, now=None):
        """
        Resets the eviction timer.
        """
        record.time = now
        
        # remove from evict list
        record.evict_prev.evict_next = record.evict_next
        record.evict_next.evict_prev = record.evict_prev
        
        # insert to evict list
        record.evict_next = self._evict_list
        record.evict_prev = self._evict_list.evict_prev
        record.evict_prev.evict_next = record
        record.evict_next.evict_prev = record
    
    
    def _evict(self, now=None):
        """
        Evict all record versions that are older than `self.eviction_time`
        """
        evict_older_than = now - self.eviction_time

        record = self._evict_list.evict_next
        while record is not self._evict_list:
            next_record = record.evict_next # do this before removing. Pointers change
            if record.time < evict_older_than:
                self._remove(record)
            record = next_record


    def _remove(self, record):
        """
        Delete the record.
        """
        del self._records[(record.record_id, record.record_version)]
        del self._idepo[(record.record_id, record.idepo_nr)]
        
        record.evict_prev.evict_next = record.evict_next
        record.evict_next.prev = record.evict_prev
        record.evict_next = None
        record.evict_prev = None
        
        is_last_version = record.version_prev is record.version_next
        record.version_prev.version_next = record.version_next
        record.version_next.prev = record.version_prev
        record.version_next = None
        record.version_prev = None
        
        if is_last_version:
            del self._versions[record.record_id]


    class _Record(object):
        
        def __init__(self, record_id, record_version, idepo_nr, time, data):
            self.record_id = record_id
            self.record_version = record_version
            self.idepo_nr = idepo_nr
            self.time = time
            self.data = data
            self.evict_next = None
            self.evict_prev = None
            self.version_next = None
            self.version_prev = None
