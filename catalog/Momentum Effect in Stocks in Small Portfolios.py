# https://quantpedia.com/Screener/Details/162
from QuantConnect.Data.UniverseSelection import *
import math
import numpy as np
import pandas as pd
import scipy as sp
from datetime import timedelta
class MomentumInSmallPortfolio(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2008, 1, 1)
        self.SetEndDate(2018, 9, 1)
        self.SetCash(1000000)
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.rebalance)
        # Count the number of months that have passed since the algorithm starts
        self.months = -1
        self.yearly_rebalance = True
        self.long = None
        self.short = None
    def CoarseSelectionFunction(self, coarse):
        if self.yearly_rebalance:
            # drop stocks which have no fundamental data or have low price
            self.filtered_coarse = [x.Symbol for x in coarse if (x.HasFundamentalData)]
            return self.filtered_coarse
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.yearly_rebalance:
            # Calculate the yearly return and market cap
            for i in fine:
                i.MarketCap = float(i.EarningReports.BasicAverageShares.ThreeMonths * (i.EarningReports.BasicEPS.TwelveMonths*i.ValuationRatios.PERatio))
            top_market_cap = sorted(fine, key = lambda x:x.MarketCap, reverse=True)[:int(len(fine)*0.75)]
            has_return = []
            for i in top_market_cap:
                history = self.History([i.Symbol], timedelta(days=365), Resolution.Daily)
                if not history.empty:
                    close = history.loc[str(i.Symbol)]['close']
                    i.returns = (close[0]-close[-1])/close[-1]
                    has_return.append(i)
            sorted_by_return = sorted(has_return, key = lambda x: x.returns)
            self.long = [i.Symbol for i in sorted_by_return[-10:]]
            self.short = [i.Symbol for i in sorted_by_return[:10]]

            return self.long+self.short
        else:
            return []

    def rebalance(self):
        # yearly rebalance
        self.months += 1
        if self.months%12 == 0:
            self.yearly_rebalance = True


    def OnData(self, data):
        if not self.yearly_rebalance: return
        if self.long and self.short:
            stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
            # liquidate stocks not in the trading list
            for i in stocks_invested:
                if i not in self.long+self.short:
                    self.Liquidate(i)
            for i in self.short:
                self.SetHoldings(i, -0.5/len(self.short))
            for i in self.long:
                self.SetHoldings(i, 0.5/len(self.long))


            self.long = None
            self.short = None
            self.yearly_rebalance = False
