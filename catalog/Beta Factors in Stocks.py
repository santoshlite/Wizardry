# https://quantpedia.com/Screener/Details/77
from QuantConnect.Data.UniverseSelection import *
from QuantConnect.Python import PythonData
from collections import deque
from datetime import datetime
import math
import numpy as np
import pandas as pd
import scipy as sp
from decimal import Decimal


class BetaFactorInStocks(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2011, 1, 1)
        self.SetEndDate(2018, 9, 1)
        self.SetCash(1000000)
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction)
        self.AddEquity("SPY", Resolution.Daily)
        # add Wilshire 5000 Total Market Index data from Dropbox
        self.AddData(Wilshire5000, "W5000", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.rebalance)
        self.data = {}
        self.monthly_rebalance = False
        self.long = None
        self.short = None
        self.market_price = deque(maxlen=253)
        hist = self.History(["W5000"], 400, Resolution.Daily)
        for i in hist.loc["W5000"].itertuples():
            self.market_price.append(i.value)

    def CoarseSelectionFunction(self, coarse):

        if self.Securities["W5000"].Price is not None:
            self.market_price.append(self.Securities["W5000"].Price)
        for i in coarse:
            if i.Symbol not in self.data:
                self.data[i.Symbol] = SymbolData(i.Symbol)
            self.data[i.Symbol].Update(i.AdjustedPrice)

        if self.monthly_rebalance:
            sortedByPrice = [i.Symbol for i in coarse if i.AdjustedPrice>5]
            ready_data = {symbol: data for symbol, data in self.data.items() if symbol in sortedByPrice and data.IsReady()}
            if len(ready_data) > 20:
                self.market_return = np.diff(np.array(self.market_price))/np.array(self.market_price)[:-1]
                # sort the dictionary in ascending order by beta value
                sorted_beta = sorted(ready_data, key = lambda x: ready_data[x].beta(self.market_return))
                self.long = sorted_beta[:5]
                self.short = sorted_beta[-5:]
                return self.long+self.short
            else:
                self.monthly_rebalance = False
                return []
        else:
            return []


    def rebalance(self):
        self.monthly_rebalance = True

    def OnData(self, data):
        if not self.monthly_rebalance: return
        if self.long is None or self.short is None: return

        long_invested = [x.Key for x in self.Portfolio if x.Value.IsLong]
        short_invested = [x.Key for x in self.Portfolio if x.Value.IsShort]

        for i in long_invested:
            if i not in self.long:
                self.Liquidate(i)

        for i in short_invested:
            if i not in self.short:
                self.Liquidate(i)

        long_scale_factor = 0.5/sum(range(1,len(self.long)+1))
        for rank, symbol in enumerate(self.long):
            self.SetHoldings(symbol, (len(self.long)-rank+1)*long_scale_factor)

        short_scale_factor = 0.5/sum(range(1,len(self.long)+1))
        for rank, symbol in enumerate(self.short):
            self.SetHoldings(symbol, -(rank+1)*short_scale_factor)


        self.monthly_rebalance = False
        self.long = None
        self.short = None

class SymbolData:
    def __init__(self, symbol):
        self.Symbol = symbol
        self.window = RollingWindow[Decimal](2)
        self.returns = deque(maxlen=252)

    def Update(self, price):
        if price != 0:
            self.window.Add(price)
            if self.window.IsReady:
                self.returns.append((self.window[0]-self.window[1])/self.window[1])

    def IsReady(self):
        return len(self.returns) == self.returns.maxlen

    def beta(self, market_ret):
        asset_return = np.array(self.returns, dtype=np.float32)
        market_return = np.array(market_ret, dtype=np.float32)
        return np.cov(asset_return, market_return)[0][1]/np.var(market_return)

class Wilshire5000(PythonData):
    "Class to import Wilshire 5000 Total Market Index data from Dropbox"

    def GetSource(self, config, date, isLiveMode):
        return SubscriptionDataSource("https://www.dropbox.com/s/z9rof4fr9cqzgpt/W5000.csv?dl=1", SubscriptionTransportMedium.RemoteFile)

    def Reader(self, config, line, date, isLiveMode):
        if not (line.strip() and line[1].isdigit()): return None
        index = Wilshire5000()
        index.Symbol = config.Symbol
        try:
            # Example File Format: (Data starts from 01/04/2010)
            # Date      Open           High           Low            Close          Adj Close      Volume
            # 1/4/10    11549.13965    11749.37012    11549.13965    11743.54004    11743.54004    0
            data = line.split(',')
            index.Time = datetime.strptime(data[0], "%Y-%m-%d")
            index.Value = Decimal(data[5])
        except:
            return None

        return index
