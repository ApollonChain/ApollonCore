from ecdsa.util import randrange_from_seed__trytryagain
from ecdsa import SECP256k1, SigningKey, VerifyingKey
from apollon import gv_, BASE58_BET
from enum import Enum as enu
import hashlib
import base58
import ecdsa




# Es wird geprüft ob die Blockchain geladen wurde
if gv_.ChainRoot is None: raise Exception('Not RootConfig, loaded')




""" Basic Types """

## Adress Typen ##
class AddressTypes(enu):
    Lagacy = 'LAGACY'
    Phantom = 'PHANTOM'
    ChainOwnAddress = 'CHAIN_ADDRESS'

## Adresse Objekt ##
class Address(object):
    def __init__(self, adr_type): self.adr_type = adr_type.value; self.can_use = False
    def __str__(self): return self.toStr()
    def getType(self): return str(self.adr_type).upper()
    def canUse(self): return self.can_use
    def toStr(self, AsBytes=False): raise Exception('Empty object')
    def validateSignature(self, Signature, SignatureData): raise Exception('Empty object')
    @classmethod
    def fromSring(cls, AddressStr): raise Exception('Empty Object')
    def getByteSize(self): raise Exception('Empty Object')
    def getHash(self, asBytes=True): raise Exception('Empty Object')




""" Lagacy Addresses """

## Lagacy Siganture ##
class LagacySignature(object):
    def __init__(self, Network, SignAddress, SignatureBytes): self.signature = SignatureBytes; self.signer_hash = SignAddress.getHash(True); self.network = Network
    def __str__(self): import base58; from apollon import BASE58_BET; return base58.b58encode(b'LS' + self.network + self.signer_hash + self.signature, alphabet=BASE58_BET).decode()
    
    # Es wird ein Hash aus der Signatur erstellt
    def getHash(self, AsBytes=False):
        from hashlib import sha3_256
        shu = sha3_256()
        shu.update(self.signer_hash)
        shu.update(self.signature)
        if AsBytes == True: return shu.digest()
        else: import base58; from apollon import BASE58_BET; return base58.b58encode(shu.digest(), alphabet=BASE58_BET).decode()
    
    # Gibt einen Hash der Adresse des Signieres aus
    def getSignerAddressHash(self, AsBytes=False): 
        if AsBytes == True: return self.signer_hash
        else: import base58; from apollon import BASE58_BET; return base58.b58encode(self.signer_hash, alphabet=BASE58_BET).decode()
    
    # Gibt die Eigentliche Signatur aus
    def getSignature(self, AsBytes=False): 
        if AsBytes == True: return self.signature
        else: import base58; from apollon import BASE58_BET; return base58.b58encode(self.signature, alphabet=BASE58_BET).decode()
    
    # Gibt die größe aus
    def getSize(self, ByteSize=False):
        if ByteSize == True: return len(self.signature + self.signer_hash)
        else: return len(self.getSignature() + self.getSignerAddressHash())

    # Exportiert die Signatur zu einem JSON String
    def toJSON(self):
        rd = dict()
        rd['sa'] = self.getSignerAddressHash()
        rd['sig'] = self.getSignature()
        return rd

