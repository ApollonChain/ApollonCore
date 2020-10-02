
""" Default Objects """

## Unsignierte Standart Transaktion ##
class UnsignedTransaction:
    # Erstellt eine Unsignierte Transaktion
    def __init__(self, *Utxos):
        # Es wird geprüft ob zulässige Daten übergeben wurden
        from apollon.utxo import LagacyInUtxo, LagacyOutUtxo
        for i in Utxos: 
            assert isinstance(i, LagacyInUtxo) or isinstance(i, LagacyOutUtxo)
            if i.isUsinglabel() == False: raise Exception('Invalid UTXO')

        # Die Objekt Variabeln werden erstellt
        self.in_utxos = list(); self.out_utxos = list()
        self.current_signatures = list()

        # Die UTXOS werden zugeordnet
        ins = 0; outs = 0
        for i in Utxos:
            if isinstance(i, LagacyInUtxo) == True: i.place_in_transaction = ins; self.in_utxos.append(i); ins += 1
            elif isinstance(i, LagacyOutUtxo) == True: i.place_in_transaction = outs; self.out_utxos.append(i); outs +=1
            else: raise Exception('Invalid UTXO Type')
        
        # Es wird final geprüft ob es sich um eine gültige Transaktion handelt
        if self.isValidateObject() == False: 
            self.in_utxos.clear(); self.out_utxos.clear(); raise Exception('Cant create invalid transaction')

    # Gibt alle Eingehenden Utxos aus
    def getInUtxos(self): return self.in_utxos

    # Gibt alle ausgehenden Utxos aus
    def getOutUtxos(self): return self.out_utxos

    # Gibt an wieviel insgesamt Eingeht
    def getTotalIn(self):
        from apollon.coin import CoinValueUnit
        tos = list()
        for i in self.in_utxos:
            found = False
            for x in tos:
                if x.coin() == i.getCoin(): x.add(i.getCoinValue()); found = True; break
            if found == False:
                na = CoinValueUnit(i.getCoin())
                na.add(i.getCoinValue())
                tos.append(na)
        return tos

    # Gibt an wieviele insgesamt raus geht
    def getTotalOut(self): 
        from apollon.coin import CoinValueUnit
        tos = list()
        for i in self.out_utxos:
            found = False
            for x in tos:
                if x.coin() == i.getCoin(): x.add(i.getCoinValue()); found = True; break
            if found == False:
                na = CoinValueUnit(i.getCoin())
                na.add(i.getCoinValue())
                tos.append(na)
        return tos

    # Gibt die Aktulle Höhe der Gebühren aus
    def getFees(self):
        from apollon.coin import CoinValueUnit
        total_in = self.getTotalIn()
        total_out = self.getTotalOut()
        rwt = list()
        for i in total_in:
            f = False
            for o in total_out:
                if i == o: rwt.append(i - o); f = True
            if f == False: rwt.append(i)
        for i in rwt: assert i.total_value >= 0 and i.total_value != 0
        return rwt
    
    # Gibt den Hash zum Signieren aus
    def getSignHash(self, AsBytes):
        from hashlib import sha3_256; hli = sha3_256()
        for i in self.in_utxos: hli.update(i.getHash(True))
        for i in self.out_utxos: hli.update(i.getHash(True))
        if AsBytes == True: return hli.digest()
        else: import base58; from apollon import BASE58_BET; return base58.b58encode(hli.digest(), alphabet=BASE58_BET).decode()

    # Gibt alle Verwendeten Coins aus
    def getUsedCoins(self):
        coinlist = list()
        for i in self.in_utxos:
            f = False
            for x in coinlist:
                if x == i.getCoin(): f = True; break
            if f == False: coinlist.append(i.getCoin())
        return coinlist

    # Gibt die Byte Größe der Transaktion aus
    def getByteSize(self):
        bsize = 0
        for i in self.in_utxos: bsize += i.getByteSize()
        for i in self.out_utxos: bsize += i.getByteSize()
        for i in self.current_signatures: bsize += len(i)
        bsize += len(self.getSignHash(True))
        return bsize

    # Gibt alle Vorhandenen Signaturen aus
    def getAllSignatures(self): return list(self.current_signatures)

    # Gibt an ob das Objekt bereit zum Siginieren ist
    def isSignlabel(self): return bool(self.in_utxos != 0 and self.out_utxos != 0 and len(self.getFees()) != 0)

    # Gibt an wieviele Signaturen insgesamt benötigt werden
    def getTotalSignaturesRequired(self):
        sign_addresses = list()
        for i in self.in_utxos:
            isin = False
            for x in sign_addresses:
                if x == i: isin = True; break
            if isin == False: sign_addresses.append(i)
        return len(sign_addresses)

    # Gibt an weiviele Signaturen noch benötugt werden
    def getStillSignaturesRequired(self): return len(self.getStillSignatureAddresses())

    # Gibt die Adressen aus, von denen noch eine Signatur benötigt wird
    def getStillSignatureAddresses(self):
        sign_addresses = list(self.getNeededSignatureAddresses())
        # Es wird geprüft welche Signaturen bereits vorhanden sind
        for i in sign_addresses:
            for x in self.current_signatures:
                if i.getHash(True) == x.getSignerAddressHash(True): sign_addresses.remove(i)
        return sign_addresses

    # Gibt die Adressen an, von denen eine Signatur benötigt wird
    def getNeededSignatureAddresses(self):
        sign_addresses = list()
        for i in self.in_utxos:
            isin = False
            for x in sign_addresses:
                if x == i.getInAccountAddress(): isin = True; break
            if isin == False: sign_addresses.append(i.getInAccountAddress())
        return sign_addresses

    # Gibt an ob alle bedinnungen für ein Unsigniertes Objektes erfüllt sind
    def isValidateObject(self):
        # Es wird geporüft ob eingangs UTXOS vorhanden sind
        if len(self.in_utxos) <= 1 and len(self.in_utxos) != 1: self.out_utxos.clear(); return False

        # Es wird geprüft ob mindestens 1 Coin verwendet wird
        if len(self.getUsedCoins()) <= 1 and len(self.getUsedCoins()) != 1: return False

        # Es wird geprüft ob es sich um gültige Input und Output UTXOs handelt
        from apollon.utxo import LagacyInUtxo, LagacyOutUtxo
        for i in list(self.in_utxos + self.out_utxos):
            if isinstance(i,LagacyInUtxo) == False and isinstance(i, LagacyOutUtxo) == False: return False

        # Es wird geprüft ob die Eingangs UTXO's größer als die Ausgangs UTXO sind
        for i in self.getTotalOut():
            found = False
            for x in self.getTotalIn():
                if i.coin() == x.coin():
                    if i >= x and i.get() != x.get(): return False
                    elif i.get() == x.get(): return False
                    else: found = True; break
            if found == False: return False

        # Es wird geprüft ob Input UTXO mehrfach verwendet werden
        for i in self.in_utxos:
            awio = 0
            for x in self.in_utxos:
                # Es wird geprüft ob die Hashes des UTXOS die gleichen sind
                if i.out_utxo_hash == x.out_utxo_hash: awio += 1
                # Es wird gepprüf ob die Ausgangs UTXO's die gleichen sind
            if awio >= 1 and awio != 1: return False

        # Das Objekt ist Valide
        return True

    # Gibt an ob die Vorhandenen Signaturen gültig sind
    def avaibleSignaturesValidate(self): return True

    # Gibt an ob aus dem Objekt ein Signiertes Objekt gebaut werden könnte
    def cannBuildSignatedTransaction(self):
        # Es wird geprüft ob noch signaturen benötigt werden
        if self.getStillSignaturesRequired() != 0: return False # Die Transaktion kann nicht gebaut werden

        # Es wird geprüft ob alle Signaturen gültig sind
        if self.avaibleSignaturesValidate() != True: return False

        # Die Transaktion kann gebaut werden
        return True

