# https://quantpedia.com/Screener/Details/20
from datetime import timedelta
from decimal import Decimal

class BullCallSpreadAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2017, 1, 1)
        self.SetEndDate(2017, 6, 1)
        self.SetCash(50000)
        equity = self.AddEquity("SPY", Resolution.Minute)
        option = self.AddOption("SPY", Resolution.Minute)
        self.symbol = equity.Symbol
        option.SetFilter(self.UniverseFunc)
        self.SetBenchmark(equity.Symbol)

    def OnData(self,slice):

        for i in slice.OptionChains:
            chains = i.Value
            if not self.Portfolio.Invested:
                # divide option chains into call and put options
                calls = list(filter(lambda x: x.Right == OptionRight.Call, chains))
                puts = list(filter(lambda x: x.Right == OptionRight.Put, chains))
                # if lists are empty return
                if not calls or not puts: return
                underlying_price = self.Securities[self.symbol].Price
                expiries = [i.Expiry for i in puts]
                # determine expiration date nearly one month
                expiry = min(expiries, key=lambda x: abs((x.date()-self.Time.date()).days-30))
                strikes = [i.Strike for i in puts]
                # determine at-the-money strike
                strike = min(strikes, key=lambda x: abs(x-underlying_price))
                # determine 15% out-of-the-money strike
                otm_strike = min(strikes, key = lambda x:abs(x-Decimal(0.85)*underlying_price))
                self.atm_call = [i for i in calls if i.Expiry == expiry and i.Strike == strike]
                self.atm_put = [i for i in puts if i.Expiry == expiry and i.Strike == strike]
                self.otm_put = [i for i in puts if i.Expiry == expiry and i.Strike == otm_strike]

                if self.atm_call and self.atm_put and self.otm_put:
                    # sell at-the-money straddle
                    self.Sell(self.atm_call[0].Symbol, 1)
                    self.Sell(self.atm_put[0].Symbol, 1)
                    # buy 15% out-of-the-money put
                    self.Buy(self.otm_put[0].Symbol, 1)

            if self.Portfolio[self.symbol].Invested:
                self.Liquidate(self.symbol)

    def OnOrderEvent(self, orderEvent):
        self.Log(str(orderEvent))

    def UniverseFunc(self, universe):
        return universe.IncludeWeeklys().Strikes(-20, 20).Expiration(timedelta(25), timedelta(35))
