from twisted.internet import reactor, defer
from twisted.web.client import HTTPConnectionPool
from twisted.web.error import Error
from Crypto.Hash import SHA
from Crypto.Cipher import AES
from Crypto import Random
import bz2
import base64
import hmac
import hashlib
import urllib
import httplib
import json
from renat import httpclient

class WebClient(object):
    
    def __init__(self, server, secret, proxy_host=None, proxy_port=80):
        self.server = server
        self.encryption_key = _make_key(secret)
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.pool = HTTPConnectionPool(reactor, persistent=True)
        self.pool.maxPersistentPerHost = 1024
    
    def close(self):
        return self.pool.closeCachedConnections()
    
   
    def put(self, key, value):
        """
        Store new key-value pair.
        @return deferred new version
        """
        key = encrypt_key(self.encryption_key, key)
        value = encrypt_value(self.encryption_key, value)
        d = self._post_request(key, "JUNGEST", value)
        d.addCallback(lambda r:r["record_version"])
        return d
    
    
    def get(self, key, version, wait=False):
        """
        Returns the value for the given key and version.
        If `wait` is `True` then we wait for the key & version
        to be stored. The deferred can be canceled.
        """
        d = self._get(key, version, wait)
        d.addCallback(lambda r:r["value"])
        return d
                    

    def get_jungest(self, key, wait=False):
        d = self._get(key, "JUNGEST", wait)
        d.addCallback(lambda r:(r["record_version"], r["value"]))
        return d
    

    def get_oldest(self, key, wait=False):
        d = self._get(key, "OLDEST", wait)
        d.addCallback(lambda r:(r["record_version"], r["value"]))
        return d
    
    def _url(self, record_id, record_version):
        record_version = str(record_version)
        url = "{base}/rec/{id}/{version}".format(
                    base=self.server,
                    id=urllib.quote(record_id, ''), 
                    version=urllib.quote(record_version, ''))
        return url


    def _get(self, key, version, wait=False):
        
        def make_request():
            d = self._get_request(record_id, version, timeout = timeout)
            d.addCallbacks(got_response, got_failure)
            return d
        
        def got_response(response):
            if "value" in response:
                response["value"] = decrypt_value(self.encryption_key, response["value"])
            return response
        
        def got_failure(failure):
            if failure.check(Error) and wait and failure.value.status == httplib.NOT_FOUND:
                return make_request()
            else:
                return failure
        
        record_id = encrypt_key(self.encryption_key, key)
        timeout = 60 if wait else None
        return make_request()


    def _get_request(self, record_id, record_version, timeout=None): 
        url = self._url(record_id, record_version)
        if timeout:
            values = {'timeout': str(timeout)}
        else:
            values = {}
        d = httpclient.request("GET", url, values, 
                    pool=self.pool, proxy_host=self.proxy_host, proxy_port=self.proxy_port)
        d.addCallback(json.loads)
        return d
        

    def _post_request(self, record_id, record_version, value):
        idepo = get_random_string()
        url = self._url(record_id, record_version)
        d = httpclient.request("POST", url, {"idepo":idepo, "data":value}, {"Content-Type":["application/x-www-form-urlencoded"]},
                    pool=self.pool, proxy_host=self.proxy_host, proxy_port=self.proxy_port)
        d.addCallback(json.loads)
        return d


def encrypt_key(key, plaintext):
    return hmac.new(key, plaintext, hashlib.sha1).hexdigest()

def get_random_string():
    binary = Random.get_random_bytes(8)
    return base64.b64encode(binary)

def encrypt_value(key, plaintext):
    compressed = bz2.compress(plaintext)
    
    digest = SHA.new(compressed).digest()
    
    unpadded = compressed + digest
    padding = _make_padding(unpadded, AES.block_size)
    padded = unpadded + padding
    
    iv = Random.get_random_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    ciphertext = cipher.encrypt(padded)
    binary = iv + ciphertext
    return base64.b64encode(binary)

def decrypt_value(key, data):
    
    binary = base64.b64decode(data)
    
    if len(binary) < AES.block_size:
        raise ValueError("decryption failed, Invalid format.")
    iv = binary[:AES.block_size]
    ciphertext = binary[AES.block_size:]
    if len(ciphertext) % AES.block_size != 0:
        raise ValueError("decryption failed, Invalid format.")
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = cipher.decrypt(ciphertext)
    if len(padded) <= 0:
        raise ValueError("decryption failed, Invalid format.")
    
    padding_length = ord(padded[-1])
    if len(padded) < padding_length:
        raise ValueError("decryption failed, Invalid format.")
    unpadded = padded[:-padding_length]
    
    if len(unpadded) < SHA.digest_size:
        raise ValueError("decryption failed, Invalid format.")
    digest_msg = unpadded[-SHA.digest_size:]
    compressed = unpadded[:-SHA.digest_size]
    
    digest_real = SHA.new(compressed).digest()
    
    if digest_msg != digest_real:
        raise ValueError("decryption failed, Invalid password or corrupted data.")
    
    plaintext = bz2.decompress(compressed)
    return plaintext

def _make_key(secret):
    return SHA.new(secret).digest()[:16]
    
def _make_padding(data, block_size):
    data_size = len(data)
    block_count = data_size / block_size + 1
    total_size = block_count * block_size
    pad_size = total_size - data_size
    return chr(pad_size) * pad_size
