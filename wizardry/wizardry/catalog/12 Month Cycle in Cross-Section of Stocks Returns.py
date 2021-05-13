class TwelveMonthCycle(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2013, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(100000)
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.Rebalance)
        self.monthly_rebalance = False
        self.filtered_fine = None
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)

    def CoarseSelectionFunction(self, coarse):
        if self.monthly_rebalance:
            coarse = [x for x in coarse if (x.HasFundamentalData)
                                        and (x.Market == "usa")]

            return [i.Symbol for i in coarse]
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.monthly_rebalance:
            fine =[i for i in fine if ((i.SecurityReference.ExchangeId == "NYS") or (i.SecurityReference.ExchangeId == "ASE"))]
            self.filtered_fine = []

            for i in fine:
                i.MarketCap = float(i.EarningReports.BasicAverageShares.TwelveMonths * (i.EarningReports.BasicEPS.TwelveMonths*i.ValuationRatios.PERatio))
                history_start = self.History([i.Symbol], TimeSpan.FromDays(365))
                history_end = self.History([i.Symbol],TimeSpan.FromDays(335))
                if not history_start.empty and not history_end.empty:
                    i.Returns = float(history_end.iloc[0]["close"] - history_start.iloc[0]["close"])
                    self.filtered_fine.append(i)

            size = int(len(fine)*.3)
            self.filtered_fine = sorted(self.filtered_fine, key = lambda x: x.MarketCap, reverse=True)
            self.filtered_fine = self.filtered_fine[:size]
            self.filtered_fine = sorted(self.filtered_fine, key = lambda x: x.Returns, reverse=True)
            symbols = [i.Symbol for i in self.filtered_fine]
            self.filtered_fine = symbols
            return symbols
        else:
            return []

    def Rebalance(self):
        self.monthly_rebalance = True


    def OnData(self, data):
        if not (self.monthly_rebalance): return
        if not (self.filtered_fine): return
        self.monthly_rebalance = False

        portfolio_size = int(len(self.filtered_fine)/10)
        short_stocks = self.filtered_fine[-portfolio_size:]
        long_stocks = self.filtered_fine[:portfolio_size]
        stocks_invested = [x.Key for x in self.Portfolio]
        for i in stocks_invested:
            #liquidate the stocks not in the filtered balance sheet accrual list
            if i not in self.filtered_fine:
                self.Liquidate(i)
            #long the stocks in the list
            elif i in long_stocks:
                self.SetHoldings(i, 1/(portfolio_size*2))
            #short the stocks in the list
            elif i in short_stocks:
                self.SetHoldings(i,-1/(portfolio_size*2))
