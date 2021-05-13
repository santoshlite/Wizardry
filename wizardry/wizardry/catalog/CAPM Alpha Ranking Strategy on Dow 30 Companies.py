import numpy as np

class BetaAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2016, 1, 1)   # Set Start Date
        self.SetEndDate(2017, 1, 1)     # Set End Date
        self.SetCash(10000)             # Set Strategy Cash

        # Dow 30 companies.
        self.symbols = [self.AddEquity(ticker).Symbol
            for ticker in ['AAPL', 'AXP', 'BA', 'CAT', 'CSCO', 'CVX', 'DD',
                           'DIS', 'GE', 'GS', 'HD', 'IBM', 'INTC', 'JPM',
                           'KO', 'MCD', 'MMM', 'MRK', 'MSFT', 'NKE', 'PFE',
                           'PG', 'TRV', 'UNH', 'UTX', 'V', 'VZ', 'WMT', 'XOM'] ]

        # Benchmark
        self.benchmark = Symbol.Create('SPY', SecurityType.Equity, Market.USA)

        # Set number days to trace back
        self.lookback = 21

        # Schedule Event: trigger the event at the begining of each month.
        self.Schedule.On(self.DateRules.MonthStart(self.symbols[0]),
                         self.TimeRules.AfterMarketOpen(self.symbols[0]),
                         self.Rebalance)


    def Rebalance(self):

        # Fetch the historical data to perform the linear regression
        history = self.History(
            self.symbols + [self.benchmark],
            self.lookback,
            Resolution.Daily).close.unstack(level=0)

        symbols = self.SelectSymbols(history)

        # Liquidate positions that are not held by selected symbols
        for holdings in self.Portfolio.Values:
            symbol = holdings.Symbol
            if symbol not in symbols and holdings.Invested:
                self.Liquidate(symbol)

        # Invest 100% in the selected symbols
        for symbol in symbols:
            self.SetHoldings(symbol, 1)


    def SelectSymbols(self, history):
        '''Select symbols with the highest intercept/alpha to the benchmark
        '''
        alphas = dict()

        # Get the benchmark returns
        benchmark = history[self.benchmark].pct_change().dropna()

        # Conducts linear regression for each symbol and save the intercept/alpha
        for symbol in self.symbols:

            # Get the security returns
            returns = history[symbol].pct_change().dropna()
            bla = np.vstack([benchmark, np.ones(len(returns))]).T

            # Simple linear regression function in Numpy
            result = np.linalg.lstsq(bla , returns)
            alphas[symbol] = result[0][1]

        # Select symbols with the highest intercept/alpha to the benchmark
        selected = sorted(alphas.items(), key=lambda x: x[1], reverse=True)[:2]
        return [x[0] for x in selected]
