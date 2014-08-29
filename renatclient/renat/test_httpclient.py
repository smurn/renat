'''
Created on Aug 26, 2014

@author: stefan
'''
import unittest
import utwist
from twisted.internet import defer

from renat import httpclient

class Test(unittest.TestCase):


    @utwist.with_reactor
    @defer.inlineCallbacks
    def test_get(self):
        def out(data):
            print data
            
        body = yield httpclient.request("GET", "http://www.python.org");
        self.assertTrue("<html" in body)
        
    @utwist.with_reactor
    @defer.inlineCallbacks
    def test_get_headers(self):
        def out(data):
            print data
            
        _, headers = yield httpclient.request("GET", "http://www.python.org", return_headers=True);
        self.assertTrue("Content-Type" in headers)
        


