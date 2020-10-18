## Blockchain Object ##
class Blockchain:
    # Es wird ein neues Blockchain Objekt erstellt
    def __init__(self, RootConfig, ChainDB):
        # Blockchain Daten
        from threading import Lock
        self.mempool = list()
        self.root_conf = RootConfig
        self.thread_lock = Lock()

        ## Chain Storage
        from apollon.chain_storage import ChainStorage
        self.ChainStorageObj = ChainDB
        self.last_block = None

        # Miner
        from apollon.miner import CryptonightMiner
        self.miner = CryptonightMiner(self, 2)

        # WebController
        from apollon.web_controller import WebController
        self.wc = WebController(self)

        # Dashboard
        from apollon.apollon_dashboard import ApollonDashboard
        self.dashboard = ApollonDashboard(self)

        # Die Coins der Chain werden im RAM abgespeichert
        self.current_coins = list()
        for i in self.root_conf.getCoins():
            i._atempChain(self)
            self.current_coins.append(i)
        
        # Die Chain eigenen Adressen werden erstellt
        from apollon.apollon_address import BlockchainAddress, AddressTypes
        self.burn_address = BlockchainAddress(ChainSeed=self.root_conf.getChainSeed(True), AddressType=AddressTypes.ChainOwnAddress, ChainAddressType=BlockchainAddress.ChainAddressTypes.BURN_ADDRESS, NetworkCMHex=self.root_conf.getNetChecksum(True))

    # Started das Mining
    def startMining(self, RewardAddress):
        # Es wird geprüft ob eine gültige Adresse übergeben wurde
        from apollon.apollon_address import LagacyAddress, PhantomAddress
        assert isinstance(RewardAddress, LagacyAddress) or isinstance(RewardAddress, PhantomAddress)

        # Es wird geprüft ob der miner bereits läuft
        if self.miner.Status() != 2: raise Exception('Alrady running')      # Es wird bereits ein Miner ausgeführt

        # Der Miner wird gestartet
        if self.miner.Start(RewardAddress) != 0: raise Exception('Miner cant start')     # Der Miner konnte nicht gestartet werden
    
    # Started den Webcontroller
    def startWebController(self):
        self.wc.Start()

    # Started das Dashboard
    def startDashboard(self):
        self.dashboard.start()

    # Fügt eine Transaktion hinzu TODO
    def addTransaction(self, *TransactionObj):
        from apollon.transaction import SignedTransaction
        for i in TransactionObj:
            assert isinstance(i, SignedTransaction)
            assert i.signaturesAreValidate() == True

            # Es wird geprüft, ob die Verwendeten UTXO's bereits ausgegeben wurden
            self.mempool.append(i)

    # Gibt die Aktuelle Block Höhe aus
    def getBlockHeight(self): return self.ChainStorageObj.getBlockHeight()

    # Fügt der Blockchain einen neuen Block hinzu TODO
    def addBlock(self, BlockObj):
        # Es wird geprüft ob es sich um einen Gültigen Block handelt
        if BlockObj.getHeight() != self.getBlockHeight() + 1: raise Exception('INVALID BLOCK HEIGHT')

        self.ChainStorageObj.addBlock(BlockObj)
        self.last_block = BlockObj

    # Gibt einen Block aus
    def getBlock(self, BlockID):
        return self.ChainStorageObj.getBlock(BlockID)

    # Gibt den Hashawert des Blockes aus, welchers als nächstes Gemint werden soll TODO
    def getBlockTemplate(self): pass

    # Erstellt einen neuen Block aus dem Blockblob sowie der Nonce  TODO
    def addBlockByMinedTemplate(self, BlobHash, Nonce, MinerAddress): pass

    # Gibt alle Coins der Blockchain aus
    def getChainCoins(self): 
        if self.current_coins is not None: return self.current_coins
        else: return []
    
    # Gibt die Hashrate des Miners aus TODO
    def getHashrate(self): return self.miner.getHashRate()

    # Gibt die Burning Adresse der Chain aus TODO
    def getChainBurningAddress(self): return self.burn_address

    # Gibt die Belohnugen für den Aktuellen Block             
    def GetRewardForBlock(self, BlockHeight):
        from apollon.coin import CoinValueUnit
        lis = list()
        for i in self.getChainCoins():
            if i.isMiningLabel() == True and i.hasRewardForBlock(BlockHeight) == True: cnv = CoinValueUnit(i); cnv.add(i.miningReward(BlockHeight)); lis.append(cnv)
        return lis

    # Diese Funktion überprüft die Nonce des geminten Hashes TODO
    def validateMinedHash(self, BlockHeight, BlockHash, Nonce): return True

    # Gibt einen Coin der Chain anhand seiner ID aus
    def getChainCoinByID(self, CoinID):
        if isinstance(CoinID, bytes) == True:
            for i in self.root_conf.getCoins():
                if i.getCoinID(True) == CoinID: return i
            return None

    # Gibt die MetaDaten des Letzten Blocks aus
    def getLastBlockMetaData(self, AsBytes=False):
        # Es wird geprüft ob bereits ein Block in der Chain vorhanden ist
        if self.ChainStorageObj.getBlockHeight() == 0:
            lbmdc = dict()
            lbmdc['block_height'] = 0
            lbmdc['block_hash'] = self.root_conf.getChainRootHash(AsBytes)
            return lbmdc
        # Es ist bereits ein Block vorhanden
        else:
            lbmd = self.ChainStorageObj.getLastBlockMetaData()
            lbmdc = dict()
            lbmdc['block_height'] = lbmd['block_height']
            if AsBytes == True: lbmdc['block_hash'] = lbmd['block_hash']
            else: from apollon.utils import encodeBase58; lbmdc['block_hash'] = encodeBase58(lbmd['block_hash'])
            return lbmdc

    # Gibt die Informationen der Letzten Blöcke aus
    def getLastBlocksMetaData(self, Blocks=50, Page=1):
        return self.ChainStorageObj.getLastBlocksMetaData(Blocks, Page)

    # Gibt alle Informationen über eine Adresse aus
    def getAddressDetails(self, Addresses):
        # Es werden alle Adress MetaDaten aus dem Storage Abgerufen
        try: storage_data = self.ChainStorageObj.getAddressDetails(Addresses)
        except Exception as E: print(E); raise Exception('Storage data')

        # Es wird geprüft ob ein gültiges Objekt abgerufen wurde
        from apollon.address_utils import AddressChainDetails
        if isinstance(storage_data, AddressChainDetails) == False: raise Exception('Invalid chain storage data')

        # Das abgerufene Objekt wird zurückgegeben
        return storage_data

    # Gibt die Schwierigkeit des Aktuellen Blocks an
    def getBlockDiff(self, BlockHeight=None):
        return 240

    # Erstellt eine Vollständig neue Blockchain
    @staticmethod
    def createNewChain(ChainPath, ChainName, ChainMasterSeed, *ChainCoins):
        # Es wird geprüft ob der Path exestiert
        import os
        if os.path.isdir(ChainPath) == False: os.mkdir(ChainPath)
        else:
            if os.path.isfile('{}/chain.cdb'.format(ChainPath)) == True: raise Exception('Alrady exists')
            if os.path.isfile('{}/chain.rc'.format(ChainPath)) == True: raise Exception('Alrady exists')

        # Die Chain Config wird erstellt
        from apollon.chain_configs import ChainRootConfig
        ChainRootConfig.newChainRootConfig('{}/chain.rc'.format(ChainPath), ChainName, ChainMasterSeed, 0, 645120, int(3*60), *ChainCoins)

        # Die Datenbank wird erstellt
        from apollon.chain_storage import ChainStorage
        ChainStorage.newFile('{}/chain.cdb'.format(ChainPath))

        # Die Chain wurde erfolgreich erstellt
        return 0

    # Gibt alle Transaktionen einer Adresse aus
    def getLagacyTransactionsByAddress(self, *Addresses, MaxEntries=25, CurrentPage=1, OutAsJSON=False):
        # Es wird geprüft ob die Adressen korrekt sind
        from apollon.apollon_address import LagacyAddress, BlockchainAddress
        for adr_i in Addresses:
            if isinstance(adr_i, LagacyAddress) == False and isinstance(adr_i, BlockchainAddress) == False: raise Exception('Invalid Address')

        # Es wird geprüft ob die MaxEntries korrekt ist
        if isinstance(MaxEntries, int) == False: raise Exception('Invalid MaxEntries')

        # Es wird geprüft ob es sich um eine Zuläassige Seitenangabe handelt
        if isinstance(CurrentPage, int) == False or CurrentPage < 1: raise Exception('Invalid CurrentPage, only Numbers')

        # Es wird geprüft ob die JSON Ausgabe korrekt ist (JSON)
        if isinstance(OutAsJSON, bool) == False: raise Exception('Invalid OutAsJSON, onyl True/False allowed')

        # Die Transaktionen werden aus dem Memorypool abgerufen
        mempool_res = list()

        # Alle Adressen werden in der Datenbank abgerufen
        storage_data = list()
        for adri in Addresses:
            # Es werden alle Transaktionen aus dem Storage abgerufen
            try: rcs = self.ChainStorageObj.getAddressTransactions(*mempool_res ,Addresses=adri, MaxEntries=MaxEntries, CurrentPage=CurrentPage)
            except: raise Exception('Internal error')
            
            # Es wird geprüft in welcher Form die Transaktionen ausgegeben werden sollen
            for xci in rcs:
                if OutAsJSON == False: storage_data.append(xci)
                else: storage_data.append(xci.toJSON())
        
        # Die Daten werden zurückgegeben
        return storage_data