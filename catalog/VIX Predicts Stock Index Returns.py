import numpy as np
from QuantConnect.Python import PythonQuandl

class VIXPredictsStockIndexReturns(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2006, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(100000)
        self.AddEquity("OEF", Resolution.Daily)
        self.vix = 'CBOE/VIX'
        self.AddData(QuandlVix, self.vix, Resolution.Daily)
        self.window = RollingWindow[float](252*2)
        hist = self.History([self.vix], 1000, Resolution.Daily)
        for close in hist.loc[self.vix]['vix close']:
            self.window.Add(close)


    def OnData(self, data):
        if not data.ContainsKey(self.vix): return
        self.window.Add(self.Securities[self.vix].Price)
        if not self.window.IsReady: return
        history_close = [i for i in self.window]

        if self.Securities[self.vix].Price > np.percentile(history_close, 90):
            self.SetHoldings("OEF", 1)
        elif self.Securities[self.vix].Price < np.percentile(history_close, 10):
            self.SetHoldings("OEF", -1)


class QuandlVix(PythonQuandl):

    def __init__(self):
        self.ValueColumnName = "VIX Close"
