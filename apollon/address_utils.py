from apollon.apollon_address import LagacyAddress, BlockchainAddress, AddressTypes
from apollon.utils import encodeBase58, decodeBase58
from apollon import gv_, BASE58_BET
from apollon.coin import Coin
import hashlib


# Es wird geprüft ob die Blockchain geladen wurde
if gv_.ChainRoot is None: raise Exception('Not RootConfig, loaded')



""" Utils Objects """
## Address Utils ##
class AddressUtils:

    # Es wird geprüft ob es sich um eine Burning adresse handelt
    @staticmethod
    def isBurningAddress(AddressString):
        if isinstance(AddressString, str) == False: return False
        return str(AddressString).startswith('BURN')

    # Gibt an ob es sich um eine gültige Adresse handelt
    @staticmethod
    def isValidateLagacyAddress(*AddressData):
        for addr_i in AddressData:
            # Es wird geprüft ob es sich um einen String handelt
            if isinstance(addr_i, str) == False: return False

            # Speichert die Daten zwischen
            netw = None; addressh = None ;chsum = None; specorder = None

            # Es wird geprüft ob es sich um einen Burn Adresse handelt
            if AddressUtils.isBurningAddress(addr_i) == True:
                raddr_i = str(addr_i)[len('BURN'):]
                specorder = 'BURN'
                
                # Es wird versucht die Daten zu Extrahieren
                try: raddr_i = decodeBase58(raddr_i)
                except: return False

                # Es wird geprüft ob es sich um eine Lagacy Adresse handelt
                if b'LCA' != raddr_i[:3]: return False
                raddr_i = raddr_i[3:]

                # Es wird geprüft ob die Mindestlänge erfüllt wird
                if len(raddr_i) != 33: return False
            
                # Das Netzwerk wird extrahiert
                netw = raddr_i[:2]

                # Die Adresse wird extrahiert
                addressh = raddr_i[2:30]

                # Die Checksume wird extrahiert
                chsum = raddr_i[30:]
            else:
                # Es wird versucht die Daten zu Extrahieren
                try: raddr_i = decodeBase58(addr_i)
                except: return False

                # Es wird geprüft ob es sich um eine Lagacy Adresse handelt
                if b'L' != raddr_i[:1]: return False
                raddr_i = raddr_i[1:]

                # Es wird geprüft ob die Mindestlänge erfüllt wird
                if len(raddr_i) != 37: return False
            
                # Das Netzwerk wird extrahiert
                netw = raddr_i[:2]

                # Die Adresse wird extrahiert
                addressh = raddr_i[2:34]

                # Die Checksume wird extrahiert
                chsum = raddr_i[34:]

            # Der Checksumme wird erstellt
            checksum_bytes = hashlib.sha3_512(netw + addressh).digest()
            checksum = checksum_bytes[0:1] + checksum_bytes[32:33] + checksum_bytes[63:64]
            if checksum != chsum: return False

            # Es wird geprüft ob es sich um eine Spizielle Adresse handelt
            if specorder is not None and specorder == 'BURN':
                chain_seed = gv_.ChainRoot.getChainSeed(True)
                nwi_ = BlockchainAddress(ChainSeed=chain_seed, AddressType=AddressTypes.ChainOwnAddress, ChainAddressType=BlockchainAddress.ChainAddressTypes.BURN_ADDRESS, NetworkCMHex=gv_.ChainRoot.getNetChecksum(True))
                if nwi_ != addr_i: return False

        # Es handelt sich um gültige Adressen
        return True

    # Lißt eine Adresse aus einem String ein
    @staticmethod
    def readLagacyAddressFromString(AddressString):
        # Es wird geprüft ob es sich um eine gültige Adresse handelt
        if AddressUtils.isValidateLagacyAddress(AddressString) == False: raise Exception('Invalid address') 

        # Es wird ermittelt um was für eine Lagacy Adresse es sich handelt
        if AddressUtils.isBurningAddress(AddressString) == True:
            chain_seed = gv_.ChainRoot.getChainSeed(True)
            nwi_ = BlockchainAddress(ChainSeed=chain_seed, AddressType=AddressTypes.ChainOwnAddress, ChainAddressType=BlockchainAddress.ChainAddressTypes.BURN_ADDRESS, NetworkCMHex=gv_.ChainRoot.getNetChecksum(True))
            return nwi_
    
        # Es wird versucht die Adresse einzulesen
        try: imported_addr = LagacyAddress.fromSring(AddressString)
        except: raise Exception('Invalid lagacy address')

        # Es wird geprüft ob es sich um die Selbe Adresse handelt
        if imported_addr.toStr(False) != AddressString: raise Exception('Address cant read')

        # Die Adresse wird als Objekt eingelesen
        return imported_addr




