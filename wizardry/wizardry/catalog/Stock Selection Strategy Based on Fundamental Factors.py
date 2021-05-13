class StockSelectionStrategyBasedOnFundamentalFactorsAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2009, 1, 2)  # Set Start Date
        self.SetEndDate(2017, 5, 2)    # Set End Date
        self.SetCash(50000)          # Set Strategy Cash

        self.current_month = -1
        self.coarse_count = 300
        self.fine_count = 10

        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)

        self.SetAlpha(ConstantAlphaModel(InsightType.Price, InsightDirection.Up, timedelta(30)))

        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel(lambda time:None))

    def CoarseSelectionFunction(self, coarse):

        if self.current_month == self.Time.month:
            return Universe.Unchanged

        self.current_month = self.Time.month

        sortedByDollarVolume = sorted([x for x in coarse if x.HasFundamentalData],
            key=lambda x: x.DollarVolume, reverse=True)[:self.coarse_count]

        return [i.Symbol for i in sortedByDollarVolume]

    def FineSelectionFunction(self, fine):

        fine = [x for x in fine if x.EarningReports.TotalDividendPerShare.ThreeMonths
                               and x.ValuationRatios.PriceChange1M
                               and x.ValuationRatios.BookValuePerShare
                               and x.ValuationRatios.FCFYield]

        sortedByfactor1 = sorted(fine, key=lambda x: x.EarningReports.TotalDividendPerShare.ThreeMonths, reverse=True)
        sortedByfactor2 = sorted(fine, key=lambda x: x.ValuationRatios.PriceChange1M, reverse=False)
        sortedByfactor3 = sorted(fine, key=lambda x: x.ValuationRatios.BookValuePerShare, reverse=True)
        sortedByfactor4 = sorted(fine, key=lambda x: x.ValuationRatios.FCFYield, reverse=True)

        stock_dict = {}

        for rank1, ele in enumerate(sortedByfactor1):
            rank2 = sortedByfactor2.index(ele)
            rank3 = sortedByfactor3.index(ele)
            rank4 = sortedByfactor4.index(ele)
            stock_dict[ele] = rank1 + rank2 + rank3 + rank4

        sorted_stock = sorted(stock_dict.items(),
            key=lambda d:d[1], reverse=True)[:self.fine_count]

        return [x[0].Symbol for x in sorted_stock]
