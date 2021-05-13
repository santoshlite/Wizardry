class EarningsQualityFactor(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2003,6,1)   #Set Start Date
        self.SetEndDate(2018,8,1)     #Set End Date
        self.SetCash(1000000)         #Set Strategy Cash
        self.UniverseSettings.Resolution = Resolution.Daily
        self.previous_fine = None
        self.long = None
        self.short = None
        self.AddUniverse(self.CoarseSelectionFunction,self.FineSelectionFunction)
        self.AddEquity("SPY", Resolution.Daily)
        # monthly scheduled event but will only rebalance once a year
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.At(23, 0), self.rebalance)
        self.yearly_rebalance = False

    def CoarseSelectionFunction(self, coarse):
        if self.yearly_rebalance:
            # drop stocks which have no fundamental data
            filtered_coarse = [x.Symbol for x in coarse if (x.HasFundamentalData) and (x.Market == "usa")]
            return filtered_coarse
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.yearly_rebalance:
            #filters out the non-financial companies that don't contain the necessary data
            fine = [x for x in fine if (x.CompanyReference.IndustryTemplateCode != "B")
                                    and (x.FinancialStatements.BalanceSheet.CurrentAssets.Value != 0)
                                    and (x.FinancialStatements.BalanceSheet.CashAndCashEquivalents.Value != 0)
                                    and (x.FinancialStatements.BalanceSheet.CurrentLiabilities.Value != 0)
                                    and (x.FinancialStatements.BalanceSheet.CurrentDebt.Value != 0)
                                    and (x.FinancialStatements.BalanceSheet.IncomeTaxPayable.Value != 0)
                                    and (x.FinancialStatements.IncomeStatement.DepreciationAndAmortization.Value != 0)]

            if not self.previous_fine:
                # will wait one year in order to have the historical fundamental data
                self.previous_fine = fine
                self.yearly_rebalance = False
                return []
            else:
                # calculate the accrual for each stock
                fine = self.CalculateAccruals(fine, self.previous_fine)
                filtered_fine = [x for x in fine if (x.FinancialStatements.CashFlowStatement.OperatingCashFlow.Value!=0)
                                                and (x.EarningReports.BasicEPS.Value!=0)
                                                and (x.EarningReports.BasicAverageShares.Value!=0)
                                                and (x.OperationRatios.DebttoAssets.Value!=0)
                                                and (x.OperationRatios.ROE.Value!=0)]
                for i in filtered_fine:
                    # cash flow to assets
                    i.CFA = i.FinancialStatements.CashFlowStatement.OperatingCashFlow.Value/(i.EarningReports.BasicEPS.Value * i.EarningReports.BasicAverageShares.Value)
                    # debt to assets
                    i.DA = i.OperationRatios.DebttoAssets.Value
                    # return on equity
                    i.ROE = i.OperationRatios.ROE.Value

                # sort stocks by four factors respectively
                sortedByAccrual = sorted(filtered_fine, key=lambda x: x.Accrual, reverse=True) # high score with low accrual
                sortedByCFA = sorted(filtered_fine, key=lambda x: x.CFA)                       # high score with high CFA
                sortedByDA = sorted(filtered_fine, key=lambda x: x.DA, reverse=True)           # high score with low leverage
                sortedByROE = sorted(filtered_fine, key=lambda x: x.ROE)                       # high score with high ROE
                # create dict to save the score for each stock
                score_dict = {}
                # assign a score to each stock according to their rank with different factors
                for i,obj in enumerate(sortedByAccrual):
                    scoreAccrual = i
                    scoreCFA = sortedByCFA.index(obj)
                    scoreDA = sortedByDA.index(obj)
                    scoreROE = sortedByROE.index(obj)
                    score = scoreAccrual + scoreCFA + scoreDA + scoreROE
                    score_dict[obj.Symbol] = score

                sortedByScore = sorted(score_dict, key = lambda x: score_dict[x], reverse = True)
                # long stocks with the top score (>30%) and short stocks with the bottom score (<70%)
                self.long = sortedByScore[:int(0.3*len(sortedByScore))]
                self.short = sortedByScore[-int(0.3*len(sortedByScore)):]

                # save the fine data for the next year's analysis
                self.previous_fine = fine

                return self.long + self.short
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
                stock_data.Accrual = ((delta_assets-delta_cash)-(delta_liabilities-delta_debt-delta_tax)-dep)/avg_total
                accruals.append(stock_data)
            except:
                #value in current universe does not exist in the previous universe
                pass
        return accruals

    def rebalance(self):
        #yearly rebalance at the end of June (start of July)
        if self.Time.month == 7:
            self.yearly_rebalance = True

    def OnData(self, data):
        if not self.yearly_rebalance: return
        if self.long and self.short:
            long_stocks = [x.Key for x in self.Portfolio if x.Value.IsLong]
            short_stocks = [x.Key for x in self.Portfolio if x.Value.IsShort]
            # liquidate the stocks not in the filtered long/short list
            for long in long_stocks:
                if long not in self.long:
                    self.Liquidate(long)

            for short in short_stocks:
                if short not in self.short:
                    self.Liquidate(short)

            long_weight = 0.8/len(self.long)
            for i in self.long:
                self.SetHoldings(i, long_weight)
            short_weight = 0.8/len(self.short)
            for i in self.short:
                self.SetHoldings(i, -short_weight)


            self.yearly_rebalance = False
            self.long = False
            self.short = False
