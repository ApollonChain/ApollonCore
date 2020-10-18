
""" Default Objects """

## CoinBaseInput UTXO ## TODO
class CoinbaseInUtxo(object):
    def __init__(self, BlockHeight, CoinObj, Value, OneTimeRewardHashBytes):
        # Es wird geprüft ob ein gültiger Wert Übergeben wurde
        assert isinstance(Value, int) and Value >= 1

        # Die Daten werden in das Objekt geschrieben
        self.coin_obj = CoinObj                                 # Speichert den Aktuellen Coin ab
        self.value = Value                                      # Speichert den Wert ab, welche mit diesem UTXIO übertragen wurde
        self.block_height = BlockHeight                         # Speichert die Nummer des Aktuellen Blocks ab
        self.one_time_reward_hash = OneTimeRewardHashBytes      # Speichert den einmaligen Hashwert ab
        self.place_in_transaction = None                        # Speichert die Position innterhalb der Transaktion ab
    
    # Gibt die Byte größe des Objektes aus
    def getByteSize(self):
        if self.place_in_transaction is None: return None
        total_size = 0
        total_size += len(self.coin_obj.getCoinID(True))
        total_size += len(str(self.value))
        total_size += len(str(self.place_in_transaction))
        total_size += len(self.one_time_reward_hash)
        return total_size

    # Gibt einen Hash des UTXO's aus
    def getHash(self, AsBytes=False):
        if self.place_in_transaction is None: return None
        import hashlib, base58
        hli = hashlib.sha3_256()
        hli.update(str(self.block_height).encode())
        hli.update(str(self.value).encode())
        hli.update(self.coin_obj.getCoinID(True))
        hli.update(str(self.place_in_transaction).encode())
        hli.update(self.one_time_reward_hash)
        if AsBytes == True: return hli.digest()
        else: from apollon import BASE58_BET; return base58.b58encode(hli.digest(), alphabet=BASE58_BET).decode()

    # Gibt den Wert des UTXO aus
    def getCoinValue(self, InSmallestUnit=True):
        if InSmallestUnit == True: return self.value
        else: return self.coin_obj.calcSmallestToPUnit(self.value)

    # Gibt den Coin des UTXO aus
    def getCoin(self): return self.coin_obj

    # Gibt die Position des UTXOS innerhalb einer Transaktion aus
    def getHeight(self): return self.place_in_transaction

    # Gibt an ob das UTXO verwendet werden kann
    def isUsinglabel(self): 
        # Es wird geprüft ob alle benötigten werte beschrieben wurden
        if self.coin_obj is None: return False
        if self.value is None: return False
        if self.block_height is None: return False
        return True

    # Gibt den OneTimeHash des Rewards aus
    def getOneTimeHash(self, AsBytes=False):
        if AsBytes == True: return self.one_time_reward_hash
        else: from apollon.utils import encodeBase58; return encodeBase58(self.one_time_reward_hash)

    # Gibt den UTXO Typ aus
    def getType(self): return 'CBRW'

    # Gibt das UTXO als JSON aus
    def toJSON(self):
        from apollon.utils import encodeBase58
        root_dict = dict()
        root_dict['type'] = 'cbiu'
        root_dict['hash'] = self.getHash()
        root_dict['coin'] = self.coin_obj.getCoinID()
        root_dict['value'] = str(self.value)
        root_dict['height'] = self.place_in_transaction
        root_dict['reward_hash'] = encodeBase58(self.one_time_reward_hash)
        return root_dict

