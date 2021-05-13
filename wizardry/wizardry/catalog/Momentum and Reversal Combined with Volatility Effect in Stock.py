# https://quantpedia.com/Screener/Details/155
from QuantConnect.Data.UniverseSelection import *
import math
import numpy as np
import pandas as pd
import scipy as sp
from collections import deque

class MomentumReversalCombinedWithVolatility(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2014, 1, 1)  # Set Start Date
        self.SetEndDate(2018, 8, 1)    # Set Start Date
        self.SetCash(100000)           # Set Strategy Cash

        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.dataDict = {}
        # 1/6 of the portfolio is rebalanced every month
        self.portfolios = deque(maxlen=6)
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"),self.TimeRules.AfterMarketOpen("SPY"), self.Rebalance)
        # the lookback period for volatility and return is six months
        self.lookback = 20*6
        self.filteredFine = None
        self.monthly_rebalance = False

    def CoarseSelectionFunction(self, coarse):
        # update the price of stocks in universe everyday
        for i in coarse:
            if i.Symbol not in self.dataDict:
                self.dataDict[i.Symbol] = SymbolData(i.Symbol, self.lookback)
            self.dataDict[i.Symbol].Update(i.AdjustedPrice)

        if self.monthly_rebalance:
            # drop stocks which have no fundamental data or have too low prices
            filteredCoarse = [x.Symbol for x in coarse if (x.HasFundamentalData) and (float(x.Price) > 5)]
            return filteredCoarse
        else:
            return []

    def FineSelectionFunction(self, fine):

        if self.monthly_rebalance:
            sortedFine = sorted(fine, key = lambda x: x.EarningReports.BasicAverageShares.Value * self.dataDict[x.Symbol].Price, reverse=True)
            # select stocks with large size
            topFine = sortedFine[:int(0.5*len(sortedFine))]
            self.filteredFine = [x.Symbol for x in topFine]
            return self.filteredFine
        else:
            return []


    def Rebalance(self):
        self.monthly_rebalance = True


    def OnData(self, data):

        if self.monthly_rebalance and self.filteredFine:

            filtered_data = {symbol: symbolData for (symbol, symbolData) in self.dataDict.items() if symbol in self.filteredFine and symbolData.IsReady()}

            self.filteredFine = None
            self.monthly_rebalance = False

            # if the dictionary is empty, then return
            if len(filtered_data) < 100: return
            # sort the universe by volatility and select stocks in the top high volatility quintile
            sortedByVol = sorted(filtered_data.items(), key=lambda x: x[1].Volatility(), reverse = True)[:int(0.2*len(filtered_data))]
            sortedByVol = dict(sortedByVol)
            # sort the stocks in top-quintile by realized return
            sortedByReturn = sorted(sortedByVol, key = lambda x: sortedByVol[x].Return(), reverse = True)
            long = sortedByReturn[:int(0.2*len(sortedByReturn))]
            short = sortedByReturn[-int(0.2*len(sortedByReturn)):]

            self.portfolios.append(short+long)

            # 1/6 of the portfolio is rebalanced every month
            if len(self.portfolios) == self.portfolios.maxlen:
                for i in list(self.portfolios)[0]:
                    self.Liquidate(i)
            # stocks are equally weighted and held for 6 months
            short_weight = 1/len(short)
            for i in short:
                self.SetHoldings(i, -1/6*short_weight)

            long_weight = 1/len(long)
            for i in long:
                self.SetHoldings(i, 1/6*long_weight)


class SymbolData:
    '''Contains data specific to a symbol required by this model'''

    def __init__(self, symbol, lookback):
        self.symbol = symbol
        # self.History = RollingWindow[Decimal](lookback)
        self.History = deque(maxlen=lookback)
        self.Price = None

    def Update(self, value):
        # update yesterday's close price
        self.Price = value
        # update the history price series
        self.History.append(float(value))
        # self.History.Add(value)

    def IsReady(self):
        return len(self.History) == self.History.maxlen

    def Volatility(self):
        # one week (5 trading days) prior to the beginning of each month is skipped
        prices = np.array(self.History)[:-5]
        returns = (prices[1:]-prices[:-1])/prices[:-1]
        # calculate the annualized realized volatility
        return np.std(returns)*np.sqrt(250/len(returns))

    def Return(self):
        # one week (5 trading days) prior to the beginning of each month is skipped
        prices = np.array(self.History)[:-5]
        # calculate the annualized realized return
        return (prices[-1]-prices[0])/prices[0]
