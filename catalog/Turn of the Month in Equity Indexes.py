# https://quantpedia.com/Screener/Details/41
class TurnOfMonthSPY(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2001, 1, 11)   # Set Start Date
        self.SetEndDate(2018, 7, 11)     # Set End Date
        self.SetCash(100000)             # Set Strategy Cash
        self.days = 0

        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol

        # This event triggers the algorithm to purchase during the last trading day of the month
        self.Schedule.On(
            self.DateRules.MonthEnd(self.spy),
            self.TimeRules.AfterMarketOpen(self.spy, 1),
            self.Purchase)

    def Purchase(self):
        ''' Immediately purchases the ETF at market opening '''
        self.SetHoldings(self.spy, 1)
        self.days = 0

    def OnData(self, data):
        if self.Portfolio.Invested:
            self.days += 1

            # Liquidates after 3 days
            if self.days > 3:
                self.Liquidate(self.spy, 'Liquidate after 3 days')
