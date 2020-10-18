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
    # Es wird geprüft ob der Path exestiert
    import os
    if os.path.isdir(ChainPath) == False: raise Exception('No chain found')

    # Es wird geprüft ob die Benötigten Daten vorhanden sind
    if os.path.isfile('{}/chain.cdb'.format(ChainPath)) == False: raise Exception('No Chain Database Found')
    if os.path.isfile('{}/chain.rc'.format(ChainPath)) == False: raise Exception('No Chain Config Found')

    # Es wird versucht die Chain Root Config zu laden
    print('Loading Chain Root config#')
    from apollon.chain_configs import ChainRootConfig
    try: gv_.ChainRoot = ChainRootConfig.loadRootConfig('{}/chain.rc'.format(ChainPath))
    except: raise Exception('Invalid Blockchain')

    # Es werden alle Verfügbaren Coins aufgelistet
    print('Avaible Coins#')
    for xi in gv_.ChainRoot.getCoins():
        print(' > Name:',xi.getName())
        print(' > Symbol:',xi.getSymbol())
        print(' > Coin-ID:',xi.getCoinID())

    # Es wird versucht die Datenbank zu Prüfen
    from apollon.chain_storage import ChainStorage
    try: gv_.ChainDB = ChainStorage.fromFile('{}/chain.cdb'.format(ChainPath), gv_.ChainRoot, FullValidate)
    except: raise Exception('Invalid Blockchain#')

    # Das Blockchainobjekt wird erstellt
    from apollon.chain import Blockchain
    try: gv_.Blockchain = Blockchain(gv_.ChainRoot, gv_.ChainDB)
    except: raise Exception('FATAL_BLOCKCHAIN_ERROR')

    # Die Blockchain wurde erfolgreich geladen
    return 0

def getChainObject():
    if gv_.Blockchain is None: raise Exception('Not Chain loaded')
    return gv_.Blockchain