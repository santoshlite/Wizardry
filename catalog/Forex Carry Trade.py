# The official interest rate is from Quandl
from QuantConnect.Python import PythonQuandl
from NodaTime import DateTimeZone


class ForexCarryTradeAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2008, 1, 1)
        self.SetEndDate(2018, 1, 1)
        self.SetCash(25000)

        tickers = ["USDEUR", "USDZAR", "USDAUD",
                   "USDJPY", "USDTRY", "USDINR",
                   "USDCNY", "USDMXN", "USDCAD"]

        rate_symbols = ["BCB/17900",  # Euro Area
                        "BCB/17906",  # South Africa
                        "BCB/17880",  # Australia
                        "BCB/17903",  # Japan
                        "BCB/17907",  # Turkey
                        "BCB/17901",  # India
                        "BCB/17899",  # China
                        "BCB/17904",  # Mexico
                        "BCB/17881"]  # Canada

        self.symbols = {}
        for i in range(len(tickers)):
            symbol = self.AddForex(tickers[i], Resolution.Daily, Market.Oanda).Symbol
            self.AddData(QuandlRate, rate_symbols[i], Resolution.Daily, DateTimeZone.Utc, True)
            self.symbols[str(symbol)] = rate_symbols[i]

        self.Schedule.On(self.DateRules.MonthStart("USDEUR"), self.TimeRules.AfterMarketOpen("USDEUR"), Action(self.Rebalance))

    def Rebalance(self):
        top_symbols = sorted(self.symbols, key = lambda x: self.Securities[self.symbols[x]].Price)

        self.SetHoldings(top_symbols[0], -0.5)
        self.SetHoldings(top_symbols[-1], 0.5)

    def OnData(self, data):
        pass

class QuandlRate(PythonQuandl):

    def __init__(self):
        self.ValueColumnName = 'Value'
