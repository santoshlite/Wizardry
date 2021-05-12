# https://quantpedia.com/Screener/Details/21
# The futures data is non-adjusted price based on spot-month continuous contract calculations.
# Raw data from ICE and CM

from QuantConnect.Python import PythonQuandl
from datetime import timedelta
class CommidityMomentumEffect(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2008,1, 1)
        self.SetEndDate(2018, 7, 1)
        self.SetCash(25000)
        self.cme_symbols = ["CHRIS/CME_S1", # Soybean Futures, Continuous Contract #1
                            "CHRIS/CME_W1", # Wheat Futures, Continuous Contract #1
                            "CHRIS/CME_SM1", # Soybean Meal Futures, Continuous Contract #1
                            "CHRIS/CME_BO1", # Soybean Oil Futures, Continuous Contract #1
                            "CHRIS/CME_C1", # Corn Futures, Continuous Contract #1
                            "CHRIS/CME_O1", # Oats Futures, Continuous Contract #1
                            "CHRIS/CME_LC1", # Live Cattle Futures, Continuous Contract #1
                            "CHRIS/CME_FC1", # Feeder Cattle Futures, Continuous Contract #1
                            "CHRIS/CME_LN1", # Lean Hog Futures, Continuous Contract #1
                            "CHRIS/CME_GC1", # Gold Futures, Continuous Contract #1
                            "CHRIS/CME_SI1", # Silver Futures, Continuous Contract #1
                            "CHRIS/CME_PL1", # Platinum Futures, Continuous Contract #1
        ]
        self.ice_symbols = ["CHRIS/ICE_B1", # Brent Crude Futures, Continuous Contract
                            "CHRIS/ICE_O1", # Heating Oil Futures, Continuous Contract #1
                            "CHRIS/ICE_M1", # UK Natural Gas Futures, Continuous Contract #1
                            "CHRIS/ICE_CT1", # Cotton No. 2 Futures, Continuous Contract
                            "CHRIS/ICE_OJ1", # Orange Juice Futures, Continuous Contract
                            "CHRIS/ICE_KC1", # Coffee C Futures, Continuous Contract
                            "CHRIS/ICE_CC1", # Cocoa Futures, Continuous Contract
                            "CHRIS/ICE_G1", # Gas Oil Futures, Continuous Contract
                            "CHRIS/ICE_RS1", # Canola Futures, Continuous Contract
                            ]
        period = 252
        self.symbols = self.cme_symbols + self.ice_symbols
        self.roc = {}
        for symbol in self.symbols:
            self.AddData(QuandlFutures, symbol, Resolution.Daily)
            self.roc[symbol] = RateOfChange(period)
            hist = self.History([symbol], 400, Resolution.Daily).loc[symbol]
            for i in hist.itertuples():
                self.roc[symbol].Update(i.Index, i.value)
        # Rebalance the portfolio every month
        self.Schedule.On(self.DateRules.MonthStart("CHRIS/CME_S1"), self.TimeRules.AfterMarketOpen("CHRIS/CME_S1"), self.Rebalance)


    def OnData(self, data):
        # Update the indicator value every day
        for symbol in self.symbols:
            if data.ContainsKey(symbol) and self.roc[symbol].IsReady:
                self.roc[symbol].Update(self.Time, data[symbol].Value)


    def Rebalance(self):
        # sorted futures by 12-month return reversely
        self.sorted_roc = sorted(self.roc, key = lambda x: self.roc[x].Current.Value, reverse=True)
        number_futures = int(0.25*len(self.sorted_roc))
        if number_futures == 0:
            number_futures = int(0.4*len(self.sorted_roc))

        self.long = self.sorted_roc[:number_futures]
        self.short = self.sorted_roc[-number_futures:]

        for kvp in self.Portfolio:
            security_hold = kvp.Value
            # liquidate the futures which is no longer in the trading list
            if security_hold.Invested and (security_hold.Symbol.Value not in (self.long+self.short)):
                self.Liquidate(security_hold.Symbol)

        for long in self.long:
            self.SetHoldings(long, 0.5/number_futures)
        for short in self.short:
            self.SetHoldings(short, -0.5/number_futures)

class QuandlFutures(PythonQuandl):

    def __init__(self):
        self.ValueColumnName = "Settle"
