from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Algorithm.Framework.Selection import *
from QuantConnect.Data import *
from QuantConnect.Data.Custom.SmartInsider import *
from QuantConnect.Data.UniverseSelection import *

class SmartInsiderTransactionAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2019, 3, 1)
        self.SetEndDate(2019, 7, 4)
        self.SetCash(1000000)

        self.AddUniverseSelection(CoarseFundamentalUniverseSelectionModel(self.CoarseUniverse))

        # Request underlying equity data.
        ibm = self.AddEquity("IBM", Resolution.Minute).Symbol
        # Add Smart Insider stock buyback transaction data for the underlying IBM asset
        si = self.AddData(SmartInsiderTransaction, ibm).Symbol
        # Request 60 days of history with the SmartInsiderTransaction IBM Custom Data Symbol
        history = self.History(SmartInsiderTransaction, si, 60, Resolution.Daily)

        # Count the number of items we get from our history request
        self.Debug(f"We got {len(history)} items from our history request")

    def CoarseUniverse(self, coarse):
        symbols = [i.Symbol for i in coarse if i.HasFundamentalData and i.DollarVolume > 50000000][:10]

        for symbol in symbols:
            self.AddData(SmartInsiderTransaction, symbol)

        return symbols

    def OnData(self, data):

        # Get all SmartInsider data available
        transactions = data.Get(SmartInsiderTransaction)

        # Loop over all the insider transactions
        for transaction in transactions.Values:
            if transaction.VolumePercentage is None or transaction.EventType is None:
                continue

            # Using the SmartInsider transaction information, buy when company does a stock buyback
            if transaction.EventType == SmartInsiderEventType.Transaction and transaction.VolumePercentage > 5:
                self.SetHoldings(transaction.Symbol.Underlying, transaction.VolumePercentage / 100)

    def OnSecuritiesChanged(self, changes):
        for r in changes.RemovedSecurities:
            # If removed from the universe, liquidate and remove the custom data from the algorithm
            self.Liquidate(r.Symbol)
            self.RemoveSecurity(Symbol.CreateBase(SmartInsiderTransaction, r.Symbol, Market.USA))
