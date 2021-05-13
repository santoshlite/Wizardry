# https://quantpedia.com/Screener/Details/4
# buy SPY ETF at its closing price and sell it at the opening each day.
import numpy as np


class OvernightTradeAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2000, 1, 1)   #Set Start Date
        self.SetEndDate(2018, 6, 1)     #Set End Date
        self.SetCash(100000)            #Set Strategy Cash
        self.spy = self.AddEquity("SPY", Resolution.Hour).Symbol
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage)
        self.Schedule.On(self.DateRules.EveryDay(self.spy), self.TimeRules.AfterMarketOpen("SPY", 0), self.EveryDayAfterMarketOpen)
        self.Schedule.On(self.DateRules.EveryDay(self.spy), self.TimeRules.BeforeMarketClose("SPY", 0), self.EveryDayBeforeMarketClose)

    def EveryDayBeforeMarketClose(self):
        if not self.Portfolio.Invested:
            self.SetHoldings(self.spy, 1)

    def EveryDayAfterMarketOpen(self):
        if self.Portfolio.Invested:
            self.Liquidate()

    def OnData(self, data):
        pass
