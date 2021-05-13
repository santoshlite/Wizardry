# https://quantpedia.com/Screener/Details/25
class SmallCapInvestmentAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2019, 7, 1)
        self.SetCash(100000)

        self.year = -1
        self.count = 10

        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)


    def CoarseSelectionFunction(self, coarse):
        ''' Drop stocks which have no fundamental data or have low price '''
        if self.year == self.Time.year:
            return Universe.Unchanged

        return [x.Symbol for x in coarse if x.HasFundamentalData and x.Price > 5]


    def FineSelectionFunction(self, fine):
        ''' Selects the stocks by lowest market cap '''
        sorted_market_cap = sorted([x for x in fine if x.MarketCap > 0],
            key=lambda x: x.MarketCap)

        return [x.Symbol for x in sorted_market_cap[:self.count]]


    def OnData(self, data):

        if self.year == self.Time.year:
            return

        self.year = self.Time.year

        for symbol in self.ActiveSecurities.Keys:
            self.SetHoldings(symbol, 1/self.count)


    def OnSecuritiesChanged(self, changes):
        ''' Liquidate the securities that were removed from the universe '''
        for security in changes.RemovedSecurities:
            symbol = security.Symbol
            if self.Portfolio[symbol].Invested:
                self.Liquidate(symbol, 'Removed from Universe')
