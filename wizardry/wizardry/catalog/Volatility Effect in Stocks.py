# https://quantpedia.com/Screener/Details/7
# The investment universe consists of global large cap stocks (or US large cap stocks).
# At the end of the each month, the investor constructs equally weighted decile portfolios
# by ranking the stocks on the past one year volatility of daily price. The investor
# goes long stocks with the lowest volatility.
from QuantConnect.Data.UniverseSelection import *
import math
import numpy as np
import pandas as pd
import scipy as sp

class ShortTermReversalAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2017, 1, 1)  # Set Start Date
        self.SetEndDate(2018, 6, 1)    # Set Start Date
        self.SetCash(100000)           # Set Strategy Cash
        self.lookback = 252

        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.symbolDataDict = {}
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"),self.TimeRules.AfterMarketOpen("SPY"), self.rebalance)

    def CoarseSelectionFunction(self, coarse):
        # drop stocks which have no fundamental data or have too low prices
        selected = [x for x in coarse if (x.HasFundamentalData) and (float(x.Price) > 5)]
        # rank the stocks by dollar volume
        filtered = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
        return [ x.Symbol for x in filtered[:100]]

    def FineSelectionFunction(self, fine):
        # filter stocks with the top market cap
        top = sorted(fine, key = lambda x: x.EarningReports.BasicAverageShares.ThreeMonths * (x.EarningReports.BasicEPS.TwelveMonths*x.ValuationRatios.PERatio), reverse=True)
        return [x.Symbol for x in top[:50]]

    def rebalance(self):
        sorted_symbolData = sorted(self.symbolDataDict, key=lambda x: self.symbolDataDict[x].Volatility())
        # pick 5 stocks with the lowest volatility
        long_stocks = sorted_symbolData[:5]
        stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        # liquidate stocks not in the list
        for i in stocks_invested:
            if i not in long_stocks:
                self.Liquidate(i)
        # long stocks with the lowest volatility
        for i in long_stocks:
            self.SetHoldings(i, 1/5)


    def OnData(self, data):
        for symbol, symbolData in self.symbolDataDict.items():
            # update the indicator value for newly added securities
            if symbol not in self.addedSymbols:
                symbolData.Price.Add(IndicatorDataPoint(symbol, self.Time, self.Securities[symbol].Close))

        self.addedSymbols = []
        self.removedSymbols = []

    def OnSecuritiesChanged(self, changes):

        # clean up data for removed securities
        self.removedSymbols = [x.Symbol for x in changes.RemovedSecurities]
        for removed in changes.RemovedSecurities:
            symbolData = self.symbolDataDict.pop(removed.Symbol, None)

        # warm up the indicator with history price for newly added securities
        self.addedSymbols = [ x.Symbol for x in changes.AddedSecurities if x.Symbol.Value != "SPY"]
        history = self.History(self.addedSymbols, self.lookback+1, Resolution.Daily)

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
        self.Price = RollingWindow[IndicatorDataPoint](lookback)

    def WarmUpIndicator(self, history):
        # warm up the RateOfChange indicator with the history request
        for tuple in history.itertuples():
            item = IndicatorDataPoint(self.symbol, tuple.Index, float(tuple.close))
            self.Price.Add(item)

    def Volatility(self):
        data = [float(x.Value) for x in self.Price]
        # time = [x.EndTime for x in self.Price]
        # price_series = pd.Series(data, index=time)
        return np.std(data)
