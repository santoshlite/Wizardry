# https://quantpedia.com/Screener/Details/66
from QuantConnect.Data.UniverseSelection import *
import math
import numpy as np
import pandas as pd
import scipy as sp
from collections import deque

class CombiningMomentumEffectWithVolume(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2012, 1, 1)  # Set Start Date
        self.SetEndDate(2018, 8, 1)    # Set Start Date
        self.SetCash(100000)           # Set Strategy Cash

        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.dataDict = {}
        # 1/3 of the portfolio is rebalanced every month
        self.portfolios = deque(maxlen=3)
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"),self.TimeRules.At(0, 0), self.Rebalance)
        # the lookback period for return calculation
        self.lookback = 252
        self.filteredFine = None
        self.monthly_rebalance = False

    def CoarseSelectionFunction(self, coarse):
        for i in coarse:
            if i.Symbol not in self.dataDict:
                self.dataDict[i.Symbol] = SymbolData(i.Symbol, self.lookback)
            self.dataDict[i.Symbol].ROC.Update(i.EndTime, i.AdjustedPrice)
            self.dataDict[i.Symbol].Volume = i.Volume

        if self.monthly_rebalance:
            # drop stocks which have no fundamental data
            filteredCoarse = [x for x in coarse if (x.HasFundamentalData)]
            return [i.Symbol for i in filteredCoarse]
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.monthly_rebalance:
            dataReady = {symbol: symbolData for (symbol, symbolData) in self.dataDict.items() if symbolData.ROC.IsReady}
            if len(dataReady) < 100:
                self.filteredFine = []
            else:
                sortedFine = [i for i in fine if i.EarningReports.BasicAverageShares.ThreeMonths != 0 and i.Symbol in dataReady]
                sortedFineSymbols = [i.Symbol for i in sortedFine]
                filteredData = {symbol: symbolData for (symbol, symbolData) in dataReady.items() if symbol in sortedFineSymbols}
                for i in sortedFine:
                    if i.Symbol in filteredData and filteredData[i.Symbol].Volume != 0:
                        filteredData[i.Symbol].Turnover = i.EarningReports.BasicAverageShares.ThreeMonths / filteredData[i.Symbol].Volume
                sortedByROC = sorted(filteredData.values(), key = lambda x: x.ROC.Current.Value, reverse = True)
                topROC = sortedByROC[:int(len(sortedByROC)*0.2)]
                bottomROC = sortedByROC[-int(len(sortedByROC)*0.2):]

                HighTurnoverTopROC = sorted(topROC, key = lambda x: x.Turnover, reverse = True)
                HighTurnoverBottomROC = sorted(bottomROC, key = lambda x: x.Turnover, reverse = True)

                self.long =  [i.Symbol for i in HighTurnoverTopROC[:int(len(HighTurnoverTopROC)*0.01)]]
                self.short = [i.Symbol for i in HighTurnoverBottomROC[:int(len(HighTurnoverBottomROC)*0.01)]]
                self.filteredFine = self.long + self.short
                self.portfolios.append(self.filteredFine)
        else:
            self.filteredFine = []

        if not self.filteredFine:
            self.monthly_rebalance = False

        return self.filteredFine


    def Rebalance(self):
        self.monthly_rebalance = True


    def OnData(self, data):

        if self.monthly_rebalance and self.filteredFine:

            self.filteredFine = None
            self.monthly_rebalance = False

            # 1/3 of the portfolio is rebalanced every month
            if len(self.portfolios) == self.portfolios.maxlen:
                for i in list(self.portfolios)[0]:
                    self.Liquidate(i)

            # stocks are equally weighted and held for 3 months
            short_weight = 1/len(self.short)
            for i in self.short:
                self.SetHoldings(i, -1/3*short_weight)

            long_weight = 1/len(self.long)
            for i in self.long:
                self.SetHoldings(i, 1/3*long_weight)


class SymbolData:
    '''Contains data specific to a symbol required by this model'''

    def __init__(self, symbol, lookback):
        self.Symbol = symbol
        self.ROC = RateOfChange(lookback)
        self.Volume = None