""" Informations Objects """

## Total Recived Object ##
class AddressCoinDetails(object):

    # Erstellt ein neues Recive Objekt
    def __init__(self, CoinObj):
        self.coin = CoinObj
        self.confirmed_input_value = 0
        self.confirmed_output_value = 0
        self.uconfirmed_output_value = 0
        self.unconfirmed_input_value = 0

        self.toal_in = 0
        self.total_out = 0
    
    # Fügt einen Eingang hinzu
    def addInput(self, Value, Confirmed):
        if Value == 0: return
        if Confirmed == True: self.confirmed_input_value += Value
        else: self.unconfirmed_input_value += Value
        self.toal_in += Value
    
    # Fügt einen Ausgang hinzu
    def addOutput(self, Value, Confirmed):
        if Value == 0: return
        if Confirmed == True: self.confirmed_output_value += Value
        else: self.uconfirmed_output_value += Value
        self.total_out += Value

    # Gibt den Verwendeten Coin aus
    def getCoin(self): return self.coin

    # Gibt die Insgesamten eingänge aus
    def getTotalIn(self, AsPrimaryUnit=True):
        if AsPrimaryUnit == True: return self.coin.calcSmallestToPUnit(self.toal_in)
        else: return self.toal_in

    # Gibt die Insgesamten ausgänge aus
    def getTotalOut(self, AsPrimaryUnit=True):
        if AsPrimaryUnit == True: return self.coin.calcSmallestToPUnit(self.total_out)
        else: return self.total_out

    # Gibt die Insgesamt bestätigten ausgänge aus
    def getTotalConfirmed(self, AsPrimaryUnit=True):
        amount = int(self.confirmed_input_value) - int(self.confirmed_output_value)
        if AsPrimaryUnit == True: return self.coin.calcSmallestToPUnit(amount)
        else: return amount

    # Gibt die Insgesamt unbestätiten ausgänge aus
    def getTotalUnconfirmed(self, AsPrimaryUnit=True):
        amount = int(self.unconfirmed_input_value) - int(self.uconfirmed_output_value)
        if AsPrimaryUnit == True: return self.coin.calcSmallestToPUnit(amount)
        else: return amount

    # Gibt den Aktuellen Kontostand aus
    def getAmount(self, AsPrimaryUnit=True):
        co_amount = int(self.confirmed_input_value + self.unconfirmed_input_value)
        uc_amount = int(self.confirmed_output_value + self.uconfirmed_output_value)
        total_amount = int(co_amount - uc_amount)
        if AsPrimaryUnit == True: return self.coin.calcSmallestToPUnit(total_amount)
        else: return total_amount

    # Gibt die Daten als JSON aus
    def toJSON(self, UsePrimaryCoinUnit=False):
        return_dict = dict()
        
        # Die Coindaten werden geschrieben
        return_dict['coin_name'] = self.coin.getName()
        return_dict['coin_symbol'] = self.coin.getSymbol()
        return_dict['coin_id'] = self.coin.getCoinID()
        return_dict['coin_decimals'] = self.coin.getDecimals()
                
        # Die Gesamt gesendeten Beträge werden geschrieben
        return_dict['total_in'] = self.toal_in
        return_dict['total_out'] = self.total_out
        
        # Das Konto guthaben wird geschrieben
        return_dict['confirmed'] = int(self.confirmed_input_value - self.confirmed_output_value)
        return_dict['unconfirmed'] = int(self.unconfirmed_input_value - self.uconfirmed_output_value)

        # Amount
        co_amount = int(self.confirmed_input_value + self.unconfirmed_input_value)
        uc_amount = int(self.confirmed_output_value + self.uconfirmed_output_value)
        return_dict['amount'] = int(co_amount - uc_amount)

        return return_dict

