import string
BASE58_BET = "apolnbcdefghijkmqystuvwxrzAPOLNBCDEFGHIJKMQRSTUVWXYZ9123456780".encode() 
VERSION = "0.1 Milestone 4.0"

from apollon.chain_configs import ChainRootConfig

class gv_:
    ChainDB = None
    ChainRoot = None
    Blockchain = None
    Services = list()
class _apli:
    HostCPUCores = None
    HostOS = None
    HostCores = None
    Finsh = False

def loadChain(ChainPath, FullValidate=False):
    import os
    if os.path.isdir(ChainPath) == False: raise Exception('No chain found')
    if os.path.isfile('{}/chain.cdb'.format(ChainPath)) == False: raise Exception('No Chain Database Found')
    if os.path.isfile('{}/chain.rc'.format(ChainPath)) == False: raise Exception('No Chain Config Found')

    print('Loading Chain Root config#')
    from apollon.chain_configs import ChainRootConfig
    try: gv_.ChainRoot = ChainRootConfig.loadRootConfig('{}/chain.rc'.format(ChainPath))
    except: raise Exception('Invalid Blockchain')

    print('Avaible Coins#')
    for xi in gv_.ChainRoot.getCoins():
        print(' > Name:',xi.getName())
        print(' > Symbol:',xi.getSymbol())
        print(' > Coin-ID:',xi.getCoinID())

    from apollon.chain_storage import ChainStorage
    try: gv_.ChainDB = ChainStorage.fromFile('{}/chain.cdb'.format(ChainPath), gv_.ChainRoot, FullValidate)
    except: raise Exception('Invalid Blockchain#')

    from apollon.chain import Blockchain
    try: gv_.Blockchain = Blockchain(gv_.ChainRoot, gv_.ChainDB)
    except: raise Exception('FATAL_BLOCKCHAIN_ERROR')

    return 0

def getChainObject():
    if gv_.Blockchain is None: raise Exception('Not Chain loaded')
    return gv_.Blockchain