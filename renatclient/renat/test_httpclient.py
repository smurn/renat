'''
Created on Aug 26, 2014

@author: stefan
'''
from twisted.trial import unittest

from renat import httpclient
from twisted.internet import reactor, defer

class Test(unittest.TestCase):



    def testName(self):
        def out(data):
            print data
            
        d = httpclient.get("http://www.google.ch/");
        d.addCallback(out)
        return d
        

