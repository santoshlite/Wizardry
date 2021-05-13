from NodaTime import DateTimeZone
from QuantConnect.Python import PythonQuandl
from decimal import Decimal

class GoldMarketTimingAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2010, 1, 1)
        self.SetEndDate(2015, 1, 1)
        self.SetCash(100000)
        # United States Government 10-Year Bond Yield
        self.bond_yield = "YC/USA10Y"
        # S&P 500 Earnings Yield. Earnings Yield = trailing 12 month earnings divided by index price
        self.earnings_yield = "MULTPL/SP500_EARNINGS_YIELD_MONTH"
        # Gold Prices (Daily) - Currency USD (All values are national currency units per troy ounce)
        self.gold = "WGC/GOLD_DAILY_USD"
        # Add custom quandl data
        self.AddData(QuandlRate, self.bond_yield, Resolution.Daily, DateTimeZone.Utc, True)
        self.AddData(QuandlValue, self.earnings_yield, Resolution.Daily, DateTimeZone.Utc, True)
        self.AddData(QuandlValue, self.gold, Resolution.Daily, DateTimeZone.Utc, True)
        self.AddEquity("SPY", Resolution.Daily)
        # Monthly rebalance
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.Rebalance)
        # Chart
        yieldPlot = Chart("Yield Plot")
        yieldPlot.AddSeries(Series("BondYield", SeriesType.Line, 0))
        yieldPlot.AddSeries(Series("EarningsYield", SeriesType.Line, 0))
        self.AddChart(yieldPlot)

    def OnData(self, data):
        if data.ContainsKey(self.bond_yield) and data.ContainsKey(self.earnings_yield):
            self.Plot("Yield Plot", "BondYield", data[self.bond_yield].Price)
            self.Plot("Yield Plot", "EarningsYield", data[self.earnings_yield].Price)

    def Rebalance(self):
        if self.Securities[self.earnings_yield].Price == 0 or self.Securities[self.bond_yield].Price == 0: return
        # Buy gold if E/P is higher than the bond yield and their ratio is at least 2
        if self.Securities[self.earnings_yield].Price > self.Securities[self.bond_yield].Price * Decimal(2):
            self.SetHoldings(self.gold, 0.9)
        else:
            self.Liquidate()

class QuandlRate(PythonQuandl):

    def __init__(self):
        self.ValueColumnName = "rate"

class QuandlValue(PythonQuandl):

    def __init__(self):
        self.ValueColumnName = "Value"
