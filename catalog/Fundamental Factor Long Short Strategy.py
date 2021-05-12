#This is a Template of dynamic stock selection.
#You can try your own fundamental factor and ranking method by editing the CoarseSelectionFunction and FineSelectionFunction

from QuantConnect.Data.UniverseSelection import *

class BasicTemplateAlgorithm(QCAlgorithm):

    def __init__(self):
    # set the flag for rebalance
        self.reb = 1
    # Number of stocks to pass CoarseSelection process
        self.num_coarse = 250
    # Number of stocks to long/short
        self.num_fine = 10
        self.symbols = None

    def Initialize(self):
        self.SetCash(100000)
        self.SetStartDate(2015,1,1)
    # if not specified, the Backtesting EndDate would be today
        # self.SetEndDate(2017,1,1)


        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol

        self.UniverseSettings.Resolution = Resolution.Daily

        self.AddUniverse(self.CoarseSelectionFunction,self.FineSelectionFunction)

    # Schedule the rebalance function to execute at the begining of each month
        self.Schedule.On(self.DateRules.MonthStart(self.spy),
        self.TimeRules.AfterMarketOpen(self.spy,5), Action(self.rebalance))


    def CoarseSelectionFunction(self, coarse):
    # if the rebalance flag is not 1, return null list to save time.
        if self.reb != 1:
            return self.long + self.short

    # make universe selection once a month
    # drop stocks which have no fundamental data or have too low prices
        selected = [x for x in coarse if (x.HasFundamentalData)
                    and (float(x.Price) > 5)]

        sortedByDollarVolume = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
        top = sortedByDollarVolume[:self.num_coarse]
        return [i.Symbol for i in top]

    def FineSelectionFunction(self, fine):
    # return null list if it's not time to rebalance
        if self.reb != 1:
            return self.long + self.short

        self.reb = 0

    # drop stocks which don't have the information we need.
    # you can try replacing those factor with your own factors here

        filtered_fine = [x for x in fine if x.OperationRatios.OperationMargin.Value
                                        and x.ValuationRatios.PriceChange1M
                                        and x.ValuationRatios.BookValuePerShare]

        self.Log('remained to select %d'%(len(filtered_fine)))

        # rank stocks by three factor.
        sortedByfactor1 = sorted(filtered_fine, key=lambda x: x.OperationRatios.OperationMargin.Value, reverse=True)
        sortedByfactor2 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.PriceChange1M, reverse=True)
        sortedByfactor3 = sorted(filtered_fine, key=lambda x: x.ValuationRatios.BookValuePerShare, reverse=True)

        stock_dict = {}

        # assign a score to each stock, you can also change the rule of scoring here.
        for i,ele in enumerate(sortedByfactor1):
            rank1 = i
            rank2 = sortedByfactor2.index(ele)
            rank3 = sortedByfactor3.index(ele)
            score = sum([rank1*0.2,rank2*0.4,rank3*0.4])
            stock_dict[ele] = score

        # sort the stocks by their scores
        self.sorted_stock = sorted(stock_dict.items(), key=lambda d:d[1],reverse=False)
        sorted_symbol = [x[0] for x in self.sorted_stock]

        # sotre the top stocks into the long_list and the bottom ones into the short_list
        self.long = [x.Symbol for x in sorted_symbol[:self.num_fine]]
        self.short = [x.Symbol for x in sorted_symbol[-self.num_fine:]]

        return self.long + self.short

    def OnData(self, data):
        pass

    def rebalance(self):
    # if this month the stock are not going to be long/short, liquidate it.
        long_short_list = self.long + self.short
        for i in self.Portfolio.Values:
            if (i.Invested) and (i not in long_short_list):
                self.Liquidate(i.Symbol)

    # Alternatively, you can liquidate all the stocks at the end of each month.
    # Which method to choose depends on your investment philosiphy
    # if you prefer to realized the gain/loss each month, you can choose this method.

        #self.Liquidate()

    # Assign each stock equally. Alternatively you can design your own portfolio construction method
        for i in self.long:
            self.SetHoldings(i, 0.9/self.num_fine)

        for i in self.short:
            self.SetHoldings(i, -0.9/self.num_fine)

        self.reb = 1
