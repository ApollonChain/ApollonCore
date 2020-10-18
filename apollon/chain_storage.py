from threading import Lock
from os import path
import os.path
import sqlite3
import hashlib


## ChainStorage Object ##
class ChainStorage(object):
    # Erstellt ein neues ChainStorage Objekt
    def __init__(self, MasterObject): 
        self.chain_file = None
        self.chain_loaded = False
        self.master_object = None
        self.thread_lock = Lock()
        self.master_object = MasterObject

    # Gibt die Aktuelle Höhe des Blocks aus
    def getBlockHeight(self):
        # Es wird geprüft ob eine Chain geladen wurden
        if self.chain_loaded == False: raise Exception('Objet not created')
        
        # Der Threadlock wird gesperrt
        self.thread_lock.acquire()

        # Es wird eine neue SQL Verbindung aufgebaut
        try: conn = sqlite3.connect(self.chain_file)
        except: self.thread_lock.release(); raise Exception('DB Error')

        # Es wird ein SQL Cursor erzeugt
        try: cur = conn.cursor()
        except: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Es wird die Anzahl der Blöcke ermittelt
        try: blocks = cur.execute("SELECT block_height FROM blocks ORDER BY block_height DESC LIMIT 1").fetchone()
        except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        if blocks is None or len(blocks) != 1 or type(blocks[0]) is not int: cur.close(); conn.close(); self.thread_lock.release(); return 0
        
        # Die SQL Verbindug wird geschlossen
        try: cur.close(); conn.close(); self.thread_lock.release()
        except: self.thread_lock.release(); raise Exception('DB Error')

        # Die Blockhöhe wird zurückgegben
        return blocks[0]

    # Gibt einen Spizeillen Block aus #TODO
    def getBlock(self, BlockID):
        # Es wird geprüft ob eine Chain geladen wurden
        if self.chain_loaded == False: raise Exception('Objet not created')
        
        # Es wird geprüft ob es sich um ein Integer oder einen Blockhash handelt
        if isinstance(BlockID, int): block_find_sql_quer_str = 'SELECT blocks.block_hash, blocks.block_timestamp, blocks.block_height, blocks.block_root_hash, blocks.block_nonce, (SELECT block_hash FROM blocks WHERE block_height = {} LIMIT 1), blocks.block_diff, blocks.block_root_hash FROM blocks WHERE block_height = {} LIMIT 1'.format(BlockID -1, BlockID)
        else: raise Exception('INVALID_BLOCK_ID')

        # Der Threadlock wird gesperrt
        self.thread_lock.acquire()
        
        # Es wird eine neue SQL Verbindung aufgebaut
        try: conn = sqlite3.connect(self.chain_file)
        except: self.thread_lock.release(); raise Exception('DB Error')

        # Es wird ein SQL Cursor erzeugt
        try: cur = conn.cursor()
        except: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Es wird versucht den Aktuellen Block abzurufen
        try: current_block = cur.execute(block_find_sql_quer_str).fetchone()
        except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        if current_block is None: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('BLOCK_NOT_FOUND')
        current_block_id = current_block[2]
        if current_block_id == 1: prev_block_hash = self.master_object.getChainRootHash(True)
        else: prev_block_hash = current_block[5]

        # Es wird die Anzahl der Blöcke ermittelt
        try: blocks = cur.execute("SELECT block_height FROM blocks ORDER BY block_height DESC LIMIT 1").fetchone()
        except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        if blocks is None or len(blocks) != 1 or type(blocks[0]) is not int: cur.close(); conn.close(); self.thread_lock.release(); return 0
        blocks = blocks[0] + 1

        # Es werden alle Transaktionen des Blocks abgerufen
        try: block_txns = cur.execute("SELECT transaction_id, transaction_hash, transaction_root_hash, transaction_type, transaction_block, transaction_timestamp FROM lagacy_transactions WHERE transaction_block = {}".format(current_block_id)).fetchall()
        except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
        txnl = list()
        for i in block_txns: txnl.append(i[0])
        txnstr = str(tuple(txnl))
        if txnstr[-2] == ',': txnstr = txnstr.replace(txnstr[-2],"")

        # Es werden alle Eingänge Abgerufen
        try: ins = cur.execute("SELECT input_transaction_id, input_type, input_utxo_hash, input_output_utxo_id, input_reward_coin_hid, input_reward_amount, input_block_height, input_one_time_reward_hash, input_height FROM lagacy_input_utxos WHERE input_transaction_id IN {}".format(txnstr)).fetchall()
        except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
        if ins == None or len(ins) == 0: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Es werden alle ausgänge abgerufen
        try: outs = cur.execute("""
        SELECT
            lagacy_output_utxos.output_transaction_id,
            lagacy_output_utxos.output_utxo_id,
            lagacy_output_utxos.output_amount,
            lagacy_output_utxos.output_coin_hid,
			lagacy_output_utxos.output_reciver_address_id,
			lagacy_output_utxos.output_utxo_hash,
			lagacy_output_utxos.output_utxo_type,
			lagacy_addresses.address,
			lagacy_addresses.address_hash,
	        CASE lagacy_input_utxos.input_output_utxo_id 
                WHEN lagacy_output_utxos.output_utxo_id
                    THEN 1
                ELSE 0
            END spendch
        FROM lagacy_output_utxos
        LEFT JOIN lagacy_input_utxos ON lagacy_input_utxos.input_output_utxo_id = lagacy_output_utxos.output_utxo_id
		LEFT JOIN lagacy_addresses ON lagacy_addresses.address_id = lagacy_output_utxos.output_reciver_address_id 
        WHERE lagacy_output_utxos.output_transaction_id IN {}""".format(txnstr)).fetchall()
        except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        if outs == None or len(outs) == 0: conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        
        # Es werden alle Signaturen abgerufen
        #try: sigs = cur.execute("SELECT sign_transaction_id FROM lagacy_transactions_signatures WHERE sign_transaction_id IN {}".format(txnstr)).fetchall()
        #except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)

        # Die SQL Verbindung wird geschlossen
        try: cur.close(); conn.close(); self.thread_lock.release()
        except: raise Exception('STORAGE_SQL_ERROR')

        # Die Transaktionen werden zusammengefasst
        retra_list = list()
        from apollon.transaction import ST_CoinbaseTransaction, SignedTransaction
        from apollon.utxo import CoinbaseInUtxo, ST_LagacyOutUtxo
        from apollon.apollon_address import LagacyAddress
        from apollon.atime import ATimeString
        for i in block_txns:
            # Speichert die UTXOs zwischen
            utxos = list()

            # Die Eingänge werden verarbeitet
            for inp in ins:
                # Es wird geprüft ob es sich um die Aktuelle Transaktion handelt
                if inp[0] == i[0]:
                    # Es wird geprüft ob es sich um ein Coinbase Reward handelt
                    if inp[1] == 0:
                        coinobj = None
                        # Es wird geprüft ob es sich um einen Zulässigen Coin handelt
                        for coib in self.master_object.getCoins():
                            if coib.getCoinID(True) == inp[4]: coinobj = coib; break
                        if coinobj is None: raise Exception('Unkown Coin')

                        # Es wird geprüft ob der Reward Hash korrekt ist
                        if coinobj.validateReward(int(inp[5], 16),inp[6]) == False: raise Exception('Invalid reward')

                        # Es wird geprüft, ob der Rewardhash korrekt ist
                        oth = coinobj.createOneTimeRewardHash(inp[6], True)
                        if oth != inp[7]: raise Exception('Invalid reward one time hash')

                        # Es wird versucht das Inout UTXO nachzubilden
                        try: nwo_inp = CoinbaseInUtxo(inp[6], coinobj, int(inp[5], 16), oth)
                        except: raise Exception('Address cant parse')
                        utxos.append(nwo_inp)

            # Die Ausgänge werden verarbeitet
            for onp in outs:
                # Es wird geprüft ob es sich um die Aktuelle Transaktion handelt
                if onp[0] == i[0]:
                    # Es wird geprüft ob es sich um ein Standart Output handelt
                    if onp[6] == 10:
                        # Es wird geprüft ob es sich um einen Zulässigen Coin handelt
                        coinobj = None
                        for coib in self.master_object.getCoins():
                            if coib.getCoinID(True) == onp[3]: coinobj = coib; break
                        if coinobj is None: raise Exception('Unkown Coin')

                        # Es werden alle Inputs mit dem Selben Coin Abgerufen
                        inch = list()
                        for inh in utxos:
                            if inh.getCoin().getCoinID(True) == coinobj.getCoinID(True): inch.append(inh)

                        # Die Verwendete Ausgangsadresse wird abgerufen
                        try: resolv_addr = LagacyAddress.fromSring(onp[7])
                        except: raise Exception('Address cant parse')

                        # Es wird geprüft ob der Verwendete Address Hash übereinstimmt
                        if resolv_addr.getHash(True) != onp[8]: raise Exception('Invalid Address')

                        # Es wird versucht das Ausgangs UTXO nachzubilden
                        try: outxo = ST_LagacyOutUtxo(resolv_addr, int(onp[2], 16), coinobj, bool(onp[9]) ,*inch)
                        except: raise Exception('Address cant parse')
                        utxos.append(outxo)

            # Es wird geprüft ob es sich um eine Coinbase Transaktion handelt
            if i[3] == 0:
                # Die Uhrzeit wird aus der Datenbank abgerufen
                try: timestr = ATimeString.readFromDBStr(i[5])
                except: raise Exception('DB Error A')

                # Die Transaktion wird Rückgebildet
                try: cb = ST_CoinbaseTransaction(*utxos, BlockNo=i[4], TStamp=timestr, Confirmations=int(blocks - i[4]))
                except Exception as E: print(E); raise Exception(E)

                # Es wird gepürft ob die Transaktion erfolgreich erstellt wurde
                if i[1] != cb.getTxHash(True): raise Exception('Invalid transaction')

                # Die Transaktion wird in die Liste der Verfügbaren Transaktionen geschrieben
                retra_list.append(cb)

        # Der Zeitstempel des Blocks wird erstellt
        try: block_timestamp = ATimeString.readFromDBStr(current_block[1])
        except: raise Exception('INVALID_BLOCK_TIME')

        # Der Miner des Blocks wird ermitelt
        first_cb_transaction = block_txns[0]
        tota_address = None
        for _oi in outs:
            # Es wird geprüft ob das Ausgangs UTXO zu dieser Transaktion gehört
            if first_cb_transaction[0] == _oi[0]:
                # Es wird geprüft ob bereits eine Adresse vohanden ist
                if tota_address is None: tota_address = _oi[7]
                else:
                    if tota_address != _oi[7]: raise Exception('INVALID_BLOCK_NO_MULTIPLE_MINER_ADDRESSES')
        if tota_address is None: raise Exception('INVALID_BLOCK_THIS_BLOCK_HAS_NOT_MINER')
        try: miner_adr = LagacyAddress.fromSring(tota_address)
        except: raise Exception('INVALID_BLOCK::INVALID_MINER_ADDRESS')

        # Der Block gebaut
        from apollon.block import BlockConstruct
        try: _rbb = BlockConstruct(prev_block_hash, current_block_id, miner_adr, block_timestamp, int(current_block[6], 16), *retra_list)
        except: raise Exception('INVALID_BLOCK')
        if _rbb.getRootHash(True) != current_block[7]: raise Exception('INVALID_BLOCK_HASH')

        # Der Block wird vollständig nachgebaut
        from apollon.block import ST_MinedBlock
        try: _frbb = ST_MinedBlock.fromConstructWithNonce(_rbb, int(current_block[4], 16), blocks - current_block_id, miner_adr)
        except: raise Exception('INVALID_BLOCK')
        if _frbb.getBlockHash(True) != current_block[0]: raise Exception('INVALID_BLOCK')

        # Die SQL Verbindug wird geschlossen
        return _frbb

    # Gibt die MetaDaten der letzten Blöcke aus # TODO
    def getLastBlocksMetaData(self, Blocks=50, Page=1):
        # Es wird geprüft ob eine Chain geladen wurden
        if self.chain_loaded == False: raise Exception('Objet not created')
        
        # Der Threadlock wird gesperrt
        self.thread_lock.acquire()

        # Es wird eine neue SQL Verbindung aufgebaut
        try: conn = sqlite3.connect(self.chain_file)
        except: self.thread_lock.release(); raise Exception('DB Error')

        # Es wird ein SQL Cursor erzeugt
        try: cur = conn.cursor()
        except: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Es wird die Anzahl der Blöcke ermittelt
        from apollon.utils import sqlPager
        try: block_meta_data = cur.execute("SELECT block_height, block_timestamp, (SELECT count(*) FROM lagacy_transactions WHERE transaction_block = block_height), block_hash FROM blocks ORDER BY block_height DESC LIMIT {}".format(sqlPager(Blocks, Page))).fetchall()
        except Exception as e: print(e); cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        if block_meta_data is None or len(block_meta_data) == 0: cur.close(); conn.close(); self.thread_lock.release(); return list()
        cur.close(); conn.close(); self.thread_lock.release()

        # Die Daten werden ausgearbetet
        relis = list()
        from apollon.atime import ATimeString
        from apollon.block import BlockMetaData
        for i in block_meta_data:
            try: ats = ATimeString.readFromDBStr(i[1])
            except: raise Exception('DATABASE_ERROR')
            relis.append(BlockMetaData(i[0], ats, i[2], i[3]))

        # Die Blockhöhe wird zurückgegben
        return relis

    # Gibt die MetaDaten des Letzten Block aus # TODO
    def getLastBlockMetaData(self): 
        # Es wird geprüft ob eine Chain geladen wurden
        if self.chain_loaded == False: raise Exception('Objet not created')
        
        # Der Threadlock wird gesperrt
        self.thread_lock.acquire()

        # Es wird eine neue SQL Verbindung aufgebaut
        try: conn = sqlite3.connect(self.chain_file)
        except: self.thread_lock.release(); raise Exception('DB Error')

        # Es wird ein SQL Cursor erzeugt
        try: cur = conn.cursor()
        except: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Es wird der letze Block ermittelt
        try: lblock = cur.execute("SELECT block_height, block_root_hash, block_nonce, block_hash FROM blocks ORDER BY block_height DESC LIMIT 1").fetchone()
        except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        if lblock is None or len(lblock) != 4: cur.close(); conn.close(); self.thread_lock.release(); return None
        
        # Die SQL Verbindug wird geschlossen
        try: cur.close(); conn.close(); self.thread_lock.release()
        except: self.thread_lock.release(); raise Exception('DB Error')

        # Die Abgerufenene Daten werden extrahiert
        rdic = dict()
        rdic['block_height'] = lblock[0]
        rdic['block_root_hash'] = lblock[1]
        rdic['nonce'] = lblock[2]
        rdic['block_hash'] = lblock[3]
        return rdic

    # Fügt der Kette einen neuen Block hinzu TODO
    def addBlock(self, BlockObj):
        # Die Chain wird geladen
        if self.chain_loaded == False: raise Exception('Objet not created')

        # Der Threadlock wird gesperrt
        self.thread_lock.acquire()

        # Es wird eine neue SQL Verbindung aufgebaut
        try: conn = sqlite3.connect(self.chain_file)
        except: self.thread_lock.release(); raise Exception('DB Error')

        # Es wird ein MySQL Cursor erzeugt
        try: cur = conn.cursor()
        except: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Es werden alle Transaktionen geprüft TODO
        from apollon.transaction import SignedTransaction, CoinbaseTransaction
        for txi in BlockObj.getAllTransactions():
            # Es wird geprüft ob die Transaktion Valide ist
            if txi.isValidateObject() == False: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Invalid Block')

            # Es wird geprüft ob es sich um eine Signierte Transaktion handelt
            if isinstance(txi, SignedTransaction) == True and txi.signaturesAreValidate() == False: raise Exception('Invalid Block')

            # Es wird geprüft ob die Transaktion bereits in der Datenbank vorhanden ist
            if isinstance(txi, SignedTransaction) == True: transcmd = 'SELECT COUNT(*) FROM lagacy_transactions WHERE transaction_root_hash = ? OR transaction_hash = ?'; transdata = [txi.getRootHash(), txi.getTxHash(True), ]
            else: transcmd = 'SELECT COUNT(*) FROM lagacy_transactions WHERE transaction_hash = ?'; transdata = [txi.getTxHash(True), ]
            try: transaction_check = bool(cur.execute(transcmd, transdata).fetchone()[0] == 0)
            except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Database error {} {}'.format(E, transcmd))
            if transaction_check != True: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Invalid Block T:: {}'.format(BlockObj.getHeight()))

            # Es wird geprüft ob die Verwendeten Ausgangs UTXOs exestieren TODO
            if isinstance(txi, SignedTransaction) == True:
                # Es werden alle Input UTXO's der Transaktion geprüft
                for input_utxos in txi.getInputUxos():
                    # Es wird geprüft ob die Verwendete Transaktion exestiert
                    out_transcheck_cmd = 'SELECT transaction_id FROM lagacy_transactions WHERE transaction_hash ? LIMIT 1'
                    out_transcheck_cmd_data = [input_utxos.getOutTransactionTxn(True), ]
                    try: transaction_check = cur.execute(out_transcheck_cmd, out_transcheck_cmd_data).fetchone()
                    except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Database error 2')
                    if len(transaction_check) == 0: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Invalid Block')
                    if isinstance(transaction_check[0], int) == False: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Invalid Block ')

                    # Es wird geprüft ob das verwendete Ausgangs UTXO exestiert
                    out_utxo_check = 'SELECT output_utxo_hash, output_height, output_amount, output_coin_hid, (SELECT address FROM lagacy_addresses WHERE address_id = output_reciver_address_id) FROM lagacy_output_utxos WHERE output_transaction_id = ? and output_utxo_hash = ? LIMIT 1'
                    out_utxo_check_data = [transaction_check[0], input_utxos.getOutUtxoHash(True), ]
                    try: out_in_utxo_check = cur.execute(out_utxo_check, out_utxo_check_data).fetchone()
                    except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Database error 3')
                    if len(out_in_utxo_check) == 0: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Invalid Block')
                    if out_in_utxo_check[0] != input_utxos.getOutUtxoHash(False): cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Invalid Block')
                    if out_in_utxo_check[1] != input_utxos.getOutUtxoHeight(): cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Invalid Block')
                    if out_in_utxo_check[3] != input_utxos.getCoinValue(True): cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Invalid Block')
                    if out_in_utxo_check[4] != input_utxos.getCoin().getCoinID(False): cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Invalid Block')

                    # Es wird geprüft ob das verwendete Ausgangs UTXO bereits verwendet wird

        # Der Block wird in die Datenbank geschrieben
        insert_block_cmd = 'INSERT INTO blocks (block_height, block_diff, block_type, block_nonce, block_root_hash, block_hash, block_total_transactions, block_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
        insert_block_cmd_data = [BlockObj.getHeight(), hex(BlockObj.getDiff()) ,0, hex(BlockObj.getBlockNonce()), BlockObj.getRootHash(True), BlockObj.getBlockHash(True), hex(BlockObj.getTotalTransactions()), BlockObj.getBlockTimestampe().toDBStr(True)]
        try: cur.execute(insert_block_cmd, insert_block_cmd_data)
        except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)

        # Die Transaktionen werden in die Datenbank geschrieben
        for txi in BlockObj.getAllTransactions():
            # Die Transaktion wird in die Chain geschrieben
            if isinstance(txi, SignedTransaction):
                txiinsert = 'INSERT INTO lagacy_transactions (transaction_hash, transaction_type, transaction_inputs, transaction_outputs, transaction_root_hash, transaction_timestamp, transaction_block_height, transaction_block) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
                txiinsert_data = [txi.getTxHash(True), 10, len(txi.getInputUxos()), len(txi.getOutputUtxos()), txi.getRootHash(), txi.getTimestamp(True), txi.getHeightInBlock() ,BlockObj.getHeight(), ]
            elif isinstance(txi, CoinbaseTransaction):
                txiinsert = 'INSERT INTO lagacy_transactions (transaction_hash, transaction_type, transaction_inputs, transaction_outputs, transaction_timestamp, transaction_block_height, transaction_block) VALUES (?, ?, ?, ?, ?, ?, ?)'
                txiinsert_data = [txi.getTxHash(True), 0, len(txi.getInputUxos()), len(txi.getOutputUtxos()), txi.getTimestamp().toDBStr(True), txi.getHeightInBlock() ,BlockObj.getHeight(), ]
            else: raise Exception('Unkown Transaction Type')
            try: cur.execute(txiinsert, txiinsert_data)
            except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)

            # Die ID der geschriebenen Transaktion wird ermittelt
            catch_txn_db_id_cmd = 'SELECT transaction_id FROM lagacy_transactions WHERE transaction_hash = ? ORDER BY transaction_id DESC LIMIT 1'
            try: transaction_id = cur.execute(catch_txn_db_id_cmd, [txi.getTxHash(True), ]).fetchone()
            except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
            if transaction_id is None or len(transaction_id) == 0: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Database error X1')

            # Die Eingangs UTXOs werden geschrieben
            from apollon.utxo import LagacyOutUtxo, LagacyInUtxo, CoinbaseInUtxo
            for iutxo in txi.getInputUxos():
                if isinstance(iutxo, CoinbaseInUtxo) == True:
                    insert_input_reward_utxo = '''
                    INSERT INTO lagacy_input_utxos (input_type, input_height, input_utxo_hash, input_block_height, input_transaction_id, input_reward_amount, input_reward_coin_hid, input_one_time_reward_hash)
                    VALUES (0, ?, ?, ?, ?, ?, ?, ?);'''
                    insert_input_reward_utxo_data = [iutxo.getHeight(), iutxo.getHash(True), BlockObj.getHeight(), transaction_id[0], hex(iutxo.getCoinValue(True)), iutxo.getCoin().getCoinID(True), iutxo.getOneTimeHash(True), ]
                    try: output_data = cur.execute(insert_input_reward_utxo, insert_input_reward_utxo_data).fetchone()
                    except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
                elif isinstance(iutxo, LagacyInUtxo) == True:
                    # Die Daten des Verwendeten Ausgangs UTXOs werden ermittelt
                    select_output_utxo = '''
                    SELECT output_utxo_id , output_transaction_id
                    FROM lagacy_output_utxos
                    WHERE output_transaction_id = (SELECT transaction_id FROM lagacy_transactions WHERE transaction_hash = ? LIMIT 1)
                    AND output_utxo_hash = ? AND output_height = ? LIMIT 1'''
                    try: output_data = cur.execute(select_output_utxo, [iutxo.getOutTransactionTxn(True), iutxo.getOutUtxoHash(True), iutxo.getOutUtxoHeight(), ]).fetchone()
                    except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
                    if output_data is None or len(output_data) == 0: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Database error X1')
                    # Das UTXO wird in die Datenbank geschrieben
                else: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Database errro X4')

            # Die Ausgangs UTXOs werden geschrieben
            for outxo in txi.getOutputUtxos():
                # Es wird geprüft ob die Verwendete Adresse bereits in der Datenbank vorhanden ist, wenn nicht wird sie Hinzugefügt
                address_check_cmd = 'SELECT count(*) FROM lagacy_addresses WHERE address_hash = ?'
                try: adr_check = cur.execute(address_check_cmd, [outxo.getReciverAddress().getHash(True), ]).fetchone()
                except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
                if len(adr_check) == 0: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Database errro X2')
                if adr_check[0] == 0:   # Die Adresse wird neu hinzugefügt
                    add_address_cmd = 'INSERT INTO lagacy_addresses (address_hash, address, add_by_block) VALUES (?,?,?)'
                    try: cur.execute(add_address_cmd, [outxo.getReciverAddress().getHash(True), outxo.getReciverAddress().toStr(True), BlockObj.getHeight(), ])
                    except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
                address_id_resolv_cmd = 'SELECT address_id FROM lagacy_addresses WHERE address_hash = ? ORDER BY address_id DESC LIMIT 1'
                try: address_id_resolv = cur.execute(address_id_resolv_cmd, [outxo.getReciverAddress().getHash(True), ]).fetchone()
                except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
                if len(address_id_resolv) == 0: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Database errro X3')

                # Das Ausgangs UTXO wird geschrieben
                if isinstance(outxo, LagacyOutUtxo):
                    output_utxo_insert_cmd = '''
                    INSERT INTO  lagacy_output_utxos (output_height, output_utxo_hash, output_coin_hid, output_amount, output_reciver_address_id, output_transaction_id, output_utxo_type, output_utxo_block_height)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''
                    output_utxo_insert_cmd_data = [outxo.getHeight(), outxo.getHash(True), outxo.getCoin().getCoinID(True), hex(outxo.getCoinValue(True)), address_id_resolv[0], transaction_id[0], 10, BlockObj.getHeight(), ]
                else: raise Exception('Invalid Out UTXO')
                try: adr_check = cur.execute(output_utxo_insert_cmd, output_utxo_insert_cmd_data).fetchone()
                except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)

            # Die Signaturen werden geschrieben
            if isinstance(txi, SignedTransaction):
                for txsign in txi.getSignatures():
                    # Die ID der Adresse wird aus dér Datenbank ermittelt
                    address_id_resolv_cmd = 'SELECT address_id FROM lagacy_addresses WHERE address_hash = ? ORDER BY address_id DESC LIMIT 1'
                    try: address_id_resolv = cur.execute(address_id_resolv_cmd, [txsign.getSignerAddressHash(True), ]).fetchone()
                    except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
                    if len(address_id_resolv) == 0: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('Database errro X3')
                    
                    # Die Signatur wird in die Datenbank geschrieben
                    sign_sql_qur = 'INSERT INTO lagacy_transactions_signatures (sign_transaction_id, sign_signer_address_id, signature, sign_block_height) VALUES (?, ?, ?, ?)'
                    sign_sql_dta = [transaction_id[0], address_id_resolv[0], txsign.getSignature(True), BlockObj.getHeight(), ]
                    try: address_id_resolv = cur.execute(sign_sql_qur, sign_sql_dta).fetchone()
                    except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)

        # Die Änderungen werden geschrieben
        try: conn.commit()
        except: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Die Daten werden entgültig in der Datenbank abgespeichert
        cur.close(); conn.close(); self.thread_lock.release()

        return

    # Gibt das Verfügabre Guthaben einer Adresse aus # TODO
    def getAddressDetails(self, Addresses, *MempoolTransactions):
        # Es wird geprüft ob eine Chain geladen wurden
        if self.chain_loaded == False: raise Exception('Objet not created')
        
        # Es wird geprüft ob es sich um eine Lagacy oder Chain eigene Adresse handelt
        from apollon.apollon_address import LagacyAddress, BlockchainAddress
        if isinstance(Addresses, LagacyAddress) == False and isinstance(Addresses, BlockchainAddress) == False: raise Exception('Invalid address type {}'.format(type(Addresses)))

        # Der Threadlock wird gesperrt
        self.thread_lock.acquire()

        # Es wird eine neue SQL Verbindung aufgebaut
        try: conn = sqlite3.connect(self.chain_file)
        except: self.thread_lock.release(); raise Exception('DB Error')

        # Es wird ein SQL Cursor erzeugt
        try: cur = conn.cursor()
        except: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Die Adresse wird aus dem Storage abgerufen
        from apollon.address_utils import AddressCoinDetails, AddressChainDetails
        try: address_id = cur.execute("SELECT address_id FROM lagacy_addresses WHERE address_hash = ? LIMIT 1", [Addresses.getHash(True)]).fetchone()
        except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        if address_id is None: conn.close(); self.thread_lock.release(); return AddressChainDetails(Addresses, 0, *self.master_object.getCoins())

        # Die Anzahl aller Transaktionen wird ermittelt
        try: total_address_transactions = cur.execute("SELECT COUNT(*) FROM lagacy_transactions WHERE lagacy_transactions.transaction_id in (SELECT lagacy_output_utxos.output_transaction_id FROM lagacy_output_utxos WHERE lagacy_output_utxos.output_reciver_address_id = ?)", [address_id[0]]).fetchone()[0]
        except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Es werden all UTXOs zusammen gezählt
        try: unspent_utxo = cur.execute("""
        SELECT 
            lagacy_output_utxos.output_utxo_id,
            lagacy_output_utxos.output_amount,
            lagacy_output_utxos.output_coin_hid,
	        CASE lagacy_input_utxos.input_output_utxo_id 
                WHEN lagacy_output_utxos.output_utxo_id
                    THEN 1
                ELSE 0
            END spendch
        FROM lagacy_output_utxos
        LEFT JOIN lagacy_input_utxos ON lagacy_input_utxos.input_output_utxo_id = lagacy_output_utxos.output_utxo_id 
        WHERE lagacy_output_utxos.output_reciver_address_id = ?""", [address_id[0]]).fetchall()
        except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        if unspent_utxo == None or len(unspent_utxo) == 0: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Die SQL Verbindung wird geschlossen
        try: cur.close(); conn.close(); self.thread_lock.release()
        except: raise Exception('STORAGE_SQL_ERROR')

        # Die Adressedetails werden erstellt
        address_details = AddressChainDetails(Addresses, total_address_transactions, *self.master_object.getCoins())

        # Es werden alle Eingänge zusammen gezählt
        for outx in unspent_utxo:
            chain_coin_check_resolv = self.master_object.getChainCoinByID(outx[2])
            if chain_coin_check_resolv is None: raise Exception('Invalid Coin')
            for coinobj in self.master_object.getCoins():
                if coinobj.getCoinID(True) == chain_coin_check_resolv.getCoinID(True):
                    address_details.addInput(chain_coin_check_resolv, int(outx[1], 16), True)
                    if outx[3] != 0: address_details.addOutput(chain_coin_check_resolv ,int(outx[1], 16), True)

        # Das Guthaben wird zurückgegben
        return address_details

    # Gibt alle Transaktionen einer Adresse aus # TODO
    def getAddressTransactions(self, *MemoryPoolTransactions, Addresses, MaxEntries=25, CurrentPage=1):
        # Es wird geprüft ob eine Chain geladen wurden
        if self.chain_loaded == False: raise Exception('Objet not created')
        
        # Der Threadlock wird gesperrt
        self.thread_lock.acquire()
        
        # Es wird eine neue SQL Verbindung aufgebaut
        try: conn = sqlite3.connect(self.chain_file)
        except: self.thread_lock.release(); raise Exception('DB Error')

        # Es wird ein SQL Cursor erzeugt
        try: cur = conn.cursor()
        except: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Es wird die Anzahl der Blöcke ermittelt
        try: blocks = cur.execute("SELECT block_height FROM blocks ORDER BY block_height DESC LIMIT 1").fetchone()
        except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        if blocks is None or len(blocks) != 1 or type(blocks[0]) is not int: cur.close(); conn.close(); self.thread_lock.release(); return 0
        blocks = blocks[0] + 1

        # Die Adresse wird aus dem Storage abgerufen
        try: address_id = cur.execute("SELECT address_id FROM lagacy_addresses WHERE address_hash = ? LIMIT 1", [Addresses.getHash(True)]).fetchone()
        except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
        if address_id is None: conn.close(); self.thread_lock.release(); return list()

        # Es wird geprüft wieviele Einträge aberufen werden
        from apollon.utils import sqlPager
        if isinstance(MaxEntries, int) == True: cmd = "SELECT transaction_id, transaction_hash, transaction_root_hash, transaction_type, transaction_block, transaction_timestamp FROM lagacy_transactions WHERE transaction_id IN (SELECT output_transaction_id FROM lagacy_output_utxos WHERE output_reciver_address_id = ?) ORDER BY transaction_block DESC LIMIT {}".format(sqlPager(MaxEntries, CurrentPage))
        else: cmd = "SELECT transaction_id, transaction_hash, transaction_root_hash, transaction_type, transaction_block, transaction_timestamp FROM lagacy_transactions WHERE transaction_id IN (SELECT output_transaction_id FROM lagacy_output_utxos WHERE output_reciver_address_id = ?) ORDER BY transaction_block DESC"

        # Es werden all Transaktionen abgerufen
        try: txns = cur.execute(cmd, [address_id[0]]).fetchall()
        except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); print(E); raise Exception('DB Error')
        if txns == None or len(txns) == 0: conn.close(); self.thread_lock.release(); return list()
        txnl = list()
        for i in txns: txnl.append(i[0])
        txnstr = str(tuple(txnl))
        if txnstr[-2] == ',': txnstr = txnstr.replace(txnstr[-2],"")

        # Es werden alle Eingänge Abgerufen
        try: ins = cur.execute("SELECT input_transaction_id, input_type, input_utxo_hash, input_output_utxo_id, input_reward_coin_hid, input_reward_amount, input_block_height, input_one_time_reward_hash, input_height FROM lagacy_input_utxos WHERE input_transaction_id IN {} ORDER BY input_transaction_id DESC, input_height ASC".format(txnstr)).fetchall()
        except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)
        if ins == None or len(ins) == 0: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Es werden alle Ausgänge Abgerufen
        try: outs = cur.execute("""
        SELECT
            lagacy_output_utxos.output_transaction_id,
            lagacy_output_utxos.output_utxo_id,
            lagacy_output_utxos.output_amount,
            lagacy_output_utxos.output_coin_hid,
			lagacy_output_utxos.output_reciver_address_id,
			lagacy_output_utxos.output_utxo_hash,
			lagacy_output_utxos.output_utxo_type,
			lagacy_addresses.address,
			lagacy_addresses.address_hash,
	        CASE lagacy_input_utxos.input_output_utxo_id 
                WHEN lagacy_output_utxos.output_utxo_id
                    THEN 1
                ELSE 0
            END spendch
        FROM lagacy_output_utxos
        LEFT JOIN lagacy_input_utxos ON lagacy_input_utxos.input_output_utxo_id = lagacy_output_utxos.output_utxo_id
		LEFT JOIN lagacy_addresses ON lagacy_addresses.address_id = lagacy_output_utxos.output_reciver_address_id 
        WHERE lagacy_output_utxos.output_transaction_id IN {} ORDER BY output_transaction_id DESC, output_height ASC""".format(txnstr)).fetchall()
        except: cur.close(); conn.close(); self.thread_lock.release(); raise Exception('DB Error')
        if outs == None or len(outs) == 0: conn.close(); self.thread_lock.release(); raise Exception('DB Error')

        # Es werden alle Signaturen abgerufen
        #try: sigs = cur.execute("SELECT sign_transaction_id FROM lagacy_transactions_signatures WHERE sign_transaction_id IN {}".format(txnstr)).fetchall()
        #except Exception as E: cur.close(); conn.close(); self.thread_lock.release(); raise Exception(E)

        # Die SQL Verbindung wird geschlossen
        try: cur.close(); conn.close(); self.thread_lock.release()
        except: raise Exception('STORAGE_SQL_ERROR')

        # Die Transaktionen werden zusammengefasst
        retra_list = list()
        from apollon.transaction import ST_CoinbaseTransaction, SignedTransaction
        from apollon.utxo import CoinbaseInUtxo, ST_LagacyOutUtxo
        from apollon.apollon_address import LagacyAddress
        from apollon.atime import ATimeString
        for i in txns:
            # Speichert die UTXOs zwischen
            utxos = list()

            # Die Eingänge werden verarbeitet
            for inp in ins:
                # Es wird geprüft ob es sich um die Aktuelle Transaktion handelt
                if inp[0] == i[0]:
                    # Es wird geprüft ob es sich um ein Coinbase Reward handelt
                    if inp[1] == 0:
                        coinobj = None
                        # Es wird geprüft ob es sich um einen Zulässigen Coin handelt
                        for coib in self.master_object.getCoins():
                            if coib.getCoinID(True) == inp[4]: coinobj = coib; break
                        if coinobj is None: raise Exception('Unkown Coin')

                        # Es wird geprüft ob der Reward Hash korrekt ist
                        if coinobj.validateReward(int(inp[5], 16),inp[6]) == False: raise Exception('Invalid reward')

                        # Es wird geprüft, ob der Rewardhash korrekt ist
                        oth = coinobj.createOneTimeRewardHash(inp[6], True)
                        if oth != inp[7]: raise Exception('Invalid reward one time hash')

                        # Es wird versucht das Inout UTXO nachzubilden
                        try: nwo_inp = CoinbaseInUtxo(inp[6], coinobj, int(inp[5], 16), oth)
                        except: raise Exception('Address cant parse')
                        utxos.append(nwo_inp)

            # Die Ausgänge werden verarbeitet
            for onp in outs:
                # Es wird geprüft ob es sich um die Aktuelle Transaktion handelt
                if onp[0] == i[0]:
                    # Es wird geprüft ob es sich um ein Standart Output handelt
                    if onp[6] == 10:
                        # Es wird geprüft ob es sich um einen Zulässigen Coin handelt
                        coinobj = None
                        for coib in self.master_object.getCoins():
                            if coib.getCoinID(True) == onp[3]: coinobj = coib; break
                        if coinobj is None: raise Exception('Unkown Coin')

                        # Es werden alle Inputs mit dem Selben Coin Abgerufen
                        inch = list()
                        for inh in utxos:
                            if inh.getCoin().getCoinID(True) == coinobj.getCoinID(True): inch.append(inh)

                        # Die Verwendete Ausgangsadresse wird abgerufen
                        try: resolv_addr = LagacyAddress.fromSring(onp[7])
                        except: raise Exception('Address cant parse')

                        # Es wird geprüft ob der Verwendete Address Hash übereinstimmt
                        if resolv_addr.getHash(True) != onp[8]: raise Exception('Invalid Address')

                        # Es wird versucht das Ausgangs UTXO nachzubilden
                        try: outxo = ST_LagacyOutUtxo(resolv_addr, int(onp[2], 16), coinobj, bool(onp[9]) ,*inch)
                        except: raise Exception('Address cant parse')
                        utxos.append(outxo)

            # Es wird geprüft ob es sich um eine Coinbase Transaktion handelt
            if i[3] == 0:
                # Die Uhrzeit wird aus der Datenbank abgerufen
                try: timestr = ATimeString.readFromDBStr(i[5])
                except: raise Exception('DB Error A')

                # Die Transaktion wird Rückgebildet
                try: cb = ST_CoinbaseTransaction(*utxos, BlockNo=i[4], TStamp=timestr, Confirmations=int(blocks - i[4]))
                except Exception as E: print(E); raise Exception(E)

                # Es wird gepürft ob die Transaktion erfolgreich erstellt wurde
                if i[1] != cb.getTxHash(True): raise Exception('Invalid transaction')

                # Die Transaktion wird in die Liste der Verfügbaren Transaktionen geschrieben
                retra_list.append(cb)

        # Die SQL Verbindug wird geschlossen
        return retra_list

    # Gibt die Version des Storage aus
    def getVersion(self): return "0.2"

    # Lädt eine Bereits vorhandene Blockchain # TODO
    @classmethod
    def fromFile(cls, DbFile, MasterObject, FullValidate):
        # Es wird geprüft ob die Datei vorhanden ist
        if path.exists(DbFile) == False: raise Exception('File not Found')

        # Es werden alle benötigten Librarys Importiert
        from apollon.console import printProgressBar, logPrint
        from apollon.atime import ATimeString

        # Gibt ein LogPrint aus
        logPrint('Loading Blockcahin Database...')

        # Es versucht eine SQL Verbindung aufzubauen
        try: conn = sqlite3.connect(DbFile)
        except: raise Exception('Invalid Database')

        # Es wird ein SQL Cursor erzeugt
        try: cur = conn.cursor()
        except: conn.close(); raise Exception('DB Error')

        # Es wird die Anzahl der Blöcke ermittelt
        try: blocks = cur.execute("SELECT (SELECT count(*) FROM blocks), block_height  FROM blocks ORDER BY block_height DESC LIMIT 1").fetchone()
        except: cur.close(); conn.close(); raise Exception('DB Error')

        # Es wird geprüft ob bereits blöcke vorhanden sind
        if blocks is not None and len(blocks) > 0 and blocks[0] != 0: # Es sind Blöcke vorhanden, es werden alle Blöcke auf ihre gültigkeit geprüft
            # Es wird geprüft ob mehr als 500 Blöcke vorhanden sind
            if blocks[0] <= 25: eval_i = blocks[0]
            else: eval_i = int(blocks[0] - 25)
            
            # Es wird jeder Block einzelen Abgerufen und geprüft
            for prog, blockheight in enumerate(list(range(1, blocks[0] +1))):
                # Es wird geprüft ob eine Vollständige Prüfung der Blockchain durchgeführt werden soll
                if FullValidate == True or (FullValidate == False and blockheight <= 25) or (FullValidate == False and (eval_i != blocks[0] and blockheight >= eval_i)):

                    # Die Daten des Blocks werden abgerufen
                    try: currblock = cur.execute('SELECT rbl.block_hash, rbl.block_root_hash, rbl.block_nonce, rbl.block_diff, rbl.block_timestamp, rbl.block_total_transactions, rbl.block_type, (SELECT bl.block_hash FROM blocks bl WHERE bl.block_height = rbl.block_height-1) as prev_hash FROM blocks rbl WHERE rbl.block_height = ?', [blockheight]).fetchone()
                    except: cur.close(); conn.close(); raise Exception('Invalid Chain')
                    if currblock is None or len(currblock) != 8: cur.close(); conn.close(); raise Exception('Invalid Chain')

                    # Es wird versucht die Blockzeit einzulesen
                    try: block_time_string = ATimeString.readFromDBStr(currblock[4])
                    except: cur.close(); conn.close(); raise Exception('Invalid Block Time')

                    # Die Transaktionen werden vollständig abgerufen
                    txnqur = "SELECT transaction_hash, transaction_root_hash, transaction_block, transaction_type, transaction_id, transaction_timestamp FROM lagacy_transactions WHERE transaction_block = ? ORDER BY transaction_block_height ASC"
                    try: transactions = cur.execute(txnqur, [blockheight]).fetchall()
                    except: cur.close(); conn.close(); raise Exception('Invalid Chain x!')

                    # Es werden alle Transaktionen geprüft
                    block_transactions = list()
                    for tx in transactions:
                        # Es wird geprüft ob es sich um einen gültigen Transaktionstypen handelt
                        if tx[3] != 0 and tx[3] != 10: cur.close(); conn.close(); raise Exception('Invalid Transaction type')

                        # Es wird geprüft ob es sich um die erste Transaktion des Blocks handelt
                        if tx[3] == 0 and len(block_transactions) != 0: cur.close(); conn.close(); raise Exception('Only the first Transaction off Block can Coinbase Transaction')

                        # Es werden alle Eingänge abgerufen
                        input_utxo_cmd = """
                        SELECT 
	                        input_type, 
	                        input_utxo_hash, 
	                        (SELECT transaction_hash FROM lagacy_transactions WHERE transaction_id = input_transaction_id LIMIT 1) as transaction_hash, 
	                        input_reward_amount,
	                        input_reward_coin_hid,
	                        input_one_time_reward_hash
                        FROM lagacy_input_utxos WHERE input_transaction_id = ? AND input_block_height = ?
                        ORDER BY input_height ASC"""
                        try: inutxo_res = cur.execute(input_utxo_cmd, [tx[4],blockheight]).fetchall()
                        except: cur.close(); conn.close(); raise Exception('Invalid Chain::X1')

                        # Es wird geprüft ob Mindestens ein Input UTXO vorhanden ist
                        if inutxo_res is None or len(inutxo_res) < 1: cur.close(); conn.close(); raise Exception('Invalid Chain::X2')

                        # Es werden alle Eingänge Kontrolliert
                        hashed_input_utxos = list()
                        for iutx in inutxo_res:
                            # Es wird geprüft ob es sich um eine CoinBase Transaktion und ein Coinbase Reward UTXO handelt
                            if tx[3] == 0 and (iutx[0] == 0 or iutx[0] == 1): 
                                
                                # Es wird geprüft ob es sich um einen Chain bekannten Coin handelt
                                chain_coin_check_resolv = MasterObject.getChainCoinByID(iutx[4])
                                if chain_coin_check_resolv is None: cur.close(); conn.close(); raise Exception('Invalid Coin')
                                
                                # Es wird geprüft ob die höhe der Belohnung korrekt ist
                                if chain_coin_check_resolv.validateReward(int(iutx[3], 16), blockheight) == False: cur.close(); conn.close(); raise Exception('Invalid Reward')

                                # Es wird geprüft ob der OneTime Reward Hash korrekt ist
                                if chain_coin_check_resolv.createOneTimeRewardHash(blockheight, True) != iutx[5]: cur.close(); conn.close(); raise Exception('Invalid Reward')

                                # Es wird ein Hash aus dem Input UTXO erstellt
                                hli = hashlib.sha3_256()
                                hli.update(str(blockheight).encode())
                                hli.update(str(int(iutx[3], 16)).encode())
                                hli.update(chain_coin_check_resolv.getCoinID(True))
                                hli.update(str(len(hashed_input_utxos)).encode())
                                hli.update(iutx[5])

                                # Es wird geprüft ob der Hash, mit dem Hash in der Datenbank übereinstimmt
                                if hli.digest() != iutx[1]: cur.close(); conn.close(); raise Exception('Invalid Reward, Invalid Chain')
                                hashed_input_utxos.append({ 'coin' : iutx[4], 'hash' : hli.digest(), 'amount' :  int(iutx[3], 16)})

                            # Es Wird geprüft ob es sich um eine Lagacy Transaktion handelt
                            elif tx[3] == 10 and iutx[0] == 10: print('Lagacy')

                            # Es handelt sich um ein Unzulässiges Input UTXO
                            else: cur.close(); conn.close(); cur.close(); conn.close(); raise Exception('Invalid Chain::X4')

                        # Es werden alle Ausgänge abgerufen
                        output_utxo_cmd = """
                        SELECT 
                            output_utxo_type,
                            output_coin_hid,
                            output_utxo_hash,
                            (SELECT transaction_hash FROM lagacy_transactions WHERE transaction_id = output_transaction_id LIMIT 1) as output_transaction_hash,
                            (SELECT address_hash FROM lagacy_addresses WHERE address_id = output_reciver_address_id) as reciver_address_hash,
                            output_amount
                        FROM lagacy_output_utxos WHERE output_transaction_id = ? AND output_utxo_block_height = ?
                        ORDER BY output_height ASC"""
                        try: oputxo_res = cur.execute(output_utxo_cmd, [tx[4],blockheight]).fetchall()
                        except: cur.close(); conn.close(); raise Exception('Invalid Chain::X3')

                        # Es wird geprüft ob Mindestens ein Ausgangs UTXO vorhanden ist
                        if oputxo_res is None or len(oputxo_res) < 1: cur.close(); conn.close(); raise Exception('Invalid Chain::X4')

                        # Es werden alle Ausgänge Kontrolliert
                        hashed_output_utxos = list()
                        for outx in oputxo_res:
                            # Es wird geprüft ob es sich um ein Lagacy UTXO handelt
                            if outx[0] == 10:

                                # Es wird geprüft ob der Hash der Transaktion übereinstimmt
                                if outx[3] != tx[0]: cur.close(); conn.close(); raise Exception('Invalid Chain::X5')

                                # Es wird geprüft ob es sich um einen gültigen Chain Coin handelt
                                chain_coin_check_resolv = MasterObject.getChainCoinByID(outx[1])
                                if chain_coin_check_resolv is None: cur.close(); conn.close(); raise Exception('Invalid Coin')

                                # Es werden alle Input Hashes extrahiert
                                input_hashes = list()
                                for u in hashed_input_utxos:
                                    if u['coin'] == outx[1]: input_hashes.append(u['hash'])

                                # Es wird geprüft ob Mindestens ein Input vorhanden ist
                                if len(input_hashes) == 0: cur.close(); conn.close(); raise Exception('Invalid Transaction')

                                # Es wird ein Input Root Hash erstellt
                                irh = hashlib.sha3_256()
                                for u in input_hashes: irh.update(u)

                                # Es wird ein Hash aus dem UXO erstellt
                                ouh = hashlib.sha3_256()
                                ouh.update(outx[4])
                                ouh.update(str(int(outx[5], 16)).encode())
                                ouh.update(outx[1])
                                ouh.update(str(len(hashed_output_utxos)).encode())
                                ouh.update(irh.digest())

                                # Es wird geprüft ob der Gebildete Hash mit dem Hash in der Datenbank übereinstimmt
                                if ouh.digest() != outx[2]: cur.close(); conn.close(); raise Exception('Invalid Transaction')

                                # Der Hash wird der Hashliste Hinzugefügt
                                hashed_output_utxos.append({ 'coin' : outx[1], 'hash' : ouh.digest(), 'amount' :  int(outx[5], 16)})

                            # Es handelt sich um ein unbekanntes Ausgangs UTXO
                            else: cur.close(); conn.close(); raise Exception('Invalid Coin')

                        # Es wird versucht die Zeit der Transaktion einzulesen
                        try: tts = ATimeString.readFromDBStr(tx[5])
                        except: cur.close(); conn.close(); raise Exception('Invalid Transaction Time')

                        # Es wird geprüft ob es sich um eine Coinbase oder eine Signierte Transaktion handelt
                        if tx[3] == 0:
                            # Der Transaktionshash wird Rückgebildet
                            hu = hashlib.sha3_384()
                            hu.update(str(int(blockheight)).encode())
                            hu.update(tts.getHash(True))
                            for k in hashed_input_utxos: hu.update(k['hash'])
                            for k in hashed_output_utxos: hu.update(k['hash'])

                            # Es wird geprüft ob der Transaktionhash korrekt ist
                            if hu.digest() != tx[0]: cur.close(); conn.close(); raise Exception('Invalid Transaction')

                            # Der Aktuelle Hash der Transaktion wird der Transaktionskette hinzugefügt
                            block_transactions.append(hu.digest())

                        # Es handelt sich um einen unbekannten Transaktionstypen
                        else: cur.close(); conn.close(); raise Exception('Invalid Transaction type')

                    # Der Block Roothash wird gebildet
                    import pycryptonight, binascii
                    hash_array = bytes(str(blockheight).encode())
                    if blockheight == 1: hash_array = hash_array + MasterObject.getChainRootHash(True)
                    else: hash_array = hash_array + currblock[7]
                    hash_array = hash_array + str(int(currblock[3], 16)).encode()
                    hash_array = hash_array + block_time_string.getHash(True)
                    for asi in block_transactions: hash_array = hash_array + asi
                    crypnhash = pycryptonight.cn_fast_hash(hash_array)

                    # Es wird geprüft ob der Block Roothash übereinstimmt
                    if currblock[1] != binascii.hexlify(crypnhash): cur.close(); conn.close();  raise Exception('Invalid Chain x {}'.format(blockheight))

                    # Es wird geprüft ob die Nonce korrekt ist
                    from apollon.utils import validateNonce
                    if validateNonce(currblock[0], binascii.hexlify(crypnhash), int(currblock[2], 16), int(currblock[3], 16)) == False: cur.close(); conn.close(); raise Exception('Invalid Chain')

                # Es wird ein QuickCheck durchgeführt
                else: 
                    # Die Daten des Blocks werden abgerufen
                    try: currblock = cur.execute('SELECT rbl.block_hash, rbl.block_root_hash, rbl.block_nonce, rbl.block_diff, rbl.block_timestamp, rbl.block_total_transactions, rbl.block_type, (SELECT bl.block_hash FROM blocks bl WHERE bl.block_height = rbl.block_height-1) as prev_hash FROM blocks rbl WHERE rbl.block_height = ?', [blockheight]).fetchone()
                    except: cur.close(); conn.close(); raise Exception('Invalid Chain')
                    if currblock is None or len(currblock) != 8: cur.close(); conn.close(); raise Exception('Invalid Chain')

                    # Es wird versucht die Blockzeit einzulesen
                    try: block_time_string = ATimeString.readFromDBStr(currblock[4])
                    except: cur.close(); conn.close(); raise Exception('Invalid Block Time')

                    # Die Transaktionen werden vollständig abgerufen
                    txnqur = "SELECT transaction_hash FROM lagacy_transactions WHERE transaction_block = ? ORDER BY transaction_block_height ASC"
                    try: transactions = cur.execute(txnqur, [blockheight]).fetchall()
                    except: cur.close(); conn.close(); raise Exception('Invalid Chain x!')

                    # Der Roothash wird gebildet
                    import pycryptonight, binascii
                    hash_array = bytes(str(blockheight).encode())
                    if blockheight == 1: hash_array = hash_array + MasterObject.getChainRootHash(True)
                    else: hash_array = hash_array + currblock[7]
                    hash_array = hash_array + str(int(currblock[3], 16)).encode()
                    hash_array = hash_array + block_time_string.getHash(True)
                    for asi in transactions: hash_array = hash_array + asi[0]
                    crypnhash = pycryptonight.cn_fast_hash(hash_array)

                    # Es wird geprüft ob der Block Roothash übereinstimmt
                    if currblock[1] != binascii.hexlify(crypnhash): cur.close(); conn.close();  raise Exception('Invalid Chain x!2')

                # Aktualisiert die Progressbar
                printProgressBar(prog + 1, blocks[0], prefix = 'Loading {} blocks:'.format(blocks[0]), suffix = 'Complete', length = 50)

        # Es handelt sich um eine Leere Chain
        else: logPrint('Empty chain')

        # Das neue Objekt wird erstellt
        c = cls(MasterObject)
        c.chain_file = DbFile
        c.chain_loaded = True
        return c

    # Erstellt eine Kompeltt leere neue Datenbank
    @classmethod
    def newFile(cls, FilePath):
        # Es werden alle benötigten Librarys Importiert
        from apollon.console import printProgressBar, logPrint
        from apollon.atime import ATimeString

        # Es versucht eine SQL Verbindung aufzubauen
        try: conn = sqlite3.connect(str(FilePath))
        except: raise Exception('Invalid Database')

        # Es wird ein MySQL Cursor erzeugt
        try: cur = conn.cursor()
        except: conn.close(); raise Exception('DB Error')

        # Es werden alle Benötigten Tabellen angelegt
        try: 
            # Die Block Tabelle wird erstellt
            cur.execute("""
            CREATE TABLE "blocks" (
                "block_height"	INTEGER,
                "block_diff"	TEXT,
                "block_type"	INTEGER,
                "block_nonce"	TEXT,
                "block_root_hash"	BLOB,
                "block_timestamp"	BLOB,
                "block_hash"	BLOB,
                "block_total_transactions"	INTEGER,
            PRIMARY KEY("block_height"))""")

            # Die Lagacy Adress Tabelle wird erstellt
            cur.execute("""
            CREATE TABLE "lagacy_addresses" (
                "address_id"	INTEGER PRIMARY KEY AUTOINCREMENT,
                "address"	BLOB,
                "address_hash"	BLOB,
                "type"	INTEGER,
                "add_by_block"	INTEGER
            )""")

            # Die Lagacy Input Tabelle wird erstellt
            cur.execute("""
            CREATE TABLE "lagacy_input_utxos" (
                "input_id"	INTEGER PRIMARY KEY AUTOINCREMENT,
                "input_type"	INTEGER,
                "input_height"	INTEGER,
                "input_utxo_hash"	BLOB,
                "input_block_height"	INTEGER,
                "input_transaction_id"	INTEGER,
                "input_output_utxo_id"	INTEGER,
                "input_reward_amount"	TEXT,
                "input_reward_coin_hid"	BLOB,
                "input_output_block_height"	INTEGER,
                "input_output_transaction_id"	INTEGER,
                "input_one_time_reward_hash"	BLOB
            )""")

            # Die Lagacy Output Tabelle wird erstellt
            cur.execute("""
            CREATE TABLE "lagacy_output_utxos" (
                "output_utxo_id"	INTEGER PRIMARY KEY AUTOINCREMENT,
                "output_height"	INTEGER,
                "output_utxo_hash"	BLOB,
                "output_coin_hid"	BLOB,
                "output_amount"	TEXT,
                "output_reciver_address_id"	INTEGER,
                "output_transaction_id"	INTEGER,
                "output_utxo_type"	INTEGER,
                "output_utxo_block_height"	INTEGER
            )""")

            # Die Lagacy Transaktions Tabelle wird erstellt
            cur.execute("""
            CREATE TABLE "lagacy_transactions" (
                "transaction_id"	INTEGER PRIMARY KEY AUTOINCREMENT,
                "transaction_hash"	BLOB,
                "transaction_type"	INTEGER,
                "transaction_inputs"	INTEGER DEFAULT 0,
                "transaction_outputs"	INTEGER DEFAULT 0,
                "transaction_root_hash"	BLOB,
                "transaction_timestamp"	TEXT,
                "transaction_block_height"	INTEGER,
                "transaction_block"	INTEGER
            )""")

            # Die Signaturen Tabelle wird erstellt
            cur.execute("""
            CREATE TABLE "lagacy_transactions_signatures" (
                "signature_id"	INTEGER PRIMARY KEY AUTOINCREMENT,
                "sign_transaction_id"	INTEGER,
                "sign_signer_address_id"	INTEGER,
                "signature"	BLOB,
                "sign_block_height"	INTEGER
            )""")
        except Exception as E: cur.close(); conn.close(); raise Exception(E)

        # Die Daten werden geschrieben
        try: conn.commit()
        except: raise Exception('Unkown error')

        # Die SQL Verbindung wird geschlossen
        cur.close(); conn.close()

        # Die Funktion Returnt
        return
