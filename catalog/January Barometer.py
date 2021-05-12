# https://quantpedia.com/Screener/Details/113
class JanuaryBarometerAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2008, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(100000)
        self.AddEquity("SPY", Resolution.Daily)
        self.AddEquity("BIL", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.Rebalance)
        self.startPrice = None

    def Rebalance(self):
        if self.Time.month == 1:
            self.Liquidate("BIL")
            self.SetHoldings("SPY", 1)
            self.startPrice = self.Securities["SPY"].Price
        if self.Time.month == 2 and self.startPrice is not None:
            returns = (self.Securities["SPY"].Price - self.startPrice)/self.startPrice
            if returns > 0:
                self.SetHoldings("SPY", 1)
            else:
                self.Liquidate("SPY")
                self.SetHoldings("BIL", 1)
