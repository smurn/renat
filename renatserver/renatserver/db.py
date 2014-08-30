# Copyright (C) 2014 Stefan C. Mueller

import datetime
from renatserver import ddlist

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
        
        #: dict that maps `id` to the linked list of the record's version list (oldest to the left)
        self._versions = {}
        
        #: evict list. Oldest records are on the left.
        self._evict_list = ddlist.LinkedList()
        

    def get(self, record_id, record_version, now):
        """
        Returns the data of the requested record or `None`, if no such record is stored.
        Resets the eviction timer.
        """
        self._evict(now)
        key = (record_id, record_version)
        record = self._records.get(key, None)
        if record:
            self._touch(record, now)
            return record.data
        else:
            return None
        
    
    def oldest_version(self, record_id, now):
        """
        Returns the oldest version of the given record id, or `None` if there is none.
        Resets the eviction timer of that version.
        """
        self._evict(now)
        versions = self._versions.get(record_id, None)
        if versions:
            record = versions.get_leftmost()
            self._touch(record, now)
            return record.record_version
        else:
            return None
    
    
    def jungest_version(self, record_id, now, touch=True):
        """
        Returns the jungest version of the given record, or `None` if there is none.
        Resets the eviction timer of that version.
        """
        self._evict(now)
        
        versions = self._versions.get(record_id, None)
        if versions:
            record = versions.get_rightmost()
            if touch:
                self._touch(record, now)
            return record.record_version
        else:
            return None
    
    
    def put(self, record_id, idepo, data, now):
        """
        Adds a new version to the given record. Returns the version number.
        
        `idepo` must be a unique identifier for this put. If a put with
        the same idepo was made before, the version number for that entry is
        returned. This gives idepotent behaviour: Put can be called
        multiple times with the exact same arguments and the behaviour is the
        same as if it was called only once.
        """
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
        
        jungest_version = self.jungest_version(record_id, now, touch=False)
        if not jungest_version:
            jungest_version = 0
        
        record_version = jungest_version + 1
        
        record = self._Record(record_id, record_version, idepo, now, data)
        self._records[(record_id, record_version)] = record
        self._idepo[(record_id, idepo)] = record_version
        self._evict_list.append_right(record)

        version_list = self._versions.get(record_id, None)
        if not version_list:
            version_list = ddlist.LinkedList()
            self._versions[record_id] = version_list
        version_list.append_right(record)
       
        return record_version
        
        
    def touch(self, record_id, record_version, now):
        """
        Resets the eviction timer.
        """
        self._evict(now)
            
        record = self._records.get((record_id, record_version), None)
        if record:
            self._touch(record, now)
        else:
            return
    
    
    def _touch(self, record, now):
        """
        Resets the eviction timer.
        """
        record.time = now
        self._evict_list.remove(record)
        self._evict_list.append_right(record)
    
    
    def _evict(self, now):
        """
        Evict all record versions that are older than `self.eviction_time`
        """
        evict_older_than = now - self.eviction_time

        scheduled_for_eviction = []
        
        for record in self._evict_list:
            if record.time < evict_older_than:
                scheduled_for_eviction.append(record)
            else:
                break

        for record in scheduled_for_eviction:
            self._remove(record)

    def _remove(self, record):
        """
        Delete the record.
        """
        del self._records[(record.record_id, record.record_version)]
        del self._idepo[(record.record_id, record.idepo_nr)]
        
        self._evict_list.remove(record)
        
        version_list = self._versions[record.record_id]
        version_list.remove(record)
        if not version_list:
            del self._versions[record.record_id]


    class _Record(object):
        
        def __init__(self, record_id, record_version, idepo_nr, time, data):
            self.record_id = record_id
            self.record_version = record_version
            self.idepo_nr = idepo_nr
            self.time = time
            self.data = data
        def __repr__(self):
            return "Record(%s, %s, %s, %s, %s)" % (repr(self.record_id), repr(self.record_version),repr(self.idepo_nr), str(self.time), repr(self.data))
