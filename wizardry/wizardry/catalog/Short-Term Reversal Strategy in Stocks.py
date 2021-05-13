from clr import AddReference
AddReference("System.Core")
AddReference("System.Collections")
AddReference("QuantConnect.Common")
AddReference("QuantConnect.Algorithm")
import statistics
from datetime import datetime
from System.Collections.Generic import List

class ShortTimeReversal(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2005, 1, 1)
        self.SetEndDate(2017, 5, 10)
        self.SetCash(1000000)

        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction)
        self._numberOfSymbols = 100
        self._numberOfTradings = int(0.1 * self._numberOfSymbols)

        self._numOfWeeks = 0
        self._LastDay = -1
        self._ifWarmUp = False

        self._stocks = []
        self._values = {}

    def CoarseSelectionFunction(self, coarse):
        sortedByDollarVolume = sorted(coarse, key=lambda x: x.DollarVolume, reverse=True)
        top100 = sortedByDollarVolume[:self._numberOfSymbols]
        return [i.Symbol for i in top100]

    def OnData(self, data):

        if not self._ifWarmUp:
            if self._LastDay == -1:
                self._LastDay = self.Time.date()
                self._stocks = []
                self.uni_symbol = None
                symbols = self.UniverseManager.Keys
                for i in symbols:
                    if str(i.Value) == "QC-UNIVERSE-COARSE-USA":
                        self.uni_symbol = i
                for i in self.UniverseManager[self.uni_symbol].Members:
                    self._stocks.append(i.Value.Symbol)
                    self._values[i.Value.Symbol] = [self.Securities[i.Value.Symbol].Price]
            else:
                delta = self.Time.date() - self._LastDay
                if delta.days >= 7:
                    self._LastDay = self.Time.date()
                    for stock in self._stocks:
                        self._values[stock].append(self.Securities[stock].Price)
            self._numOfWeeks += 1
            if self._numOfWeeks == 3:
                self._ifWarmUp = True
        else:
            delta = self.Time.date() - self._LastDay
            if delta.days >= 7:
                self._LastDay = self.Time.date()

                returns = {}
                for stock in self._stocks:
                    newPrice = self.Securities[stock].Price
                    oldPrice = self._values[stock].pop(0)
                    self._values[stock].append(newPrice)
                    try:
                        returns[stock] = newPrice/oldPrice
                    except:
                        returns[stock] = 0

                newArr = [(v,k) for k,v in returns.items()]
                newArr.sort()
                for ret, stock in newArr[self._numberOfTradings:-self._numberOfTradings]:
                    if self.Portfolio[stock].Invested:
                        self.Liquidate(stock)
                for ret, stock in newArr[0:self._numberOfTradings]:
                    self.SetHoldings(stock, 0.5/self._numberOfTradings)
                for ret, stock in newArr[-self._numberOfTradings:]:
                    self.SetHoldings(stock, -0.5/self._numberOfTradings)
                self._LastDay = self.Time.date()
