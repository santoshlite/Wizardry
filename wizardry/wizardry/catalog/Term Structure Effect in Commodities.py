# http://quantpedia.com/Screener/Details/22
from datetime import timedelta
from math import floor
from decimal import Decimal
import numpy as np

class CommodityTermStructureAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2018, 7, 1)
        self.SetCash(1000000)
        tickers = [
                Futures.Softs.Cocoa,
                Futures.Softs.Coffee,
                Futures.Grains.Corn,
                Futures.Softs.Cotton2,
                Futures.Grains.Oats,
                Futures.Softs.OrangeJuice,
                Futures.Grains.SoybeanMeal,
                Futures.Grains.SoybeanOil,
                Futures.Grains.Soybeans,
                Futures.Softs.Sugar11,
                Futures.Grains.Wheat,
                Futures.Meats.FeederCattle,
                Futures.Meats.LeanHogs,
                Futures.Meats.LiveCattle,
                Futures.Energies.CrudeOilWTI,
                Futures.Energies.HeatingOil,
                Futures.Energies.NaturalGas,
                Futures.Energies.Gasoline,
                Futures.Metals.Gold,
                Futures.Metals.Palladium,
                Futures.Metals.Platinum,
                Futures.Metals.Silver
            ]
        for ticker in tickers:
            future = self.AddFuture(ticker)
            future.SetFilter(timedelta(0), timedelta(days = 90))
        self.chains = {}
        self.AddEquity("SPY", Resolution.Minute)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY", 30), self.Rebalance)

    def OnData(self,slice):
        # Saves the Futures Chains
        for chain in slice.FutureChains:
            if chain.Value.Contracts.Count < 2:
                continue
            if chain.Value.Symbol.Value not in self.chains:
                self.chains[chain.Value.Symbol.Value] =  [i for i in chain.Value]

            self.chains[chain.Value.Symbol.Value] = [i for i in chain.Value]


    def Rebalance(self):

        self.Liquidate()
        quintile = floor(len(self.chains)/5)
        roll_returns = {}
        for symbol, chain in self.chains.items():
            contracts = sorted(chain, key = lambda x: x.Expiry)

            # R = (log(Pn) - log(Pd)) * 365 / (Td - Tn)
            # R - Roll returns
            # Pn - Nearest contract price
            # Pd - Distant contract price
            # Tn - Nearest contract expire date
            # Pd - Distant contract expire date

            near_contract = contracts[0]
            distant_contract = contracts[-1]
            price_near = near_contract.LastPrice if near_contract.LastPrice>0 else 0.5*float(near_contract.AskPrice+near_contract.BidPrice)
            price_distant = distant_contract.LastPrice if distant_contract.LastPrice>0 else 0.5*float(distant_contract.AskPrice+distant_contract.BidPrice)

            if distant_contract.Expiry == near_contract.Expiry:
                self.Debug("ERROR: Near and distant contracts have the same expiry!" + str(near_contract))
                return
            expire_range = 365 / (distant_contract.Expiry - near_contract.Expiry).days
            roll_returns[symbol] = (np.log(float(price_near)) - np.log(float(price_distant)))*expire_range
            positive_roll_returns = { symbol: returns for symbol, returns in roll_returns.items() if returns > 0 }
            negative_roll_returns = { symbol: returns for symbol, returns in roll_returns.items() if returns < 0 }

        backwardation = sorted(positive_roll_returns , key = lambda x: positive_roll_returns[x], reverse = True)[:quintile]
        contango = sorted(negative_roll_returns , key = lambda x: negative_roll_returns[x])[:quintile]
        count = min(len(backwardation), len(contango))
        if  count != quintile:
            backwardation = backwardation[:count]
            contango = contango[:count]

        #  We cannot long-short if count is zero
        if count == 0:
            self.chains = {}
            return

        for short_symbol in contango:
            sort = sorted(self.chains[short_symbol], key = lambda x: x.Expiry)
            self.SetHoldings(sort[1].Symbol, -0.5/count)

        for long_symbol in backwardation:
            sort = sorted(self.chains[long_symbol], key = lambda x: x.Expiry)
            self.SetHoldings(sort[1].Symbol, 0.5/count)


        self.chains = {}
