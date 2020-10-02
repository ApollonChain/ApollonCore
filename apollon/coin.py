from hashlib import sha3_512, sha256, sha3_256

class Coin(object):
    def __init__(self, Name, Symbol, SmallestUnitName,
                        SmallestUnitSymbol, DecimalPlaces, NetworkCHSum,
                        ChainSeed, MineReward=0, HalvingToEndNewCoin=True,
                        TotalHalvenings=0, RewardAtBlock=0, HalvinAtBlocks=0,
                        Burnable=False, TxnFeeBurning=False, TxnFeeBurningPerc=0):

        # Es wird geprüft ob die benötigten Daten übergeben wurden
        assert isinstance(Name, str)
        assert isinstance(Symbol, str)
        assert isinstance(SmallestUnitName, str)
        assert isinstance(SmallestUnitSymbol, str)
        assert isinstance(DecimalPlaces, int)
        assert isinstance(NetworkCHSum, bytes)
        assert isinstance(ChainSeed, bytes)
        assert isinstance(MineReward, int)
        assert isinstance(RewardAtBlock, int)
        assert isinstance(HalvinAtBlocks, int)
        assert isinstance(Burnable, bool)
        assert isinstance(TxnFeeBurning, bool)
        assert isinstance(TxnFeeBurningPerc, int)

        # Die Daten werden in das Objekt geschrieben
        self.name = Name
        self.symbol = Symbol
        self.smallest_unit_name = SmallestUnitName
        self.smallest_unit_symbol = SmallestUnitSymbol
        self.decimal_places = DecimalPlaces
        self.network = NetworkCHSum
        self.chain_seed = ChainSeed
        self.mine_reward = MineReward
        self.reward_at_block = RewardAtBlock
        self.halvening_at = HalvinAtBlocks
        self.burnable = Burnable
        self.txn_fee_burning = TxnFeeBurning
        self.txn_fee_burning_perc = TxnFeeBurningPerc
        self.__achain = None

    def __str__(self): return "{} / {}".format(self.name, self.symbol)

    # Wird aufgerufen um die Chain hinzuzufügen
    def _atempChain(self, ChainObj):
        self.__achain = ChainObj

    # Gibt den Namen des Coins aus
    def getName(self, SmallestName=False):
        if SmallestName == True: return self.smallest_unit_name
        else: return self.name

    # Gibt das Symbol des Coins aus
    def getSymbol(self, SmallestUnitSymbol=False):
        if SmallestUnitSymbol == True: return self.smallest_unit_symbol
        else: return self.symbol

    # Gibt die Decimalstellen des Coins aus
    def getDecimals(self): return self.decimal_places
    
    # Gibt den SeedHash des Coins aus
    def getSeedHash(self, AsBytes=False):
        from apollon.utils import encodeBase58
        if AsBytes == True: return sha3_512(self.chain_seed).digest()
        else: return encodeBase58(sha3_512(self.chain_seed).digest())

    # Gibt die CoinID aus, anhand dieser CoinID, wird der Coin Identifiziert
    def getCoinID(self, AsBytes=False):
        # Es wird ein SHA3-256 Hash aus allen Daten erzeugt
        total_hash = sha3_512()
        total_hash.update(self.name.encode())                           # Coin Name / Bytes
        total_hash.update(self.symbol.encode())                         # Coin Symbol / Bytes
        total_hash.update(self.smallest_unit_name.encode())             # Coin Smallest Unit Name / Bytes
        total_hash.update(self.smallest_unit_symbol.encode())           # Coin Smallest Unit Symbol / Bytes
        total_hash.update(hex(self.decimal_places).encode())            # Coin Decimal Places / Hexed-Bytes
        total_hash.update(self.network)                                 # Network Checksume / Bytes
        total_hash.update(self.chain_seed)                              # Network Seed / Bytes
        total_hash.update(hex(self.mine_reward).encode())               # Mininer Reward / Hexed-Bytes
        total_hash.update(hex(self.halvening_at).encode())              # Halving at / Hexed Bytes
        total_hash.update(hex(int(self.burnable)).encode())             # Burnable / Hexed-Bytes
        total_hash.update(hex(int(self.txn_fee_burning)).encode())      # TX-Bruning Fee / Hexed-Bytes
        total_hash.update(hex(self.txn_fee_burning_perc).encode())      
        
        # Der Hash wird gekürtzt
        smal_hash = sha256(total_hash.digest()).digest()
        smal_hash2 = sha3_256(total_hash.digest()).digest()
        chsum = sha3_256(smal_hash[16:] + smal_hash2[16:]).digest()
        chsum_bytes = chsum[0:2] + chsum[32:34] + chsum[62:64]
        
        # Die Coin ID wird zurückgegeben
        from apollon import BASE58_BET; import base58
        if AsBytes == True: return smal_hash[16:] + smal_hash2[16:] + chsum_bytes
        else: return base58.b58encode(smal_hash[16:] + smal_hash2[16:] + chsum_bytes, alphabet=BASE58_BET).decode()

    # Gibt an ob der Coin Minebar ist
    def isMiningLabel(self): return bool(self.mine_reward != 0)

    # Gibt an, wieviele Coins bei Block X exestieren
    def getCirculatingSupplyByBlock(self, PrimaryUnit=False):
        current_block = self.__achain.getBlockHeight()
        if self.reward_at_block != 0 and self.__achain is not None and self.halvening_at != 0:
            tota = 0
            for xo in range(1, current_block):
                if self.hasRewardForBlock(xo) == True: tota += self.miningReward(xo)
            if PrimaryUnit == True: return self.calcSmallestToPUnit(tota)
            else: return tota
        else:
            tota = 0
            for xo in range(1, current_block+1): tota += self.miningReward(xo)
            if PrimaryUnit == True: return self.calcSmallestToPUnit(tota)
            else: return tota

    # Gibt an ob der Coin Brennbar ist
    def isBurnable(self): return self.burnable

    # Gibt die Höhe des Rewards an
    def miningReward(self, BlockHeight=None) -> int:
        from apollon.amath import crbb
        if self.isMiningLabel() == False: return 0
        if BlockHeight is None or self.halveningIsEnabled() == False: return int(self.mine_reward * (10 ** self.decimal_places))
        if BlockHeight <= self.halvening_at and BlockHeight != self.halvening_at: return int(self.mine_reward * (10 ** self.decimal_places))
        if self.reward_at_block <= 2 and self.reward_at_block != 2: return crbb(BlockHeight, self.mine_reward, self.halvening_at, self.decimal_places)
        else: return crbb(BlockHeight, self.mine_reward, self.halvening_at * self.reward_at_block, self.decimal_places)
    
    # Erstellt ein Reward UTXO um neue Coins zu erschaffen #TODO
    def createNewRewardInputUtxo(self, BlockHeight):
        # Es wird geprüft ob es eine Belohnung für diesen Block gibt
        if self.isMiningLabel() == False or self.hasRewardForBlock(BlockHeight) == False: return None
        # Es wird eine OneTimeHash für den Reward erstellt
        one_time_reward_hash = self.createOneTimeRewardHash(BlockHeight, True)
        from apollon.utxo import CoinbaseInUtxo
        if self.hasRewardForBlock(BlockHeight) == False: return None
        new_reward = CoinbaseInUtxo(BlockHeight, self, self.miningReward(BlockHeight), one_time_reward_hash )
        return new_reward

    # Erstellt einen Einmalligen Hash um ein Reward zu erstellen
    def createOneTimeRewardHash(self, BlockHeight, AsBytes=False):
        # Es wird geprüft ob es eine Belohung für diesen Block gibt
        if self.isMiningLabel() == False or self.hasRewardForBlock(BlockHeight) == False: return None
        
        # Es wird ein einmaliger Salz erstellt
        salt = self.getSeedHash(True) + str(BlockHeight).encode() + str(self.miningReward(BlockHeight)).encode()

        # Aus dem Coin und dem ChainSeed wird ein Hash gebildet
        from hashlib import sha3_224
        hlib = sha3_224()
        hlib.update(salt)
        hlib.update(self.getCoinID(True) + self.getSeedHash(True))
        
        # Der OneTime Reward Hash wird ausgegeben
        if AsBytes == True: return hlib.digest()
        else: from apollon.utils import encodeBase58; return encodeBase58(hlib.digest())

    # Gibt an wieviele Coin-Gebühren vom Miner verbrannt werden müssen
    def calcMinerBurningAmountValue(self, TotalAmountValue):
        return 0

    # Gibt an ob für den Aktuellen Block ein Reward vorhanden ist
    def hasRewardForBlock(self, BlockHeight:int) -> bool:
        if self.isMiningLabel() == False: return False
        if self.reward_at_block <= 1 or self.reward_at_block == 1: return True
        if BlockHeight == 1: return True
        from apollon.amath import foiwp
        return foiwp(BlockHeight/(self.reward_at_block))

    # Gibt an ob der Reward Korrekt ist TODO
    def validateReward(self, RewardHight:int, BlockHeight:int) -> bool:
        # Es wird geprüft ob der Coin eine Mining Belohnung besitzt
        if self.isMiningLabel() == False: return False

        # Es wird geprüft ob für diesen Block eine Belohnung verfügbar ist
        if self.hasRewardForBlock(BlockHeight) == False: return False

        # Es wird die höhe des Rewards für diesen Block ermittelt
        if self.miningReward(BlockHeight) != RewardHight: return False

        # Es handelt sich um eine Zulässige Belohnung
        return True

    # Gibt an ob das Halvening für diesen Coin Aktiv ist
    def halveningIsEnabled(self): return bool(self.halvening_at != 0)

    # Gibt an, aller wieviel Blöcke, der Reward Halbiert werden soll
    def halveningAtBlocks(self): return self.halvening_at

    # Gibt an, wieviel Prozent des Coins Verbrannt werden sollen, wenn mit ihm Gebühren gezahlt werden
    def burningFeePrecAtTransaction(self): return self.txn_fee_burning_perc

    # Gibt an ob ein Teil der gebühren vom Miner Verbrannt werden soll
    def minerForceBurnFee(self): return bool(self.burnable == True and self.txn_fee_burning == True)

    # Gibt die Gesamtmenge an
    def totalSupply(self, PrimaryUnit=False):
        if self.halveningIsEnabled() == False: return -1
        from apollon.amath import tsc
        if PrimaryUnit == True: return self.calcSmallestToPUnit(tsc(self.mine_reward, self.halvening_at, self.decimal_places))
        else: return tsc(self.mine_reward, self.halvening_at, self.decimal_places)

    # Formartiert die kleinste Einheit in Haupteinheit um
    def calcSmallestToPUnit(self, recalcval):
        if isinstance(recalcval, int) == False: return None
        from apollon.amath import sutc
        return sutc(recalcval, self.decimal_places)

    # Formatiert die Haupteinheit in die kleinste einheit um
    def calcPToSmallest(self, recval):
        if isinstance(recval, str) == False: return None
        from apollon.amath import fstiwc
        return fstiwc(recval)
    
    # Gibt den Gesamten Coin als JSON aus
    def toJSON(self):
        # Es werden alle Coindaten abgespeichert
        bd = dict()
        bd['name'] = self.name
        bd['symbol'] = self.symbol
        bd['su_name'] = self.smallest_unit_name
        bd['su_symbol'] = self.smallest_unit_symbol
        bd['decimal_places'] = hex(self.decimal_places)
        bd['block_reward'] = hex(self.mine_reward)
        bd['reward_at_block'] = hex(self.reward_at_block)
        bd['halvening_at'] = hex(self.halvening_at)
        bd['burnable'] = self.burnable
        bd['burning_fee'] = hex(self.txn_fee_burning_perc)
        bd['coind_id'] = self.getCoinID()
        return bd

    # Erstellt ein Coin aus einem JSON String
    @classmethod
    def fromJSON(cls, jsonString, NetwokCheckSum, ChainSeed):
        # Es wird geprüft ob alle benötigten Felder vorhanden sind
        if ('name' in jsonString) == False: raise Exception('Invalid object')
        if ('symbol' in jsonString) == False: raise Exception('Invalid object')
        if ('su_name' in jsonString) == False: raise Exception('Invalid object')
        if ('su_symbol' in jsonString) == False: raise Exception('Invalid object')
        if ('decimal_places' in jsonString) == False: raise Exception('Invalid object')
        if ('block_reward' in jsonString) == False: raise Exception('Invalid object')
        if ('reward_at_block' in jsonString) == False: raise Exception('Invalid object')
        if ('halvening_at' in jsonString) == False: raise Exception('Invalid object')
        if ('burnable' in jsonString) == False: raise Exception('Invalid object')
        if ('burning_fee' in jsonString) == False: raise Exception('Invalid object')
        if ('coind_id' in jsonString) == False: raise Exception('Invalid object')

        # Es wird geprüft ob die Datentypen korrekt sind
        if isinstance(jsonString['name'], str) == False: raise Exception('Invalid Coinname Type, only str allowed')
        if isinstance(jsonString['symbol'], str) == False: raise Exception('Invalid Coinsymbol Type, only str allowed')
        if isinstance(jsonString['su_name'], str) == False: raise Exception('Invalid Coinname Type, only str allowed')
        if isinstance(jsonString['su_symbol'], str) == False: raise Exception('Invalid Coinsymbol Type, only str allowed')
        if isinstance(jsonString['decimal_places'], str) == False: raise Exception('Invalid Decimal Places Type, only str allowed')
        if isinstance(jsonString['block_reward'], str) == False: raise Exception('Invalid Blockreward Type, only str allowed')
        if isinstance(jsonString['reward_at_block'], str) == False: raise Exception('Invalid Block Reward Type, only str allowed')
        if isinstance(jsonString['halvening_at'], str) == False: raise Exception('Invalid Halving at Type, only str allowed')
        if isinstance(jsonString['burnable'], bool) == False: raise Exception('Invalid Burnable Type, only bool allowed')
        if isinstance(jsonString['burning_fee'], str) == False: raise Exception('Invalid Burningfee Type, only str allowed')
        if isinstance(jsonString['coind_id'], str) == False: raise Exception('Invalid CoindID Type, only str allowed')

        # Das Coinobjekt wird erstellt
        nwo = cls(
            Name=jsonString['name'],
            Symbol=jsonString['symbol'],
            SmallestUnitName=jsonString['su_name'],
            SmallestUnitSymbol=jsonString['su_symbol'],
            DecimalPlaces=int(jsonString['decimal_places'], 16),
            NetworkCHSum=NetwokCheckSum,
            ChainSeed=ChainSeed,
            MineReward=int(jsonString['block_reward'], 16),
            HalvingToEndNewCoin=True,
            TotalHalvenings=False,
            RewardAtBlock=int(jsonString['reward_at_block'], 16),
            HalvinAtBlocks=int(jsonString['halvening_at'], 16),
            Burnable=jsonString['burnable'],
            TxnFeeBurning=bool(int(jsonString['burning_fee'], 16) != 0),
            TxnFeeBurningPerc=int(jsonString['burning_fee'], 16)
        )
        # Die CoinID wird geprüft
        if nwo.getCoinID() != jsonString['coind_id']: 
            print(nwo.getCoinID())
            print(jsonString['coind_id'])
            raise Exception('Invalid Exception')

        # Das Coin Objekt wird zurückgegeben
        return nwo