## Privater Lagacy Schlüssel ##
class PrivateLagacyKey(object):
    # Erstellt eine leere Lagacy Key Objekt
    def __init__(self):
        self.private_key_obj = None
        self.public_key_obj = None
        self.network = None

    # Erstellt eine Adresse aus dem Privaten Schlüssel
    def toAddress(self): return LagacyAddress.fromPublicKey(self.public_key_obj.to_string(), self.network.hex())

    # Gibt das Verwendete Netzwerk des Schlüssel aus
    def getNetwork(self): return hex(self.network)

    # Signiert eine Transaktion
    def signTransaction(self, UnsigTransaction):
        # Es wird geprüft ob eine UnsignedLagacyTransaction übergeben wurde
        from apollon.transaction import UnsignedTransaction
        assert isinstance(UnsigTransaction, UnsignedTransaction)

        # Es wird geprüft ob die Transaction bereit zum Signieren ist
        if UnsigTransaction.isSignlabel() == False: raise Exception('This transaction cannot be signed by you')

        # Es wird geprüft wieviele Signaturen benötigt werden, wenn keine Signaturen benötit werden, wird ein Fehler erzeugt
        if UnsigTransaction.getTotalSignaturesRequired() <= 1 and UnsigTransaction.getTotalSignaturesRequired() != 1: raise Exception('a')

        # Es wird geprüft wieviele Signaturen noch benötigt werden, wenn keine Signaturen mehr benötigt werden, wird ein Fehler erzeugt
        if UnsigTransaction.getStillSignaturesRequired() <= 1 and UnsigTransaction.getStillSignaturesRequired() != 1: raise Exception('b')

        # Es wird geprüft ob die Aktuelle Adresse zum Signieren benötigt wird
        current_address_needed = False
        for i in UnsigTransaction.getNeededSignatureAddresses():
            if self.toAddress() == i: current_address_needed = True; break
        if current_address_needed == False: raise Exception('C')

        # Es wird geprüft ob die noch eine Signatur von der Aktuellen Adresse benötigt wird
        current_address_needed = False
        for i in UnsigTransaction.getStillSignatureAddresses():
            if self.toAddress() == i: current_address_needed = True; break
        if current_address_needed == False: raise Exception('D')

        # Es wird geprüft, ob bereits eine Uhrzeit vorhanden ist

        # Es wird versucht eine Signatur zu erstellen
        try: sigo = LagacySignature(self.network, self.toAddress(), self.private_key_obj.sign_digest(digest=UnsigTransaction.getSignHash(True)))
        except Exception as E: raise E

        # Die Signatur wird der Transaktion hinzugefügt
        UnsigTransaction.current_signatures.append(sigo)

        # Es wird eine Signierte Transaktion erstellt
        return UnsigTransaction

    # Erstellt einen Schlüssel aus einem Seed
    @classmethod
    def fromSeed(cls, Seed, Index=0, Network=gv_.ChainRoot.getNetChecksum()):
        from apollon.utils import isBase58, isHex
        if isinstance(Seed, bytes) == True: seed_bytes = Seed
        elif isBase58(Seed) == True: seed_bytes = base58.b58decode(Seed)
        elif isHex(Seed) == False: seed_bytes = bytes.fromhex(Seed)
        else: raise Exception('Invalid seed')
        
        # Generate Privatekey from Seed
        total_seed = "LGY:%s/%s" % (seed_bytes, Index)
        key_from_seed = SigningKey.from_secret_exponent(randrange_from_seed__trytryagain(total_seed, SECP256k1.order), SECP256k1,hashfunc=hashlib.sha3_256) 

        # Create the new Key object
        nwo = cls()
        nwo.private_key_obj = key_from_seed
        nwo.public_key_obj = key_from_seed.get_verifying_key()
        nwo.network = bytes.fromhex(Network)
        nwo.algo = "SECP256k1".lower()
        return nwo

