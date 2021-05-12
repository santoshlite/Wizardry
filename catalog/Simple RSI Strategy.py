class AdaptableYellowRat(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020,1, 1)
        self.SetEndDate(2021,1,1)
        self.SetCash(100000)
        self.AddEquity("TSLA", Resolution.Minute)
        self.rsi = self.RSI("TSLA", 14)
        self.SetWarmUp(14)

    def OnData(self, data):
        if self.IsWarmingUp:
            return
        if not self.Portfolio["TSLA"].Invested:
            if self.rsi.Current.Value < 60:
                self.MarketOrder("TSLA", 100)
        else:
            if self.rsi.Current.Value > 85:
                self.Liquidate()

    def OnEndOfDay(self):
        self.Plot("Indicators","RSI", self.rsi.Current.Value)
