from sha3 import keccak_224, keccak_256, keccak_384, keccak_512
from Cryptodome.Random import get_random_bytes
from base58 import b58encode, RIPPLE_ALPHABET
from hashlib import blake2b, pbkdf2_hmac
from Cryptodome.Cipher import AES
from enum import Enum
import bcrypt


class ApxSize(Enum):
    S3224=keccak_224
    S3256=keccak_256
    S3384=keccak_384
    S3512=keccak_512

class ApXHash(object):
    def __init__(self, *Data, HashSize = ApxSize.S3256):
        self.plain_hash_buffer = None
        self.in_hash_algo = HashSize
        for i in Data: self.update(i)

    def update(self, *data):
        for base_data_in in data:
            input_sha3_hash = bytes(self.in_hash_algo.value(base_data_in).digest())
            
            # Loop to BcrypHash
            bcrypted_hash = bcrypt.kdf(password=base_data_in, salt=input_sha3_hash, desired_key_bytes=48, rounds=64)
            
            # Total EndBytes
            end_total_bytes = bytes(input_sha3_hash + bcrypted_hash)

            # Safe Current Hash
            if self.plain_hash_buffer is not None: self.plain_hash_buffer = self.in_hash_algo.value(self.plain_hash_buffer + end_total_bytes).digest()
            else: self.plain_hash_buffer = self.in_hash_algo.value(end_total_bytes).digest()

    def digest(self): return self.plain_hash_buffer

    def hexdigest(self): return self.digest().hex()

    def intdigest(self): return int.from_bytes(bytes(self.digest()), "little")

    def basedigest(self): return b58encode(self.digest(), alphabet=b"apolnbcdefghijkmqystuvwxrzAPOLNBCDEFGHIJKMQRSTUVWXYZ9123456780").decode()

    def bindigest(self): return bin(int.from_bytes(self.digest(), byteorder="big")).strip('0b')

    def verifyData(self, *data):
        ntH = ApXHash(HashSize=self.in_hash_algo)
        for i in data: ntH.update(i)
        if self.plain_hash_buffer != ntH.plain_hash_buffer: return False
        return True


current_nonce = 0
found = False

maxNonce = 2**32
target = 2 ** (256-8)

import time, secrets
k = 0; rn = secrets.token_bytes(128)
start = time.time()
for n in range(maxNonce):
    hu = ApXHash(HashSize=ApxSize.S3256)
    hu.update(rn)
    hu.update('{}{}'.format(k,current_nonce).encode())
    hu.update(str(current_nonce).encode())
    if int(hu.hexdigest(), 16) <= target: 
        found = hu.digest()
        k += 1
        current_nonce = 0
        rn = secrets.token_bytes(128)
        end = time.time()
        print('FOUND', found.hex(), end - start)
        start = time.time()
    else: current_nonce += 1


