import numpy as np
from datetime import timedelta

class PreHolidayEffectAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2000, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(100000)
        self.AddEquity("SPY", Resolution.Daily)


    def OnData(self, data):
        calendar1 = self.TradingCalendar.GetDaysByType(TradingDayType.PublicHoliday, self.Time, self.Time+timedelta(days=2))
        calendar2 = self.TradingCalendar.GetDaysByType(TradingDayType.Weekend, self.Time, self.Time+timedelta(days=2))
        holidays = [i.Date for i in calendar1]
        weekends = [i.Date for i in calendar2]
        # subtract weekends in all holidays
        public_holidays = list(set(holidays) - set(weekends))

        if not self.Portfolio.Invested and len(public_holidays)>0:
            self.SetHoldings("SPY", 1)
        elif self.Portfolio.Invested and len(public_holidays)==0:
            self.Liquidate()
