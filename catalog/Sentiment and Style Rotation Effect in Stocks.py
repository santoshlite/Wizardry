# https://quantpedia.com/Screener/Details/53
from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Data import SubscriptionDataSource
from QuantConnect.Python import PythonData
from QuantConnect.Python import PythonQuandl
from datetime import date, timedelta, datetime
from decimal import Decimal
import numpy as np
from math import floor
import json

class SentimentAndStyleRotationAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2010, 1, 1)
        self.SetEndDate(2018, 7, 1)
        self.SetCash(100000)

        self.AddData(QuandlVix, "CBOE/VIX", Resolution.Daily)
        self.AddData(CBOE, "PutCallRatio", Resolution.Daily)

        self.vix_SMA_1 = SimpleMovingAverage(21)
        self.vix_SMA_6 = SimpleMovingAverage(21*6)
        self.PCRatio_SMA_1 = SimpleMovingAverage(21)
        self.PCRatio_SMA_6 = SimpleMovingAverage(21*6)
        # initialize the indicator with the history request
        PCRatio_history = self.History(["PutCallRatio"], 21*10, Resolution.Daily)
        vix_history = self.History(["CBOE/VIX"], 21*10, Resolution.Daily)

        for tuple in vix_history.loc["CBOE/VIX"].itertuples():
            self.vix_SMA_6.Update(tuple.Index, tuple.value)
            self.vix_SMA_1.Update(tuple.Index, tuple.value)
        for tuple in PCRatio_history.loc["PUTCALLRATIO"].itertuples():
            self.PCRatio_SMA_1.Update(tuple.Index, tuple.value)
            self.PCRatio_SMA_6.Update(tuple.Index, tuple.value)
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.At(0, 0), self.rebalance)
        self.month_start = False
        self.selection = False
        self.months = -1

    def CoarseSelectionFunction(self, coarse):

        if self.month_start:
            # drop stocks which have no fundamental data or have low price
            self.filtered_coarse = [x.Symbol for x in coarse if (x.HasFundamentalData)]
            return self.filtered_coarse
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.month_start:
            self.selection = True

            fine = [i for i in fine if i.EarningReports.BasicAverageShares.ThreeMonths>0
                                    and i.EarningReports.BasicEPS.TwelveMonths>0
                                    and i.ValuationRatios.PERatio>0
                                    and i.ValuationRatios.PBRatio>0]
            # Calculate the market cap and add the "MakretCap" property to fine universe object
            for i in fine:
                i.MarketCap = float(i.EarningReports.BasicAverageShares.ThreeMonths * (i.EarningReports.BasicEPS.TwelveMonths*i.ValuationRatios.PERatio))

            sotrted_market_cap = sorted(fine, key = lambda x:x.MarketCap, reverse=True)
            decile_top1 = sotrted_market_cap[:floor(len(sotrted_market_cap)/10)]
            decile_top2 = sotrted_market_cap[floor(len(sotrted_market_cap)/10):floor(len(sotrted_market_cap)*2/10)]
            decile_top3 = sotrted_market_cap[floor(len(sotrted_market_cap)*2/10):floor(len(sotrted_market_cap)*3/10)]
            sorted_PB1 = sorted(decile_top1, key = lambda x: x.ValuationRatios.PBRatio)
            sorted_PB2 = sorted(decile_top2, key = lambda x: x.ValuationRatios.PBRatio)
            sorted_PB3 = sorted(decile_top3, key = lambda x: x.ValuationRatios.PBRatio)
            # The value portfolio consists of all firms included in the quintile with the lowest P/B ratio
            PB_bottom1 = sorted_PB1[:floor(len(decile_top1)/5)]
            PB_bottom2 = sorted_PB2[:floor(len(decile_top2)/5)]
            PB_bottom3 = sorted_PB3[:floor(len(decile_top3)/5)]
            self.value_portfolio = [i.Symbol for i in PB_bottom1 + PB_bottom2 + PB_bottom3]

            # The growth portfolio consists of all firms included in the quintile with the highest P/B ratio
            PB_top1 = sorted_PB1[-floor(len(decile_top1)/5):]
            PB_top2 = sorted_PB2[-floor(len(decile_top2)/5):]
            PB_top3 = sorted_PB3[-floor(len(decile_top3)/5):]
            self.growth_portfolio = [i.Symbol for i in PB_top1 + PB_top2 + PB_top3]

            return  self.value_portfolio + self.growth_portfolio

        else:
            return []

    def rebalance(self):
        # rebalance every three months
        self.months += 1
        if self.months%3 == 0:
            self.month_start = True

    def OnData(self, data):
        if self.Securities["CBOE/VIX"].Price == 0 or self.Securities["PutCallRatio"].Price == 0: return
        self.vix_SMA_1.Update(self.Time, self.Securities["CBOE/VIX"].Price)
        self.vix_SMA_6.Update(self.Time, self.Securities["CBOE/VIX"].Price)
        self.PCRatio_SMA_1.Update(self.Time, self.Securities["PutCallRatio"].Price)
        self.PCRatio_SMA_6.Update(self.Time, self.Securities["PutCallRatio"].Price)

        if self.month_start and self.selection:
            self.month_start = False
            self.selection = False

            stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
            for i in stocks_invested:
                if i not in self.value_portfolio+self.growth_portfolio:
                    self.Liquidate(i)

            if self.vix_SMA_1.Current.Value > self.vix_SMA_6.Current.Value:
                if self.PCRatio_SMA_1.Current.Value < self.PCRatio_SMA_6.Current.Value:
                    long_weight = 1/len(self.value_portfolio)
                    for long in self.value_portfolio:
                        self.SetHoldings(long, long_weight)
                elif self.PCRatio_SMA_1.Current.Value > self.PCRatio_SMA_6.Current.Value:
                    short_weight = 1/len(self.value_portfolio)
                    for short in self.value_portfolio:
                        self.SetHoldings(short, -short_weight)

            else:
                long_weight = 1/len(self.value_portfolio+self.growth_portfolio)
                for long in self.value_portfolio+self.growth_portfolio:
                    self.SetHoldings(long, long_weight)


class QuandlVix(PythonQuandl):

    def __init__(self):
        self.ValueColumnName = "VIX Close"


class CBOE(PythonData):
    '''Cboe Equity Volume Put/Call Ratios (11-01-2006 to present) Custom Data Class'''
    def GetSource(self, config, date, isLiveMode):
        return SubscriptionDataSource("http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/equitypc.csv", SubscriptionTransportMedium.RemoteFile)

    def Reader(self, config, line, date, isLiveMode):
        if not (line.strip() and line[0].isdigit()): return None
        index = CBOE()
        index.Symbol = config.Symbol

        try:
            # Example File Format:
            # DATE       CALL      PUT       TOTAL      P/C Ratio
            # 11/1/06    976510    623929    1600439    0.64
            data = line.split(',')
            index.Time = datetime.strptime(data[0], "%m/%d/%Y").strftime("%Y-%m-%d")
            index.Value = Decimal(data[4])

        except ValueError:
                return None

        return index