## Speichert die Werte eines Coins ab und macht diese berechenbar
class CoinValueUnit(object):
    def __init__(self, CoinObj): self.coin_obj = CoinObj; self.total_value = 0
    def __str__(self): return "{} {}".format(self.total_value, self.coin_obj.getSymbol(True))
    def __eq__(self, other):
        if isinstance(other, CoinValueUnit) == False: return False
        return self.coin_obj.getCoinID(True) == other.coin_obj.getCoinID(True)
    def __sub__(self, other):
        if isinstance(other, CoinValueUnit) == False and isinstance(other, int) == False: return None
        if isinstance(other, int) == True:
            nwv = CoinValueUnit(self.coin_obj)
            nwv.add(self.total_value - other)
            return nwv
        if self.coin_obj == other.coin_obj:
            nwv = CoinValueUnit(self.coin_obj)
            nwv.add(self.total_value - other.total_value)
            return nwv
    def __le__(self,p2):
        if self.coin_obj != p2.coin_obj: return False
        return self.total_value <= p2.total_value
    def __ge__(self, p2):
        if self.coin_obj != p2.coin_obj: return False
        return self.total_value >= p2.total_value
    def add(self,ValueX): self.total_value += ValueX
    def get(self, AsSmallUnit=True):
        if AsSmallUnit == True: return self.total_value
        else: return self.coin_obj.calcSmallestToPUnit(self.total_value)
    def getFull(self, AsSmallUnit=False):
        if AsSmallUnit == True: return "{} {}".format(self.total_value, self.coin_obj.getSymbol(True))
        else: 
            r = self.coin_obj.calcSmallestToPUnit(self.total_value)
            if r == None: return "ERROR"
            return "{} {}".format(r, self.coin_obj.getSymbol(False))
    def coin(self): return self.coin_obj

# Prüft ob es sich um einen Zulässigen Coin handelt, der Coin muss der Chain bekannt sein
def isValidateCoin(coinobj):
    # Es wird geprüft ob es sich um ein Coin Objekt handelt
    if isinstance(coinobj, Coin) == False and isinstance(coinobj, str) == False: return False # Es handelt sich nicht um ein Coin Objekt
    # Es wird geprüft ob der Verwendete Coin in der Liste der Verfügbaren Coins vorhanden ist
    from apollon import gv_
    for i in gv_.ChainRoot.getCoins():
        if i == coinobj: return True    # Der Aktuelle Coin ist zulässig
    return False    # Der Aktuelle Coin ist nicht zulässig