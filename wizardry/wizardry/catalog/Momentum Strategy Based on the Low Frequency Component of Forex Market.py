import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
import numpy as np


class TrendFollowingAlgorithm(QCAlgorithm):
    def Initialize(self):
		self.SetStartDate(2011,1,1)
		self.SetEndDate(2017,5,30)
		self.SetCash(100000)
		self.numdays = 360*5  # set the length of training period
		self.syl = self.AddSecurity(SecurityType.Forex, "EURUSD", Resolution.Daily).Symbol
		self.n,self.m = 2, 1
		self.trend = None
		self.SetBenchmark(self.sylStock Selection Strategy Based on Fundamental Factors
		self.MA_rules = None
		history = self.History(self.numdays,Resolution.Daily)
		self.close = [slice[self.syl].Close for slice in history]

    def hpfilter(self,X, lamb=1600):
    	X = np.asarray(X, float)
    	if X.ndim > 1:
			X = X.squeeze()
        nobs = len(X)
        I = sparse.eye(nobs,nobs)
        offsets = np.array([0,1,2])
        data = np.repeat([[1.],[-2.],[1.]], nobs, axis=1)
        K = sparse.dia_matrix((data, offsets), shape=(nobs-2,nobs))
        use_umfpack = True
        self.trend = spsolve(I+lamb*K.T.dot(K), X, use_umfpack=use_umfpack)
        self.cycle = X - self.trend

    def OnData(self,data):
        self.close.append(self.Portfolio[self.syl].Price)
        self.hpfilter(self.close[-self.numdays:len(self.close)+1], 100)
        self.MA_rules_today = (np.mean(self.trend[-self.m : len(self.trend)]) - np.mean(self.trend[-self.n : len(self.trend)]))
        self.MA_rules_yesterday = (np.mean(self.trend[-self.m-1: len(self.trend)-1]) - np.mean(self.trend[-self.n-1 : len(self.trend)-1]))
        holdings = self.Portfolio[self.syl].Quantity

        if self.MA_rules_today > 0 and self.MA_rules_yesterday < 0:
        	self.SetHoldings(self.syl, 1)
        elif self.MA_rules_today < 0 and self.MA_rules_yesterday > 0:
            self.SetHoldings(self.syl, -1)
