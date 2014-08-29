import unittest
from renat import webclient
from utwist import with_reactor
from twisted.internet import defer

key = "x"*16

class TestWebClientIntegration(unittest.TestCase):
    
    @with_reactor
    @defer.inlineCallbacks
    def test_put(self):
        client = webclient.WebClient("http://localhost:8888", 'foo')
        version = yield client.put("mykey", "myvalue")
        print version


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
        cipher = cipher[:pos] + 'x' + cipher[pos+1:]
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
        