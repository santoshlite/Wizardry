# https://www.quantconnect.com/tutorials/strategy-library/momentum-and-style-rotation-effect
# https://quantpedia.com/Screener/Details/91

class MomentumAndStyleRotationAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2001, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(100000)

        tickers = ["IJJ",   # iShares S&P Mid-Cap 400 Value Index ETF
                   "IJK",   # iShares S&P Mid-Cap 400 Growth ETF
                   "IJS",   # iShares S&P Small-Cap 600 Value ETF
                   "IJT",   # iShares S&P Small-Cap 600 Growth ETF
                   "IVE",   # iShares S&P 500 Value Index ETF
                   "IVW"]   # iShares S&P 500 Growth ETF

        lookback = 12*20

        # Save all momentum indicator into the dictionary
        self.mom = dict()
        for ticker in tickers:
            symbol = self.AddEquity(ticker, Resolution.Daily).Symbol
            self.mom[symbol] = self.MOM(symbol, lookback)

        self.SetWarmUp(lookback)

        # Portfolio monthly rebalance
        self.Schedule.On(self.DateRules.MonthStart("IJJ"), self.TimeRules.At(0, 0), self.Rebalance)


    def Rebalance(self):
        '''Sort securities by momentum.
        Short the one with the lowest momentum.
        Long the one with the highest momentum.
        Liquidate positions of other securities'''

        # Order the MOM dictionary by value
        sorted_mom = sorted(self.mom, key = lambda x: self.mom[x].Current.Value)

        # Liquidate the ETFs that are no longer selected
        for symbol in sorted_mom[1:-1]:
            if self.Portfolio[symbol].Invested:
                self.Liquidate(symbol, 'No longer selected')

        self.SetHoldings(sorted_mom[-1], -0.5)   # Short the ETF with lowest MOM
        self.SetHoldings(sorted_mom[0], 0.5)     # Long the ETF with highest MOM