## Lagacy Adresse ##
class LagacyAddress(Address):
    # Erstellt eine leere Lagacy Adresse
    def __init__(self): 
        super().__init__(AddressTypes.Lagacy)
        self.address_hash = None; self.checksum = None; self.network = None

    # Diese Funktion überprüft zwei Lagacy Addressen
    def __eq__(self, other):
        if isinstance(other, LagacyAddress) == True: return self.getHash(True) == other.getHash(True)
        elif isinstance(other, BlockchainAddress) == True: return self.getHash(True) == other.getHash(True) 
        elif isinstance(other, str) == True: return self.toStr() == other
        else: return False

    @staticmethod
    # Erstellt einen AdressHash aus einem Öffentlichen Schlüssel
    def _calcAddressHash(PublicKey):
        # Die PublicKey wird gehasht
        public_key_long_hash_sha3_512 = hashlib.sha3_512(PublicKey).digest()
        public_key_long_hash_sha2_512 = hashlib.sha512(PublicKey).digest()
        adress_short_hash_sha2_256 = hashlib.sha3_256(public_key_long_hash_sha2_512 + public_key_long_hash_sha3_512).digest()
        hli = hashlib.new('ripemd160'); hli.update(public_key_long_hash_sha2_512 + public_key_long_hash_sha3_512)
        address_short_ripemd160 = hli.digest()

        # Die Adresse wird aus den zwei Short Hashes erstellt
        new_address_hash_bytes = address_short_ripemd160[3:16] + adress_short_hash_sha2_256[13:32]

        # Die Daten werden zurückegeben
        return new_address_hash_bytes

    # Gibt die Adresse als String aus
    def toStr(self, AsBytes=False):
        if self.can_use == False: raise Exception('Incomplete object')
        if AsBytes == True: return b'L' + self.network + self.address_hash + self.checksum
        else: return base58.b58encode(b'L' + self.network + self.address_hash + self.checksum, alphabet=BASE58_BET).decode()

    # Gibt das Netzwerk aus
    def getNetworkCH(self, AsBytes=False):
        if AsBytes == True: return self.checksum
        else: return self.checksum.hex()

    # Gibt den Hash der Adresse aus
    def getHash(self, asBytes=False):
        hashx = hashlib.sha3_384()
        hashx.update(self.network)
        hashx.update(self.address_hash)
        hashx.update(self.checksum)
        if asBytes == False: return base58.b58encode(hashx.digest(), alphabet=BASE58_BET).decode()
        else: return hashx.digest()

    # Überprüft eine Signatur
    def validateSignature(self, Signature, SignatureDataHash):
        # Es wird geprüft ob ein LagacySignaturObjekt übergeben wurde
        if isinstance(Signature, LagacySignature) == False: raise Exception('Only signature objects allowed:: {} not allowed'.format(type(Signature)))

        # Es wird geprüft ob es sich bei den zu Überprüfenden Daten um Bytes handelt
        if isinstance(SignatureDataHash, bytes) == False: raise Exception('Only bytes as SignatureHash allowed')

        # Es wird geprüft ob die Signatur und die Adresse, das gleiche Netzwerk verwenden
        if Signature.network != self.network: raise Exception('The addresss hasent, same network')

        # Es wird versucht den öffentlichen Schlüssel aus der Signature zu extrahiereren
        try: recoverd_key = VerifyingKey.from_public_key_recovery_with_digest(signature=Signature.signature, digest=SignatureDataHash, curve=SECP256k1, hashfunc=hashlib.sha3_256)
        except: raise Exception('Invalid Signature')    # Es handelt sich nicht um eine zulässige Signatur

        # Es wird vesucht den passenden PublicKey zu finden
        resolv_pub_key = None
        for i in recoverd_key:
            try: address_key_hash = LagacyAddress._calcAddressHash(i.to_string())
            except: return False
            if address_key_hash == self.address_hash: resolv_pub_key = i; break
        if resolv_pub_key == None: return False # Es wurde kein passender Schlüssel gefunden

        # Es wird geprüft ob die gefundene Signatur gültig ist
        try: idata = resolv_pub_key.verify_digest(digest=SignatureDataHash, signature=Signature.signature)
        except: return False
        if idata == False: return False # Es handelt sich um ein ungültige Signatur

        # Es wird eine vollwertige Adresse gebildet
        try: resolv_address = LagacyAddress.fromPublicKey(resolv_pub_key.to_string(),Signature.network.hex())
        except: return False    # Es konnte aus unbekannten gründen keine Adresse aus dem Schlüssel gebildet werden
    
        # Der Hash der Rückgebildeten Adresse wird mit dem Hash der Aktuellen Adrsse verglichen
        if resolv_address.getHash(True) != self.getHash(True): return False # Die Hashs der Adressen stimmen nicht übereien

        # Es handelt sich um eine gültige Signatur
        return True

    # Erstellt eine Adresse aus einem Öffentlichen Schlüssel
    @classmethod
    def fromPublicKey(cls, PublicKey, NetworkCMHex=gv_.ChainRoot.getNetChecksum()):
        # Es wird versucht die Adresse zu erstellen
        try: new_address_hash_bytes = LagacyAddress._calcAddressHash(PublicKey)
        except: raise Exception('Invalid public key')

        # Es wird eine Checksume erstellt
        checksum_bytes = hashlib.sha3_512(bytes.fromhex(NetworkCMHex) + new_address_hash_bytes).digest()
        checksum = checksum_bytes[0:1] + checksum_bytes[32:33] + checksum_bytes[63:64]

        # Das Objekt wird erstellt
        nwo = cls()
        nwo.address_hash = new_address_hash_bytes
        nwo.checksum = checksum
        nwo.network = bytes.fromhex(NetworkCMHex)
        nwo.can_use = True
        return nwo

    # Erstellt eine Adresse aus einem String
    @classmethod
    def fromSring(cls, AddressStr, AllowAnotherChainAdresses=False):
        # Es wird geprüft ob es sich um eine Gebaste Adresse handelt
        from apollon.utils import isBase58, decodeBase58
        
        # Es handelt sich um eine Base58 Adresse
        if isinstance(AddressStr, str) and isBase58(AddressStr) == True: 
            try: AdressByteStr = decodeBase58(AddressStr)
            except: raise Exception('Invalid Base58')
        # Es handelt sich um Adress bytes
        elif isinstance(AddressStr, bytes): AdressByteStr = AddressStr
        # Es handelt sich um einen Unzulässigen Datentypen
        else: raise Exception('Invalid Datatype')

        # Es wird geprüft ob die Bytes die Mindestlänge erfüllen
        if len(AdressByteStr) != 38: raise Exception('Invalid Address bytes')

        # Es wird geprüft ob die Bytes, mit dem Benötigtem Header beginnen
        if AdressByteStr[0:1] != b'L': raise Exception('Invalid Address header')

        # Das Netzwerk wird ermittelt
        network = AdressByteStr[1:3]

        # Es wird geprüft ob es sich um ein Zulässiges Netzwerk handelt oder nicht
        if AllowAnotherChainAdresses == False and gv_.ChainRoot.getNetChecksum(True) != network: 
            print(network.hex())
            print(gv_.ChainRoot.getNetChecksum(True).hex())
            raise Exception('Invalid Network')

        # Der Adresshash wird ermittelt
        address_hash = AdressByteStr[3:35]

        # Die Checksume wird ermittelt
        address_chsum = AdressByteStr[35:38]

        # Die Checksume wird geprüft
        checksum_bytes = hashlib.sha3_512(network + address_hash).digest()
        checksum = checksum_bytes[0:1] + checksum_bytes[32:33] + checksum_bytes[63:64]
        if address_chsum != checksum: raise Exception('Invalid Adress Checksume')

        # Es wird ein neues Adress Objekt erstellt
        nwo = cls()
        nwo.checksum = address_chsum
        nwo.address_hash = address_hash
        nwo.network = network
        nwo.can_use = True

        # Das erstellte Objekt wird zurückgegben
        return nwo

    # Gibt die Größe der Adresse in Bytes aus
    def getByteSize(self): return int(len(self.network + self.address_hash + self.checksum))

