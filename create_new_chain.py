from apollon.chain_configs import ChainRootConfig
from apollon.chain_storage import ChainStorage
from apollon.chain import Blockchain
from apollon.coin import Coin

NETWORK_NAME = "Apollon Chain"
CHAIN_SEED = "cc1bdfccf953799a7972bb2888d8472f974bba6f559cd52e0cb80a2fdc8409ef7c719f35a21337830640bbde95aedf5a4168cb976daf50a6889d79d2843c3a1a"

# Gibt eine Checksume des Aktuellen Netwzerkes aus
def get_net_chsum(): 
    import hashlib
    netw_hash_bytes = hashlib.sha3_512()
    netw_hash_bytes.update(str(NETWORK_NAME).upper().encode())
    netw_hash_bytes.update(bytes.fromhex(CHAIN_SEED))
    netw_hash_bytes = netw_hash_bytes.digest()
    return netw_hash_bytes[0:1] + netw_hash_bytes[63:64]

# Network Adress and Signature Checksum
NET_CHSUM = get_net_chsum()
print(NET_CHSUM.hex())

# Der Tarium Coin wird erzeugt
TARIUM_COIN = Coin(
    Name="Tarium",
    Symbol="TAR",
    SmallestUnitName='Trium',
    SmallestUnitSymbol='TRM',
    DecimalPlaces=18,
    NetworkCHSum=NET_CHSUM,
    ChainSeed=CHAIN_SEED.encode(),
    MineReward=70,
    RewardAtBlock=3,
    HalvingToEndNewCoin=True,
    TotalHalvenings=66,
    HalvinAtBlocks=1411255)

# Der Narium Coin wird erzeugt
OCTARIUM_COIN = Coin(
    Name="Octarium", 
    Symbol="OAM", 
    SmallestUnitName="Octrium", 
    SmallestUnitSymbol="OCT",
    DecimalPlaces=12,
    NetworkCHSum=NET_CHSUM,
    ChainSeed=CHAIN_SEED.encode(),
    MineReward=50,
    Burnable=True,
    TxnFeeBurning=True,
    HalvingToEndNewCoin=False,
    TotalHalvenings=7,
    TxnFeeBurningPerc=250)       

# Die Apollon Chain wird erstellt
blch = Blockchain.createNewChain('/home/gabriel/Dokumente/Database/', NETWORK_NAME, CHAIN_SEED, *[ TARIUM_COIN, OCTARIUM_COIN ])