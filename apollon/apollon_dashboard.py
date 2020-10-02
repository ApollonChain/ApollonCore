class ApollonDashboard(object):
    def __init__(self, ChainMaster):
        from flask import Flask
        self.fl = Flask(__name__, static_url_path='', template_folder="dashboard/templates", static_folder="dashboard/static")
        self.chain_obj = ChainMaster
        self._pages()

    def _pages(self):
        from flask import render_template

        # Index Page
        @self.fl.route("/")
        def _index():
            # Die Metadaten der Letzten Blöcke werden abgerufen
            last_blocks = self.chain_obj.getLastBlocksMetaData()
            return render_template('index.html', page_title='Startpage', diff=self.chain_obj.getBlockDiff(), bheight=self.chain_obj.getBlockHeight(), hrate=self.chain_obj.getHashrate() ,lblocks=last_blocks, page='home')

        # Blocks Page
        @self.fl.route("/blocks")
        @self.fl.route("/blocks/<page>")
        def _blocks(page=1):
            # Die Metadaten der Letzten Blöcke werden abgerufen
            last_blocks = self.chain_obj.getLastBlocksMetaData(Blocks=25, Page=int(page))
            # Die Anzahl der Seiten wird ermittelt
            total_pages = range(1)
            if len(last_blocks) != 0:
                # Die letzte Block Höhe wird ermittelt
                last_block_height = last_blocks[0].getBlockHeight()
                # Es wird errechnet, wieviele Seiten vorhanden sind
                from apollon.amath import capg
                from apollon.utils import paginationSizer
                total_pages = paginationSizer(page, capg(25, last_block_height))

            # Die Seite wird angezeigt
            return render_template('blocks.html', page='blocks', page_title='Blocks', last_blocks=last_blocks, total_pages=total_pages)

        # Rewards Page
        @self.fl.route("/rewards_emission")
        @self.fl.route("/rewards_emission/<int:page>")
        def _rewards_emission(page=1):
            return render_template('rewards.html', page='rewards', page_title='Rewards / Emission', coins=self.chain_obj.getChainCoins())
        

    def start(self):
        import threading
        def thr_(): self.fl.run(host='0.0.0.0', port=8080)
        threading.Thread(target=thr_).start()