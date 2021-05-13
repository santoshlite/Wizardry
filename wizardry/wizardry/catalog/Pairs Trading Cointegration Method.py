from sklearn.linear_model import LinearRegression
import numpy as np

class PairsTradingAlgorithm(QCAlgorithm):

    closes_by_symbol = {}

    def Initialize(self):

        self.SetStartDate(2010,1,1)
        self.SetEndDate(2020,1,1)
        self.SetCash(100000)

        self.threshold = 1.
        self.numdays = 250  # set the length of training period

        self.x_symbol = self.AddEquity("XLK", Resolution.Daily).Symbol
        self.y_symbol = self.AddEquity("QQQ", Resolution.Daily).Symbol

        for symbol in [self.x_symbol, self.y_symbol]:
            history = self.History(symbol, self.numdays, Resolution.Daily)
            self.closes_by_symbol[symbol] = history.loc[symbol].close.values \
                if not history.empty else np.array([])

    def OnData(self, data):

        for symbol in self.closes_by_symbol.keys():
            if not data.Bars.ContainsKey(symbol):
                return

        for symbol, closes in self.closes_by_symbol.items():
            self.closes_by_symbol[symbol] = np.append(closes, data[symbol].Close)[-self.numdays:]

        log_close_x = np.log(self.closes_by_symbol[self.x_symbol])
        log_close_y = np.log(self.closes_by_symbol[self.y_symbol])

        spread, beta = self.regr(log_close_x, log_close_y)

        mean = np.mean(spread)
        std = np.std(spread)

        x_holdings = self.Portfolio[self.x_symbol]

        if x_holdings.Invested:
            if x_holdings.IsShort and spread[-1] <= mean or \
                x_holdings.IsLong and spread[-1] >= mean:
                self.Liquidate()
        else:
            if beta < 1:
                x_weight = 0.5
                y_weight = 0.5 / beta
            else:
                x_weight = 0.5 / beta
                y_weight = 0.5

            if spread[-1] < mean - self.threshold * std:
                self.SetHoldings(self.y_symbol, -y_weight)
                self.SetHoldings(self.x_symbol, x_weight)
            if spread[-1] > mean + self.threshold * std:
                self.SetHoldings(self.x_symbol, -x_weight)
                self.SetHoldings(self.y_symbol, y_weight)

        scale = 10000
        self.Plot("Spread", "Top", (mean + self.threshold * std) * scale)
        self.Plot("Spread", "Value", spread[-1] * scale)
        self.Plot("Spread", "Mean", mean * scale)
        self.Plot("Spread", "Bottom", (mean - self.threshold * std) * scale)
        self.Plot("State", "Value", np.sign(x_holdings.Quantity))

    def regr(self, x, y):
        regr = LinearRegression()
        x_constant = np.column_stack([np.ones(len(x)), x])
        regr.fit(x_constant, y)
        beta = regr.coef_[1]
        alpha = regr.intercept_
        spread = y - x*beta - alpha
        return spread, beta