## AddressChainDetials Oject ##
class AddressChainDetails(object):

    # Erstellt ein neues AddressChainDetials Objekt
    def __init__(self, Address, TotalTransactions, *AvaibleCoins):
        # Es wird gepfüt ob Coins Übergeben wurden
        if len(AvaibleCoins) == 0: raise Exception('AVAIBLE_COINS_NEEDED')

        # Es wird geprüft ob es sich um eine gültige Adresse handelt
        if isinstance(Address, LagacyAddress) == False and isinstance(Address, BlockchainAddress) == False: raise Exception('INVALID ADDRESS')

        # Die derzeit verwendete Adresse wird verwendet
        self.address = Address

        # Die Verfügabren Coins werden gespeichert
        self.avaible_coins = list()

        # Die Address Informationen werden gespeichert
        self.address_coin_details = list()

        # Die Anzahl der Transaktionen werden gespeichert
        self.total_txn = TotalTransactions

        # Die Verfügbaren Coins werden hinzugefügt
        for coin_i in AvaibleCoins:
            for coin_ci in self.avaible_coins:
                if coin_ci == coin_i: raise Exception('COIN_ALRADY_USED')
            self.avaible_coins.append(coin_i)
            self.address_coin_details.append(AddressCoinDetails(coin_i))
            
    # Fügt einen Eingang hinzu
    def addInput(self, CoinObj, Value, Confirmed):
        # Es wird geprüft ob es sich um ein Coin Objekt handelt
        if isinstance(CoinObj, Coin) == False: raise Exception('INVALID COIN OBJECT')

        # Es wird geprüft ob der wert ein Gültiger Integer ist
        if isinstance(Value, int) == False: raise Exception('INVALID VALUE, ONLY INTEGER ALLOWED')

        # Es wird geprüft ob ein gültiger Confirmed Wert übergeben wurden
        if isinstance(Confirmed, bool) == False: raise Exception('INVALID CONFIRMED, ONLY BOOL ALLOWED')

        # Es wird geprüft ob der Coin bereits vorhanden ist
        for amount_i in self.address_coin_details:
            if amount_i.coin == CoinObj:
                amount_i.addInput(Value, Confirmed)
                return
        
        # Der Verwendete Coin wurde nicht gefunden
        raise Exception('INVALID COIN')
    
    # Fügt einen Ausgang hinzu
    def addOutput(self, CoinObj, Value, Confirmed):
        # Es wird geprüft ob es sich um ein Coin Objekt handelt
        if isinstance(CoinObj, Coin) == False: raise Exception('INVALID COIN OBJECT')

        # Es wird geprüft ob der wert ein Gültiger Integer ist
        if isinstance(Value, int) == False: raise Exception('INVALID VALUE, ONLY INTEGER ALLOWED')

        # Es wird geprüft ob ein gültiger Confirmed Wert übergeben wurden
        if isinstance(Confirmed, bool) == False: raise Exception('INVALID CONFIRMED, ONLY BOOL ALLOWED')

        # Es wird geprüft ob der Coin bereits vorhanden ist
        for amount_i in self.address_coin_details:
            if amount_i.coin == CoinObj:
                amount_i.addOutput(Value, Confirmed)
                return
        
        # Der Verwendete Coin wurde nicht gefunden
        raise Exception('INVALID COIN')

    # Gibt alle Werte aus
    def getValues(self): return self.address_coin_details

    # Gibt die Verwendete Adresse aus
    def getAddress(self): return self.address

    # Gibt die Anzahl der Transaktionen aus
    def getTotalTransactions(self): return self.total_txn
    
    # Gibt die Daten als JSON aus
    def toJSON(self, UsePrimaryCoinUnit=False):
        out_json_list = list()
        for detail_i in self.address_coin_details: out_json_list.append(detail_i.toJSON(UsePrimaryCoinUnit=UsePrimaryCoinUnit))
        redict = dict()
        redict['amount'] = out_json_list
        redict['total_transactions'] = self.total_txn
        redict['current_address'] = self.address.toStr()
        return redict