## Ethereum HashBased Lagacy Address ## TODO
class LagacyEthereumHashBasedAddress(LagacyAddress):
    def __init__(self): return
    # Erstellt eine Adresse aus einem Öffentlichen Schlüssel
    @classmethod
    def fromPublicKey(cls, PublicKey, NetworkCMHex=gv_.ChainRoot.getNetChecksum()):
        # Es wird eine Ethereum Adresse aus dem PublicKey erzeugt
        import Crypto.Hash.SHA3_256
        sha3_keccak = Crypto.Hash.SHA3_256.new()
        sha3_keccak.update(PublicKey)
        
        # Aus der Erzeugten Ethereum Adresse, wird eine Ethereum Based Adresse
        address = '0x{}'.format(sha3_keccak.hexdigest()[24:])

        return

    # Erstellt eine Adresse aus einem String
    @classmethod
    def fromSring(cls, AddressStr): return

    # Erstellt eine Ethereum Based Lagacy Adresse aus einer Ethereum Adresse
    @classmethod
    def fromEthereumAddress(cls, AddressStr): return




""" Blockchain Address """

## Blockchain Adresse ##
class BlockchainAddress(object):

    ## Chain Address Types ##
    class ChainAddressTypes(enu):
        BURN_ADDRESS = [hashlib.sha384(b'BURN_ADDRESS').digest(), 'BURN']

    # Erstellt eine neue Blockchain eigene Adresse
    def __init__(self, ChainSeed, AddressType, ChainAddressType, NetworkCMHex=gv_.ChainRoot.getNetChecksum()):        
        # Der ChainSeed wird gespeichert
        self.chain_address_type = AddressType.value
        self.chain_address_hash = hashlib.sha256(ChainSeed + ChainAddressType.value[0] + ChainAddressType.value[1].encode()).digest()[:28]
        self.address_member = ChainAddressType.value[1]

        # Es wird eine Checksume erstellt
        checksum_bytes = hashlib.sha3_512(NetworkCMHex + self.chain_address_hash).digest()
        checksum = checksum_bytes[0:1] + checksum_bytes[32:33] + checksum_bytes[63:64]

        # Das Netzwerk wird abgespeichert
        self.network = NetworkCMHex

        # Die Netzwerkchecksume wird abgespeichert
        self.checksum = checksum

        # Dir Adresse wird als Anwendbar Makiert
        self.can_use = True

    # Gibt die Adresse als String aus
    def __str__(self): return self.toStr()

    # Vergeleicht zwei Adressen
    def __eq__(self, other):
        if isinstance(other, LagacyAddress) == True: return self.getHash(True) == other.getHash(True)
        if isinstance(other, BlockchainAddress) == True: return self.getHash(True) == other.getHash(True)
        elif isinstance(other, str) == True: return self.toStr() == other
        else: return False

    # Diese Funktion gibt die Adresse als String aus
    def toStr(self, AsBytes=False):
        if self.can_use == False: raise Exception('Incomplete object')
        if AsBytes == True: return self.address_member.encode('UTF-8') + b'LCA' + self.network + self.chain_address_hash + self.checksum
        else: return self.address_member + base58.b58encode(b'LCA' + self.network + self.chain_address_hash + self.checksum, alphabet=BASE58_BET).decode()

    # Gibt den Hash der Adresse aus
    def getHash(self, asBytes=False):
        hashx = hashlib.sha3_384()
        hashx.update(self.address_member.encode('UTF-8'))
        hashx.update(self.network)
        hashx.update(self.chain_address_hash)
        hashx.update(self.checksum)
        if asBytes == False: return base58.b58encode(hashx.digest(), alphabet=BASE58_BET).decode()
        else: return hashx.digest()

    # Gibt die Größe der Adresse in Bytes aus
    def getByteSize(self): return int(len(self.network + self.chain_address_hash + self.checksum))

    # Gibt den Typen der Adresse aus
    def getType(self): return self.address_member




