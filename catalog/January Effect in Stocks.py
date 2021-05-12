class JanuaryEffectInStocksAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2008, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(100000)
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.Rebalance)
        self.monthly_rebalance = False
        self.coarse = False
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)

    def CoarseSelectionFunction(self, coarse):
        if self.monthly_rebalance:
            self.coarse = True
            coarse = [x for x in coarse if (x.AdjustedPrice > 10)]
            topDollarVolume = sorted(coarse, key=lambda x: x.DollarVolume, reverse=True)[:1000]
            return [i.Symbol for i in topDollarVolume]
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.monthly_rebalance:
            fine =[i for i in fine if i.EarningReports.BasicAverageShares.ThreeMonths!=0
                                  and i.EarningReports.BasicEPS.TwelveMonths!=0
                                  and i.ValuationRatios.PERatio!=0]
            for i in fine:
                i.MarketCap = float(i.EarningReports.BasicAverageShares.ThreeMonths * (i.EarningReports.BasicEPS.TwelveMonths*i.ValuationRatios.PERatio))
            sorted_market_cap = sorted(fine, key = lambda x:x.MarketCap, reverse=True)
            symbols = [i.Symbol for i in sorted_market_cap]
            self.top_market_cap = symbols[:10]
            self.bottom_market_cap = symbols[-10:]
            return self.top_market_cap + self.bottom_market_cap
        else:
            return []

    def Rebalance(self):
        self.monthly_rebalance = True


    def OnData(self, data):
        if not (self.monthly_rebalance and self.coarse): return
        self.coarse = False
        self.monthly_rebalance = False
        stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        # invest in small cap stocks at the beginning of each January
        if self.Time.month == 1:
          # liquidate stocks not in the small-cap group
          for i in stocks_invested:
              if i not in self.bottom_market_cap:
                  self.Liquidate(i)
          weight = 1/len(self.bottom_market_cap)
          for i in self.bottom_market_cap:
              self.SetHoldings(i, weight)
        # invest in large cap stocks for rest of the year
        else:
          # liquidate stocks not in the large-cap group
          for i in stocks_invested:
              if i not in self.top_market_cap:
                  self.Liquidate(i)

          weight = 1/len(self.top_market_cap)
          for i in self.top_market_cap:
              self.SetHoldings(i, weight)
