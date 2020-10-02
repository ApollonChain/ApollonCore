class ChainRootConfig(object):
    
    def __init__(self):
        self.Coins = list()
        self.ChainName = str()
        self.ChainSeed = bytes()
        self.NetworkID = int()
        self.ConfigFile = None
        self.BlockSize = int()
        self.BlockTime = int()

    # Gibt alle Verfügbaren Coins der Blockchain aus
    def getCoins(self):
        return self.Coins

    # Gibt den Namen der Blockchain aus
    def getChainName(self):
        return self.ChainName

    # Gibt die Netzwerk Checksumme aus
    def getNetChecksum(self, AsBytes=False):
        import hashlib
        netw_hash_bytes = hashlib.sha3_512()
        netw_hash_bytes.update(str(self.getChainName()).upper().encode())
        netw_hash_bytes.update(bytes.fromhex(self.ChainSeed))
        netw_hash_bytes = netw_hash_bytes.digest()
        netw_hash_bytes = bytes(netw_hash_bytes[0:1] + netw_hash_bytes[63:64])
        if AsBytes == True: return netw_hash_bytes
        else: return netw_hash_bytes.hex() 

    # Gibt den Seed der Blockchain aus
    def getChainSeed(self):
        return self.ChainSeed
    
    # Gibt die NetzwerkID aus
    def getChainNetworkID(self):
        return self.NetworkID

    # Gibt den Hash aller Einstellungen aus
    def getConfigsHash(self, AsBytes=False):
        from hashlib import sha3_512
        shu = sha3_512()
        shu.update(self.ChainName.encode('UTF-8'))
        shu.update(self.ChainSeed.encode('UTF-8'))
        shu.update(hex(self.NetworkID).encode('UTF-8'))
        shu.update(hex(self.BlockSize).encode('UTF-8'))
        shu.update(hex(self.BlockTime).encode('UTF-8'))
        for i in self.Coins: shu.update(i.getCoinID(True))
        if AsBytes == True: return shu.digest()
        else: from apollon.utils import encodeBase58; return encodeBase58(shu.digest())

    # Gibt einen Coin der Chain anhand seiner ID aus
    def getChainCoinByID(self, CoinID):
        if isinstance(CoinID, bytes) == True:
            for i in self.Coins:
                if i.getCoinID(True) == CoinID: return i
            return None

    # Gibt den RootHash der Chain aus
    def getChainRootHash(self, AsBytes=False):
        from hashlib import sha3_384
        shaunit = sha3_384()
        shaunit.update(self.getChainName().encode('UTF-8'))
        shaunit.update(self.getChainSeed().encode('UTF-8'))
        shaunit.update(self.getConfigsHash(True))
        shaunit.update(self.getConfigFileHash(True))
        if AsBytes == True: return shaunit.digest()
        else: from apollon.utils import encodeBase58; return encodeBase58(shaunit.digest())

    # Gibt den Hash der Konfigurationsdatei aus
    def getConfigFileHash(self, AsBytes=False):
        from hashlib import sha3_512
        hu = sha3_512()
        with open(self.ConfigFile) as fp:
            line = fp.readline()
            cnt = 1
            while line:
                hu.update(line.strip().encode('UTF-8'))
                line = fp.readline()
                cnt += 1
        if AsBytes == True: return hu.digest()
        else: from apollon.utils import encodeBase58; return encodeBase58(hu.digest())

    # Gibt die gesamte Config als JSON aus
    def toJSON(self):
        base_dic = dict()
        base_dic['name'] = self.ChainName
        base_dic['seed'] = self.ChainSeed
        base_dic['network_id'] = self.NetworkID
        base_dic['block_time'] = self.BlockTime
        base_dic['block_size'] = self.BlockSize
        coin_dic = list()
        for i in self.Coins: coin_dic.append(i.toJSON())
        base_dic['coins'] = coin_dic
        return base_dic

    # Erstellt eine neue Config Datei
    @classmethod
    def newChainRootConfig(cls, SavePath, ChainName, ChainSeed, NetworkID, BlockSize, BlockTime, *ChainCoins):
        nwo = cls()

        # Es werdne alle Chain Coin in die RootConfig geschrieben
        for i in ChainCoins: nwo.Coins.append(i)

        # Der ChainName wird geschrieben
        nwo.ChainName = ChainName
        
        # Der ChainSeed wird geschrieben
        nwo.ChainSeed = ChainSeed

        # Die NetzwerkID wird geschrieben
        nwo.NetworkID = NetworkID

        # Die Blockgröße wird geschrieben 
        nwo.BlockSize = BlockSize

        # Die Blockzeit wird geschrieben
        nwo.BlockTime = BlockTime

        # Die RootConfig wird abgespeichert
        from json import dumps
        f = open(SavePath, 'w')
        f.write(dumps(nwo.toJSON(), indent=4, sort_keys=False))
        f.close()
        nwo.ConfigFile = SavePath

        # Gibt die neue Config aus
        return nwo

    # Lädt eine Vorhandene Config Datei
    @classmethod
    def loadRootConfig(cls, ConfigFilePath):
        # Es wird versucht die Daten zu laden
        from json import load
        loaded_data = None
        try:
            with open(ConfigFilePath) as json_file:
                data = load(json_file)
                # Es wird geprüft ob alle Benötigten Datenfelder vorhanden sind
                if ('name' in data) == False: raise Exception('INVALID_CONFIG')
                if ('seed' in data) == False: raise Exception('INVALID_CONFIG')
                if ('network_id' in data) == False: raise Exception('INVALID_CONFIG')
                if ('block_time' in data) == False: raise Exception('INVALID_CONFIG')
                if ('block_size' in data) == False: raise Exception('INVALID_CONFIG')
                if ('coins' in data) == False: raise Exception('INVALID_CONFIG')
                # Die geladenen JSON Daten werden geschrieben
                loaded_data = data
        except Exception as E: raise E

        # Es wird geprüft ob Mindestens ein Coin vorhanden ist
        if len(loaded_data['coins']) == 0: raise Exception('Invalid Root Config')

        """Es werden alle Einstellungen aus der Konfigurationsdatei extrahiert und eingelesen"""

        # Es wird versucht eine Network Checksume zu erstellen
        import hashlib
        netw_hash_bytes = hashlib.sha3_512()
        netw_hash_bytes.update(str(loaded_data['name']).upper().encode())
        netw_hash_bytes.update(bytes.fromhex(loaded_data['seed']))
        netw_hash_bytes = netw_hash_bytes.digest()
        netw_hash_bytes = netw_hash_bytes[0:1] + netw_hash_bytes[63:64]

        # Es wird ein neues RootConfig Object erstellt
        nwo = cls()
        
        # Die Coins werden geschrieben
        from apollon.coin import Coin
        for coin_i in loaded_data['coins']:
            try: nwo.Coins.append(Coin.fromJSON(coin_i, netw_hash_bytes, loaded_data['seed'].encode()))
            except Exception as E: raise Exception('Invalid Coin: '+ E)

        # Die Restlichen Chaindaten werden geschrieben
        nwo.ChainName = loaded_data['name']
        nwo.ChainSeed = loaded_data['seed']
        nwo.NetworkID = loaded_data['network_id']
        nwo.BlockSize = loaded_data['block_size']
        nwo.BlockTime = loaded_data['block_time']
        nwo.ConfigFile = ConfigFilePath

        # Das Objekt wird zurückgegeben
        return nwo
