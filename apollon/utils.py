# Gibt an ob es sich um Base58 handelt
def isBase58(datain):
    from apollon import BASE58_BET; import base58
    try: base58.b58decode(datain, alphabet=BASE58_BET)
    except: return False
    return True

# Gibt an ob es sich um Hexadezimal handelt
def isHex(datain):
    return False

# Wandelt Base58 in bytes um
def decodeBase58(datain):
    from apollon import BASE58_BET; import base58
    try: deco = base58.b58decode(datain, alphabet=BASE58_BET)
    except: return False
    return deco

# Wandelt Bytes in Base58 um
def encodeBase58(datain):
    from apollon import BASE58_BET; import base58
    try: enco = base58.b58encode(datain, alphabet=BASE58_BET).decode()
    except: return False
    return enco

# Wandelt Base58 in ein Integer um
def decodeBase58Int(datain):
    from apollon import BASE58_BET; import base58
    try: deco = base58.b58decode_int(datain, alphabet=BASE58_BET)
    except: return False
    return deco

# Wandelt ein Integer in Base58 um
def encodeBase58Int(datain):
    from apollon import BASE58_BET; import base58
    try: enco = base58.b58encode_int(datain, alphabet=BASE58_BET).decode()
    except: return False
    return enco

# Überprüft, ob es sich um eine Zulässige Nonce handelt
def validateNonce(bhash, rhash, nonce, diff):
    import pycryptonight, binascii
    try: bh = pycryptonight.cn_slow_hash( bytes( rhash + str(nonce).encode() ), 4, 0, 1)
    except: return False
    if binascii.hexlify(bh) != bhash: return False
    return True

# Erstellt einen MySQL Pager
def sqlPager(max_entrys, page):
    if page == 1: return '{} OFFSET 0'.format(max_entrys)
    if page == 2: return '{} OFFSET {}'.format(max_entrys, max_entrys)
    return '{} OFFSET {}'.format(max_entrys, max_entrys*(page-1))
