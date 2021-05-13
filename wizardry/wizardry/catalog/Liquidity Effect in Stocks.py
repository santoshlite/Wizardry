# https://quantpedia.com/Screener/Details/18
from QuantConnect.Data.UniverseSelection import *
import math
import numpy as np
import pandas as pd
import scipy as sp

class LiquidityEffectAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2018, 7, 1)
        self.SetCash(1000000)
        self.num_coarse = 500
        self.UniverseSettings.Resolution = Resolution.Daily
        self.long = None
        self.short = None
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.rebalance)
        # Count the number of months that have passed since the algorithm starts
        self.months = -1
        self.yearly_rebalance = True
    def CoarseSelectionFunction(self, coarse):
        if self.yearly_rebalance:
            # drop stocks which have no fundamental data or have low price
            selected = [x for x in coarse if (x.HasFundamentalData) and (float(x.AdjustedPrice) > 5)]
            # rank the stocks by dollar volume
            filtered = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
            self.filtered_coarse = [ x.Symbol for x in filtered[:self.num_coarse]]
            return self.filtered_coarse
        else:
            return self.filtered_coarse

    def FineSelectionFunction(self, fine):
        if self.yearly_rebalance:
            # Calculate the market cap and add the "MakretCap" property to fine universe object
            for i in fine:
                i.MarketCap = float(i.EarningReports.BasicAverageShares.ThreeMonths * (i.EarningReports.BasicEPS.TwelveMonths*i.ValuationRatios.PERatio))
            # The market capitalization must be no less than $10 million
            top_market_cap = list(filter(lambda x: x.MarketCap > 10000000, fine))
            # Save all market cap values
            market_caps = [i.MarketCap for i in top_market_cap]
            # Calculate the lowest market-cap quartile
            lowest_quartile = np.percentile(market_caps, 25)
            # Filter stocks in the lowest market-cap quartile
            lowest_market_cap = list(filter(lambda x: x.MarketCap <= lowest_quartile, top_market_cap))
            turnovers = []
            # Divide into quartiles based on their turnover (the number of shares traded divided by the stock’s outstanding shares) in the last 12 months
            for i in lowest_market_cap[:]:
                hist = self.History([i.Symbol], 21*12, Resolution.Daily)
                if not hist.empty:
                    mean_volume = np.mean(hist.loc[str(i.Symbol)]['volume'])
                    i.Turnover =  mean_volume / float(i.EarningReports.BasicAverageShares.ThreeMonths)
                    turnovers.append(i.Turnover)
                else:
                    lowest_market_cap.remove(i)
            bottom_turnover = np.percentile(turnovers, 5)
            top_turnover = np.percentile(turnovers, 95)
            self.long = [x.Symbol for x in lowest_market_cap if x.Turnover < bottom_turnover]
            self.short = [x.Symbol for x in lowest_market_cap if x.Turnover > top_turnover]

            self.yearly_rebalance = False

            return self.long+self.short
        else:
            return self.long+self.short

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
            # goes long on stocks with the lowest turnover
            for short_stock in self.short:
                self.SetHoldings(short_stock, -0.5/len(self.short))
            # short on stocks with the highest turnover
            for long_stock in self.long:
                self.SetHoldings(long_stock, 0.5/len(self.long))