## Fee Input UTXO ## TODO
class FeeInputUtxo(object):
    def __init__(self, BlockHeight, CoinObj, Value, *Transactions):
        # Es wird geprüft ob ein gültiger Wert Übergeben wurde
        assert isinstance(Value, int) and Value >= 1

        # Die Daten werden in das Objekt geschrieben
        self.coin_obj = CoinObj                         # Speichert den Aktuellen Coin ab
        self.value = Value                              # Speichert den Wert ab, welche mit diesem UTXIO übertragen wurde
        self.block_height = BlockHeight                 # Speichert die Nummer des Aktuellen Blocks ab
        self.transaction_hashes = list()                # Speichert die Hashes der Verwendeten Transaktionen
        self.place_in_transaction = None                # Speichert die Position innterhalb der Transaktion ab

        # Die Hashes der Transaktionen werden extrahiert
        from apollon.transaction import SignedTransaction
        for i in Transactions:
            if isinstance(i, SignedTransaction) == True: self.transaction_hashes.append(i.getTxHash(True))
            elif isinstance(i, bytes) == True: self.transaction_hashes.append(i)
            else: raise Exception('Invalid Transaction Hash')
    
    # Gibt die Byte größe des Objektes aus
    def getByteSize(self):
        if self.place_in_transaction is None: return None
        total_size = 0
        total_size += len(self.coin_obj.getCoinID(True))
        total_size += len(str(self.value))
        total_size += len(str(self.place_in_transaction))
        return total_size

    # Gibt einen Hash des UTXO's aus
    def getHash(self, AsBytes=False):
        if self.place_in_transaction is None: return None
        import hashlib, base58
        hli = hashlib.sha3_256()
        hli.update(str(self.block_height).encode())
        hli.update(str(self.value).encode())
        hli.update(self.coin_obj.getCoinID(True))
        hli.update(str(self.place_in_transaction).encode())
        if AsBytes == True: return hli.digest()
        else: from apollon import BASE58_BET; return base58.b58encode(hli.digest(), alphabet=BASE58_BET).decode()

    # Gibt den Wert des UTXO aus
    def getCoinValue(self, InSmallestUnit=True): return self.value

    # Gibt den Coin des UTXO aus
    def getCoin(self): return self.coin_obj

    # Gibt die Position des UTXOS innerhalb einer Transaktion aus
    def getHeight(self): return self.place_in_transaction

    # Gibt an ob das UTXO verwendet werden kann
    def isUsinglabel(self): 
        # Es wird geprüft ob alle benötigten werte beschrieben wurden
        if self.coin_obj is None: return False
        if self.value is None: return False
        if self.block_height is None: return False
        return True

    # Gibt den UTXO Typ aus
    def getType(self): return 'CBFU'

    # Gibt das UTXO als JSON aus
    def toJSON(self):
        root_dict = dict()
        root_dict['type'] = 'cbfi'
        root_dict['hash'] = self.getHash()
        root_dict['coin'] = self.coin_obj.getCoinID()
        root_dict['value'] = str(self.value)
        root_dict['height'] = self.place_in_transaction
        return root_dict

## Eingangs UTXO ##
class LagacyInUtxo(object):
    # Erstellt das UTXO
    def __init__(self, OutTransactionHash, ReciverAddress, OutUTXOHash, OutUTXOHeight, OutUTXOCoinObj, OutUtxoAmount):
        from apollon.transaction import SignedTransaction, CoinbaseTransaction

        # Die Daten werden in das Object geschrieben
        self.in_account_address = ReciverAddress
        self.out_transaction_id = OutTransactionHash
        self.out_utxo_hash = OutUTXOHash
        self.coin_vlaue = OutUtxoAmount
        self.coin = OutUTXOCoinObj
        self.out_utxo_height = OutUTXOHeight
        self.place_in_transaction = None

    # Gibt die Byte größe des Objektes aus
    def getByteSize(self):
        if self.place_in_transaction is None: return None
        total_size = 0
        total_size += len(self.out_transaction_id)
        total_size += len(str(self.out_utxo_height))
        total_size += len(self.out_utxo_hash)
        total_size += self.in_account_address.getByteSize()
        total_size += len(self.coin.getCoinID(True))
        total_size += len(str(self.coin_vlaue))
        total_size += len(str(self.place_in_transaction))
        return total_size

    # Gibt den aktuellen Hash des InUtxo aus
    def getHash(self, AsBytes=False):
        if self.place_in_transaction is None: return None
        import hashlib, base58
        hli = hashlib.sha3_256()
        hli.update(self.out_transaction_id)
        hli.update(str(self.out_utxo_height).encode())
        hli.update(self.out_utxo_hash)
        hli.update(self.in_account_address.getHash(True))
        hli.update(self.coin.getCoinID(True))
        hli.update(str(self.coin_vlaue).encode())
        hli.update(str(self.place_in_transaction).encode())
        if AsBytes == True: return hli.digest()
        else: from apollon import BASE58_BET; return base58.b58encode(hli.digest(), alphabet=BASE58_BET).decode()

    # Gibt den Wert des UTXO aus
    def getCoinValue(self, InSmallestUnit=True): return self.coin_vlaue

    # Gibt den Coin des UTXO aus
    def getCoin(self): return self.coin

    # Gibt die TrabsaktionsID an, mit welchem dieses InUtxo erzeugt wurde
    def getOutTransactionTxn(self, AsBytes=False): 
        from apollon.utils import encodeBase58
        if AsBytes == True: return self.out_transaction_id
        else: return encodeBase58(self.out_transaction_id)
    
    # Gibt die Höhe des Ausgangs Utxos aus
    def getOutUtxoHeight(self): return self.out_utxo_height

    # Gibt den Hash des Ausgangs Utxos aus
    def getOutUtxoHash(self, AsBytes=False):
        from apollon.utils import encodeBase58
        if AsBytes == True: return self.out_utxo_hash
        else: return encodeBase58(self.out_utxo_hash)
 
    # Gibt die Account Adresse des Utxos aus
    def getInAccountAddress(self): return self.in_account_address

    # Gibt die Position des UTXOS innerhalb einer Transaktion aus
    def getHeight(self): return self.place_in_transaction

    # Gibt an ob das UTXO verwendet werden kann
    def isUsinglabel(self):
        # Es wird geprüft ob alle erforderlichen Daten vorhanden sind
        if self.in_account_address is None: return False
        if self.out_transaction_id is None: return False
        if self.out_utxo_hash is None: return False
        if self.coin_vlaue is None: return False
        if self.coin is None: return False
        if self.out_utxo_height is None: return False
        return True

    # Gibt das UTXO als JSON aus
    def toJSON(self):
        root_dict = dict()
        root_dict['type'] = 'lgiu'
        root_dict['out_txn'] = self.getOutTransactionTxn()
        root_dict['out_utxo_height'] = str(self.getOutUtxoHeight())
        root_dict['out_utxo_hash'] = str(self.getOutUtxoHash())
        root_dict['hash'] = self.getHash()
        root_dict['reciver'] = self.in_account_address.toStr()
        root_dict['coin'] = self.coin.getCoinID()
        root_dict['value'] = str(self.coin_vlaue)
        root_dict['height'] = self.place_in_transaction
        return root_dict

