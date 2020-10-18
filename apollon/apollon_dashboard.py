## Apollon Dashboard Object ##
class ApollonDashboard(object):
    
    # Erstellt ein neues Apollon Dashboard Objekt
    def __init__(self, ChainMaster):
        from flask import Flask
        self.fl = Flask(__name__, static_url_path='', template_folder="dashboard/templates", static_folder="dashboard/static")
        self.chain_obj = ChainMaster
        self._pages()

    # Erstellt die Seiten für 
    def _pages(self):
        from flask import render_template

        # Index Page
        @self.fl.route("/")
        def _index():
            from apollon.utils import encodeBase58
            # Die Metadaten der Letzten Blöcke werden abgerufen
            last_blocks = self.chain_obj.getLastBlocksMetaData()
            return render_template(
                'index.html', 
                page_title='Startpage',
                diff=self.chain_obj.getBlockDiff(),
                bheight=self.chain_obj.getBlockHeight(),
                hrate=self.chain_obj.getHashrate(),
                lblocks=last_blocks,
                page='home',
                chain_burn_address=str(self.chain_obj.getChainBurningAddress()),
                chain_seed=str(encodeBase58(self.chain_obj.root_conf.getChainSeed(True)))
            )

        # Blocks Page
        @self.fl.route("/blocks")
        @self.fl.route("/blocks/<page>")
        def _blocks(page=1):
            last_blocks = self.chain_obj.getLastBlocksMetaData(Blocks=25, Page=int(page))
            last_block_height = self.chain_obj.getBlockHeight()
            if last_block_height != 0:
                from apollon.amath import capg
                page = int(page)
                total_pages = capg(25, last_block_height)
                # Es wird geprüft ob die Vorherige Seite vorhanden ist
                if page == 1: _prev = False; _prev_page = page
                else: _prev = True; _prev_page = page - 1
                # Es wird geprüft ob die Nächste Seite verfügbar ist
                if page == total_pages: _nex = False; _nex_page = page
                else: _nex = True; _nex_page = page + 1
            else: _prev = False; _prev_page = page; _nex = False; _nex_page = page; total_pages = 1

            # Die Seite wird angezeigt
            return render_template('blocks.html', page='blocks', page_title='Blocks', last_blocks=last_blocks, HasPrevPage=_prev, HasNextPage=_nex, PrevPage=_prev_page, NextPage=_nex_page, TotalPages=total_pages)

        # Rewards Page
        @self.fl.route("/emission")
        def _rewards_emission():
            return render_template('rewards.html', page='rewards', page_title='Rewards / Emission', coins=self.chain_obj.getChainCoins())
        
        # OpenBlock
        @self.fl.route('/block/<bid>')
        def _block_page(bid):
            current_block = self.chain_obj.getBlock(int(bid))
            return render_template('block.html', page='blocks', page_title='Block # {}'.format(bid), block_obj=current_block)

        # Open Transaction
        @self.fl.route('/tx/<idx>')
        def _txn(idx):
            return render_template('tx.html', page_title='Transaction #', txid=idx)

        # Address Page
        @self.fl.route('/address/<addressid>')
        def _adress(addressid):
            # Es wird geprüft ob es sich um eine gültige Adresse handelt
            from apollon.address_utils import AddressUtils
            from apollon.apollon_address import LagacyAddress, BlockchainAddress
            if AddressUtils.isValidateLagacyAddress(addressid) == False: return 'INVALID_ADDRESS'

            # Es wird versucht die Addresse einzulesen
            try: readed_address = AddressUtils.readLagacyAddressFromString(addressid)
            except: return 'INVALID_ADDRESS'

            # Es wird eine Abfrage an die Blockchain gestellt um die Address MetaDaten abzufragen
            try: adr_mdata = self.chain_obj.getAddressDetails(readed_address)
            except: return 'CHAIN_META_DATA'

            # Es wird versucht, die letzten 25 Transaktionen der Adresse abzurufen
            #try: transactions = self.chain_obj.getLagacyTransactionsByAddress(adr_mdata, MaxEntries=25, CurrentPage=1)
            #except: return 'CHAIN_TRANSACTIONS_META_DATA'

            # Die Seite wird ausgegeben
            return render_template('address.html', page_title='Address details # {}'.format(addressid), address_metadata=adr_mdata)

    # Startet das Apollon Dashboard
    def start(self):
        import threading
        def thr_(): self.fl.run(host='0.0.0.0', port=8080)
        threading.Thread(target=thr_).start()