## Signierte Standart Transaktion ##
class SignedTransaction:
    def __init__(self):
        self.input_utxos = list()
        self.output_utxos = list()
        self.signatures = list()
        self.place_in_block = None

    # Gibt die Eingangsutxos aus
    def getInputUxos(self): return list(self.input_utxos)

    # Gibt an, an welcher Position innerhalb des Blockes sich die Transaktion befindet
    def getHeightInBlock(self): return self.place_in_block

    # Gibt die Ausgangsutxos aus
    def getOutputUtxos(self, ForSpeficAddress=None, SpeficCoin=None):
        if ForSpeficAddress is None and SpeficCoin is None: return list(self.output_utxos)
        resolv = list()
        for i in self.output_utxos:
            if ForSpeficAddress != None and SpeficCoin == None and i.getReciverAddress() == ForSpeficAddress: resolv.append(i)
            elif ForSpeficAddress != None and SpeficCoin != None and i.getReciverAddress() == ForSpeficAddress and i.getCoin() == SpeficCoin: return i
        if len(resolv) == 0: return None
        return resolv

    # Gibt alle Signaturen aus
    def getSignatures(self): return list(self.signatures)

    # Gibt an wieviel insgesamt Eingeht
    def getTotalIn(self):
        from apollon.coin import CoinValueUnit
        tos = list()
        for i in self.input_utxos:
            found = False
            for x in tos:
                if x.coin() == i.getCoin(): x.add(i.getCoinValue()); found = True; break
            if found == False:
                na = CoinValueUnit(i.getCoin())
                na.add(i.getCoinValue())
                tos.append(na)
        return tos

    # Gibt an wieviele insgesamt raus geht
    def getTotalOut(self): 
        from apollon.coin import CoinValueUnit
        tos = list()
        for i in self.output_utxos:
            found = False
            for x in tos:
                if x.coin() == i.getCoin(): x.add(i.getCoinValue()); found = True; break
            if found == False:
                na = CoinValueUnit(i.getCoin())
                na.add(i.getCoinValue())
                tos.append(na)
        return tos

    # Gibt die Aktulle Höhe der Gebühren aus
    def getFees(self):
        from apollon.coin import CoinValueUnit
        total_in = self.getTotalIn()
        total_out = self.getTotalOut()
        rwt = list()
        for i in total_in:
            f = False
            for o in total_out:
                if i == o: rwt.append(i - o); f = True
            if f == False: rwt.append(i)
        for i in rwt: assert i.total_value >= 0 and i.total_value != 0
        return rwt

    # Gibt alle Verwendeten Coins aus
    def getUsedCoins(self):
        coinlist = list()
        for i in self.input_utxos:
            f = False
            for x in coinlist:
                if x == i.getCoin(): f = True; break
            if f == False: coinlist.append(i.getCoin())
        return coinlist

    # Gibt ob das Objekt Valide ist
    def objectIsValidate(self):
        # Es wird geprüft ob mindestens 1 eingang und ein ausgang vorhanden ist
        if len(self.input_utxos) <= 1 and len(self.input_utxos) != 1: return False
        if len(self.output_utxos) <= 1 and len(self.output_utxos) != 1: return False

        # Es wird geprüft ob mindestens eine Signatur vorhanden ist
        if len(self.signatures) <= 1 and len(self.signatures) != 1: return False

        # Es wird geprüft ob die Ausgänge kleiner als die Eingänge sind

        # Es wird geprüft ob für jede benötigte Adresse, eine Signatur vorhanden ist
        total_addresses = list()
        for i in self.input_utxos:
            in_lis = False
            for x in total_addresses:
                if i.getInAccountAddress().getHash(True) == x.getHash(True): in_lis = True; break
            if in_lis == False: total_addresses.append(i.getInAccountAddress())

        # Es wird geprüft ob für alle Adressen eine Signatur vorhanden ist
        for i in self.signatures:
            for x in total_addresses:
                if i.getSignerAddressHash(True) == x.getHash(True): total_addresses.remove(x); break
        if len(total_addresses) != 0: return False  # Es ist nicht für jede Adresse eine Signatur vorhanden

        return True # Das Objekt ist Valide

    # Erstellt einen Hash aus allen Ein und Ausgängen
    def getRootHash(self, AsBytes=False):
        from hashlib import sha3_256; hli = sha3_256()
        for i in self.input_utxos: hli.update(i.getHash(True))
        for i in self.output_utxos: hli.update(i.getHash(True))
        if AsBytes == True: return hli.digest()
        else: import base58; from apollon import BASE58_BET; return base58.b58encode(hli.digest(), alphabet=BASE58_BET).decode()

    # Gibt die Transaktions ID aus
    def getTxHash(self, AsBytes=False):
        from hashlib import sha3_384; hli = sha3_384()
        for i in self.input_utxos: hli.update(i.getHash(True))
        for i in self.output_utxos: hli.update(i.getHash(True))
        for i in self.signatures: hli.update(i.getHash(True))
        if AsBytes == True: return hli.digest()
        else: import base58; from apollon import BASE58_BET; return base58.b58encode(hli.digest(), alphabet=BASE58_BET).decode()

    # Gibt an ob alle vorhandenen Signaturen korrekt sind
    def signaturesAreValidate(self):
        # Es wird geprüft ob mindestens eine Signatur vorhanden ist
        if len(self.signatures) <= 1 and len(self.signatures) != 1: return False

        # Es werden alle Signaturen einer Adresse zu geordnet und geprüft
        total_addresses = list()
        for i in self.input_utxos:
            in_lis = False
            for x in total_addresses:
                if i.getInAccountAddress().getHash(True) == x.getHash(True): in_lis = True; break
            if in_lis == False: total_addresses.append(i.getInAccountAddress())
        for i in self.signatures:
            for x in total_addresses:
                if i.getSignerAddressHash(True) == x.getHash(True):
                    try: x.validateSignature(i, self.getRootHash(True))
                    except: return False
                    total_addresses.remove(x)
        
        # Es wird geprüft ob alle benötigten Signaturen vorhanden waren
        if len(total_addresses) != 0: return False

        # Es handelt sich um eine gültige Transaktion
        return True

    # Gibt die Größe der Transaktion aus
    def getByteSize(self):
        total = 0
        for i in self.input_utxos: total += i.getByteSize()
        for i in self.output_utxos: total += i.getByteSize()
        for i in self.signatures: total += i.getSize(True)
        if self.place_in_block == None: return 0
        total += len(str(self.place_in_block))
        return total

    # Gibt an ob alle bedinnungen für ein Unsigniertes Objektes erfüllt werden
    def isValidateObject(self):
        # Es wird geporüft ob eingangs UTXOS vorhanden sind
        if len(self.input_utxos) <= 1 and len(self.output_utxos) != 1: self.input_utxos.clear(); return False

        # Es wird geprüft ob die Eingangs UTXO's größer als die Ausgangs UTXO sind
        for i in self.getTotalOut():
            found = False
            for x in self.getTotalIn():
                if i.coin() == x.coin():
                    if i >= x and i.get() != x.get(): return False
                    elif i.get() == x.get(): return False
                    else: found = True; break
            if found == False: return False

        # Es wird geprüft ob Input UTXO mehrfach verwendet werden
        for i in self.input_utxos:
            awio = 0
            for x in self.input_utxos:
                # Es wird geprüft ob die Hashes des UTXOS die gleichen sind
                if i.out_utxo_hash == x.out_utxo_hash: awio += 1
                # Es wird gepprüf ob die Ausgangs UTXO's die gleichen sind
            if awio >= 1 and awio != 1: return False

        # Das Objekt ist Valide
        return True

    # Gibt den Zeitstempel der Transaktion aus
    def getTimestamp(self, AsString=True): return 'Time'

    # Gibt das UTXO als JSON aus
    def toJSON(self):
        root_dict = dict()
        root_dict['type'] = 'lct'
        root_dict['txn'] = self.getTxHash()
        inl = list()
        ol = list()
        sigs = list()
        for i in self.input_utxos: inl.append(i.toJSON())
        for i in self.output_utxos: ol.append(i.toJSON())
        for i in self.signatures: sigs.append(i.toJSON())
        root_dict['inputs'] = inl
        root_dict['outputs'] = ol
        root_dict['signatures'] = sigs
        return root_dict

    # Erstellt eine Signierte Transaktion aus einer Unsignierten Transaktion welche jedoch alle benötigten Signaturen enthält
    @classmethod
    def createFinalFromUnsignedObjectWithSignatures(cls, UnsignedLagacyTransactionObj):
        # Es wird geprüft ob die erforderten Datentypen übergeben wurden
        assert isinstance(UnsignedLagacyTransactionObj, UnsignedTransaction)

        # Es wird geprüft ob das Objekt Valide ist
        assert UnsignedLagacyTransactionObj.isValidateObject() == True

        # Es wird geprüft, ob das Objekt im allgemeinen Signatur fähig ist
        assert UnsignedLagacyTransactionObj.isSignlabel() == True

        # Es wird geprüft ob alle benötigten Signaturen vorhnanden sind
        assert UnsignedLagacyTransactionObj.getStillSignaturesRequired() == 0

        # Es wird geprüft ob aus der Unsignierten Transaktion eine Signierte Transatkion gebaut werden kann
        assert UnsignedLagacyTransactionObj.cannBuildSignatedTransaction() == True

        
        ### Signierte Transaktion wird erstellt

        # Es wird ein leeres Signiertes Objekt erstellt
        clear_sig_trans = cls()
        
        # Die Eingangs UTXOs werden übertragen
        for i in UnsignedLagacyTransactionObj.in_utxos: clear_sig_trans.input_utxos.append(i)

        # Die Ausgangs UTXOs werden übertragen
        for i in UnsignedLagacyTransactionObj.out_utxos: clear_sig_trans.output_utxos.append(i)

        # Die Signaturen werden übertagen
        for i in UnsignedLagacyTransactionObj.current_signatures: clear_sig_trans.signatures.append(i)

        # Es wird geprüft ob das Objekt Valide ist
        assert clear_sig_trans.objectIsValidate() == True

        # Es wird geprüft ob alle benötigten Signaturen korrekt sind
        assert clear_sig_trans.signaturesAreValidate() == True

        # Das Objekt wird final erstellt
        return clear_sig_trans

