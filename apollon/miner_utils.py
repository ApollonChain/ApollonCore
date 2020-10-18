
## Miner Utils Static Object ##
class MinerUtils:
   
    # Es wird ein Input erstellt
    @staticmethod
    def createFeeInput(*Transactions, CoinObj, BlockHeight):
        # Es wird geprüt ob es sich um ein Zulässiges Coinobjekt handelt
        from apollon.coin import Coin
        if isinstance(CoinObj, Coin) == False: raise Exception('INVALID_COIN_OBJECT')

        # Es wird geprüft ob es sich um einen Zulässige Blockhöhe handelt
        if isinstance(CoinObj, Coin) == False: raise Exception('INVALID_BLOCK_HEIGHT')

        # Es wird geprüt ob es sich um eine gültige Transaktion handelt
        from apollon.transaction import SignedTransaction
        for txi in Transactions:
            if isinstance(txi, SignedTransaction) == False: raise Exception('INVALID_TRANSACTION_TYPE')
            if txi.objectIsValidate() == False: raise Exception('INVALID_TRANSACTION_TYPE')
            if txi.signaturesAreValidate() == False: raise Exception('SIGNATURE_INVALID')

        # Die gebühren der Transaktionen werden ermittelt
        total = 0
        for txi in Transactions:
            for feei in txi.getFees():
                if feei.coin() == CoinObj: total += feei.get()

        # Es wird ein Input erstellt
        from apollon.utxo import FeeInputUtxo
        try: fee_input = FeeInputUtxo(BlockHeight, CoinObj, total, *Transactions)
        except: raise Exception('INVALID')

        # Das erstellt Input wird zurückgegeben
        return fee_input


    # Es werden ausgänge aus den Eingängen erstellt
    @staticmethod
    def createOutputsFromInputs(FeeInput, CoinbaseInput, CoinObj, BlockHeight, MinerAddress, BlockchainRoot):
        # Es wird geprüft ob das Coinobjekt zulässig ist
        from apollon.coin import Coin
        if isinstance(CoinObj, Coin) == False: raise Exception('INVALID_COIN_OBJECT')

        # Es wird geprüft ob die Blockhöhe korrekt ist
        if isinstance(BlockHeight, int) == False: raise Exception('INVALID_BLOCK_HEIGHT')

        # Es wird geprüft ob die Mineradresse korrekt ist
        from apollon.apollon_address import LagacyAddress, LagacyEthereumHashBasedAddress
        if isinstance(MinerAddress, LagacyAddress) == False and isinstance(MinerAddress, LagacyEthereumHashBasedAddress) == False: raise Exception('INVALID_MINER_ADDRESS')

        # Es wird geprüft ob eingänge vorhanden sind
        if FeeInput is None and CoinbaseInput is None: return list()

        # Speichert die Ausgänge ab
        outputs = list()

        # Es wird geprüft ob es ein Fee und ein Reward Input gibt
        if FeeInput is not None and CoinbaseInput is not None:
            # Es wird geprüft ob ein Teil der Gebühr verbrannt werden soll
            if CoinObj.minerForceBurnFee() == True:
                # FeeInput wert wird ausgegeben
                try: fee_input_total_value = FeeInput.getCoinValue(True)
                except: raise Exception('MINER_UTILS_ERROR_K10_100')

                # Der zuverbennende Wert wird ausgerechnet
                try: burn_value = CoinObj.calcMinerBurningAmountValue(fee_input_total_value)
                except: raise Exception('MINER_UTILS_ERRO_K10_110')

                # Der betrag für den Miner wird ausgerechnet
                try: fee_and_reward_value = int(fee_input_total_value - burn_value) + int(CoinbaseInput.getCoinValue(True))
                except: raise Exception('MINER_UTILS_ERRO_K10_120')

                # Der Ausgang für den Miner wird erstellt
                from apollon.utxo import LagacyOutUtxo
                try: miner_output = LagacyOutUtxo(MinerAddress, fee_and_reward_value, CoinObj, *[FeeInput, CoinbaseInput])
                except: raise Exception('MINER_UTILS_ERRO_K10_130')

                # Die Bruning Adresse wird abgerufen
                try: chain_burn_address = BlockchainRoot.getChainBurningAddress()
                except: raise Exception('MINER_UTILS_ERRO_K10_140')

                # Der ausgang für die Burningadresse wird erstellt
                try: burning_output = LagacyOutUtxo(chain_burn_address, burn_value, CoinObj, *[FeeInput, CoinbaseInput])
                except: raise Exception('MINER_UTILS_ERRO_K10_150')

                # Die ausgänge werden gelistet
                outputs.append(miner_output)
                outputs.append(burning_output)
            else:
                # FeeInput wert wird ausgegeben
                try: fee_input_total_value = FeeInput.getCoinValue(True)
                except: raise Exception('MINER_UTILS_ERROR_K20_100')

                # Der betrag für den Miner wird ausgerechnet
                try: fee_and_reward_value = int(fee_input_total_value) + int(CoinbaseInput.getCoinValue(True))
                except: raise Exception('MINER_UTILS_ERRO_K20_120')

                # Der Ausgang für den Miner wird erstellt
                from apollon.utxo import LagacyOutUtxo
                try: miner_output = LagacyOutUtxo(MinerAddress, fee_and_reward_value, CoinObj, *[FeeInput, CoinbaseInput])
                except: raise Exception('MINER_UTILS_ERRO_K20_130')

                # Die ausgänge werden gelistet
                outputs.append(miner_output)

        # Es wird geprüft ob es ein Fee Input gibt
        elif FeeInput is not None and CoinbaseInput is None:
            pass

        # Es wird geprüft ob ein Reward Input gibt
        elif FeeInput is None and CoinbaseInput is not None:
            pass

        # Die ausgänge werden ausgegeben
        return outputs


    # Diese Funktion erstellt eine Coinbase Transaktion
    @staticmethod
    def createCoinBaseTransaction(*Transactions, BlockchainRoot, BlockHeight, MinerAddress):
        # Es wird geprüft ob es sich um ein gültiges Chain Objekt handelt
        from apollon.chain import Blockchain
        if isinstance(BlockchainRoot, Blockchain) == False: raise Exception('INVALID_BLOCKCHAIN_OBJECT')

        # Es wird geprüft ob es sich um eine Gültige Blockhöhe handelt
        if isinstance(BlockHeight, int) == False: raise Exception('INVALID_BLOCK_HEIGHT')

        # Es wird geprüft ob es sich um eine gültige Mineradresse handelt
        from apollon.apollon_address import LagacyAddress, LagacyEthereumHashBasedAddress
        if isinstance(MinerAddress, LagacyAddress) == False and isinstance(MinerAddress, LagacyEthereumHashBasedAddress) == False: raise Exception('INVALID_MINER_ADDRESS')

        # Es wird geprüft alle Transaktionen gültig sind
        from apollon.transaction import SignedTransaction
        if len(Transactions) != 0:
            for txi in Transactions:
                if isinstance(txi, SignedTransaction) == False: raise Exception('INVALID_TRANSACTION_TYPE')
                if txi.objectIsValidate() == False: raise Exception('INVALID_TRANSACTION_TYPE')
                if txi.signaturesAreValidate() == False: raise Exception('SIGNATURE_INVALID')

        # Die Coins der Blockchain werden abgerufen
        try: avaible_coins = BlockchainRoot.getChainCoins()
        except: raise Exception('INTERNAL_UTILS_ERROR_70')

        # Die Coins werden abgearbeitet
        ios = list()
        for coin_i in avaible_coins:
            # Es wird geprüft ob es einen Reward gibt
            reward_input = None
            if coin_i.hasRewardForBlock(BlockHeight) == True:
                try: reward_input = coin_i.createNewRewardInputUtxo(BlockHeight)
                except: raise Exception('INTERNAL_UTILS_ERROR_80')

            # Es wird ein Fee Input erstellt
            fee_input = None
            if len(Transactions) != 0:
                try: fee_input = MinerUtils.createFeeInput(*Transactions, CoinObj=coin_i, BlockHeight=BlockHeight)
                except: raise Exception('INTERNAL_UTILS_ERROR_90')

            # Die Ausgänge für die Inputs werden erstellt
            if reward_input is not None or fee_input is not None:
                # Es wird versucht die Ausgänge zu erstellen
                try: outs = MinerUtils.createOutputsFromInputs(FeeInput=fee_input, CoinbaseInput=reward_input, CoinObj=coin_i, BlockHeight=BlockHeight, MinerAddress=MinerAddress, BlockchainRoot=BlockchainRoot)
                except: raise Exception('INTERNAL_MINER_UTILS_ERROR_100')

                # Die Ein und Ausgänge werden in die 'input and output (ios)' list geschrieben
                if len(outs) != 0:
                    if reward_input is not None: ios.append(reward_input)
                    if fee_input is not None: ios.append(fee_input)
                    for ou_i in outs: ios.append(ou_i)

        # Es wird geprüft ob ein und ausgänge vorhanden sind
        if len(ios) == 0: return None

        # Es wird versucht die Coinbase Transaktion zu erstellen
        from apollon.transaction import CoinbaseTransaction
        try: coinbase_transaction = CoinbaseTransaction(*ios, BlockNo=BlockHeight)
        except: raise Exception('INTERNAL_UTILS_ERROR_110')

        # Die Coinbase Transaktion wird ausgegeben
        return coinbase_transaction


    @staticmethod
    # Diese Funktion ermittelt die Aktuelle Hashrate
    def calculateHashrate():
        pass