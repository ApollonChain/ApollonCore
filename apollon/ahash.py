import hashlib, hmac, scrypt, time


## ApoxHash Object ##
class ApoxHash(object):

    # Slow ApoxHash
    @staticmethod
    def slowHash(byte_data, nonce, p=2, buflen=32, r=4, n=16384):
        shah = hashlib.sha3_512(byte_data + hex(nonce).encode()).digest()
        blakh = hashlib.blake2b(key=shah, digest_size=64).digest()
        hmch = hmac.new(key=blakh, msg=byte_data + shah, digestmod=hashlib.sha3_512).digest()
        scrph = scrypt.hash(hmch, salt=blakh, N=n, r=r, p=p, buflen=buflen)
        key = hashlib.pbkdf2_hmac( 'sha256', byte_data, blakh, 100000, dklen=256 )
        return hashlib.sha3_512(byte_data + shah + blakh + scrph + hmch + key).digest()

    # Validate ApoxHash
    @staticmethod
    def validateHash(byte_data, nonce, verify_hash, p=2, buflen=32, r=4, n=16384):
        shah = hashlib.sha3_512(byte_data + hex(nonce).encode()).digest()
        blakh = hashlib.blake2b(key=shah, digest_size=64).digest()
        hmch = hmac.new(key=blakh, msg=byte_data + shah, digestmod=hashlib.sha3_512).digest()
        scrph = scrypt.hash(hmch, salt=blakh, N=n, r=r, p=p, buflen=buflen)
        return hashlib.sha3_512(byte_data + shah + blakh + scrph + hmch).digest() == verify_hash




maxNonce = 2**64
target = 2 ** (512-13)
current_nonce = 0
current_hash = None
start = time.time()
timev = None
rounds = 0
for n in range(maxNonce):
    current_hash = ApoxHash.slowHash(b'hallo welt2sdsaed', current_nonce)
    rounds += 1
    if int(current_hash.hex(), 16) <= target:
        timev = time.time() - start
        break
    else: current_nonce += 1

import base58
print(base58.b58encode(current_hash).decode())
print(rounds)
print(timev/60, int(timev))