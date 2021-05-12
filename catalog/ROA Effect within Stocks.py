# https://quantpedia.com/Screener/Details/199
class ROAEffectWithinStocks(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2014, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(10000000)
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.Rebalance)
        self.monthly_rebalance = False
        self.coarse = False
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)

    def CoarseSelectionFunction(self, coarse):
        if self.monthly_rebalance:
            self.coarse = True
            filteredCoarse = [x.Symbol for x in coarse if x.HasFundamentalData]
            return filteredCoarse
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.monthly_rebalance:
            fine =[i for i in fine if i.EarningReports.BasicAverageShares.ThreeMonths != 0
                                  and i.EarningReports.BasicEPS.TwelveMonths != 0
                                  and i.ValuationRatios.PERatio != 0
                                  # sales is greater than 10 million
                                  and i.ValuationRatios.SalesPerShare*i.EarningReports.DilutedAverageShares.Value > 10000000
                                  and i.OperationRatios.ROA.Value != 0]
            for i in fine:
                i.MarketCap = float(i.EarningReports.BasicAverageShares.ThreeMonths * (i.EarningReports.BasicEPS.TwelveMonths*i.ValuationRatios.PERatio))
            # sort into 2 halfs based on market capitalization
            sorted_market_cap = sorted(fine, key = lambda x:x.MarketCap, reverse=True)
            top = sorted_market_cap[:int(len(sorted_market_cap)*0.5)]
            bottom = sorted_market_cap[-int(len(sorted_market_cap)*0.5):]
            # each half is then divided into deciles based on Return on Assets (ROA)
            sortedTopByROA = sorted(top, key = lambda x: x.OperationRatios.ROA.Value, reverse = True)
            sortedBottomByROA = sorted(bottom, key = lambda x: x.OperationRatios.ROA.Value, reverse = True)
            # long top decile from each market capitalization group
            long = sortedTopByROA[:int(len(sortedTopByROA)*0.1)] + sortedBottomByROA[:int(len(sortedTopByROA)*0.1)]
            self.longStocks = [i.Symbol for i in long]
            # short bottom decile from each market capitalization group
            short = sortedTopByROA[-int(len(sortedTopByROA)*0.1):] + sortedBottomByROA[-int(len(sortedTopByROA)*0.1):]
            self.shortStocks = [i.Symbol for i in short]

            return self.longStocks+self.shortStocks
        else:
            return []

    def Rebalance(self):
        self.monthly_rebalance = True

    def OnData(self, data):
        if not (self.monthly_rebalance and self.coarse): return
        self.coarse = False
        self.monthly_rebalance = False
        stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        for i in stocks_invested:
            if i not in self.longStocks+self.shortStocks:
                self.Liquidate(i)

        long_weight = 0.5/len(self.longStocks)
        for i in self.longStocks:
            self.SetHoldings(i, long_weight)

        short_weight = 0.5/len(self.shortStocks)
        for i in self.shortStocks:
            self.SetHoldings(i, -short_weight)
