import numpy as np
import math

class StandardizedUnexpectedEarnings(QCAlgorithm):
    '''Step 1. Calculate the change in quarterly EPS from its value four quarters ago
       Step 2. Calculate the st dev of this change over the prior eight quarters
       Step 3. Get standardized unexpected earnings (SUE) from dividing results of step 1 by step 2
       Step 4. Each month, sort universe by SUE and long the top quantile

       Reference:
       [1] Foster, Olsen and Shevlin, 1984, Earnings Releases, Anomalies, and the Behavior of Security Returns,
           The Accounting Review. URL: https://www.jstor.org/stable/pdf/247321.pdf?casa_token=KHX3qwnGgTMAAAAA:
           ycgY-PzPfQ9uiYzVYeOF6yRDaNcRkL6IhLmRJuFpI6iWxsXJgB2BcM6ylmjy-g6xv-PYbXySJ_VxDpFETxw1PtKGUi1d91ce-h-V6CaL_SAAB56GZRQ
       [2] Hou, Xue and Zhang, 2018, Replicating Anomalies, Review of Financial Studies,
           URL: http://theinvestmentcapm.com/HouXueZhang2019RFS.pdf
    '''

    def Initialize(self):

        self.SetStartDate(2007, 1, 1)                               # Set Start Date. Warm up for first 36 months
        self.SetEndDate(2019, 9, 1)                                 # Set End Date
        self.SetCash(100000)                                        # Set Strategy Cash

        self.months_eps_change = 12                                 # Number of months of lag to calculate eps change
        self.months_count = 36                                      # Number of months of rolling window object
        self.num_coarse = 1000                                      # Number of new symbols selected at Coarse Selection
        self.top_percent = 0.05                                     # Percentage of symbols selected based on SUE sorting

        self.eps_by_symbol = {}                                     # Contains RollingWindow objects for all stocks
        self.new_fine = []                                          # Contains new symbols selected at Coarse Selection
        self.long = []                                              # Contains symbols that we will long
        self.next_rebalance = self.Time                             # Define next rebalance time

        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionAndSueSorting)


    def CoarseSelectionFunction(self, coarse):
        '''Get dynamic coarse universe to be further selected in fine selection
        '''
        # Before next rebalance time, just remain the current universe
        if self.Time < self.next_rebalance:
            return Universe.Unchanged

        ### Run the coarse selection to narrow down the universe
        # filter by fundamental data and price & Sort descendingly by daily dollar volume
        sorted_by_volume = sorted([ x for x in coarse if x.HasFundamentalData and x.Price > 5 ],
                                    key = lambda x: x.DollarVolume, reverse = True)
        self.new_fine = [ x.Symbol for x in sorted_by_volume[:self.num_coarse] ]

        # Return all symbols that have appeared in Coarse Selection
        return list( set(self.new_fine).union( set(self.eps_by_symbol.keys()) ) )


    def FineSelectionAndSueSorting(self, fine):
        '''Select symbols to trade based on sorting of SUE'''

        sue_by_symbol = dict()

        for stock in fine:

            ### Save (symbol, rolling window of EPS) pair in dictionary
            if not stock.Symbol in self.eps_by_symbol:
                self.eps_by_symbol[stock.Symbol] = RollingWindow[float](self.months_count)
            # update rolling window for each stock
            self.eps_by_symbol[stock.Symbol].Add(stock.EarningReports.BasicEPS.ThreeMonths)

            ### Calculate SUE

            if stock.Symbol in self.new_fine and self.eps_by_symbol[stock.Symbol].IsReady:

                # Calculate the EPS change from four quarters ago
                rw = self.eps_by_symbol[stock.Symbol]
                eps_change = rw[0] - rw[self.months_eps_change]

                # Calculate the st dev of EPS change for the prior eight quarters
                new_eps_list = list(rw)[:self.months_count - self.months_eps_change:3]
                old_eps_list = list(rw)[self.months_eps_change::3]
                eps_std = np.std( [ new_eps - old_eps for new_eps, old_eps in
                                    zip( new_eps_list, old_eps_list )
                                ] )

                # Get Standardized Unexpected Earnings (SUE)
                sue_by_symbol[stock.Symbol] = eps_change / eps_std

        # Sort and return the top quantile
        sorted_dict = sorted(sue_by_symbol.items(), key = lambda x: x[1], reverse = True)

        self.long = [ x[0] for x in sorted_dict[:math.ceil( self.top_percent * len(sorted_dict) )] ]
        # If universe is empty, OnData will not be triggered, then update next rebalance time here
        if not self.long:
            self.next_rebalance = Expiry.EndOfMonth(self.Time)

        return self.long


    def OnSecuritiesChanged(self, changes):
        '''Liquidate symbols that are removed from the dynamic universe
        '''
        for security in changes.RemovedSecurities:
            if security.Invested:
                self.Liquidate(security.Symbol, 'Removed from universe')


    def OnData(self, data):
        '''Monthly rebalance at the beginning of each month. Form portfolio with equal weights.
        '''
        # Before next rebalance, do nothing
        if self.Time < self.next_rebalance or not self.long:
            return

        # Placing orders (with equal weights)
        equal_weight = 1 / len(self.long)
        for stock in self.long:
            self.SetHoldings(stock, equal_weight)

        # Rebalance at the beginning of every month
        self.next_rebalance = Expiry.EndOfMonth(self.Time)
