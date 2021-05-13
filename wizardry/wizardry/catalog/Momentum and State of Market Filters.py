# https://quantpedia.com/Screener/Details/54
from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Data import SubscriptionDataSource
from QuantConnect.Python import PythonData
from datetime import date, timedelta, datetime
from decimal import Decimal
import numpy as np

class MomentumandStateofMarketFiltersAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2011, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(100000)
        # add Wilshire 5000 Total Market Index data from Dropbox
        self.AddData(Wilshire5000, "W5000", Resolution.Daily)
        self.W5000Return = self.ROC("W5000", 252)
        # initialize the RateOfChange indicator of Wilshire 5000 total market index
        history = self.History(["W5000"], 500, Resolution.Daily)
        for tuple in history.loc["W5000"].itertuples():
            self.W5000Return.Update(tuple.Index, tuple.value)

        self.Debug("W5000 Rate of Change indicator isReady: "+ str(self.W5000Return.IsReady))
        self.AddEquity("SPY", Resolution.Daily)
        self.AddUniverse(self.CoarseSelectionFunction)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.At(0, 0), self.rebalance)
        # mark it's the start of each month
        self.month_start = False
        # mark the coarse universe selection has finished
        self.selection = False
        self.mom = {}
        self.lookback = 20*6
        self.long = None
        self.short = None
        self.tlt = self.AddEquity("TLT", Resolution.Daily).Symbol

    def CoarseSelectionFunction(self, coarse):
        coarse = [x for x in coarse if (x.HasFundamentalData and x.AdjustedPrice > 1)]
        for i in coarse:
            if i.Symbol not in self.mom:
                self.mom[i.Symbol] = SymbolData(i.Symbol, self.lookback)
            self.mom[i.Symbol].MOM.Update(self.Time, i.AdjustedPrice)

        if self.month_start:
            self.selection = True
            self.MOMReady = {symbol: SymbolData for symbol, SymbolData in self.mom.items() if SymbolData.MOM.IsReady}
            if self.MOMReady:
                # sort stocks by 6-month momentum
                sortByMOM = sorted(self.MOMReady, key = lambda x: self.MOMReady[x].MOM.Current.Value, reverse = True)
                self.long = sortByMOM[:20]
                self.short = sortByMOM[-20:]
                return self.long+self.short
            else:
                return []
        else:
            return []

    def rebalance(self):
        # rebalance every month
        self.month_start = True

    def OnData(self, data):
        if self.month_start and self.selection:
            self.month_start = False
            self.selection = False
            if self.long is None or self.short is None: return
            # if the previous 12 months return on the broad equity market was positive
            if self.W5000Return.Current.Value > 0:
                stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
                for i in stocks_invested:
                    if i not in self.long+self.short:
                        self.Liquidate(i)

                short_weight = 0.5/len(self.short)
                # goes short on the prior six-month losers (lowest decile)
                for short_symbol in self.short:
                    self.SetHoldings(short_symbol, -short_weight)
                # goes long on the prior six-month winners (highest decile)
                long_weight = 0.5/len(self.long)
                for long_symbol in self.long:
                    self.SetHoldings(long_symbol, long_weight)
            else:
                self.Liquidate()
                self.SetHoldings(self.tlt, 1)


class Wilshire5000(PythonData):
    "Class to import Wilshire 5000 Total Market Index data from Dropbox"

    def GetSource(self, config, date, isLiveMode):
        return SubscriptionDataSource("https://www.dropbox.com/s/z9rof4fr9cqzgpt/W5000.csv?dl=1", SubscriptionTransportMedium.RemoteFile)

    def Reader(self, config, line, date, isLiveMode):
        if not (line.strip() and line[1].isdigit()): return None
        index = Wilshire5000()
        index.Symbol = config.Symbol
        try:
            # Example File Format: (Data starts from 01/04/2010)
            # Date      Open           High           Low            Close          Adj Close      Volume
            # 1/4/10    11549.13965    11749.37012    11549.13965    11743.54004    11743.54004    0
            data = line.split(',')
            index.Time = datetime.strptime(data[0], "%Y-%m-%d")
            index.Value = Decimal(data[5])
        except:
            return None

        return index

class SymbolData:
    '''Contains data specific to a symbol required by this model'''

    def __init__(self, symbol, lookback):
        self.symbol = symbol
        self.MOM = Momentum(lookback)
