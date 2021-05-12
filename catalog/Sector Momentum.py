# https://quantpedia.com/Screener/Details/3
# Use 10 sector ETFs. Pick 3 ETFs with strongest 12 month momentum into your portfolio
# and weigh them equally. Hold for 1 month and then rebalance.

import pandas as pd
from datetime import datetime

class SectorMomentumAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2007, 1, 1)
        self.SetEndDate(datetime.now())
        self.SetCash(100000)
        # create a dictionary to store momentum indicators for all symbols
        self.data = {}
        period = 3*21
        # choose ten sector ETFs
        self.symbols = ["VNQ",  # Vanguard Real Estate Index Fund
                        "XLK",  # Technology Select Sector SPDR Fund
                        "XLE",  # Energy Select Sector SPDR Fund
                        "XLV",  # Health Care Select Sector SPDR Fund
                        "XLF",  # Financial Select Sector SPDR Fund
                        "KBE",  # SPDR S&P Bank ETF
                        "VAW",  # Vanguard Materials ETF
                        "XLY",  # Consumer Discretionary Select Sector SPDR Fund
                        "XLP",  # Consumer Staples Select Sector SPDR Fund
                        "VGT"]  # Vanguard Information Technology ETF

        # warm up the MOM indicator
        self.SetWarmUp(period)
        for symbol in self.symbols:
            self.AddEquity(symbol, Resolution.Daily)
            self.data[symbol] = self.MOM(symbol, period, Resolution.Daily)
        # shcedule the function to fire at the month start
        self.Schedule.On(self.DateRules.MonthStart("VNQ"), self.TimeRules.AfterMarketOpen("VNQ"), self.Rebalance)

    def OnData(self, data):
        pass

    def Rebalance(self):
        if self.IsWarmingUp: return
        top3 = pd.Series(self.data).sort_values(ascending = False)[:3]
        for kvp in self.Portfolio:
            security_hold = kvp.Value
            # liquidate the security which is no longer in the top3 momentum list
            if security_hold.Invested and (security_hold.Symbol.Value not in top3.index):
                self.Liquidate(security_hold.Symbol)

        for symbol in top3.index:
            self.SetHoldings(symbol, 1/len(top3))
