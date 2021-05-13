import numpy as np
import pandas as pd
import statsmodels.formula.api as sm
from scipy import stats
import datetime as datetime

class Forex(QCAlgorithm):


    def get_history(self,symbol, num):
        data = {}
        dates = []
        history = self.History([symbol], num, Resolution.Daily).loc[symbol]['close'] #request the historical data for a single symbol
        for time in history.index:
            t = time.to_pydatetime().date()
            dates.append(t)
        dates = pd.to_datetime(dates)
        df = pd.DataFrame(history)
        df.reset_index(drop=True)
        df.index = dates
        df.columns = ['price']

        return df



    def calculate_return(self,df):
        #calculate the mean for further use
        mean = np.mean(df.price)
        # cauculate the standard deviation
        sd = np.std(df.price)
        # pandas method to take the last datapoint of each month.
        df = df.resample('BM',how = lambda x: x[-1])
        # the following three lines are for further experiment purpose
        # df['j1'] = df.price.shift(1) - df.price.shift(2)
        # df['j2'] = df.price.shift(2) - df.price.shift(3)
        # df['j3'] = df.price.shift(3) - df.price.shift(4)
        # take the return as depend variable
        df['log_return'] = df.price - df.price.shift(1)
        # calculate the reversal factor
        df['reversal'] = (df.price.shift(1) - mean)/sd
        # calculate the momentum factor
        df['mom'] = df.price.shift(1) - df.price.shift(4)
        df = df.dropna() #remove nan value
        return (df,mean,sd)




    def calculate_input(self,df,mean,sd):
        # df['j1'] = df.price - df.price.shift(1)
        # df['j2'] = df.price.shift(1) - df.price.shift(2)
        # df['j3'] = df.price.shift(2) - df.price.shift(3)
        df['reversal'] = (df.price - mean)/sd
        df['mom'] = df.price - df.price.shift(3)
        df = df.dropna()
        return df



    def OLS(self,df):
        res = sm.ols(formula = 'log_return ~ reversal + mom',data = df).fit()
        return res


    def out_params(self,symbol,num):

        his = self.get_history(symbol.Value,num)
        his = self.calculate_return(his)
        res = self.OLS(his[0])
        return (res,his[1])


    def concat(self):
        # we requested as many daily tradebars as we can
        his = self.get_history(self.quoted[0].Value,20*365)
        # get the clean DataFrame for linear regression
        his = self.calculate_return(his)
        # add property to the symbol object for further use.
        self.quoted[0].mean = his[1]
        self.quoted[0].sd = his[2]
        df = his[0]
        # repeat the above procedure for each symbols, and concat the dataframes
        for i in range(1,len(self.quoted)):
            his = self.get_history(self.quoted[i].Value,20*365)
            his = self.calculate_return(his)
            self.quoted[i].mean = his[1]
            self.quoted[i].sd = his[2]
            df = pd.concat([df,his[0]])
        df = df.sort_index()
        # remove outliers that outside the 99.9% confidence interval
        df = df[df.apply(lambda x: np.abs(x - x.mean()) / x.std() < 3).all(axis=1)]
        return df

    def predict(self,symbol):
    # get current month in string
        month = str(self.Time).split(' ')[0][5:7]
    # request the data in the last three months
        res = self.get_history(symbol.Value,33*3)
    # pandas method to take the last datapoint of each month
        res = res.resample('BM',how = lambda x: x[-1])
    # remove the data points in the current month
        res = res[res.index.month != int(month)]
    # calculate the variables
        res = self.calculate_input(res,symbol.mean,symbol.sd)
        res = res.ix[0]
    # take the coefficient. The first one will not be used for sum-product because it's the intercept
        params = self.formula.params[1:]
    # calculate the expected return
        re = sum([a*b for a,b in zip(res[1:],params)]) + self.formula.params[0]
        return re



    def Initialize(self):
        self.SetStartDate(2013,6,1)
        self.SetEndDate(2016,6,1)
        self.SetCash(10000)
        self.syls = ['EURUSD','GBPUSD','USDCAD','USDJPY']
        self.quoted = []
        for i in range(len(self.syls)):
            self.quoted.append(self.AddForex(self.syls[i],Resolution.Daily,Market.Oanda).Symbol)

        df = self.concat()
        self.Log(str(df))
        self.formula = self.OLS(df)
        self.Log(str(self.formula.summary()))
        self.Log(str(df))
        self.Log(str(df.describe()))
        for i in self.quoted:
            self.Log(str(i.mean) + '   ' + str(i.sd))

        self.Schedule.On(self.DateRules.MonthStart(), self.TimeRules.At(9,31), Action(self.action))


    def OnData(self,data):
        self.data = data
        pass



    def action(self):
        rank = []
        long_short = []
        for i in self.quoted:
            rank.append((i,self.predict(i)))
    # rank the symbols by their expected return
        rank.sort(key = lambda x: x[1],reverse = True)
    # the first element in long_short is the one with the highest expected return, which we are going to long, and the second one is going to be shorted.
        long_short.append(rank[0])
        long_short.append(rank[-1])
        self.Liquidate()

    # the product < 0 means the expected return of the first one is positive and that of the second one is negative--we are going to long and short.
        if long_short[0][1]*long_short[1][1] < 0:
            self.SetHoldings(long_short[0][0],1)
            self.SetHoldings(long_short[1][0],-1)
    # this means we long only because all of the expected return is positive
        elif long_short[0][1] > 0 and long_short[1][1] > 0:
            self.SetHoldings(long_short[0][0],1)
    # short only
        else:
            self.SetHoldings(long_short[1][0],-1)
