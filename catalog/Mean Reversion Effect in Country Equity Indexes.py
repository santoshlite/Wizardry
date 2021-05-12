# https://quantpedia.com/Screener/Details/16
import pandas as pd
from datetime import datetime

class CountryEquityIndexesMeanReversionAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2000, 1, 1)
        self.SetEndDate(datetime.now())
        self.SetCash(100000)
        # create a dictionary to store return indicators for all symbols
        self.data = {}
        period = 21*36
        self.symbols = ["EWJ",  # iShares MSCI Japan Index ETF
                        "EFNL", # iShares MSCI Finland Capped Investable Market Index ETF
                        "EWW",  # iShares MSCI Mexico Inv. Mt. Idx
                        "ERUS", # iShares MSCI Russia ETF
                        "IVV",  # iShares S&P 500 Index
                        "AUD",  # Australia Bond Index Fund
                        "EWQ",  # iShares MSCI France Index ETF
                        "EWH",  # iShares MSCI Hong Kong Index ETF
                        "EWI",  # iShares MSCI Italy Index ETF
                        "EWY",  # iShares MSCI South Korea Index ETF
                        "EWP",  # iShares MSCI Spain Index ETF
                        "EWD",  # iShares MSCI Sweden Index ETF
                        "EWL",  # iShares MSCI Switzerland Index ETF
                        "EWC",  # iShares MSCI Canada Index ETF
                        "EWZ",  # iShares MSCI Brazil Index ETF
                        "EWO",  # iShares MSCI Austria Investable Mkt Index ETF
                        "EWK",  # iShares MSCI Belgium Investable Market Index ETF
                        "BRAQ", # Global X Brazil Consumer ETF
                        "ECH"]  # iShares MSCI Chile Investable Market Index ETF

        # warm up the Return indicator
        self.SetWarmUp(period)
        for symbol in self.symbols:
            self.AddEquity(symbol, Resolution.Daily)
            self.data[symbol] = self.ROC(symbol, period, Resolution.Daily)
        # shcedule the function to fire at the month start
        self.Schedule.On(self.DateRules.MonthStart("IVV"), self.TimeRules.AfterMarketOpen("IVV"), self.Rebalance)
        # create the flag variable to save the number of months passed
        self.months = -1

    def OnData(self, data):
        pass

    def Rebalance(self):
        # rebalance the portfolio every three years
        self.months += 1
        if self.months % 36 != 0: return
        sorted_symbols = sorted(self.data, key=lambda x: self.data[x].Current.Value)

        top = sorted_symbols[-4:]
        bottom = sorted_symbols[:4]
        for kvp in self.Portfolio:
            security_hold = kvp.Value
            # liquidate the security which is no longer in the list
            if security_hold.Invested and (security_hold.Symbol.Value not in top+bottom):
                self.Liquidate(security_hold.Symbol)
        for short in top:
            if not self.Portfolio[short].Invested:
                self.SetHoldings(short, -0.4/len(top))
        for long in bottom:
            if not self.Portfolio[long].Invested:
                self.SetHoldings(long, 0.4/len(bottom))
