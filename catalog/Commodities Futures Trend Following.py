from QuantConnect.Python import PythonQuandl
import numpy as np

class CommodityFutureTrendFollowing(QCAlgorithm):
    '''
    Two Centuries of Trend Following

    This paper demonstrates the existence of anomalous excess returns based on trend following strategies
    across commodities, currencies, stock indices, and bonds, and over very long time scales.

    Reference:
    [1] Y. Lempérière, C. Deremble, P. Seager, M. Potters, J. P. Bouchaud, "Two centuries of trend following", April 15, 2014.
        URL: https://arxiv.org/pdf/1404.3274.pdf
    '''
    def Initialize(self):

        self.SetStartDate(1998,1, 1)
        self.SetEndDate(2019, 9, 1)
        self.SetCash(25000)

        tickers = ["CHRIS/CME_W1",   # Wheat Futures, Continuous Contract #1
                   "CHRIS/CME_C1",   # Corn Futures, Continuous Contract #1
                   "CHRIS/CME_LC1",  # Live Cattle Futures, Continuous Contract #1
                   "CHRIS/CME_CL1",  # Crude Oil Futures, Continuous Contract #1
                   "CHRIS/CME_NG1",  # Natural Gas (Henry Hub) Physical Futures, Continuous Contract #1
                   "CHRIS/LIFFE_W1", # White Sugar Future, Continuous Contract #1
                   "CHRIS/CME_HG1"]  # Copper Futures, Continuous Contract #1

        # Container to store the SymbolData object for each security
        self.Data = {}

        for ticker in tickers:
            # Add Quandl data and set desired leverage
            data = self.AddData(QuandlFutures, ticker, Resolution.Daily)
            data.SetLeverage(3)

            # Create a monthly consolidator for each security
            self.Consolidate(data.Symbol, CalendarType.Monthly, self.CalendarHandler)

            # Create a SymbolData object for each security to store relevant indicators
            # and calculate quantity of contracts to Buy/Sell
            self.Data[data.Symbol] = SymbolData()

        # Set decay rate equal to 5 months (150 days) and warm up period
        self.SetWarmUp(150)

        # Set monthly rebalance
        self.nextRebalance = self.Time

    def CalendarHandler(self, bar):
        '''
        Event Handler that updates the SymbolData object for each security when a new monthly bar becomes available
        '''
        self.Data[bar.Symbol].Update(bar)

    def OnData(self, data):
        '''
        Buy/Sell security every month
        '''
        if self.Time < self.nextRebalance or self.IsWarmingUp:
            return

        for symbol in data.Keys:
            symbolData = self.Data[symbol]
            if symbolData.Quantity != 0:
                self.MarketOrder(symbol, symbolData.Quantity)

        self.nextRebalance = Expiry.EndOfMonth(self.Time)


class QuandlFutures(PythonQuandl):
    def __init__(self):
        self.ValueColumnName = "Settle"


class SymbolData:
    '''
    Contains the relevant indicators used to calculate number of contracts to Buy/Sell
    '''
    def __init__(self):
        self.ema = ExponentialMovingAverage("MonthEMA", 5)

        # Volatility estimation is defined as the EMA of absolute monthly price changes
        # Use Momentum indicator to get absolute monthly price changes
        # Then use the IndicatorExtensions.EMA and pass the momentum indicator values to get the volatility
        self.mom = Momentum("MonthMOM", 1)
        # Note: self.vol will automatically be updated with self.mom
        self.vol = IndicatorExtensions.EMA(self.mom, 5)

        self.Quantity = 0


    def Update(self, bar):
        self.ema.Update(bar.Time, bar.Value)
        self.mom.Update(bar.Time, bar.Value)

        if self.ema.IsReady and self.vol.IsReady:
            # Equation 1 in [1]
            signal = (bar.Value - self.ema.Current.Value) / self.vol.Current.Value
            # Equation 2 in [1]
            self.Quantity = np.sign(signal)/abs(self.vol.Current.Value)

        return self.Quantity != 0
