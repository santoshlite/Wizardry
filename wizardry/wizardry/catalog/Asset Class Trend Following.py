# https://quantpedia.com/Screener/Details/1
# Use 5 ETFs (SPY - US stocks, EFA - foreign stocks, BND - bonds, VNQ - REITs,
# GSG - commodities), equal weight the portfolio. Hold asset class ETF only when
# it is over its 10 month Simple Moving Average, otherwise stay in cash.

import numpy as np
from datetime import datetime

class BasicTemplateAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2007, 5, 1)
        self.SetEndDate(datetime.now())
        self.SetCash(100000)
        self.data = {}
        period = 10*21
        self.SetWarmUp(period)
        self.symbols = ["SPY", "EFA", "BND", "VNQ", "GSG"]
        for symbol in self.symbols:
            self.AddEquity(symbol, Resolution.Daily)
            self.data[symbol] = self.SMA(symbol, period, Resolution.Daily)


    def OnData(self, data):
        if self.IsWarmingUp: return
        isUptrend = []
        for symbol, sma in self.data.items():
            if self.Securities[symbol].Price > sma.Current.Value:
                isUptrend.append(symbol)
            else:
                self.Liquidate(symbol)

        for symbol in isUptrend:
            self.SetHoldings(symbol, 1/len(isUptrend))
