import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.decomposition import PCA

class PcaStatArbitrageAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2010, 1, 1)       # Set Start Date
        self.SetEndDate(2019, 8, 1)         # Set End Date
        self.SetCash(100000)                # Set Strategy Cash

        self.nextRebalance = self.Time      # Initialize next rebalance time
        self.rebalance_days = 30            # Rebalance every 30 days

        self.lookback = 60                  # Length(days) of historical data
        self.num_components = 3             # Number of principal components in PCA
        self.num_equities = 20              # Number of the equities pool
        self.weights = pd.DataFrame()       # Pandas data frame (index: symbol) that stores the weight

        self.UniverseSettings.Resolution = Resolution.Hour   # Use hour resolution for speed
        self.AddUniverse(self.CoarseSelectionAndPCA)         # Coarse selection + PCA


    def CoarseSelectionAndPCA(self, coarse):
        '''Drop securities which have too low prices.
        Select those with highest by dollar volume.
        Finally do PCA and get the selected trading symbols.
        '''

        # Before next rebalance time, just remain the current universe
        if self.Time < self.nextRebalance:
            return Universe.Unchanged

        ### Simple coarse selection first

        # Sort the equities in DollarVolume decendingly
        selected = sorted([x for x in coarse if x.Price > 5],
                          key=lambda x: x.DollarVolume, reverse=True)

        symbols = [x.Symbol for x in selected[:self.num_equities]]

        ### After coarse selection, we do PCA and linear regression to get our selected symbols

        # Get historical data of the selected symbols
        history = self.History(symbols, self.lookback, Resolution.Daily).close.unstack(level=0)

        # Select the desired symbols and their weights for the portfolio from the coarse-selected symbols
        self.weights = self.GetWeights(history)

        # If there is no final selected symbols, return the unchanged universe
        if self.weights.empty:
            return Universe.Unchanged

        return [x for x in symbols if str(x) in self.weights.index]


    def GetWeights(self, history):
        '''
        Get the finalized selected symbols and their weights according to their level of deviation
        of the residuals from the linear regression after PCA for each symbol
        '''
        # Sample data for PCA (smooth it using np.log function)
        sample = np.log(history.dropna(axis=1))
        sample -= sample.mean() # Center it column-wise

        # Fit the PCA model for sample data
        model = PCA().fit(sample)

        # Get the first n_components factors
        factors = np.dot(sample, model.components_.T)[:,:self.num_components]

        # Add 1's to fit the linear regression (intercept)
        factors = sm.add_constant(factors)

        # Train Ordinary Least Squares linear model for each stock
        OLSmodels = {ticker: sm.OLS(sample[ticker], factors).fit() for ticker in sample.columns}

        # Get the residuals from the linear regression after PCA for each stock
        resids = pd.DataFrame({ticker: model.resid for ticker, model in OLSmodels.items()})

        # Get the Z scores by standarize the given pandas dataframe X
        zscores = ((resids - resids.mean()) / resids.std()).iloc[-1] # residuals of the most recent day

        # Get the stocks far from mean (for mean reversion)
        selected = zscores[zscores < -1.5]

        # Return the weights for each selected stock
        weights = selected * (1 / selected.abs().sum())
        return weights.sort_values()


    def OnData(self, data):
        '''
        Rebalance every self.rebalance_days
        '''
        ### Do nothing until next rebalance
        if self.Time < self.nextRebalance:
            return

        ### Open positions
        for symbol, weight in self.weights.items():
            # If the residual is way deviated from 0, we enter the position in the opposite way (mean reversion)
            self.SetHoldings(symbol, -weight)

        ### Update next rebalance time
        self.nextRebalance = self.Time + timedelta(self.rebalance_days)


    def OnSecuritiesChanged(self, changes):
        '''
        Liquidate when the symbols are not in the universe
        '''
        for security in changes.RemovedSecurities:
            if security.Invested:
                self.Liquidate(security.Symbol, 'Removed from Universe')
