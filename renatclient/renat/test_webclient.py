'''
Created on Aug 26, 2014

@author: stefan
'''
import unittest
from renat import webclient

class TestWebClient(unittest.TestCase):

    def test_no_plain_in_cipher(self):
        plain = "Hello World!"
        cipher = webclient.encrypt("abc", plain)
        self.assertFalse(plain in cipher)

    def test_decrypt(self):
        plain = "Hello World!"
        cipher = webclient.encrypt("abc", plain)
        plain_decrypted = webclient.decrypt("abc", cipher)
        self.assertEqual(plain, plain_decrypted)
        
    def test_decrypt_wrong_pass(self):
        plain = "Hello World!"
        cipher = webclient.encrypt("abc", plain)
        self.assertRaises(ValueError, webclient.decrypt, "123", cipher)
        
    def test_decrypt_tampered(self):
        plain = "Hello World!"
        cipher = webclient.encrypt("abc", plain)
        pos = len(cipher)/2
        cipher = cipher[:pos] + 'x' + cipher[pos+1:]
        self.assertRaises(ValueError, webclient.decrypt, "abc", cipher)
        
    def test_random(self):
        plain = "Hello World!"
        cipher1 = webclient.encrypt("abc", plain)
        cipher2 = webclient.encrypt("abc", plain)
        self.assertNotEqual(cipher1, cipher2)
        
    