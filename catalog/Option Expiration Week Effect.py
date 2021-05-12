from datetime import timedelta, datetime
class OptionExpirationWeekEffectAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2013, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(10000)
        self.AddEquity("OEF", Resolution.Minute)
        option = self.AddOption("OEF")
        option.SetFilter(-3, 3, timedelta(0), timedelta(days = 60))
        self.Schedule.On(self.DateRules.Every(DayOfWeek.Monday, DayOfWeek.Monday), self.TimeRules.At(10, 0), self.Rebalance)
        self.lastest_expiry = datetime.min
        self.SetBenchmark("OEF")

    def OnData(self, slice):

        if self.Time.date() == self.lastest_expiry.date():
            self.Liquidate()


    def Rebalance(self):
        calendar = self.TradingCalendar.GetDaysByType(TradingDayType.OptionExpiration, self.Time, self.EndDate)
        expiries = [i.Date for i in calendar]
        if len(expiries) == 0: return
        self.lastest_expiry = expiries[0]

        if (self.lastest_expiry - self.Time).days <= 5:
            self.SetHoldings("OEF", 1)
