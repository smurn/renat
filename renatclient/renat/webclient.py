from twisted.internet import reactor
from twisted.web.client import HTTPConnectionPool
from Crypto.Hash import SHA
from Crypto.Cipher import AES
from Crypto import Random
import bz2
import urllib
from renat import httpclient

class WebClient(object):
    
    def __init__(self, server, secret, proxy_host=None, proxy_port=80):
        self.server = server
        self.secret = secret
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.pool = HTTPConnectionPool(reactor, persistent=True)
        self.pool.maxPersistentPerHost = 1024
    
    def put(self, key, value):
        return self._post(key, "JUNGEST", value)
        
    
    def _url(self, record_id, record_version):
        url = "{base}/rec/{id}/{version}".format(
                    base=self.server,
                    id=urllib.quote(record_id, ''), 
                    version=urllib.quote(record_version, ''))
        return url
    
    def _post(self, record_id, record_version, value):
        data = encrypt(self.secret, value)
        idepo = Random.get_random_bytes(8)
        url = self._url(record_id, record_version)
        return httpclient.post(url, {"idepo":idepo, "data":data}, self.pool, self.proxy_host, self.proxy_port)


def encrypt(secret, plaintext):
    compressed = bz2.compress(plaintext)
    
    digest = SHA.new(compressed).digest()
    
    unpadded = compressed + digest
    padding = make_padding(unpadded, AES.block_size)
    padded = unpadded + padding
    
    key = make_key(secret)
    iv = Random.get_random_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    ciphertext = cipher.encrypt(padded)
    return iv + ciphertext

def decrypt(secret, data):
    if len(data) < AES.block_size:
        raise ValueError("decryption failed, Invalid format.")
    iv = data[:AES.block_size]
    ciphertext = data[AES.block_size:]
    if len(ciphertext) % AES.block_size != 0:
        raise ValueError("decryption failed, Invalid format.")
    
    key = make_key(secret)
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

def make_key(secret):
    return SHA.new(secret).digest()[:16]
    
def make_padding(data, block_size):
    data_size = len(data)
    block_count = data_size / block_size + 1
    total_size = block_count * block_size
    pad_size = total_size - data_size
    return chr(pad_size) * pad_size
