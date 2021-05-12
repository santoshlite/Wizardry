class SeasonalitySignalAlgorithm(QCAlgorithm):
    '''
    A strategy that takes long and short positions based on historical same-calendar month returns
    Paper: https://www.nber.org/papers/w20815.pdf
    '''
    def Initialize(self):
        self.SetStartDate(2010, 1, 1)   # Set Start Date
        self.SetEndDate(2019, 8, 1)     # Set End Date
        self.SetCash(100000)            # Set Strategy Cash

        self.num_coarse = 100           # Number of equities for coarse selection
        self.num_long = 5               # Number of equities to long
        self.num_short = 5              # Number of equities to short
        self.longSymbols = []           # Contain the equities we'd like to long
        self.shortSymbols = []          # Contain the equities we'd like to short

        self.UniverseSettings.Resolution = Resolution.Daily     # Resolution of universe selection
        self.AddUniverse(self.SameMonthReturnSelection)         # Universe selection based on historical same-calendar month returns

        self.nextRebalance = self.Time  # Next rebalance time


    def SameMonthReturnSelection(self, coarse):
        '''
        Universe selection based on historical same-calendar month returns
        '''
        # Before next rebalance time, just remain the current universe
        if self.Time < self.nextRebalance:
            return Universe.Unchanged

        # Sort the equities with prices > 5 in DollarVolume decendingly
        selected = sorted([x for x in coarse if x.Price > 5],
                          key=lambda x: x.DollarVolume, reverse=True)

        # Get equities after coarse selection
        symbols = [x.Symbol for x in selected[:self.num_coarse]]

        # Get historical close data for coarse-selected symbols of the same calendar month
        start = self.Time.replace(day = 1, year = self.Time.year-1)
        end = Expiry.EndOfMonth(start) - timedelta(1)
        history = self.History(symbols, start, end, Resolution.Daily).close.unstack(level=0)

        # Get the same calendar month returns for the symbols
        MonthlyReturn = {ticker: prices.iloc[-1]/prices.iloc[0] for ticker, prices in history.iteritems()}

        # Sorted the values of monthly return
        sortedReturn = sorted(MonthlyReturn.items(), key=lambda x:x[1], reverse=True)

        # Get the symbols to long / short
        self.longSymbols = [x[0] for x in sortedReturn[:self.num_long]]
        self.shortSymbols = [x[0] for x in sortedReturn[-self.num_short:]]

        # Note that self.longSymbols/self.shortSymbols contains strings instead of symbols
        return [x for x in symbols if str(x) in self.longSymbols + self.shortSymbols]


    def OnData(self, data):
        '''
        Rebalance every month based on same-calendar month returns effect
        '''
        # Before next rebalance, do nothing
        if self.Time < self.nextRebalance:
            return

        count = len(self.longSymbols + self.shortSymbols)
        # Open long positions
        for symbol in self.longSymbols:
            self.SetHoldings(symbol, 1/count)

        # Open short positions
        for symbol in self.shortSymbols:
            self.SetHoldings(symbol, -1/count)

        # Rebalance at the end of every month
        self.nextRebalance = Expiry.EndOfMonth(self.Time) - timedelta(1)


    def OnSecuritiesChanged(self, changes):
        '''
        Liquidate the stocks that are not in the universe
        '''
        for security in changes.RemovedSecurities:
            if security.Invested:
                self.Liquidate(security.Symbol, 'Removed from Universe')
