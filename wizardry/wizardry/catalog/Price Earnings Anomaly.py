from QuantConnect.Data.UniverseSelection import *
import math
import numpy as np
import pandas as pd
import scipy as sp

class PriceEarningsAnamoly(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2019, 7, 1)
        self.SetCash(100000)
        self.SetBenchmark("SPY")

        self.UniverseSettings.Resolution = Resolution.Daily
        self.symbols = []

        # record the year that have passed since the algorithm starts
        self.year = -1
        self._NumCoarseStocks = 200
        self._NumStocksInPortfolio = 10

        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)


    def CoarseSelectionFunction(self, coarse):

        if self.Time.year == self.year:
            return self.symbols

        # drop stocks which have no fundamental data or have low price
        CoarseWithFundamental = [x for x in coarse if x.HasFundamentalData and x.Price > 5]
        sortedByDollarVolume = sorted(CoarseWithFundamental, key=lambda x: x.DollarVolume, reverse=False)

        return [i.Symbol for i in sortedByDollarVolume[:self._NumCoarseStocks]]

    def FineSelectionFunction(self, fine):

        if self.Time.year == self.year:
            return self.symbols

        self.year = self.Time.year

        fine = [x for x in fine if x.ValuationRatios.PERatio > 0]
        sortedPERatio = sorted(fine, key=lambda x: x.ValuationRatios.PERatio)

        self.symbols = [i.Symbol for i in sortedPERatio[:self._NumStocksInPortfolio]]

        return self.symbols

    def OnSecuritiesChanged(self, change):

        # liquidate securities that removed from the universe
        for security in change.RemovedSecurities:
            if self.Portfolio[security.Symbol].Invested:
                self.Liquidate(security.Symbol)

        count = len(change.AddedSecurities)

        # evenly invest on securities that newly added to the universe
        for security in change.AddedSecurities:
            self.SetHoldings(security.Symbol, 1.0/count)
