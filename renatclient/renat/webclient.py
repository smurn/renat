from twisted.internet import reactor
from twisted.web.client import HTTPConnectionPool
from Crypto.Hash import SHA
from Crypto.Cipher import AES
import bz2

class WebClient(object):
    
    def __init__(self, secret, proxy_host=None, proxy_port=80):
        self.secret = secret
        self.pool = HTTPConnectionPool(reactor, persistent=True)
        self.pool.maxPersistentPerHost = 1024
    
    def put(self, key, value):
        pass
    


def encrypt(secret, plaintext, rnd):
    digest = SHA.new(plaintext).digest()
    compressed = bz2.compress(plaintext)
    unpadded = compressed + digest
    padding = make_padding(unpadded, AES.block_size)
    padded = unpadded + padding
    
    key = make_key(secret)
    iv = rnd.get_random_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    ciphertext = cipher.encrypt(padded)
    return iv + ciphertext

def decrypt(secret, encrypted):
    pass

def make_key(secret):
    return SHA.new(secret).digest()[:16]
    
def make_padding(data, block_size):
    data_size = len(data)
    block_count = data_size / block_size + 1
    total_size = block_count * block_size
    pad_size = total_size - data_size
    return chr(pad_size) * pad_size