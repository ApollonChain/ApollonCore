
# Extrahiert die Transaktionen aus dem Mempool
def getTxnsFromPool(MasterObj):
    rwo = list()
    for i in MasterObj.mempool: rwo.append(i); MasterObj.mempool.remove(i); print('Transaction {} selected'.format(i.getTxHash()))
    return rwo

# Gibt die Höhe aller Gebühren welche verwendet werden an
def getTransactionsTotalFee(CoinObj, *Transactions):
    total = 0
    for txi in Transactions:
        for feei in txi.getFees():
            if feei.coin() == CoinObj: total += feei.get()
    return total


def CryptoNightMinerFnc(q, block_root_hash, diff):
    current_nonce = 0
    base_diff = 2**256-1

    import time, datetime, struct, binascii, pycryptonight, time
    started = time.time()
    hash_count = 0
    for n in range(base_diff):
        hashy = pycryptonight.cn_slow_hash( bytes( block_root_hash + str(current_nonce).encode() ), 4, 0, 1)
        hex_hash = binascii.hexlify(hashy)
        hash_count += 1

        if base_diff / int(hex_hash, 16) >= diff:
            elapsed = time.time() - started
            hr = int(int(hash_count) / int(elapsed))
            q.put({ 'hash' : hex_hash, 'nonce' : current_nonce, 'hrate' : hr, 'trate' : hash_count })
            return
        else: current_nonce += 1


