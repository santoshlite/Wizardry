from datetime import datetime, timedelta

class MomentumInREIT(QCAlgorithm):

    def Initialize(self):
        #rebalancing should occur in July
        self.SetStartDate(2010,12,15)  #Set Start Date
        self.SetEndDate(2018,7,15)    #Set End Date
        self.SetCash(1000000)           #Set Strategy Cash
        self.UniverseSettings.Resolution = Resolution.Daily
        self.filtered_fine = None
        self.AddUniverse(self.CoarseSelectionFunction,self.FineSelectionFunction)
        self.AddEquity("SPY", Resolution.Daily)
        #monthly scheduled event
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.At(23, 0), self.rebalance)
        self.months = -1
        self.quarterly_rebalance = False

    def CoarseSelectionFunction(self, coarse):
        if self.quarterly_rebalance:
            # drops penny stocks and stocks with no fundamental data
            self.filtered_coarse = [x.Symbol for x in coarse if (float(x.Price) > 1)
                                                            and (x.HasFundamentalData)
                                                            and float(x.Volume) > 10000]
            return self.filtered_coarse
        else:
            return []

    def FineSelectionFunction(self, fine):
        if self.quarterly_rebalance:
            #filters out the companies that are not REITs
            fine = [x for x in fine if (x.CompanyReference.IsREIT == 1)]

            #calculating the 11 month (1-month lagged) returns
            start = self.Time-timedelta(days = 365)
            end = self.Time-timedelta(days = 30)
            for x in fine:
                hist = self.History([x.Symbol],start,end,Resolution.Daily)
                if not hist.empty:
                    start_price = hist["close"].iloc[0]
                    end_price = hist["close"].iloc[-1]
                    x.momentum = (end_price-start_price)/start_price

            fine = [x for x in fine if hasattr(x, 'momentum')]
            #we sort REITs based on their returns
            sorted_filter = sorted(fine, key=lambda x: x.momentum)
            self.filtered_fine = [i.Symbol for i in sorted_filter]
            return self.filtered_fine
        else:
            return []

    def rebalance(self):
        #quarterly rebalance
        self.months+=1
        if self.months%3 == 0:
            self.quarterly_rebalance = True

    def OnData(self, data):
        if not self.quarterly_rebalance: return
        if self.filtered_fine:
            portfolio_size = int(len(self.filtered_fine)/3)
            #pick the upper trecile to short and the lower decile to long
            long_stocks = self.filtered_fine[-portfolio_size:]
            stocks_invested = [x.Key for x in self.Portfolio]
            for i in stocks_invested:
                #liquidate the stocks not in our filtered_fine list
                if i not in long_stocks:
                    self.Liquidate(i)
                #long the stocks in the list
                elif i in long_stocks:
                    self.SetHoldings(i, 1/(portfolio_size))
            self.quarterly_rebalance = False
            self.filtered_fine = None
