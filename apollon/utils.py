def isBase58(datain):
    from apollon import BASE58_BET; import base58
    try: base58.b58decode(datain, alphabet=BASE58_BET)
    except: return False
    return True

def isHex(datain):
    return False

def decodeBase58(datain):
    from apollon import BASE58_BET; import base58
    try: deco = base58.b58decode(datain, alphabet=BASE58_BET)
    except: return False
    return deco

def encodeBase58(datain):
    from apollon import BASE58_BET; import base58
    try: enco = base58.b58encode(datain, alphabet=BASE58_BET).decode()
    except: return False
    return enco

def decodeBase58Int(datain):
    from apollon import BASE58_BET; import base58
    try: deco = base58.b58decode_int(datain, alphabet=BASE58_BET)
    except: return False
    return deco

def encodeBase58Int(datain):
    from apollon import BASE58_BET; import base58
    try: enco = base58.b58encode_int(datain, alphabet=BASE58_BET).decode()
    except: return False
    return enco

def validateNonce(bhash, rhash, nonce, diff):
    import pycryptonight, binascii
    try: bh = pycryptonight.cn_slow_hash( bytes( rhash + str(nonce).encode() ), 4, 0, 1)
    except: return False
    if binascii.hexlify(bh) != bhash: return False
    return True

def sqlPager(max_entrys, page):
    if page == 1: return '{} OFFSET 0'.format(max_entrys)
    if page == 2: return '{} OFFSET {}'.format(max_entrys, max_entrys)
    return '{} OFFSET {}'.format(max_entrys, max_entrys*(page-1))

def paginationSizer(CurrentPage, totalPages):
    if totalPages < 12: return range(totalPages)
    _x = [1, 2, 3, '...', totalPages-2, totalPages-1, totalPages]
    return _x