## CryptonightMiner
class CryptonightMiner:
    def __init__(self,ChainObject,UseCPPBinary=False): 
        self.chain = ChainObject
        self.shutdown = False
        self.miner_address = None
        self.running = False
        self.hrate = 0

        # Der Miner Thread wird deklariert
        import threading
        def miner_thread():
            from apollon.utxo import CoinbaseInUtxo, LagacyOutUtxo, createFeeInputUtxo
            from apollon.transaction import CoinbaseTransaction
            from apollon.block import BlockConstruct

            # Es wird Signalisiert das der Thread läuft
            self.running = True

            # Die Aktuelle Miner Adresse wird abgespeichert
            curr_miner = self.miner_address

            # Es wird eine Schleife ausgeführt, welche dafür sorgt das permant ein neuer Block entsteht
            while not self.shutdown:              
                # Es wird eine liste offener Transaktionen aus dem Memorypool extrahiert
                cur_transactions = getTxnsFromPool(self.chain)
                
                # Der letzte Block wird extrahiert
                last_block_mdata = self.chain.getLastBlockMetaData(True)
                next_block_height = last_block_mdata['block_height'] + 1
                last_block_hash = last_block_mdata['block_hash']

                # Die Ausgangs UTXOS werden erstellt #TODO
                coinbase_utxo_pairs = list()
                for i in self.chain.getChainCoins():
                    # Es wird ermittelt ob es einen Reward gibt
                    has_reward = i.hasRewardForBlock(next_block_height)

                    # Die höhe der Gesamten Transationsgebühren wird ermittelt
                    transaction_total_fees = getTransactionsTotalFee(i, *cur_transactions)
                   
                    # Es wird geprüt ob es einen Reward und oder die Gebühren der Transaktionen gibt # TODO
                    if has_reward == True and transaction_total_fees != 0:
                        # Es wird ein Eingangs UTXO für den Reward erstellt
                        reward_in_utxo = i.createNewRewardInputUtxo(next_block_height)
                        
                        # Es wird ein Eingangs UTXO für die Gebühren erstellt
                        fee_in_utxo = createFeeInputUtxo(i, cur_transactions)

                        # Es wird geprüft ob ein Teil der Transaktionsgebühren Verbrannt werden sollen
                        if i.minerForceBurnFee() == True:
                            # Es wird ermittelt wieviel verbrannt werden soll
                            burn_value = i.calcMinerBurningAmountValue(fee_in_utxo.getCoinValue(True))
                            reciver_value_total = reward_in_utxo.getCoinValue(True) + (fee_in_utxo.getCoinValue(True) - burn_value)
                            
                            # Es werden zwei Ausgangs UTXO's erzeugt
                            miner_outxo = LagacyOutUtxo(curr_miner, reciver_value_total, i, *[reward_in_utxo, fee_in_utxo])
                            burn_outxo = LagacyOutUtxo(curr_miner, burn_value, i, *[reward_in_utxo, fee_in_utxo])
                            
                            # Die UTXOS werden der Liste hinzugefügt
                            coinbase_utxo_pairs.append(reward_in_utxo)
                            coinbase_utxo_pairs.append(fee_in_utxo)
                            coinbase_utxo_pairs.append(miner_outxo)
                            coinbase_utxo_pairs.append(burn_outxo)
                        else:
                            # Es wird ein Ausgangs UTXO erzeugt
                            miner_outxo = LagacyOutUtxo(curr_miner, reward_in_utxo.getCoinValue(True) + fee_in_utxo.getCoinValue(True), i, *[reward_in_utxo, fee_in_utxo])
                            # Die UTXOS werden der Liste hinzugefügt
                            coinbase_utxo_pairs.append(reward_in_utxo)
                            coinbase_utxo_pairs.append(fee_in_utxo)
                            coinbase_utxo_pairs.append(miner_outxo)

                    # Der Miner erhält nur einen Reward für das Finden des Blockes
                    elif has_reward == True and transaction_total_fees == 0:
                        # Es wird ein Eingangs UTXO für den Reward erstellt
                        reward_in_utxo = i.createNewRewardInputUtxo(next_block_height)
                        
                        # Es wird ein Ausgangs UTXO für die Belohnung erstellt
                        reward_out_utxo = LagacyOutUtxo(curr_miner, reward_in_utxo.getCoinValue(True), i, reward_in_utxo)
                        
                        # Die UTXOs werden der Liste hinzugefügt
                        coinbase_utxo_pairs.append(reward_in_utxo)
                        coinbase_utxo_pairs.append(reward_out_utxo)
                    
                    # Der Miner erhält keine Block belohnung sondern nur die Gebühren der Transaktionen
                    elif has_reward == False and transaction_total_fees != 0:
                        # Es wird ein Eingangs UTXO für die Gebühren erstellt
                        reward_in_utxo = None
                    
                # Es wird eine Coinbase Transaktion aus allen UTXOS erstellt
                coinbase = CoinbaseTransaction(*coinbase_utxo_pairs, BlockNo=next_block_height)

                # Es wird eine Liste aus allen Transaktionen erzeuegt
                totalls = list(); totalls.append(coinbase); totalls = totalls + cur_transactions

                # Die Schwierigkeit wird ermittelt
                cdiff = self.chain.getBlockDiff(next_block_height)

                # Es wird ein Block Construtor erzeugt
                from apollon.atime import ATimeString
                
                try: new_block = BlockConstruct(last_block_hash, next_block_height, curr_miner, ATimeString.now(), cdiff, *totalls)
                except Exception as E: raise Exception(E)

                # Es wird geprüft ob es sich um ein Valides Objekt handelt
                if new_block.isValidateObject() == True and new_block.validateBlockTransactions() == True:
                    # Der Mining vorgang wird gestartet
                    try: nwoblck = self.MineBlock(new_block, cdiff); print('New Blocke Mined: {} @ {} :: {}'.format(nwoblck.getHeight(), nwoblck.getBlockHash(), nwoblck.getBlockTimestampe()))
                    except Exception as E: raise Exception(E)
                    # Der Block wird der Kette angehängt
                    try: self.chain.addBlock(nwoblck)
                    except Exception as E: raise Exception(E)
                else: print('Invalid New Block, abort')
            
            # Es wird dem Objekt signalisiert dass der Thread beendet wurde
            self.running = False

        self.miner_thread = threading.Thread(target=miner_thread)

    # Startet das Mining
    def Start(self, MinerAddress):
        # Es wird geprüft ob eine gültige Adresse übergeben wurde
        from apollon.apollon_address import LagacyAddress, PhantomAddress
        assert isinstance(MinerAddress, LagacyAddress) or isinstance(MinerAddress, PhantomAddress)

        # Es wird geprüft ob der Miner bereits ausgeführt wird
        if self.miner_address != None or self.running != False: raise Exception('Miner alrady running')

        # Es wird versucht den Miner zu Starten
        print('Starting Miner')
        self.miner_address = MinerAddress
        self.miner_thread.start()

        # Es wird geprüft ob der Miner gestartet wurde
        import time
        for i in range(2*10):
            if self.running == True and self.miner_address is not None: print('Miner started'); return 0    # Der Miner wurde gestartet
            time.sleep(0.01)

        # Der Miner konnte nicht gestartet werden
        print('Miner start, aborted')
        return 1

    # Gibt die Hashrate aus
    def getHashRate(self): return self.hrate

    # Gibt den Mining Status an
    def Status(self):
        if self.running == True: return 0
        elif self.running == False and self.miner_address is None: return 2
        else: return 1

    # Gibt den Aktuell zu Minenden Block aus
    def getUnminedBlock(self):
        return

    # Mint den eigentlichen Block
    def MineBlock(self, constructed_block, diff): 
        # Es wird geprüft ob ein gülter Block Constructor übergeben wurde
        from apollon.block import BlockConstruct, MinedBlock
        assert isinstance(constructed_block, BlockConstruct)

        # Es wird geprüft ob der Block laut der Blockchain Regeln Valide ist
        assert constructed_block.isValidateObject() == True

        # Es wird geprüft ob alle Transaktionen zulässig sind
        assert constructed_block.validateBlockTransactions() == True

        # Der Mining Prozess wird erstellt
        import multiprocessing as mp
        ctx = mp.get_context('spawn')
        q = ctx.Queue()

        # Es wird auf das Ergebniss vom Miner gewartet
        p = ctx.Process(target=CryptoNightMinerFnc, args=(q, constructed_block.getRootHash(True), diff))
        p.start()
        resolv = q.get()
        p.terminate()

        # Es wird ein neuer Geminter Block erstellt
        mined_block = MinedBlock.fromConstructWithNonce(constructed_block, resolv['nonce'])
        if mined_block.getRootHash(True) != constructed_block.getRootHash(True): raise Exception('Unkown error')
        if mined_block.getBlockHash(True) != resolv['hash']: raise Exception('Not same hash')

        # Die Hashrate wird gespeichert
        self.hrate = resolv['hrate']
        
        # Gibt den gemiten Block zurück
        return mined_block