## Coinbase Transaktion ##
class CoinbaseTransaction:

    from apollon.atime import ATimeString
    def __init__(self, *Utxos, BlockNo, TStamp=ATimeString.now()):
        self.coinbase_input_utxos = list()
        self.coinbase_output_utxos = list()
        self.place_in_block = None
        self.block_no = BlockNo
        
        # Die UTXOs werden Sortiert
        from apollon.utxo import CoinbaseInUtxo, LagacyOutUtxo, FeeInputUtxo
        ins = 0; outs = 0
        for i in Utxos: 
            if isinstance(i, CoinbaseInUtxo) == True: i.place_in_transaction = ins; self.coinbase_input_utxos.append(i); ins += 1
            elif isinstance(i, FeeInputUtxo) == True: i.place_in_transaction = ins; self.coinbase_input_utxos.append(i); ins += 1
            elif isinstance(i, LagacyOutUtxo) == True: i.place_in_transaction = outs; self.coinbase_output_utxos.append(i); outs += 1
            else: raise Exception('Unkown UTXO type {}'.format(type(i)))
        
        # Die Aktuelle Uhrzeit wird geschrieben
        self.timestamp = TStamp
        
        # Es wird geprüft ob es sich um eine Zulässige Transaktion handelt
        assert self.isValidateObject() == True

    # Gibt an, an welcher Position innerhalb des Blockes sich die Transaktion befindet
    def getHeightInBlock(self): return self.place_in_block

    # Gibt die Eingangsutxos aus
    def getInputUxos(self): return list(self.coinbase_input_utxos)

    # Gibt die Ausgangsutxos aus
    def getOutputUtxos(self, ForSpeficAddress=None, SpeficCoin=None):
        if ForSpeficAddress is None and SpeficCoin is None: return list(self.coinbase_output_utxos)
        resolv = list()
        for i in self.coinbase_output_utxos:
            if ForSpeficAddress != None and SpeficCoin == None and i.getReciverAddress() == ForSpeficAddress: resolv.append(i)
            elif ForSpeficAddress != None and SpeficCoin != None and i.getReciverAddress() == ForSpeficAddress and i.getCoin() == SpeficCoin: return i
        if len(resolv) == 0: return None
        return resolv

    # Gibt die TransactionsID aus
    def getTxHash(self, AsBytes=False):
        from hashlib import sha3_384
        hu = sha3_384()
        hu.update(str(self.block_no).encode())
        hu.update(self.timestamp.getHash(True))
        for i in self.coinbase_input_utxos: hu.update(i.getHash(True))
        for i in self.coinbase_output_utxos: hu.update(i.getHash(True))
        if AsBytes == True: return hu.digest()
        else: import base58; from apollon import BASE58_BET; return base58.b58encode(hu.digest(), alphabet=BASE58_BET).decode()

    # Gibt an wieviel insgesamt Eingeht
    def getTotalIn(self):
        from apollon.coin import CoinValueUnit
        tos = list()
        for i in self.coinbase_input_utxos:
            found = False
            for x in tos:
                if x.coin() == i.getCoin(): x.add(i.getCoinValue()); found = True; break
            if found == False:
                na = CoinValueUnit(i.getCoin())
                na.add(i.getCoinValue())
                tos.append(na)
        return tos

    # Gibt an wieviele insgesamt raus geht
    def getTotalOut(self): 
        from apollon.coin import CoinValueUnit
        tos = list()
        for i in self.coinbase_output_utxos:
            found = False
            for x in tos:
                if x.coin() == i.getCoin(): x.add(i.getCoinValue()); found = True; break
            if found == False:
                na = CoinValueUnit(i.getCoin())
                na.add(i.getCoinValue())
                tos.append(na)
        return tos

    # Gibt die Aktulle Höhe der Gebühren aus
    def getFees(self):
        from apollon.coin import CoinValueUnit
        total_in = self.getTotalIn()
        total_out = self.getTotalOut()
        rwt = list()
        for i in total_in:
            f = False
            for o in total_out:
                if i == o: rwt.append(i - o); f = True
            if f == False: rwt.append(i)
        for i in rwt: assert i.total_value == 0
        return rwt

    # Gibt alle Verwendeten Coins aus
    def getUsedCoins(self):
        coinlist = list()
        for i in self.coinbase_input_utxos:
            f = False
            for x in coinlist:
                if x == i.getCoin(): f = True; break
            if f == False: coinlist.append(i.getCoin())
        return coinlist

    # Gibt die Größe der Transaktion aus
    def getByteSize(self):
        total = 0
        for i in self.coinbase_input_utxos: total += i.getByteSize()
        for i in self.coinbase_output_utxos: total += i.getByteSize()
        if self.place_in_block == None: return 0
        if self.block_no == None: return 0
        total += len(str(self.place_in_block))
        total += len(str(self.block_no))
        return total

    # Gibt an ob alle bedinnungen für ein Unsigniertes Objektes erfüllt werden
    def isValidateObject(self):
        # Es wird geporüft ob eingangs UTXOS vorhanden sind
        if len(self.coinbase_input_utxos) <= 1 and len(self.coinbase_output_utxos) != 1: self.coinbase_output_utxos.clear(); return False

        # Es wird geprüft ob die Eingangs UTXO's gleichgroß mit den Ausgangs UTXO's sind
        for i in self.getTotalOut():
            found = False
            for x in self.getTotalIn():
                if i.coin() == x.coin():
                    if i.get() != x.get(): return False
                    else: found = True; break
            if found == False: return False

        # Es wird geprüft ob Input UTXO mehrfach verwendet werden
        from apollon.utxo import LagacyInUtxo
        for i in self.coinbase_input_utxos:
            if isinstance(i,LagacyInUtxo) == True:
                awio = 0
                for x in self.coinbase_input_utxos:
                    # Es wird geprüft ob die Hashes des UTXOS die gleichen sind
                    if i.out_utxo_hash == x.out_utxo_hash: awio += 1
                    # Es wird gepprüf ob die Ausgangs UTXO's die gleichen sind
                if awio >= 1 and awio != 1: return False

        # Das Objekt ist Valide
        return True

    # Gibt den Zeitstempel der Transaktion aus
    def getTimestamp(self): return self.timestamp

    # Gibt das UTXO als JSON aus
    def toJSON(self):
        root_dict = dict()
        root_dict['type'] = 'cbt'
        root_dict['tx_hash'] = self.getTxHash()
        inl = list()
        ol = list()
        for i in self.coinbase_input_utxos: inl.append(i.toJSON())
        for i in self.coinbase_output_utxos: ol.append(i.toJSON())
        root_dict['inputs'] = inl
        root_dict['outputs'] = ol
        return root_dict



""" Storage Objects """

class ST_CoinbaseTransaction(CoinbaseTransaction):
    def __init__(self, *Utxos, BlockNo, TStamp, Confirmations):
        super().__init__(*Utxos, BlockNo=BlockNo, TStamp=TStamp)
        self.confirmations = Confirmations
    def getConfirmations(self): return self.confirmations
    def isConfirmed(self): return self.confirmations != 0
    def toJSON(self):
        root_dict = dict()
        root_dict['type'] = 'cbt'
        root_dict['tx_hash'] = self.getTxHash()
        root_dict['in_block'] = self.inBlock()
        root_dict['confirmed'] = self.isConfirmed()
        root_dict['confirmations'] = self.getConfirmations()
        inl = list()
        ol = list()
        for i in self.coinbase_input_utxos: inl.append(i.toJSON())
        for i in self.coinbase_output_utxos: ol.append(i.toJSON())
        root_dict['inputs'] = inl
        root_dict['outputs'] = ol
        return root_dict
    def inBlock(self): return self.block_no