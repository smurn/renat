import unittest
from Crypto import Random
from renat import webclient
from utwist import with_reactor
from twisted.internet import defer

key = "x"*16

class TestWebClientIntegration(unittest.TestCase):
    
    def setUp(self):
        # each test uses a different secret. That way the tests 
        # don't interfer with each other, even when they use the same keys.
        secret = Random.get_random_bytes(64)
        self.client = webclient.WebClient("http://localhost:8888", secret)
    
    @with_reactor
    @defer.inlineCallbacks
    def _test_put(self):
        version = yield self.client.put("mykey", "myvalue")
        
    @with_reactor
    @defer.inlineCallbacks
    def test_get(self):
        version = yield self.client.put("mykey", "myvalue")
        actual = yield self.client.get("mykey", version)
        self.assertEqual("myvalue", actual)

    @with_reactor
    @defer.inlineCallbacks
    def _test_get_jungest(self):
        yield self.client.put("mykey", "myvalue1")
        yield self.client.put("mykey", "myvalue2")
        actual = yield self.client.get_jungest("mykey")
        self.assertEqual("myvalue2", actual)

    @with_reactor
    @defer.inlineCallbacks
    def _test_get_oldest(self):
        yield self.client.put("mykey", "myvalue1")
        yield self.client.put("mykey", "myvalue2")
        actual = yield self.client.get_oldest("mykey")
        self.assertEqual("myvalue1", actual)


class TestWebClient(unittest.TestCase):

    def test_no_plain_in_cipher(self):
        plain = "Hello World!"
        cipher = webclient.encrypt_value(key, plain)
        self.assertFalse(plain in cipher)

    def test_decrypt(self):
        plain = "Hello World!"
        cipher = webclient.encrypt_value(key, plain)
        plain_decrypted = webclient.decrypt_value(key, cipher)
        self.assertEqual(plain, plain_decrypted)
        
    def test_decrypt_wrong_pass(self):
        plain = "Hello World!"
        cipher = webclient.encrypt_value(key, plain)
        self.assertRaises(ValueError, webclient.decrypt_value, "y"*16, cipher)
        
    def test_decrypt_tampered(self):
        plain = "Hello World!"
        cipher = webclient.encrypt_value(key, plain)
        pos = len(cipher)/2
        replace_by = "x" if  cipher[pos] != "x" else "y"
        cipher = cipher[:pos] + replace_by + cipher[pos+1:]
        self.assertRaises(ValueError, webclient.decrypt_value, key, cipher)
        
    def test_random(self):
        plain = "Hello World!"
        cipher1 = webclient.encrypt_value(key, plain)
        cipher2 = webclient.encrypt_value(key, plain)
        self.assertNotEqual(cipher1, cipher2)
        
    def test_encrypt_key_equal(self):
        plain = "Hello World!"
        cipher1 = webclient.encrypt_key(key, plain)
        cipher2 = webclient.encrypt_key(key, plain)
        self.assertEqual(cipher1, cipher2)
        