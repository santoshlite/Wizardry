# https://quantpedia.com/Screener/Details/55
import numpy as np
import pandas as pd
from scipy import stats
from math import floor
from datetime import timedelta
from collections import deque
import itertools as it
from decimal import Decimal

class PairsTradingwithCountryETFsAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2011, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(100000)
        # choose ten sector ETFs
        tickers =  ["GAF",  # SPDR S&P Emerging Middle East & Africa ETF 2007.4
                    "ENZL", # iShares MSCI New Zealand Investable Market Index Fund 2010.9
                    "NORW",  # Global X FTSE Norway 30 ETF 2011
                    "EWY",  # iShares MSCI South Korea Index ETF 2000.6
                    "EWP",  # iShares MSCI Spain Index ETF 1996
                    "EWD",  # iShares MSCI Sweden Index ETF 1996
                    "EWL",  # iShares MSCI Switzerland Index ETF 1996
                    "GXC",  # SPDR S&P China ETF 2007.4
                    "EWC",  # iShares MSCI Canada Index ETF 1996
                    "EWZ",  # iShares MSCI Brazil Index ETF 2000.8
                    # "AND",  # Global X FTSE Andean 40 ETF 2011.3
                    "AIA",  # iShares S&P Asia 50 Index ETF 1996
                    "EWO",  # iShares MSCI Austria Investable Mkt Index ETF 1996
                    "EWK",  # iShares MSCI Belgium Investable Market Index ETF 1996
                    "ECH",  # iShares MSCI Chile Investable Market Index ETF 2018  2008
                    # "EGPT", # Market Vectors Egypt Index ETF 2011
                    "EWJ",  # iShares MSCI Japan Index ETF 1999
                    "EZU",  # iShares MSCI Eurozone ETF 2000
                    "EWW",  # iShares MSCI Mexico Inv. Mt. Idx 2000
                    # "ERUS", # iShares MSCI Russia ETF 2011
                    "IVV",  # iShares S&P 500 Index 2001
                    "AAXJ", # iShares MSCI All Country Asia ex Japan Index ETF 2008.8
                    "EWQ",  # iShares MSCI France Index ETF 2000
                    "EWH",  # iShares MSCI Hong Kong Index ETF 1999
                    # "EPI",  # WisdomTree India Earnings ETF 2008.3
                    "EIDO",  # iShares MSCI Indonesia Investable Market Index ETF 2008.3
                    "EWI",  # iShares MSCI Italy Index ETF 1996
                    "ADRU"] # BLDRS Europe 100 ADR Index ETF 2003

        self.threshold = 0.5
        self.symbols = []
        for i in tickers:
            self.symbols.append(self.AddEquity(i, Resolution.Daily).Symbol)

        self.pairs = {}
        self.formation_period = 121

        self.history_price = {}
        for symbol in self.symbols:
            hist = self.History([symbol.Value], self.formation_period+1, Resolution.Daily)
            if hist.empty:
                self.symbols.remove(symbol)
            else:
                self.history_price[symbol.Value] = deque(maxlen=self.formation_period)
                for tuple in hist.loc[str(symbol)].itertuples():
                    self.history_price[symbol.Value].append(float(tuple.close))
                if len(self.history_price[symbol.Value]) < self.formation_period:
                    self.symbols.remove(symbol)
                    self.history_price.pop(symbol.Value)

        self.symbol_pairs = list(it.combinations(self.symbols, 2))
        # Add the benchmark
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.Rebalance)
        self.sorted_pairs = None


    def OnData(self, data):
        # Update the price series everyday
        for symbol in self.symbols:
            if data.Bars.ContainsKey(symbol) and symbol.Value in self.history_price:
                self.history_price[symbol.Value].append(float(data[symbol].Close))
        if self.sorted_pairs is None: return

        for i in self.sorted_pairs:
            pair = Pair(i[0], i[1], self.history_price[i[0].Value],  self.history_price[i[1].Value])
            index_a = pair.index_a[-1]
            index_b = pair.index_b[-1]
            delta = pair.distance()
            if index_a - index_b > self.threshold*delta:
                if not self.Portfolio[pair.symbol_a].Invested and not self.Portfolio[pair.symbol_b].Invested:
                    ratio = self.Portfolio[pair.symbol_a].Price / self.Portfolio[pair.symbol_b].Price
                    quantity = int(self.CalculateOrderQuantity(pair.symbol_a, 0.2))
                    self.Sell(pair.symbol_a, quantity)
                    self.Buy(pair.symbol_b,  floor(ratio*quantity))

            elif index_a - index_b < -self.threshold*delta:
                if not self.Portfolio[pair.symbol_a].Invested and not self.Portfolio[pair.symbol_b].Invested:
                    ratio = self.Portfolio[pair.symbol_b].Price / self.Portfolio[pair.symbol_a].Price
                    quantity = int(self.CalculateOrderQuantity(pair.symbol_b, 0.2))
                    self.Sell(pair.symbol_b, quantity)
                    self.Buy(pair.symbol_a, floor(ratio*quantity))

            # the position is closed when prices revert back
            elif self.Portfolio[i[0]].Invested and self.Portfolio[i[1]].Invested:
                    self.Liquidate(pair.symbol_a)
                    self.Liquidate(pair.symbol_b)


    def Rebalance(self):
        # schedule the event to fire every half year to select pairs with the smallest historical distance
        distances = {}
        for i in self.symbol_pairs:
            if i[0].Value in self.history_price and i[1].Value in self.history_price:
                distances[i] = Pair(i[0], i[1], self.history_price[i[0].Value],  self.history_price[i[1].Value]).distance()
        self.sorted_pairs = sorted(distances, key = lambda x: distances[x])[:5]

class Pair:
    def __init__(self, symbol_a, symbol_b, price_a, price_b):
        self.symbol_a = symbol_a
        self.symbol_b = symbol_b
        self.price_a = np.array(price_a)
        self.price_b = np.array(price_b)
        # compute normalized cumulative price indices
        self.index_a = np.cumprod(self.price_a[1:]/self.price_a[:-1])
        self.index_b = np.cumprod(self.price_b[1:]/self.price_b[:-1])


    def distance(self):
        return 1/120*sum(abs(self.index_a -self.index_b))
