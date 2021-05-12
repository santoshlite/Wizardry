import numpy as np

class FamaFrenchFiveFactorsAlgorithm(QCAlgorithm):
    ''' Stocks Selecting Strategy based on Fama French 5 Factors Model
        Reference: https://tevgeniou.github.io/EquityRiskFactors/bibliography/FiveFactor.pdf
    '''
    def Initialize(self):
        self.SetStartDate(2010, 1, 1)    # Set Start Date
        self.SetEndDate(2019, 8, 1)      # Set End Date
        self.SetCash(100000)             # Set Strategy Cash

        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)

        self.num_coarse = 200            # Number of symbols selected at Coarse Selection
        self.num_long = 5                # Number of stocks to long
        self.num_short = 5               # Number of stocks to short

        self.longSymbols = []            # Contains the stocks we'd like to long
        self.shortSymbols = []           # Contains the stocks we'd like to short

        self.nextLiquidate = self.Time   # Initialize last trade time
        self.rebalance_days = 30

        # Set the weights of each factor
        self.beta_m = 1
        self.beta_s = 1
        self.beta_h = 1
        self.beta_r = 1
        self.beta_c = 1


    def CoarseSelectionFunction(self, coarse):
        '''Drop securities which have no fundamental data or have too low prices.
        Select those with highest by dollar volume'''

        if self.Time < self.nextLiquidate:
            return Universe.Unchanged

        selected = sorted([x for x in coarse if x.HasFundamentalData and x.Price > 5],
                          key=lambda x: x.DollarVolume, reverse=True)

        return [x.Symbol for x in selected[:self.num_coarse]]


    def FineSelectionFunction(self, fine):
        '''Select securities with highest score on Fama French 5 factors'''

        # Select stocks with these 5 factors:
        # MKT -- Book value per share: Value
        # SMB -- TotalEquity: Size
        # HML -- Operation profit margin: Quality
        # RMW -- ROE: Profitability
        # CMA -- TotalAssetsGrowth: Investment Pattern
        filtered = [x for x in fine if x.ValuationRatios.BookValuePerShare
                                    and x.FinancialStatements.BalanceSheet.TotalEquity
                                    and x.OperationRatios.OperationMargin.Value
                                    and x.OperationRatios.ROE
                                    and x.OperationRatios.TotalAssetsGrowth]

        # Sort by factors
        sortedByMkt = sorted(filtered, key=lambda x: x.ValuationRatios.BookValuePerShare, reverse=True)
        sortedBySmb = sorted(filtered, key=lambda x: x.FinancialStatements.BalanceSheet.TotalEquity.Value, reverse=True)
        sortedByHml = sorted(filtered, key=lambda x: x.OperationRatios.OperationMargin.Value, reverse=True)
        sortedByRmw = sorted(filtered, key=lambda x: x.OperationRatios.ROE.Value, reverse=True)
        sortedByCma = sorted(filtered, key=lambda x: x.OperationRatios.TotalAssetsGrowth.Value, reverse=False)

        stockBySymbol = {}

        # Get the rank based on 5 factors for every stock
        for index, stock in enumerate(sortedByMkt):
            mktRank = self.beta_m * index
            smbRank = self.beta_s * sortedBySmb.index(stock)
            hmlRank = self.beta_h * sortedByHml.index(stock)
            rmwRank = self.beta_r * sortedByRmw.index(stock)
            cmaRank = self.beta_c * sortedByCma.index(stock)
            avgRank = np.mean([mktRank,smbRank,hmlRank,rmwRank,cmaRank])
            stockBySymbol[stock.Symbol] = avgRank

        sorted_dict = sorted(stockBySymbol.items(), key = lambda x: x[1], reverse = True)
        symbols = [x[0] for x in sorted_dict]

        # Pick the stocks with the highest scores to long
        self.longSymbols= symbols[:self.num_long]
        # Pick the stocks with the lowest scores to short
        self.shortSymbols = symbols[-self.num_short:]

        return self.longSymbols + self.shortSymbols


    def OnData(self, data):
        '''Rebalance Every self.rebalance_days'''

        # Liquidate stocks in the end of every month
        if self.Time >= self.nextLiquidate:
            for holding in self.Portfolio.Values:
                # If the holding is in the long/short list for the next month, don't liquidate
                if holding.Symbol in self.longSymbols or holding.Symbol in self.shortSymbols:
                    continue
                # If the holding is not in the list, liquidate
                if holding.Invested:
                    self.Liquidate(holding.Symbol)

        count = len(self.longSymbols + self.shortSymbols)

        # It means the long & short lists for the month have been cleared
        if count == 0:
            return

        # Open long position at the start of every month
        for symbol in self.longSymbols:
            self.SetHoldings(symbol, 1/count)

        # Open short position at the start of every month
        for symbol in self.shortSymbols:
            self.SetHoldings(symbol, -1/count)

        # Set the Liquidate Date
        self.nextLiquidate = self.Time + timedelta(self.rebalance_days)

        # After opening positions, clear the long & short symbol lists until next universe selection
        self.longSymbols.clear()
        self.shortSymbols.clear()
