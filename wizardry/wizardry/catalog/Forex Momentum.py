# https://quantpedia.com/Screener/Details/8
# Create an investment universe consisting of several currencies (15).
# Go long 3 currencies with strongest 12 month momentum against USD and
# go short 3 currencies with lowest 12 month momentum against USD.
import pandas as pd
from datetime import datetime

class FXMomentumAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2006, 1, 1)
        self.SetEndDate(datetime.now())
        self.SetCash(100000)
        # create a dictionary to store momentum indicators for all symbols
        self.data = {}
        period = 12*21
        # choose 15 forex pairs
        self.symbols = ["USDAUD", "USDCAD", "USDCHF", "USDEUR", "USDGBP",
                        "USDHKD", "USDJPY", "USDDKK", "USDCZK", "USDZAR",
                        "USDSEK", "USDSAR", "USDNOK", "USDMXN", "USDHUF"]

        # warm up the MOM indicator
        self.SetWarmUp(period)
        for symbol in self.symbols:
            self.AddForex(symbol, Resolution.Daily, Market.Oanda)
            self.data[symbol] = self.MOM(symbol, period, Resolution.Daily)
        # shcedule the function to fire at the month start
        self.Schedule.On(self.DateRules.MonthStart("USDEUR"), self.TimeRules.AfterMarketOpen("USDEUR"), self.Rebalance)

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

        added_symbols = []
        for symbol in top3.index:
            if not self.Portfolio[symbol].Invested:
                added_symbols.append(symbol)
        for added in added_symbols:
            self.SetHoldings(added, 1/len(added_symbols))
