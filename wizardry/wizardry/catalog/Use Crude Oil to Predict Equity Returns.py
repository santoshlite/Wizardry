from datetime import datetime

from clr import AddReference
AddReference("System")
AddReference("QuantConnect.Algorithm")
AddReference("QuantConnect.Indicators")
AddReference("QuantConnect.Common")

from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Data import *
from QuantConnect.Indicators import *
from QuantConnect.Orders import *
from QuantConnect.Securities import *
from QuantConnect.Python import PythonData
import decimal
import numpy as np
from scipy.stats import pearsonr

class CrudeOilPredictsEqeuityReturns(QCAlgorithm):

    def Initialize(self):
        # Set the cash we'd like to use for our backtest
        self.SetCash(100000)

        # Start and end dates for the backtest.
        self.SetStartDate(2010, 1, 1)
        self.SetEndDate(2017, 1, 1)

        # Add assets we'd like to incorporate into our portfolio
        self.oil = self.AddEquity("oil", Resolution.Daily).Symbol
        self.spy = self.AddEquity("spy", Resolution.Daily).Symbol
        self.AddData(TBill, "tbill")
        self.tbill = self.Securities["tbill"].Symbol
        # We may also use imported data from Quandl by using the following comments
        # self.AddData(Oil, "oil")
        # self.oil = self.Securities["oil"].Symbol

        # Number of month in look-back peroid, Number of days in a month
        self.regPeriod = 24
        self.daysInMonth = 21

        # Event is triggered every month
        self.Schedule.On(self.DateRules.MonthStart(self.spy), self.TimeRules.AfterMarketOpen(self.spy),Action(self.MonthlyReg))

    def MonthlyReg(self):
        # Get historical data
        hist = self.History([self.oil, self.spy], self.regPeriod*self.daysInMonth, Resolution.Daily)
        oilSeries = hist.loc[str(self.oil)]['close'][self.daysInMonth-1:self.regPeriod*self.daysInMonth:self.daysInMonth]
        spySeries = hist.loc[str(self.spy)]['close'][self.daysInMonth-1:self.regPeriod*self.daysInMonth:self.daysInMonth]
        rf = float(self.Securities[self.tbill].Price)/12.0

        # Regression analysis and prediction
        x = np.array(oilSeries)
        x = (np.diff(x)/x[:-1])
        y = np.array(spySeries)
        y = (np.diff(y)/y[:-1])
        A = np.vstack([x[:-1],np.ones(len(x[:-1]))]).T
        beta, alpha = np.linalg.lstsq(A,y[1:])[0]
        yPred = alpha + x[-1]*beta

        # Make investment decisions based on regression result
        if yPred > rf:
            self.SetHoldings(self.spy, 1)
        else:
            self.Liquidate(self.spy)

        # Use the following comments to have better understanding of the regression
        # r, p = pearsonr(x[:-1],y[1:])
        # self.Log("Risk free rate {0}".format(rf))
        # self.Log("Beta {0}, Alpha {1}, P-value {2}".format(beta, alpha,p))
        # self.Log("YPred {0}".format(yPred))

    def OnData(self,data):
        pass

class TBill(PythonData):

    def GetSource(self, config, date, isLiveMode):
        # Get the data source from Quandl
        # Ascending order of the data file is essential!
        return SubscriptionDataSource("https://www.quandl.com/api/v3/datasets/USTREASURY/BILLRATES.csv?api_key=zxb6rfszSQW5-SLkaj3t&order=asc", SubscriptionTransportMedium.RemoteFile)

    def Reader(self, config, line, date, isLiveMode):
        tbill = TBill()
        tbill.Symbol = config.Symbol

        # Example Line Format:
        # Date      4 Wk Bank Discount Rate
        # 2017-06-01         0.8
        if not (line.strip() and line[0].isdigit()): return None

        # Parse the file based on how it is organized
        try:
            data = line.split(',')
            value = float(data[1])*0.01
            value = decimal.Decimal(value)
            if value == 0: return None
            tbill.Time = datetime.strptime(data[0], "%Y-%m-%d")
            tbill.Value = value
            tbill["Close"] = float(value)
            return tbill;
        except ValueError:
            return None

# We may also use imported data from Quandl by using the following comments
# class Oil(PythonData):
#     def GetSource(self, config, date, isLiveMode):
#         return SubscriptionDataSource("https://www.quandl.com/api/v3/datasets/OPEC/ORB.csv?order=asc", SubscriptionTransportMedium.RemoteFile)
#     def Reader(self, config, line, date, isLiveMode):
#         oil = Oil()
#         oil.Symbol = config.Symbol
#         if not (line.strip() and line[0].isdigit()): return None
#         try:
#             data = line.split(',')
#             value = float(data[1])
#             value = decimal.Decimal(value)
#             if value == 0: return None
#             oil.Time = datetime.strptime(data[0], "%Y-%m-%d")
#             oil.Value = value
#             oil["Close"] = float(value)
#             return oil;
#         except ValueError:
#             return None
