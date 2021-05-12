# https://quantpedia.com/Screener/Details/51

import numpy as np
class MomentumShortTermReversalAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2004,1,1)
        self.SetEndDate(2018,5,10)
        self.SetCash(100000)

        self.UniverseSettings.Resolution = Resolution.Daily

        self.AddEquity("SPY", Resolution.Daily)
        self.AddUniverse(self.CoarseSelectionFunction)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.At(0, 0), self.Rebalance)
        self.month_start = False
        self.coarse = False
        self.SymbolPrice = {}
        self.decrease_winner = None
        self.increase_loser = None



    def CoarseSelectionFunction(self, coarse):
        if self.month_start:
            self.coarse = True
            # coarse = [i for i in coarse if i.AdjustedPrice > 5]
            for i in coarse:
                if i.Symbol not in self.SymbolPrice:
                    self.SymbolPrice[i.Symbol] = SymbolData(i.Symbol)

                self.SymbolPrice[i.Symbol].window.Add(float(i.AdjustedPrice))
                if self.SymbolPrice[i.Symbol].window.IsReady:
                    price = np.array([i for i in self.SymbolPrice[i.Symbol].window])
                    returns = (price[:-1]-price[1:])/price[1:]
                    self.SymbolPrice[i.Symbol].yearly_return = (price[0]-price[-1])/price[-1]
                    GARR_12 = np.prod([(1+i)**(1/12) for i in returns])-1
                    GARR_1 = (1+returns[0])**(1/12)-1
                    self.SymbolPrice[i.Symbol].GARR_ratio = GARR_1 / GARR_12

            ReadySymbolPrice = {symbol: SymbolData for symbol, SymbolData in self.SymbolPrice.items() if SymbolData.window.IsReady}
            if ReadySymbolPrice and len(ReadySymbolPrice)>50:
                sorted_by_return = sorted(ReadySymbolPrice, key = lambda x: ReadySymbolPrice[x].yearly_return, reverse = True)
                winner = sorted_by_return[:int(len(sorted_by_return)*0.3)]
                loser = sorted_by_return[-int(len(sorted_by_return)*0.3):]
                self.decrease_winner = sorted(winner, key = lambda x: ReadySymbolPrice[x].GARR_ratio)[:15]
                self.increase_loser = sorted(loser, key = lambda x: ReadySymbolPrice[x].GARR_ratio)[-15:]
                return self.decrease_winner+self.increase_loser
            else:
                return []
        else:
            return []


    def OnData(self, data):
        if self.month_start and self.coarse:
            self.month_start = False
            self.coarse = False

            if all([self.decrease_winner, self.increase_loser]):

                stocks_invested = [x.Key for x in self.Portfolio]
                for i in stocks_invested:
                    if i not in self.decrease_winner+self.increase_loser:
                        self.Liquidate(i)

                short_weight = 0.5/len(self.increase_loser)
                for j in self.increase_loser:
                    self.SetHoldings(j, -short_weight)

                long_weight = 0.5/len(self.decrease_winner)
                for i in self.decrease_winner:
                    self.SetHoldings(i, long_weight)


    def Rebalance(self):
        self.month_start = True


class SymbolData:
    def __init__(self, symbol):
        self.symbol = symbol
        self.window = RollingWindow[float](13)
        self.GARR_ratio = None
        self.yearly_return = None
