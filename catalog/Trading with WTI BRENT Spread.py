# https://quantpedia.com/Screener/Details/100
from QuantConnect.Data import SubscriptionDataSource
from QuantConnect.Python import PythonData
from datetime import date, timedelta, datetime
from decimal import Decimal
import numpy as np
from sklearn import datasets, linear_model

class TradeWtiBrentSpreadAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2009, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(100000)
        # import the custom data
        self.AddData(WTI, "WTI", Resolution.Daily)
        self.AddData(BRENT, "BRENT", Resolution.Daily)
        # create the moving average indicator of the pread = WTI price - BRENT price
        self.SpreadSMA = SimpleMovingAverage(20)
        hist = self.History(["WTI", "BRENT"], 400, Resolution.Daily)["value"].unstack(level=0).dropna()
        hist_20days = hist[-20:]
        spread = (hist_20days["WTI"] - hist_20days["BRENT"]).dropna()
        for index, value in spread.items():
            self.SpreadSMA.Update(index, value)
        # linear regression to decide the fair value
        hist_one_year = hist[-252:]
        X = hist_one_year["WTI"][:, np.newaxis]
        y = hist_one_year["BRENT"]
        self.regr = linear_model.LinearRegression()
        self.regr.fit(X, y)

        # Add the spread plot and mark the long/short spread point
        spreadPlot = Chart("Spread Plot")
        spreadPlot.AddSeries(Series("Spread", SeriesType.Line, 0))
        spreadPlot.AddSeries(Series("Long Spread Trade", SeriesType.Scatter, 0))
        spreadPlot.AddSeries(Series("Short Spread Trade", SeriesType.Scatter, 0))
        self.AddChart(spreadPlot)

    def OnData(self, data):
        if not (data.ContainsKey("WTI") and data.ContainsKey("BRENT")): return
        self.Plot("Spread Plot", "Spread", data["WTI"].Price - data["BRENT"].Price)

        self.SpreadSMA.Update(self.Time, data["WTI"].Price - data["BRENT"].Price)
        if not self.SpreadSMA.IsReady: return
        spread = self.Securities["WTI"].Price - self.Securities["BRENT"].Price
        fair_value =self.Securities["WTI"].Price - Decimal(self.regr.predict([[self.Securities["WTI"].Price]])[0])

        if spread > self.SpreadSMA.Current.Value and not (self.Portfolio["WTI"].IsShort and self.Portfolio["BRENT"].IsLong):
            self.Log("spread > self.SpreadSMA.Current.Value")
            self.SetHoldings("WTI", -0.5)
            self.SetHoldings("BRENT", 0.5)
            self.Plot("Spread Plot", "Long Spread Trade", data["WTI"].Price - data["BRENT"].Price)


        elif spread < self.SpreadSMA.Current.Value and not (self.Portfolio["WTI"].IsLong and self.Portfolio["BRENT"].IsShort):
            self.Log("spread < self.SpreadSMA.Current.Value")
            self.SetHoldings("WTI", 0.5)
            self.SetHoldings("BRENT", -0.5)
            self.Plot("Spread Plot", "Short Spread Trade", data["WTI"].Price - data["BRENT"].Price)

        if self.Portfolio["WTI"].IsShort and self.Portfolio["BRENT"].IsLong and spread < fair_value:
            self.Liquidate()


        if self.Portfolio["WTI"].IsLong and self.Portfolio["BRENT"].IsShort and spread > fair_value:
            self.Liquidate()


class WTI(PythonData):
    "Class to import WTI Spot Price(Dollars per Barrel) data from Dropbox"

    def GetSource(self, config, date, isLiveMode):
        return SubscriptionDataSource("https://www.dropbox.com/s/jpie3z6j0stp97d/wti-crude-oil-prices-10-year-daily.csv?dl=1", SubscriptionTransportMedium.RemoteFile)

    def Reader(self, config, line, date, isLiveMode):
        if not (line.strip() and line[1].isdigit()): return None
        index = WTI()
        index.Symbol = config.Symbol
        try:
            # Example File Format: (Data starts from 08/11/2008)
            # date     value
            # 8/11/08    114.44
            data = line.split(',')
            index.Time = datetime.strptime(data[0], "%Y-%m-%d")
            index.Value = Decimal(data[1])
        except:
            return None

        return index

class BRENT(PythonData):
    "Class to import BRENT Spot Price(Dollars per Barrel) data from Dropbox"

    def GetSource(self, config, date, isLiveMode):
        return SubscriptionDataSource("https://www.dropbox.com/s/w380c4n7xjmdqxl/brent-crude-oil-prices-10-year-daily.csv?dl=1", SubscriptionTransportMedium.RemoteFile)

    def Reader(self, config, line, date, isLiveMode):
        if not (line.strip() and line[1].isdigit()): return None
        index = BRENT()
        index.Symbol = config.Symbol
        try:
            # Example File Format: (Data starts from 08/11/2008)
            # date     value
            # 8/11/08    110.54
            data = line.split(',')
            index.Time = datetime.strptime(data[0], "%Y-%m-%d")
            index.Value = Decimal(data[1])
        except:
            return None

        return index
