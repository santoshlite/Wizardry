class AssetGrowth(QCAlgorithm):

    def Initialize(self):
        #rebalancing should occur in July
        self.SetStartDate(2008,6,15)  #Set Start Date
        self.SetEndDate(2018,7,15)    #Set End Date
        self.SetCash(1000000)           #Set Strategy Cash
        self.UniverseSettings.Resolution = Resolution.Daily
        self.previous_fine = None
        self.filtered_fine = None
        self.AddUniverse(self.CoarseSelectionFunction,self.FineSelectionFunction)
        self.AddEquity("SPY", Resolution.Daily)
        #monthly scheduled event but will only rebalance once a year
        self.Schedule.On(self.DateRules.MonthEnd("SPY"), self.TimeRules.At(23, 0), self.rebalance)
        self.months = -1
        self.yearly_rebalance = False

    def CoarseSelectionFunction(self, coarse):
        if self.yearly_rebalance:
            # drop stocks which have no fundamental data
            filtered_coarse = [x.Symbol for x in coarse if (x.HasFundamentalData)
                                                            and (x.Market == "usa")]
            return filtered_coarse
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.yearly_rebalance:
            fine = [x for x in fine if x.FinancialStatements.BalanceSheet.TotalAssets.Value > 0
                    and ((x.SecurityReference.ExchangeId == "NYS") or (x.SecurityReference.ExchangeId == "NAS") or (x.SecurityReference.ExchangeId == "ASE"))
                    and (x.CompanyReference.IndustryTemplateCode!="B")
                    and (x.CompanyReference.IndustryTemplateCode!="I")]
            if not self.previous_fine:
                #will wait one year in order to have the historical fundamental data
                self.previous_fine = fine
                self.yearly_rebalance = False
                return []
            else:
                #will calculate and sort the stocks on asset growth
                self.filtered_fine = self.Calculate(fine,self.previous_fine)
                sorted_filter = sorted(self.filtered_fine, key=lambda x: x.delta_assets)
                self.filtered_fine = [i.Symbol for i in sorted_filter]
                #we save the fine data for the next year's analysis
                self.previous_fine = fine
                return self.filtered_fine
        else:
            return []

    def Calculate(self, current, previous):
        growth = []
        for stock_data in current:
            #compares this and last year's fine fundamental objects
            try:
                prev_data = None
                for x in previous:
                    if x.Symbol == stock_data.Symbol:
                        prev_data = x
                        break
                #growth = (tota_assets(t)-total_assets(t-1))/total_assets(t-1)
                stock_data.delta_assets = (float(stock_data.FinancialStatements.BalanceSheet.TotalAssets.Value)-float(prev_data.FinancialStatements.BalanceSheet.TotalAssets.Value))/float(prev_data.FinancialStatements.BalanceSheet.TotalAssets.Value)
                growth.append(stock_data)
            except:
                #value in current universe does not exist in the previous universe
                pass
        return growth

    def rebalance(self):
        #yearly rebalance
        self.months+=1
        if self.months%12 == 0:
            self.yearly_rebalance = True
            self.Debug("true")

    def OnData(self, data):
        if not self.yearly_rebalance: return
        if self.filtered_fine:
            self.Debug("inside")
            portfolio_size = int(len(self.filtered_fine)/10)
            #pick the upper decile to short and the lower decile to long
            short_stocks = self.filtered_fine[-portfolio_size:]
            long_stocks = self.filtered_fine[:portfolio_size]
            stocks_invested = [x.Key for x in self.Portfolio]
            for i in stocks_invested:
                if i not in self.filtered_fine:
                    self.Liquidate(i)
                #long the stocks in the list
                elif i in long_stocks:
                    self.SetHoldings(i, 1/(portfolio_size*2))
                #short the stocks in the list
                elif i in short_stocks:
                    self.SetHoldings(i,-1/(portfolio_size*2))
            self.yearly_rebalance = False
            self.filtered_fine = False
