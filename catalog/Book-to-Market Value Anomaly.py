# https://quantpedia.com/Screener/Details/26
from QuantConnect.Data.UniverseSelection import *
import math
import numpy as np
import pandas as pd
import scipy as sp

class BooktoMarketAnomaly(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2004, 1, 1)
        self.SetEndDate(2018, 7, 1)
        self.SetCash(1000000)
        self.UniverseSettings.Resolution = Resolution.Daily
        self.sorted_by_bm = None
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.rebalance)
        # Count the number of months that have passed since the algorithm starts
        self.months = -1
        self.yearly_rebalance = True
    def CoarseSelectionFunction(self, coarse):
        if self.yearly_rebalance:
            # drop stocks which have no fundamental data or have low price
            self.filtered_coarse = [x.Symbol for x in coarse if (x.HasFundamentalData)]
            return self.filtered_coarse
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.yearly_rebalance:
            # Filter stocks with positive PB Ratio
            fine = [x for x in fine if (x.ValuationRatios.PBRatio > 0)]
            # Calculate the market cap and add the "MakretCap" property to fine universe object
            for i in fine:
                i.MarketCap = float(i.EarningReports.BasicAverageShares.ThreeMonths * (i.EarningReports.BasicEPS.TwelveMonths*i.ValuationRatios.PERatio))
            top_market_cap = sorted(fine, key = lambda x:x.MarketCap, reverse=True)[:int(len(fine)*0.2)]
            # sorted stocks in the top market-cap list by book-to-market ratio
            top_bm = sorted(top_market_cap, key = lambda x: 1 / x.ValuationRatios.PBRatio, reverse=True)[:int(len(top_market_cap)*0.2)]
            self.sorted_by_bm = [i.Symbol for i in top_bm]
            total_market_cap = np.sum([i.MarketCap for i in top_bm])
            # calculate the weight with the market cap
            self.weights = {}
            for i in top_bm:
                self.weights[str(i.Symbol)] = i.MarketCap/total_market_cap
            return self.sorted_by_bm
        else:
            return []

    def rebalance(self):
        # yearly rebalance
        self.months += 1
        if self.months%12 == 0:
            self.yearly_rebalance = True


    def OnData(self, data):
        if not self.yearly_rebalance: return
        if self.sorted_by_bm:
            stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
            # liquidate stocks not in the trading list
            for i in stocks_invested:
                if i not in self.sorted_by_bm:
                    self.Liquidate(i)
            # goes long on stocks with the highest book-to-market ratio
            for i in self.sorted_by_bm:
                self.SetHoldings(i, self.weights[str(i)])

            self.yearly_rebalance = False
