
""" Blöcke """

## Wird benötigt um einen neen Block zu erstellen ##
class BlockConstruct:
    def __init__(self, PreviousBlockHash, BlockHeight ,MinerAddress ,TimestampObj, Diff, *Transactions):
        # Die Blockdaten werden geschrieben
        self.height = BlockHeight
        self.transactions = list()
        self.prev_block_hash_bytes = PreviousBlockHash
        
        self.diff = Diff

        # Der Zeitstempel wird erstellt
        import datetime
        self.timestamp = TimestampObj

        # Die Transaktionen werden geprüft
        from apollon.transaction import CoinbaseTransaction, SignedTransaction
        for i in Transactions:
            if isinstance(i, CoinbaseTransaction) == True:
                if len(self.transactions) != 0: raise Exception('Only one Coinbase Transaction allowed')
                i.place_in_block = len(self.transactions)
                self.transactions.append(i)
            elif isinstance(i, SignedTransaction) == True:
                i.place_in_block = len(self.transactions)
                self.transactions.append(i)
            else: raise Exception('Invalid Input UTXO')
            
    def getRootHash(self, AsBytes=False): 
        import pycryptonight, binascii
        hash_array = bytes(str(self.height).encode())
        hash_array = hash_array + self.prev_block_hash_bytes
        hash_array = hash_array + str(self.diff).encode()
        hash_array = hash_array + self.timestamp.getHash(True)
        for i in self.transactions: hash_array = hash_array + i.getTxHash(True)
        crypnhash = pycryptonight.cn_fast_hash(hash_array)
        if AsBytes == True: return binascii.hexlify(crypnhash)
        else: from apollon.utils import encodeBase58; return encodeBase58(binascii.hexlify(crypnhash))

    def isValidateObject(self): return True

    def validateBlockTransactions(self): return True

## Geminter Block ##
class MinedBlock:
    def __init__(self):
        self.height = 0
        self.transactions = list()
        self.previous_hash = None
        self.timestamp = None
        self.diff = 0
        self.nonce = 0

    def getHeight(self): return self.height

    def getRootHash(self, AsBytes=False):
        import pycryptonight, binascii
        hash_array = bytes(str(self.height).encode())
        hash_array = hash_array + self.previous_hash
        hash_array = hash_array + str(self.diff).encode()
        hash_array = hash_array + self.timestamp.getHash(True)
        for i in self.transactions: hash_array = hash_array + i.getTxHash(True)
        crypnhash = pycryptonight.cn_fast_hash(hash_array)
        if AsBytes == True: return binascii.hexlify(crypnhash)
        else: from apollon.utils import encodeBase58; return encodeBase58(binascii.hexlify(crypnhash))

    def getDiff(self): return self.diff

    def getBlockHash(self, AsBytes=False):
        import pycryptonight, binascii
        b = pycryptonight.cn_slow_hash( bytes( self.getRootHash(True) + str(self.nonce).encode() ), 4, 0, 1)
        if AsBytes == True: return binascii.hexlify(b)
        else: from apollon.utils import encodeBase58; return encodeBase58(binascii.hexlify(b))

    def getBlockSize(self):
        tota = 0
        tota += len(str(self.height))
        tota += len(self.previous_hash)
        tota += len(str(self.timestamp))
        tota += len(str(self.diff))
        tota += len(str(self.nonce))
        for i in self.transactions: tota += i.getByteSize()
        return tota

    def isGenesisBlock(self): return False

    def getAllTransactions(self, AddressObj=None): return list(self.transactions)

    def getTotalTransactions(self): return len(self.transactions)

    def getAllCoinsOfCurrentBlock(self): return list()

    def getTransactionByID(self, *txid): return list()

    def getTotalFeeRewards(self): return list()

    def getBlockNonce(self): return self.nonce

    def getPreviousBlockHash(self, AsBytes=False):
        if AsBytes == True: return self.previous_hash
        else: from apollon.utils import encodeBase58; return encodeBase58(self.previous_hash)

    def preValidateBlockTransactions(self): return True

    def getBlockTimestampe(self): return self.timestamp

    @classmethod
    def fromConstructWithNonce(cls, ConstructedBlock, Nonce):
        new_block = cls()
        for i in ConstructedBlock.transactions: new_block.transactions.append(i)
        new_block.height = ConstructedBlock.height
        new_block.timestamp = ConstructedBlock.timestamp
        new_block.nonce = Nonce
        new_block.diff = ConstructedBlock.diff
        new_block.previous_hash = ConstructedBlock.prev_block_hash_bytes
        return new_block

    # Gibt den Block als JSON aus
    def toJSON(self):
        rd = dict()
        rd['type'] = 'md'
        rd['height'] = str(self.getHeight())
        rd['block_hash'] = self.getBlockHash()
        rd['perv_block'] = self.getPreviousBlockHash()
        rd['root_hash'] = self.getRootHash()
        rd['nonce'] = str(self.nonce)
        rd['tstamp'] = str(self.timestamp)
        transac = list()
        for i in self.transactions: transac.append(i.toJSON())
        rd['transactions'] = transac
        return rd



"""Block Storage object"""

## Mined Storage Block Object ##
class ST_MinedBlock(MinedBlock):

    # Erstellte einen Geminten Block aus dem Storage
    def __init__(self):
        super().__init__()
        self.confirms = 0
        self.miner_adr = None
    
    # Gibt die Anzahl der Bestätigungen aus
    def getConfirmations(self): return self.confirms
    
    # Gibt an ob der Block bestätigt wurde
    def isConfirmed(self): return self.confirms != 0
    
    # Gibt die Adresse des Miners aus
    def getMinerAddress(self): return self.miner_adr

    @classmethod
    def fromConstructWithNonce(cls, ConstructedBlock, Nonce, Confirms, MinerAddress):
        new_block = cls()
        for i in ConstructedBlock.transactions: new_block.transactions.append(i)
        new_block.height = ConstructedBlock.height
        new_block.timestamp = ConstructedBlock.timestamp
        new_block.nonce = Nonce
        new_block.confirms = Confirms
        new_block.miner_adr = MinerAddress
        new_block.diff = ConstructedBlock.diff
        new_block.previous_hash = ConstructedBlock.prev_block_hash_bytes
        return new_block



"""Block tools"""

## Metadaten des Blocks ##
class BlockMetaData(object):
    def __init__(self, BlockHeight, Timestamp, TxnNo, BlockHash):
        self.block_no = BlockHeight
        self.timestamp = Timestamp
        self.tx_no = TxnNo
        self.block_hash = BlockHash
    def getTimestamp(self): return self.timestamp.toStr()
    def getTxCount(self): return self.tx_no
    def getBlockHash(self):
        from apollon.utils import encodeBase58
        return encodeBase58(self.block_hash)
    def getBlockHeight(self): return self.block_no