""" Phantom Addresses """


## Privater Phantom Schlüssel
class PrivatePhantomKey(object):
    def __init__(self):
        self.private_view_key_obj = None
        self.private_spend_key_obj = None
        self.public_view_key_obj = None
        self.public_spend_key_obj = None
        self.network = None

    def toAddress(self):return PhantomAddress.fromPublicKeyPair(self.public_view_key_obj.to_string("compressed"), self.public_spend_key_obj.to_string("compressed"),self.network.hex())

    def getNetwork(self): return hex(self.network)

    @classmethod
    def fromSeed(cls, Seed, Index=0, Network=gv_.ChainRoot.getNetChecksum()):
        from apollon.utils import isHex, isBase58
        if isinstance(Seed, bytes) == True: seed_bytes = Seed
        elif isBase58(Seed) == True: seed_bytes = base58.b58decode(Seed)
        elif isHex(Seed) == False: seed_bytes = bytes.fromhex(Seed)
        else: raise Exception('Invalid seed')
        
        # Generate View Key from Seed
        total_seed_view = "PHV:%s/%s" % (seed_bytes, Index)
        private_view_key_obj = SigningKey.from_secret_exponent(randrange_from_seed__trytryagain(total_seed_view, SECP256k1.order), SECP256k1, hashfunc=hashlib.sha256)

        # Generate Spend Key from Seed
        total_seed_spend = "PHS:%s/%s" % (seed_bytes, Index)
        private_spend_key_obj = SigningKey.from_secret_exponent(randrange_from_seed__trytryagain(total_seed_spend, SECP256k1.order), SECP256k1, hashfunc=hashlib.sha256)

        # Create the new Key object
        nwo = cls()
        nwo.private_view_key_obj = private_view_key_obj
        nwo.private_spend_key_obj = private_spend_key_obj
        nwo.public_view_key_obj = private_view_key_obj.get_verifying_key()
        nwo.public_spend_key_obj = private_spend_key_obj.get_verifying_key()
        nwo.network = bytes.fromhex(Network)
        nwo.algo = "SECP256k1".lower()
        return nwo