## Ausgangs UTXO ##
class LagacyOutUtxo(object):
    # Erstellt das UTXO
    def __init__(self, ReciverAccountAddress, CoinValue, SelectedCoin, *InUtxos):
        # Es wird geprüft ob es sich um eine gültige Adresse handelt
        from apollon.apollon_address import LagacyAddress, BlockchainAddress
        if isinstance(ReciverAccountAddress, LagacyAddress) == False and isinstance(ReciverAccountAddress, BlockchainAddress) == False: raise Exception('Only Address Object allowed')
        if ReciverAccountAddress.canUse() == False: raise Exception('Address isn uselabel')

        # Es wird geprüft ob ein zulässiger Wert übergeben wurde
        if isinstance(CoinValue, int) == False: raise Exception('Only int as Value allowed')
        if CoinValue <= 0 and CoinValue != 0: raise Exception('Invalid Value')

        # Es wird geprüft ob ein gültiger Coin verwendet wird
        from apollon.coin import Coin, isValidateCoin
        if isinstance(SelectedCoin, Coin) == False: raise Exception('Only coin objects can be transferred as coins.')
        if isValidateCoin(SelectedCoin) == False: raise Exception('Unknown coin')

        # Die Daten werden in das Objekt geschrieben
        self.reciver_account = ReciverAccountAddress
        self.value = CoinValue
        self.coin_obj = SelectedCoin
        self.in_utxos_hashes = list()
        self.place_in_transaction = None

        # Die EingansUTXOs werden geprüft
        for i in InUtxos:
            if isinstance(i, LagacyInUtxo) == True:
                if i.getCoin() == self.coin_obj and (i.getCoinValue() >= self.value and i.getCoinValue() != self.value): self.in_utxos_hashes.append(i)
                else: raise Exception('Input and Output need same Coin')
            elif isinstance(i, CoinbaseInUtxo) == True:
                if i.getCoin() == self.coin_obj: self.in_utxos_hashes.append(i)
                else: raise Exception('Input and Output need same Coin')
            else: raise Exception('Invalid Input UTXOS {}'.format(type(i)))

    # Gibt die Byte größe des Objektes aus
    def getByteSize(self):
        if self.place_in_transaction is None: return None
        bsize = 0
        bsize += self.reciver_account.getByteSize()
        bsize += len(str(self.value))
        bsize += len(self.coin_obj.getCoinID(True))
        bsize += len(str(self.place_in_transaction))
        return bsize

    # Gibt den InputUTXO Hash aus (Setzt sich aus allen Hashes der Inputs zusammen)
    def getInputRootHash(self, AsBytes=False):
        from hashlib import sha3_256; import base58; from apollon import BASE58_BET
        hli = sha3_256()
        for i in self.in_utxos_hashes: hli.update(i.getHash(True))
        if AsBytes == True: return hli.digest()
        else: return base58.b58encode(hli.digest(), alphabet=BASE58_BET).decode()
        
    # Gibt den Hash des OutUtxos aus
    def getHash(self, AsBytes=False):
        if self.place_in_transaction is None: return None
        from hashlib import sha3_256; import base58; from apollon import BASE58_BET
        hli = sha3_256()
        hli.update(self.reciver_account.getHash(True))
        hli.update(str(self.value).encode())
        hli.update(self.coin_obj.getCoinID(True))
        hli.update(str(self.place_in_transaction).encode())
        hli.update(self.getInputRootHash(True))
        if AsBytes == True: return hli.digest()
        else: return base58.b58encode(hli.digest(), alphabet=BASE58_BET).decode()

    # Gibt den Bertrag aus
    def getCoinValue(self, InSmallestUnit=True): return self.value

    # Gibt den Verwendeten Coin aus
    def getCoin(self): return self.coin_obj

    # Gibt den UTXO Typ aus
    def getType(self): return 'LOO'

    # Gibt die Position des UTXOS innerhalb einer Transaktion aus
    def getHeight(self): return self.place_in_transaction

    # Gibt die Adresse des Empfängers aus
    def getReciverAddress(self): return self.reciver_account

    # Gibt an ob das UTXO verwendet werden kann
    def isUsinglabel(self):
        # Es wird geprüft ob die benötigten Daten vorhanden sind
        if self.reciver_account is None: return False
        if self.value is None: return False
        if self.coin_obj is None: return False
        if self.in_utxos_hashes is None: return False
        if len(self.in_utxos_hashes) == 0: return False
        return True

    # Gibt das UTXO als JSON aus
    def toJSON(self):
        root_dict = dict()
        root_dict['type'] = 'lgou'
        root_dict['hash'] = self.getHash()
        root_dict['reciver'] = self.reciver_account.toStr()
        root_dict['coin'] = self.coin_obj.getCoinID()
        root_dict['value'] = str(self.value)
        root_dict['height'] = self.place_in_transaction
        in_utxos = list()
        for i in self.in_utxos_hashes: in_utxos.append(i.getHash())
        root_dict['in'] = in_utxos
        return root_dict



