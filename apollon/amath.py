import math

# Git an wieviele Halvenings bei einem Block durchgeführt wurden
def thvs(currblock : int, halve_at_blocks : int) -> int:
    assert isinstance(currblock, int) and isinstance(halve_at_blocks, int)
    if int(currblock) <= int(halve_at_blocks) and int(currblock) != int(halve_at_blocks): return 0
    arc = math.modf(float(int(currblock) / int(halve_at_blocks)))
    return int(arc[1])

# Diese Funktion rechnet die Gesamtzahl eines Coins anhand seiner Halvenings aus
def tsc(Reward, HalveAt, Decimals):
    hreward = Reward * (10**Decimals)
    total = 0; rnd = 0; hvas = 0
    while hreward >= 0:
        total += hreward * HalveAt
        hreward = hreward // 2
        rnd += 1; hvas += HalveAt
        if hreward <= 0: break
    return total

# Erstellt eine Decimalzahl aus einem Integer ohne es umzurechnen
def sutc(ins : int, lenx : int) -> str:
    if isinstance(ins, str) == False and isinstance(ins, int) == False: nwas = "0"*(lenx-len(ins)); return "0.{}{}".format(nwas, ins)
    if isinstance(ins, int): ins = str(ins)
    if len(ins) == 0: return "0.{}".format("0"*lenx)
    if len(ins) >= lenx + 1: return str("{}.{}".format(ins[0:len(ins)-lenx], ins[len(ins)-lenx:]))
    else: nwas = "0"*(lenx-len(ins)); return "0.{}{}".format(nwas, ins)

# Wandelt ein Decimal in ein Integer ohne es umzuberechnen
def fstiwc(iflotstr) -> int: return int(str(iflotstr).replace(".",""))

# Gibt an ob es sich um eine Zahl ohne rest handelt
def foiwp(ints) -> bool:
    if isinstance(ints, float) == False: return False
    arc, varc = math.modf(ints)
    return arc == 0 and varc >= 0 and varc != 0

# Rechnet die Belohnung für einen Spiziellen Block aus
def crbb(block_height:int, reward:int, halving_at:int, decimals:int) ->int:
    hreward = reward * (10**decimals)
    if block_height <= halving_at and block_height != halving_at: return int(hreward)
    if block_height == halving_at: return int(hreward//2)
    tch = thvs(block_height, halving_at)
    if tch == 0: return int(hreward)
    if tch == 1: return int(hreward//2)
    return int(hreward//(2)**tch)
    
# Rechnet aus wieiviel % x von y sind
def calcPercage(value, percage, perweih=1000):
    return 0

# Rechnet aus, weiviele Seiten es gibt
def capg(ItemsPerPage, TotalItems):
    if TotalItems <= ItemsPerPage: return 1
    _a = TotalItems/ItemsPerPage
    if _a == 0: return 1
    if foiwp(_a) == True: return int(_a)
    else: return int(_a) + 1 