## Phantom Adresse ##
class PhantomAddress(Address):
    def __init__(self): 
        super().__init__(AddressTypes.Phantom)
        self.pub_spend_key_bytes = None; self.pub_view_key_bytes = None; self.checksum = None; self.network = None

    def toStr(self):
        if self.can_use == False: raise Exception('Incomplete object')
        return base58.b58encode(b'P' + self.network + self.pub_view_key_bytes + self.pub_spend_key_bytes, alphabet=BASE58_BET).decode()

    @classmethod
    def fromPublicKeyPair(cls, PublicViewKey, PublicSpendKey, Network=gv_.ChainRoot.getNetChecksum()):
        # Es wird eine Checksume erstellt
        checksum_full_bytes = hashlib.sha3_512(bytes.fromhex(Network) + PublicViewKey + PublicSpendKey).digest()
        checksum = checksum_full_bytes[0:2] + checksum_full_bytes[30:32] + checksum_full_bytes[62:64]

        # Das Objekt wird erstellt
        nwo = cls()
        nwo.pub_view_key_bytes = PublicViewKey
        nwo.pub_spend_key_bytes = PublicSpendKey
        nwo.network = bytes.fromhex(Network)
        nwo.checksum = checksum
        nwo.can_use = True
        return nwo




""" Wallet """

## Wallet Objekt ##
class Wallet(object):
    # Erstellt eine leere Wallet
    def __init__(self):
        self.lagacy_addresses = list()
        self.phantom_addresses = list()
        self.seed = str()
        return

    # Gibt alle Lagacy Adrssen aus
    def getLagacyAddresses(self):
        re = list()
        for i in self.lagacy_addresses: re.append(i)
        return re

    # Gibt alle Privaten Schlüssel der Phantom Adressen aus
    def getPhantomAddresses(self):
        re = list()
        for i in self.phantom_addresses: re.append(i)
        return re

    # Signiert eine Transaktion
    def signTransaction(self, UnsigTransactionObj): return

    # Erstellt einen Wallet Mnemonic
    @staticmethod
    def genMnemonic(lang = 'english'):
        from mnemonic import Mnemonic
        mnemo = Mnemonic(str(lang))
        words = mnemo.generate(strength=256)
        return words

    # Erstellt eine Wallet von einem Mnomenic
    @classmethod
    def fromMnemonic(cls, mnemonicStr, lang = 'english'):
        from mnemonic import Mnemonic
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(mnemonicStr)
        mwp = cls()
        # Es werden 25 Lagacy Adressen erstellt
        for i in range(0,25): mwp.lagacy_addresses.append(PrivateLagacyKey.fromSeed(seed,i))
        # Es werden 6 Phantom Adressen erstellt
        for i in range(0,6): mwp.phantom_addresses.append(PrivatePhantomKey.fromSeed(seed,i))
        
        # Die Wallet wird zurückgegeben
        return mwp

    # Erstellt eine neue Wallet
    @staticmethod
    def genNew(): return Wallet.fromMnemonic(Wallet.genMnemonic()) 
 

# Liest eine Adresse ein OLD
def addressStringReader(AddressIn):
    try: return LagacyAddress.fromSring(AddressIn)
    except: raise Exception('Cant parse Address')