""" Storage Objects """

## Storage LagacyOutput Utxos Object ##
class ST_LagacyOutUtxo(LagacyOutUtxo):
    # Erstellt ein neues Ausgangsobjekt
    def __init__(self, ReciverAccountAddress, CoinValue, SelectedCoin, Spended ,*InUtxos):
        super().__init__(ReciverAccountAddress, CoinValue, SelectedCoin, *InUtxos)
        self.spended = Spended
    
    # Gibt an ob der Ausgang ausgegeben wurde
    def isSpend(self): return self.spended
   
    # Wandelt den Ausgang in JSON um
    def toJSON(self):
        root_dict = dict()
        root_dict['type'] = 'lgou'
        root_dict['spend'] = self.isSpend()
        root_dict['hash'] = self.getHash()
        root_dict['reciver'] = self.reciver_account.toStr()
        root_dict['coin'] = self.coin_obj.getCoinID()
        root_dict['value'] = str(self.value)
        root_dict['height'] = self.place_in_transaction
        in_utxos = list()
        for i in self.in_utxos_hashes: in_utxos.append(i.getHash())
        root_dict['in'] = in_utxos
        return root_dict



""" Funktionen """

# Erstellt ein eingangs UTXOs für die Gebühren
def createFeeInputUtxo(CoinObj, BlockHeight, *Transactions):
    from apollon.utxo import getTotalSumeFromInputs
    total_in = 0; in_transaction_hasches = list()
    for txni in Transactions:
        for feesi in txni.getFees():
            if feesi.coin() == CoinObj:
                if feesi.get() != 0: 
                    total_in += feesi.get(); in_transaction_hasches.append(txni)
    return FeeInputUtxo(BlockHeight, CoinObj, total_in, *in_transaction_hasches)

# Diese Funktion ermittelt aus allen Eingängen die Totale Summe
def getTotalSumeFromInputs(CoinObj, *InputLagacyUtxos):
    return 0
