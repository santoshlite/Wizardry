class NetCurrentAssetValue(QCAlgorithm):

    def Initialize(self):
        #rebalancing should occur in July
        self.SetStartDate(2007,5,15)  #Set Start Date
        self.SetEndDate(2018,7,15)    #Set End Date
        self.SetCash(1000000)           #Set Strategy Cash
        self.UniverseSettings.Resolution = Resolution.Daily
        self.previous_fine = None
        self.filtered_fine = None
        self.AddUniverse(self.CoarseSelectionFunction,self.FineSelectionFunction)
        self.AddEquity("SPY", Resolution.Daily)
        #monthly scheduled event but will only rebalance once a year
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.At(23, 0), self.rebalance)
        self.months = -1
        self.yearly_rebalance = False

    def CoarseSelectionFunction(self, coarse):
        if self.yearly_rebalance:
            # drop stocks which have no fundamental data
            self.filtered_coarse = [x.Symbol for x in coarse if (x.HasFundamentalData)
                                                            and (x.Market == "usa")]
            return self.filtered_coarse
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.yearly_rebalance:
            #filters out the companies that don't contain the necessary data
            fine = [x for x in fine if (float(x.FinancialStatements.BalanceSheet.CurrentAssets.Value) > 0)
                                    and (float(x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value) > 0)
                                   and (float(x.FinancialStatements.BalanceSheet.CurrentLiabilities.Value) > 0)
                                    and (float(x.FinancialStatements.BalanceSheet.CurrentDebt.Value) > 0)
                                    and (float(x.FinancialStatements.BalanceSheet.IncomeTaxPayable.Value) > 0)
                                    and (float(x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value) > 0)]

            if not self.previous_fine:
                #will wait one year in order to have the historical fundamental data
                self.previous_fine = fine
                self.yearly_rebalance = False
                return []
            else:
                #will calculate and sort the balance sheet accruals
                self.filtered_fine = self.CalculateAccruals(fine,self.previous_fine)
                sorted_filter = sorted(self.filtered_fine, key=lambda x: x.bs_acc)
                self.filtered_fine = [i.Symbol for i in sorted_filter]
                #we save the fine data for the next year's analysis
                self.previous_fine = fine
                return self.filtered_fine
        else:
            return []

    def CalculateAccruals(self, current, previous):
        accruals = []
        for stock_data in current:
            #compares this and last year's fine fundamental objects
            try:
                prev_data = None
                for x in previous:
                    if x.Symbol == stock_data.Symbol:
                        prev_data = x
                        break

                #calculates the balance sheet accruals and adds the property to the fine fundamental object
                delta_assets = float(stock_data.FinancialStatements.BalanceSheet.CurrentAssets.Value)-float(prev_data.FinancialStatements.BalanceSheet.CurrentAssets.Value)
                delta_cash = float(stock_data.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value)-float(prev_data.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value)
                delta_liabilities = float(stock_data.FinancialStatements.BalanceSheet.CurrentLiabilities.Value)-float(prev_data.FinancialStatements.BalanceSheet.CurrentLiabilities.Value)
                delta_debt = float(stock_data.FinancialStatements.BalanceSheet.CurrentDebt.Value)-float(prev_data.FinancialStatements.BalanceSheet.CurrentDebt.Value)
                delta_tax = float(stock_data.FinancialStatements.BalanceSheet.IncomeTaxPayable.Value)-float(prev_data.FinancialStatements.BalanceSheet.IncomeTaxPayable.Value)
                dep = float(stock_data.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value)
                avg_total = (float(stock_data.FinancialStatements.BalanceSheet.TotalAssets.Value)+float(prev_data.FinancialStatements.BalanceSheet.TotalAssets.Value))/2
                #accounts for the size difference
                stock_data.bs_acc = ((delta_assets-delta_cash)-(delta_liabilities-delta_debt-delta_tax)-dep)/avg_total
                accruals.append(stock_data)
            except:
                #value in current universe does not exist in the previous universe
                pass
        return accruals

    def rebalance(self):
        #yearly rebalance
        self.months+=1
        if self.months%12 == 0:
            self.yearly_rebalance = True

    def OnData(self, data):
        if not self.yearly_rebalance: return
        if self.filtered_fine:
            portfolio_size = int(len(self.filtered_fine)/10)
            #pick the upper decile to short and the lower decile to long
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
            self.yearly_rebalance = False
            self.filtered_fine = False
