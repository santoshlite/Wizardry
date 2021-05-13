import math
import numpy as np
import pandas as pd
import statsmodels.api as sm
from datetime import date, datetime, timedelta
from scipy import stats

class ExpectedIdiosyncraticSkewness(QCAlgorithm):
    '''Step 1. Calculating Fama-French daily regression residuals
       Step 2. Using daily residuals to calculate historical monthly moments
       Step 3. Run regression of historical monthly moments to estimate regression coefficients
       Step 4. Using historical monthly moments and estimated coefficients to calculate expected skewness
       Step 5. Sorting symbols by skewness and long the ones with lowest skewness

       Note: Fama-French factors daily data are only available up to 06/30/2019.
       So, backtest is implemented up to end of June, 2019. And, live trading is not feasible for current version.

       Reference:
       [1] "Expected Idiosyncratic Skewness" by Boyer, Mitton and Vorkink, Rev Financ Stud, June 2009
           URL: https://academic.oup.com/rfs/article-abstract/23/1/169/1578688?redirectedFrom=PDF
       [2] Fama-French official data: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
    '''

    def Initialize(self):

        self.SetStartDate(2009, 7, 1)                          # Set Start Date: Right after original paper published
        self.SetEndDate(2019, 7, 30)                           # Set End Date
        self.SetCash(100000)                                   # Set Strategy Cash

        # Download Fama French factors data as a dataframe
        self.fama_french_factors_per_day = self._get_fama_french_factors()

        self.number_of_coarse_symbol = 200                     # Set the number of coarse symbol to be further filtered by expected skewness
        self.bottom_percent = 0.05                             # Set the bottom percent to long out of coarse symbols according to skewness ranking
        self.weights = {}                                      # Dictionary to save desired weights with symbols as key
        self.nextRebalance = self.Time                         # Define next rebalance time

        self.UniverseSettings.Resolution = Resolution.Daily    # Subscribe daily data for selected symbols in universe
        self.AddUniverse(self.CoarseSelectionAndSkewnessSorting, self.GetWeightsInFineSelection)


    def CoarseSelectionAndSkewnessSorting(self, coarse):
        '''Coarse selection to get an initial universe for the skewness sorting trade logic.
           Then, select the symbols to trade monthly based on skewness sorting.
        '''
        # Before next rebalance time, keep the current universe unchanged
        if self.Time < self.nextRebalance:
            return Universe.Unchanged

        ### Run the coarse selection to narrow down the universe
        # Filter stocks by price and whether they have fundamental data in QC
        # Then, sort descendingly by daily dollar volume
        sorted_by_volume = sorted([ x for x in coarse if x.HasFundamentalData and x.Price > 5 ],
                                    key = lambda x: x.DollarVolume, reverse = True)
        high_volume_stocks = [ x.Symbol for x in sorted_by_volume[:self.number_of_coarse_symbol] ]

        ### Select symbols to trade based on expected skewness at each month end

        # Estimate expected idiosyncratic skewness and select the lowest 5%
        symbol_and_skew = self.CalculateExpectedSkewness(high_volume_stocks)
        symbol_and_skew = symbol_and_skew.loc[:math.ceil(self.number_of_coarse_symbol * self.bottom_percent)]

        # Return the symbols
        return [self.Symbol(x) for x in symbol_and_skew.symbol.values]


    def GetWeightsInFineSelection(self, fine):
        '''Get fine fundamental data and calculate portfolio weights based on market capitalization
        '''
        # Calculate market cap as shares outstanding multiplied by stock price
        self.weights = { f.Symbol: f.EarningReports.BasicAverageShares.ThreeMonths * f.Price
            for f in fine }

        # Form value-weighted portfolio
        total_cap = sum(self.weights.values())

        # Compute the weights and sort them descendingly to place bigger orders first
        self.weights = { k: v / total_cap
            for k, v in sorted(self.weights.items(), key=lambda kv: kv[1], reverse=True) }

        return [ x.Symbol for x in fine ]


    def OnSecuritiesChanged(self, changes):
        '''Liquidate symbols that are removed from the dynamic universe
        '''
        for security in changes.RemovedSecurities:
            if security.Invested:
                self.Liquidate(security.Symbol, 'Removed from universe')


    def OnData(self, data):
        '''Rebalance the porfolio once a month with weights based on market cap
        '''
        # Before next rebalance, do nothing
        if self.Time < self.nextRebalance:
            return

        # Placing orders
        for symbol, weight in self.weights.items():
            self.SetHoldings(symbol, weight)

        # Rebalance at the end of every month
        self.nextRebalance = Expiry.EndOfMonth(self.Time)


    def CalculateExpectedSkewness(self, universe):
        '''Calculate expected skewness using historical moments and estimated regression coefficients
        '''

        ### Get predictors

        # Get historical returns for two months
        monthEnd_this = self.Time
        monthEnd_lag_1 = (self.Time - timedelta(days = 10)).replace(day = 1)
        monthEnd_lag_2 = (monthEnd_lag_1 - timedelta(days = 10)).replace(day = 1)
        history = self.History(universe, monthEnd_lag_2 - timedelta(days = 1), monthEnd_this, Resolution.Daily)
        history = history["close"].unstack(level = 0)
        daily_returns = (np.log(history) - np.log(history.shift(1)))[1:]

        # Merge Fama-French factors to daily returns based on dates available in return series
        daily_returns['time'] = daily_returns.index
        daily_returns = daily_returns.merge(self.fama_french_factors_per_day, left_on = 'time', right_on = 'time')

        daily_returns_this = daily_returns[daily_returns['time'] > monthEnd_lag_1]
        daily_returns_last = daily_returns[daily_returns['time'] <= monthEnd_lag_1]
        daily_returns_dict = {monthEnd_this: daily_returns_this, monthEnd_lag_1: daily_returns_last}

        # For each stock and each month, run fama-french time-series regression and calculate historical moments
        column_list = list(daily_returns.columns)
        predictor_list = []

        for month, returns in daily_returns_dict.items():

            for symbol in universe:

                if str(symbol) not in column_list:
                    predictor_list.append([str(symbol), month, np.nan, np.nan])
                    continue

                Y = (returns[str(symbol)] - returns['RF']).values
                X = returns[['Mkt_RF', 'SMB', 'HML']].values
                X = sm.add_constant(X)
                results = sm.OLS(Y, X).fit()

                # Use daily residual to calculate monthly moments
                hist_skew, hist_vol = stats.skew(results.resid), stats.tstd(results.resid)
                predictor_list.append([str(symbol), month, hist_skew, hist_vol])

        predictor = pd.DataFrame(predictor_list, columns = ['symbol', 'time', 'skew', 'vol'])

        ### Estimate coefficients by regressing current skewness on historical moments
        Y = predictor[predictor['time'] == monthEnd_this]['skew'].values
        X = predictor[predictor['time'] == monthEnd_lag_1][['skew', 'vol']].values
        X = sm.add_constant(X)
        results = sm.OLS(Y, X, missing = 'drop').fit()
        coef = results.params

        ### Calculate expected skewness
        predictor_t = predictor[predictor['time'] == monthEnd_this][['skew', 'vol']].values
        ones = np.ones([len(predictor_t), 1])
        predictor_t = np.append(ones, predictor_t, 1)
        exp_skew = np.inner(predictor_t, coef)

        skew_df = predictor[predictor['time'] == monthEnd_this][['symbol']].reset_index(drop = True)
        skew_df.loc[:,'skew'] = exp_skew
        skew_df = skew_df.sort_values(by = ['skew']).reset_index(drop = True)

        return skew_df


    def _get_fama_french_factors(self):
        '''Download fama-french factors data from Github repo and read it as a DataFrame.
           Data is originally from Kenneth French's official homepage. I unzip the data folder and upload to Github repo.
        '''
        content = self.Download("https://raw.githubusercontent.com/QuantConnect/Tutorials/master/04%20Strategy%20Library/354%20Expected%20Idiosyncratic%20Skewness/F-F_Research_Data_Factors_daily.CSV")

        # Drop the first 5 and last 2 lines which are not data that we need
        data = content.splitlines()
        data = [x.split(',') for x in data[5:-2]]

        df = pd.DataFrame(data, columns = ['time', 'Mkt_RF', 'SMB', 'HML', 'RF'], dtype=np.float64)
        # Add one day to match Lean behavior: daily data is timestamped at UTC 00:00 the next day from the actual day that produced the data
        df.time = pd.to_datetime(df.time, format='%Y%m%d') + timedelta(1)
        return df.set_index('time')
