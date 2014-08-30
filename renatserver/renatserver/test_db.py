'''
Created on Aug 29, 2014

@author: stefan
'''
import unittest
import datetime
from renatserver import db


class TestDB(unittest.TestCase):

    def setUp(self):
        self.target = db.InMemoryRecordDatabase()
        self.now = datetime.datetime.now() # not evicted at `later`. Evicted at `muchlater`
        self.later = self.now + datetime.timedelta(seconds=150)   # not evicted at `later`.not evicted at `muchlater`
        self.muchlater = self.now + datetime.timedelta(seconds=310)

    def test_put_get(self):
        version = self.target.put("key", "1", "value", self.now)
        actual = self.target.get("key", version, self.now)
        self.assertEqual("value", actual)
        
    def test_jungest_one(self):
        version = self.target.put("key", "1", "value", self.now)
        actual = self.target.jungest_version("key", self.now)
        self.assertEqual(version, actual)
        
    def test_oldest_one(self):
        version = self.target.put("key", "1", "value", self.now)
        actual = self.target.oldest_version("key", self.now)
        self.assertEqual(version, actual)

    def test_jungest_two(self):
        self.target.put("key", "1", "value1", self.now)
        version2 = self.target.put("key", "2", "value2", self.now)
        actual = self.target.jungest_version("key", self.now)
        self.assertEqual(version2, actual)
        
    def test_oldest_two(self):
        version1 = self.target.put("key", "1", "value1", self.now)
        self.target.put("key", "2", "value2", self.now)
        actual = self.target.oldest_version("key", self.now)
        self.assertEqual(version1, actual)
        
    def test_noevict(self):
        version = self.target.put("key", "1", "value", self.now)
        actual = self.target.get("key", version, self.later)
        self.assertEqual("value", actual)
        
    def test_evict(self):
        version = self.target.put("key", "1", "value", self.now)
        actual = self.target.get("key", version, self.muchlater)
        self.assertEqual(None, actual)
        
    def test_jungest_evict(self):
        self.target.put("key", "1", "value1", self.now)
        version2 = self.target.put("key", "2", "value2", self.later)
        actual = self.target.jungest_version("key", self.muchlater)
        self.assertEqual(version2, actual)
        
    def test_oldest_evict(self):
        self.target.put("key", "1", "value1", self.now)
        version2 = self.target.put("key", "2", "value2", self.later)
        actual = self.target.oldest_version("key", self.muchlater)
        self.assertEqual(version2, actual)