class ChainConfiguration:
    ChainCoins = list()
    

class Blockchain:
    def __init__(self, RootConfig, ChainDB):
        # Blockchain Daten
        self.mempool = list()
        self.root_conf = RootConfig
        from threading import Lock
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

    # Fügt eine Transaktion hinzu
    def addTransaction(self, *TransactionObj):
        from apollon.transaction import SignedTransaction
        for i in TransactionObj:
            assert isinstance(i, SignedTransaction)
            assert i.signaturesAreValidate() == True
            self.mempool.append(i)

    # Gibt die Aktuelle Block Höhe aus
    def getBlockHeight(self): return self.ChainStorageObj.getBlockHeight()

    # Fügt der Blockchain einen neuen Block hinzu
    def addBlock(self, BlockObj):
        self.ChainStorageObj.addBlock(BlockObj)
        self.last_block = BlockObj

    # Gibt alle Coins der Blockchain aus
    def getChainCoins(self): return self.current_coins
    
    # Gibt die Hashrate des Miners aus
    def getHashrate(self): return self.miner.getHashRate()

    # Gibt die Burning Adresse der Chain aus
    def getChainBurningAddress(self):
        return

    # Gibt die Belohnug für den Aktuellen Block             
    def GetRewardForBlock(self, BlockHeight):
        from apollon.coin import CoinValueUnit
        lis = list()
        for i in self.getChainCoins():
            # Es wird geprüft ob es sich um einen Mining fähigen Coin handelt
            if i.isMiningLabel() == True and i.hasRewardForBlock(BlockHeight) == True:
                cnv = CoinValueUnit(i); cnv.add(i.miningReward(BlockHeight)); lis.append(cnv)   # Der Coin wird hinzugefügt
        return lis

    # Diese Funktion überprüft die Nonce des geminten Hashes
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
        except Exception as E: raise Exception(E)

        # Es wird eine Liste, mit allen Coin der Blockchain erstellt
        chain_coins = list()
        for i in self.root_conf.getCoins():
            r = dict()
            r['name'] = i.getName()
            r['symbol'] = i.getSymbol()
            r['coin_id'] = i.getCoinID(False)
            r['confirmed'] = 0
            r['unconfirmed'] = 0
            r['total_recived'] = 0
            r['total_send'] = 0
            chain_coins.append(r)

        # Die Daten aus dem Storage werden geschrieben
        for i in chain_coins:
            for x in storage_data['coin_values']:
                if i['coin_id'] == x['coin'].getCoinID(False):
                    i['total_recived'] += x['total_recived']
                    i['total_send'] += x['total_send']
                    i['confirmed'] += x['amount']

        # Die Daten werden zurückegeben
        return dict({ 'amount' : chain_coins, 'total_transactions' : storage_data['total_txn'] })    

    # Gibt die Schwierigkeit des Aktuellen Blocks an
    def getBlockDiff(self, BlockHeight=None):
        return 460

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

    # Gibt alle Informationen über eine Spizielle Lagacy Adresse aus
    def getLagacyAddressRAW(self, Address):
        # Es werden alle Transaktionen, welche diese Adresse betreffen aus dem Memorypool abgerufen
        #mempool_transactions = list()

        # Es werden alle Transaktionen aus dem Storage abgerufen
        #storage_transactions = list()

        # Beide Listen werden zusammengeführt
        pass

    # Gibt alle Transaktionen einer Adresse aus
    def getLagacyTransactionsByAddress(self, *Addresses, MaxEntries=25, CurrentPage=1, OutAsJSON=False):
        # Es wird geprüft ob die Adressen korrekt sind
        from apollon.apollon_address import LagacyAddress
        for adr_i in Addresses:
            if isinstance(adr_i, LagacyAddress) == False: raise Exception('Invalid Address')

        # Es wird geprüft ob die MaxEntries korrekt ist

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

    # Ruft die Aktuellen Smart Contract Daten ab
    def getEthereumCrossMempoolTransactions(self):
        from web3 import Web3   
        w3 = Web3(Web3.WebsocketProvider("ws://ropsten.infura.io/v3"))
        abi = [{"constant":True,"inputs":[],"name":"mintingFinished","outputs":[{"name":"","type":"bool"}],"payable":False,"type":"function"},{"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":False,"type":"function"},{"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[],"payable":False,"type":"function"},{"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":False,"type":"function"},{"constant":False,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[],"payable":False,"type":"function"},{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint256"}],"payable":False,"type":"function"},{"constant":False,"inputs":[],"name":"unpause","outputs":[{"name":"","type":"bool"}],"payable":False,"type":"function"},{"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"}],"name":"mint","outputs":[{"name":"","type":"bool"}],"payable":False,"type":"function"},{"constant":True,"inputs":[],"name":"paused","outputs":[{"name":"","type":"bool"}],"payable":False,"type":"function"},{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":False,"type":"function"},{"constant":False,"inputs":[],"name":"finishMinting","outputs":[{"name":"","type":"bool"}],"payable":False,"type":"function"},{"constant":False,"inputs":[],"name":"pause","outputs":[{"name":"","type":"bool"}],"payable":False,"type":"function"},{"constant":True,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":False,"type":"function"},{"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":False,"type":"function"},{"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[],"payable":False,"type":"function"},{"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_releaseTime","type":"uint256"}],"name":"mintTimelocked","outputs":[{"name":"","type":"address"}],"payable":False,"type":"function"},{"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"payable":False,"type":"function"},{"constant":False,"inputs":[{"name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"payable":False,"type":"function"},{"anonymous":False,"inputs":[{"indexed":True,"name":"to","type":"address"},{"indexed":False,"name":"value","type":"uint256"}],"name":"Mint","type":"event"},{"anonymous":False,"inputs":[],"name":"MintFinished","type":"event"},{"anonymous":False,"inputs":[],"name":"Pause","type":"event"},{"anonymous":False,"inputs":[],"name":"Unpause","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"owner","type":"address"},{"indexed":True,"name":"spender","type":"address"},{"indexed":False,"name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"name":"from","type":"address"},{"indexed":True,"name":"to","type":"address"},{"indexed":False,"name":"value","type":"uint256"}],"name":"Transfer","type":"event"}]
        contract = w3.eth.contract(Web3.toChecksumAddress("0x3b69af380941a05c87c0aa9f6e618b7898852951"), abi=abi)
        balance = contract.functions.balanceOf('0xFa618a5a36B0Cc99845F36ddDCF7AC54c2aB02F9').call()
