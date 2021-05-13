class RiskPremiaForexAlgorithm(QCAlgorithm):
    '''
    Asymmetric Tail Risks and Excess Returns in Forex Markets
    Paper: https://arxiv.org/pdf/1409.7720.pdf
    '''
    def Initialize(self):
        self.SetStartDate(2009, 1, 1)   # Set Start Date
        self.SetEndDate(2019, 9, 1)     # Set End Date
        self.SetCash(100000)            # Set Strategy Cash

        # Add forex data of the following symbols
        for pair in ['EURUSD', 'AUDUSD', 'USDCAD', 'USDJPY']:
            self.AddForex(pair, Resolution.Hour, Market.FXCM)

        self.lookback = 30              # Length(days) of historical data
        self.nextRebalance = self.Time  # Next time to rebalance
        self.rebalanceDays = 7          # Rebalance every 7 days (weekly)

        self.longSkewLevel = -0.6       # If the skewness of a pair is less than this level, enter a long postion
        self.shortSkewLevel = 0.6       # If the skewness of a pair is larger than this level, enter a short position

    def OnData(self, data):
        '''
        Rebalance weekly for each forex pair
        '''
        # Do nothing until next rebalance
        if self.Time < self.nextRebalance:
            return

        # Get historical close data for the symbols
        history = self.History(self.Securities.Keys, self.lookback, Resolution.Daily)
        history = history.drop_duplicates().close.unstack(level=0)

        # Get the skewness of the historical data
        skewness = self.GetSkewness(history)

        longSymbols = [k for k,v in skewness.items() if v < self.longSkewLevel]
        shortSymbols = [k for k,v in skewness.items() if v > self.shortSkewLevel]

        # Liquidate the holdings for pairs that will not trade
        for holding in self.Portfolio.Values:
            symbol = holding.Symbol
            if holding.Invested and symbol.Value not in longSymbols + shortSymbols:
                self.Liquidate(symbol, 'Not selected pair')

        # Open positions for the symbols with equal weights
        count = len(longSymbols) + len(shortSymbols)

        for pair in longSymbols:
            self.SetHoldings(pair, 1/count)

        for pair in shortSymbols:
            self.SetHoldings(pair, -1/count)

        # Set next rebalance time
        self.nextRebalance += timedelta(self.rebalanceDays)


    def GetSkewness(self, values):
        '''
        Get the skewness for all forex symbols based on its historical data
        Ref: https://www.itl.nist.gov/div898/handbook/eda/section3/eda35b.htm
        '''
        # Get the numerator of the skewness
        numer = ((values - values.mean()) ** 3).sum()

        # Get the denominator of the skewness
        denom = self.lookback * values.std() ** 3

        # Return the skewness
        return (numer/denom).to_dict()
