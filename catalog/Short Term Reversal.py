# https://quantpedia.com/Screener/Details/13
# The investment universe consists of the 100 biggest companies by market capitalization.
# The investor goes long on the 10 stocks with the lowest performance in the previous month
# and goes short on the 10 stocks with the greatest performance from the previous month.
# The portfolio is rebalanced weekly.
from QuantConnect.Data.UniverseSelection import *
import math
import numpy as np
import pandas as pd
import scipy as sp

class ShortTermReversalAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2016, 1, 1)  # Set Start Date
        self.SetEndDate(2018, 9, 1)    # Set Start Date
        self.SetCash(5000000)          # Set Strategy Cash
        self.lookback = 20

        self.UniverseSettings.Resolution = Resolution.Daily
        self.num_screener = 20
        self.num_trade = 10
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.symbolDataDict = {}
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.Every(DayOfWeek.Monday, DayOfWeek.Monday), self.TimeRules.AfterMarketOpen("SPY", 0), self.Rebalance)
        self.weekly_rebalance = True
        self.filtered_coarse = []
        self.filtered_fine = []


    def CoarseSelectionFunction(self, coarse):
        if self.weekly_rebalance:
            # drop stocks which have no fundamental data or have too low prices
            selected = [x for x in coarse if (x.HasFundamentalData) and (float(x.Price) > 5)]
            # rank the stocks by dollar volume
            filtered = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
            self.filtered_coarse = [ x.Symbol for x in filtered[:1000]]
            return self.filtered_coarse
        else:
            return self.filtered_fine



    def FineSelectionFunction(self, fine):
        if self.weekly_rebalance:
            filtered_fine = [x for x in fine if x.EarningReports.BasicEPS.TwelveMonths > 0
                                                and x.ValuationRatios.PERatio > 0
                                                and x.EarningReports.BasicAverageShares.ThreeMonths > 0
                                                and x.EarningReports.BasicAverageShares.ThreeMonths > 0]
            # filter 100 stocks with the top market cap
            top = sorted(filtered_fine, key = lambda x: x.EarningReports.BasicAverageShares.ThreeMonths * (x.EarningReports.BasicEPS.TwelveMonths*x.ValuationRatios.PERatio), reverse=True)[:100]
            self.filtered_fine = [i.Symbol for i in top]
            return self.filtered_fine
        else:
            return self.filtered_fine


    def OnData(self, data):
        for symbol, symbolData in self.symbolDataDict.items():
            # update the indicator value for newly added securities
            if symbol not in self.addedSymbols:
                symbolData.ROC.Update(IndicatorDataPoint(symbol, self.Time, self.Securities[symbol].Close))

        if  self.weekly_rebalance and self.filtered_fine:
            self.addedSymbols = []
            # sorted the stocks by the monthly return (RateOfReturn)
            readyROC = {key: value for key, value in self.symbolDataDict.items() if value.ROC.IsReady}
            sorted_symbolData = sorted(readyROC, key=lambda x: readyROC[x].ROC.Current.Value)
            short_stocks = sorted_symbolData[-self.num_trade:]
            long_stocks = sorted_symbolData[:self.num_trade]
            invested = [x.Key for x in self.Portfolio if x.Value.Invested]
            for i in invested:
                if i not in short_stocks+long_stocks:
                    self.Liquidate(i)

            for short in short_stocks:
                self.SetHoldings(short, -0.5/self.num_trade)
            for long in long_stocks:
                self.SetHoldings(long, 0.5/self.num_trade)

            self.weekly_rebalance = False


    def Rebalance(self):
        self.weekly_rebalance = True


    def OnSecuritiesChanged(self, changes):

        for removed in changes.RemovedSecurities:
            symbolData = self.symbolDataDict.pop(removed.Symbol, None)
        # warm up the indicator with history price for newly added securities
        self.addedSymbols = [x.Symbol for x in changes.AddedSecurities if x.Symbol.Value != "SPY"]
        history = self.History(self.addedSymbols, self.lookback+10, Resolution.Daily)

        for symbol in self.addedSymbols:
            if symbol not in self.symbolDataDict.keys():
                symbolData = SymbolData(symbol, self.lookback)
                self.symbolDataDict[symbol] = symbolData
                if str(symbol) in history.index:
                    symbolData.WarmUpIndicator(history.loc[str(symbol)])


class SymbolData:
    '''Contains data specific to a symbol required by this model'''

    def __init__(self, symbol, lookback):
        self.symbol = symbol
        self.ROC = RateOfChange(lookback)

    def WarmUpIndicator(self, history):
        # warm up the RateOfChange indicator with the history request
        for tuple in history.itertuples():
            item = IndicatorDataPoint(self.symbol, tuple.Index, float(tuple.close))
            self.ROC.Update(item)
