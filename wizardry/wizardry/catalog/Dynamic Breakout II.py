from datetime import datetime
import decimal
import numpy as np

class DynamicBreakoutAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2010,1,15)
        self.SetEndDate(2016,2,15)
        self.SetCash(100000)
        fx = self.AddForex("EURUSD", Resolution.Hour, Market.Oanda)
        self.syl = fx.Symbol
        self.Schedule.On(self.DateRules.EveryDay(self.syl), self.TimeRules.BeforeMarketClose(self.syl,1),Action(self.SetSignal))
        self.numdays = 20
        self.ceiling,self.floor = 60,20
        self.buypoint, self.sellpoint= None, None
        self.longLiqPoint, self.shortLiqPoint, self.yesterdayclose= None, None, None
        self.SetBenchmark(self.syl)
        self.Bolband = self.BB(self.syl, self.numdays, 2, MovingAverageType.Simple, Resolution.Daily)

    def SetSignal(self):

        close = self.History(self.syl, 31, Resolution.Daily)['close']
        todayvol = np.std(close[1:31])
        yesterdayvol = np.std(close[0:30])
        deltavol = (todayvol - yesterdayvol) / todayvol
        self.numdays = int(round(self.numdays * (1 + deltavol)))

        if self.numdays > self.ceiling:
           self.numdays = self.ceiling
        elif self.numdays < self.floor:
            self.numdays = self.floor

        self.high = self.History(self.syl, self.numdays, Resolution.Daily)['high']
        self.low = self.History(self.syl, self.numdays, Resolution.Daily)['low']

        self.buypoint = max(self.high)
        self.sellpoint = min(self.low)
        historyclose = self.History(self.syl, self.numdays, Resolution.Daily)['close']
        self.longLiqPoint = np.mean(historyclose)
        self.shortLiqPoint = np.mean(historyclose)
        self.yesterdayclose = historyclose.iloc[-1]

        # wait for our BollingerBand to fully initialize
        if not self.Bolband.IsReady: return

        holdings = self.Portfolio[self.syl].Quantity

        if self.yesterdayclose > self.Bolband.UpperBand.Current.Value and self.Portfolio[self.syl].Price >= self.buypoint:
            self.SetHoldings(self.syl, 1)
        elif self.yesterdayclose < self.Bolband.LowerBand.Current.Value and self.Portfolio[self.syl].Price <= self.sellpoint:
            self.SetHoldings(self.syl, -1)

        if holdings > 0 and self.Portfolio[self.syl].Price <= self.shortLiqPoint:
            self.Liquidate(self.syl)
        elif holdings < 0 and self.Portfolio[self.syl].Price >= self.shortLiqPoint:
            self.Liquidate(self.syl)

        self.Log(str(self.yesterdayclose)+(" # of days ")+(str(self.numdays)))

    def OnData(self,data):
        pass
