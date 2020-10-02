from flask import Flask, jsonify, make_response


def FlaskSites(FlaskO, ChainObj):
    # Index Page
    @FlaskO.route('/')
    def index():
        redict = dict()
        # Die Programmversion wird geschrieben
        from apollon import VERSION, gv_
        redict['node_version'] = VERSION

        # Die Storage Funktion wird geschrieben
        redict['storage_version'] = gv_.ChainDB.getVersion()

        # Die Nodesprache wird festgehalten
        redict['node_lang'] = 'Python 3.8'

        # Der Verwendete Mining Hash Algorhytmus wird geschrieben
        redict['mining_hash_algo'] = 'RandomX / Cryptonight v8'

        # Gibt die Hashrate aus
        redict['hashrate'] = ChainObj.getHashrate()

        # Die Zeitzone wird ermittelt
        redict['timezone'] = 'UTC'

        # Die Aktuellen Block Informationen werden abgerufen
        last_block_meta_data = ChainObj.getLastBlockMetaData(False)
        if last_block_meta_data['block_height'] == 0: redict['block_height'] = 0
        else: redict['block_height'] = last_block_meta_data['block_height']
        
        # Die Schwierigkeit wird geschrieben
        redict['difficult'] = ChainObj.getBlockDiff(last_block_meta_data['block_height'])

        # Die Anzahl der Verbundenen Nodes wird ermittelt
        redict['connected_nodes'] = 0

        # Der Roothash der Chain wird ausgegeben
        redict['root_hash'] = ChainObj.root_conf.getChainRootHash()

        # Es werden alle Verfügabren Chain Coins aufgelistet
        chain_coins = list()
        for i in gv_.ChainRoot.getCoins():
            coin_ = dict()
            coin_['name'] = i.getName()
            coin_['symbol'] = i.getSymbol()
            coin_['coin_id'] = i.getCoinID(False)
            coin_['decimals'] = i.getDecimals()
            coin_['smallest_unit_name'] = i.getName(True)
            coin_['smallest_unit_symbol'] = i.getSymbol(True)
            coin_['ethereum_smart_contract_address'] = ""
            if i.isMiningLabel() == True: coin_['reward_amount'] = i.miningReward(last_block_meta_data['block_height'])
            else: coin_['reward_amount'] = 0
            if i.totalSupply() != -1: coin_['total_supply'] = i.totalSupply()
            else: coin_['total_supply'] = 'unlimited'
            coin_['circulating_supply'] = i.getCirculatingSupplyByBlock(last_block_meta_data['block_height'])
            coin_['burned_supply'] = 0
            chain_coins.append(coin_)
        redict['coins'] = chain_coins

        # Gibt die Daten aus
        return jsonify(redict)

    # Coins Page
    @FlaskO.route('/coins')
    def coins():
        from apollon import VERSION, gv_

        # Die Aktuellen Block Informationen werden abgerufen
        last_block_meta_data = ChainObj.getLastBlockMetaData(False)
        
        # Es werden alle Verfügabren Chain Coins aufgelistet
        chain_coins = list()
        for i in gv_.ChainRoot.getCoins():
            coin_ = dict()
            coin_['name'] = i.getName()
            coin_['symbol'] = i.getSymbol()
            coin_['coin_id'] = i.getCoinID(False)
            coin_['decimals'] = i.getDecimals()
            coin_['smallest_unit_name'] = i.getName(True)
            coin_['smallest_unit_symbol'] = i.getSymbol(True)
            coin_['ethereum_smart_contract_address'] = ""
            if i.isMiningLabel() == True: coin_['reward_amount'] = i.miningReward(last_block_meta_data['block_height'])
            else: coin_['reward_amount'] = 0
            if i.totalSupply() != -1: coin_['total_supply'] = i.totalSupply()
            else: coin_['total_supply'] = 'unlimited'
            coin_['circulating_supply'] = i.getCirculatingSupplyByBlock(last_block_meta_data['block_height'])
            coin_['burned_supply'] = 0
            chain_coins.append(coin_)
        
        # Gibt die Daten aus
        return jsonify(chain_coins)

    # Address Page
    @FlaskO.route('/address_details/<address>')
    def addressInfo(address):
        # Es wird geprüft, ob es sich um eine Zulässige Adresse handelt
        from apollon.apollon_address import addressStringReader
        try: resolved_address = addressStringReader(address)
        except: return jsonify({ 'error' : 'invalid_address' })

        # Es werden alle Address Daten abgerufen
        try: addr_details = ChainObj.getAddressDetails(resolved_address)
        except: return jsonify({ 'error' : 'internal_error' })

        # Die Daten werden abgezeigt
        return jsonify({ 'amount' : addr_details['amount'], 'total_transactions' : addr_details['total_transactions'] })
    
    # Get Unspent Address UTXO's
    @FlaskO.route('/unspent_utxos/<address>')
    def getUnspentUTXOs(address):
        return

    # Get Address Transactions
    @FlaskO.route('/address_transactions/<address>')
    @FlaskO.route('/address_transactions/<address>,<perpage>')
    @FlaskO.route('/address_transactions/<address>/<cpage>')
    @FlaskO.route('/address_transactions/<address>,<perpage>/<cpage>')
    def getAddressTransactions(address, perpage=25, cpage=1):
        # Es wird geprüft, ob es sich um eine Zulässige Adresse handelt
        from apollon.apollon_address import addressStringReader
        try: resolved_address = addressStringReader(address)
        except: return jsonify({ 'error' : 'invalid_address' })

        # Es wird geprüft ob die Itemanzahl angabe korrekt ist
        try: perpage = int(perpage) 
        except: return jsonify({ 'error' : 'invalid_per_page' })
        if perpage == 0: perpage = None

        # Es wird geprüft, ob die Seiteangabe korrekt ist
        try: cpage = int(cpage) 
        except: return jsonify({ 'error' : 'invalid_per_page' })
        if cpage < 1: return jsonify({ 'error' : 'invalid_page' })

        # Es wird versucht, alle Transaktionen abzurufen
        try: trans = ChainObj.getLagacyTransactionsByAddress(resolved_address, OutAsJSON=True, MaxEntries=perpage, CurrentPage=cpage)
        except Exception as E: return jsonify({ 'error' : 'internal_error', 'ecode' : str(E) })

        # Es wird geprüft, ob 
        return jsonify(trans)

class WebController():
    def __init__(self, ChainObject):
        # Der Flask Webserer wird erstellt
        self.fserver = Flask(__name__)
        self.master_chain = ChainObject
        self.fserver.config['JSON_SORT_KEYS'] = False
        FlaskSites(self.fserver, ChainObject)

    def Start(self):
        import threading
        def thr_(): self.fserver.run(host='::')
        threading.Thread(target=thr_).start()