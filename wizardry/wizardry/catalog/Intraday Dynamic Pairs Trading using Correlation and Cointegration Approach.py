import numpy as np
import pandas as pd
import datetime as datetime
import statsmodels.formula.api as sm
from pandas.core import datetools
import statsmodels.tsa.stattools as ts
from pair import *

class pairs(object):

    def __init__(self,a,b):
        self.a = a
        self.b = b
        self.name = str(a) + ':' + str(b)
        self.df = pd.concat([a.df,b.df],axis = 1).dropna()
        self.num_bar = self.df.shape[0]
        self.cor = self.df.corr().ix[0][1]
        self.error = 0
        self.last_error = 0
        self.a_price = []
        self.a_date = []
        self.b_price = []
        self.b_date = []

    def cor_update(self):
        self.cor = self.df.corr().ix[0][1]

    def cointegration_test(self):
        self.model = sm.ols(formula = '%s ~ %s'%(str(self.a),str(self.b)), data = self.df).fit()
        self.adf = ts.adfuller(self.model.resid,autolag = 'BIC')[0]
        self.mean_error = np.mean(self.model.resid)
        self.sd = np.std(self.model.resid)

    def price_record(self,data_a,data_b):
        self.a_price.append(float(data_a.Close))
        self.a_date.append(data_a.EndTime)
        self.b_price.append(float(data_b.Close))
        self.b_date.append(data_b.EndTime)

    def df_update(self):
        new_df = pd.DataFrame({str(self.a):self.a_price,str(self.b):self.b_price},index = [self.a_date]).dropna()
        self.df = pd.concat([self.df,new_df])
        self.df = self.df.tail(self.num_bar)
        for i in [self.a_price,self.a_date,self.b_price,self.b_date]:
            i = []

class PairsTrading(QCAlgorithm):

    def __init__(self):
        self.symbols = [
        'ASB', 'AF', 'BANC', 'BBVA', 'BBD', 'BCH', 'BLX', 'BSBR', 'BSAC', 'SAN',
        'CIB', 'BXS', 'BAC', 'BOH', 'BMO', 'NTB', 'BK', 'BNS', 'BKU', 'BCS', 'BBT',
        'BFR', 'CM', 'COF', 'C', 'CFG', 'CMA', 'CBU', 'CPF', 'BAP', 'CFR', 'CUBI',
        'DKT', 'DB', 'EVER', 'FNB', 'FBK', 'FCB', 'FBP', 'FCF', 'FHN', 'FBC', 'FSB',
        'GWB', 'AVAL', 'BSMX', 'SUPV', 'HDB', 'HTH', 'HSBC', 'IBN', 'ING', 'ITUB', 'JPM',
        'KB', 'KEY', 'LYG', 'MTB', 'BMA', 'MFCB', 'MSL', 'MTU', 'MFG', 'NBHC', 'OFG', 'PNC',
        'PVTD', 'PB', 'PFS', 'RF', 'RY', 'RBS', 'SHG', 'STT', 'STL', 'SCNB', 'SMFG', 'STI',
        'SNV', 'TCB', 'TD', 'USB', 'UBS', 'VLY', 'WFC', 'WAL', 'WBK', 'WF', 'YDKN', 'ZBK']
        self.data_resolution = 10
        self.num_bar = 6.5*60*60/(self.data_resolution)
        self.one_month = 6.5*20*60/(self.data_resolution)
        self.selected_num = 10
        self.pair_num = 120
        self.pair_threshod = 0.88
        self.BIC = -3.34
        self.count = 0
        self.pair_list = []
        self.selected_pair = []
        self.trading_pairs = []
        self.generate_count = 0
        self.open_size = 2.32
        self.close_size = 0.5
        self.stop_loss = 6
        self.data_count = 0

    def Initialize(self):
        self.SetStartDate(2016,1,1)
        self.SetEndDate(2018,5,1)
        self.SetCash(50000)

        for i in range(len(self.symbols)):
            equity = self.AddEquity(self.symbols[i],Resolution.Minute).Symbol
            self.symbols[i] = equity
            self.symbols[i].prices = []
            self.symbols[i].dates = []


    def generate_pairs(self):
        for i in range(len(self.symbols)):
            for j in range(i+1,len(self.symbols)):
                self.pair_list.append(pairs(self.symbols[i],self.symbols[j]))

        self.pair_list = [x for x in self.pair_list if x.cor > self.pair_threshod]

        self.pair_list.sort(key = lambda x: x.cor, reverse = True)

        if len(self.pair_list) > self.pair_num:
            self.pair_list = self.pair_list[:self.pair_num]


    def pair_clean(self,list):
        l = []
        l.append(list[0])
        for i in list:
            symbols = [x.a for x in l] + [x.b for x in l]
            if i.a not in symbols and i.b not in symbols:
                l.append(i)
            else:
                pass
        return l

    def OnData(self,data):
        if not self.Securities[self.symbols[0]].Exchange.ExchangeOpen:
            return
        #data aggregation
        if self.data_count < self.data_resolution:
            self.data_count +=1
            return
        # refill the initial df
        if len(self.symbols[0].prices) < self.num_bar:
            for i in self.symbols:
                if data.ContainsKey(i) is True:
                    i.prices.append(float(data[i].Close))
                    i.dates.append(data[i].EndTime)
                else:
                    self.Log('%s is missing'%str(i))
                    self.symbols.remove(i)
            self.data_count = 0
            return
        # generate paris
        if self.count == 0 and len(self.symbols[0].prices) == self.num_bar:
            if self.generate_count == 0:
                for i in self.symbols:
                    i.df = pd.DataFrame(i.prices, index = i.dates, columns = ['%s'%str(i)])

                self.generate_pairs()
                self.generate_count +=1


            self.Log('pair list length:'+str(len(self.pair_list)))
        # correlation selection
            for i in self.pair_list:
                i.cor_update()
        # updatet the dataframe and correlation selection
            if len(self.pair_list[0].a_price) != 0:
                for i in self.pair_list:
                    i.df_update()
                    i.cor_update()

            self.selected_pair = [x for x in self.pair_list if x.cor > 0.9]
        # cointegration selection
            for i in self.selected_pair:
                i.cointegration_test()

            self.selected_pair = [x for x in self.selected_pair if x.adf < self.BIC]
            self.selected_pair.sort(key = lambda x: x.adf)

            if len(self.selected_pair) == 0:
                self.Log('no selected pair')
                self.count += 1
                return

            self.selected_pair = self.pair_clean(self.selected_pair)
            for i in self.selected_pair:
                i.touch = 0
                self.Log(str(i.adf) + i.name)

            if len(self.selected_pair) > self.selected_num:
                self.selected_pair = self.selected_pair[:self.selected_num]

            self.count +=1
            self.data_count = 0
            return

        #update the pairs
        if self.count != 0 and self.count < self.one_month:

            num_select = len(self.selected_pair)

            for i in self.pair_list:
                if data.ContainsKey(i.a) is True and data.ContainsKey(i.b) is True:
                    i.price_record(data[i.a],data[i.b])
                else:
                    self.Log('%s has no data'%str(i.name))
                    self.pair_list.remove(i)
        ## selected pairs

            for i in self.selected_pair:
                i.last_error = i.error

            for i in self.trading_pairs:
                i.last_error = i.error

        ## enter
            for i in self.selected_pair:
                price_a = float(data[i.a].Close)
                price_b = float(data[i.b].Close)
                i.error = price_a - (i.model.params[0] + i.model.params[1]*price_b)
                if (self.Portfolio[i.a].Quantity == 0 and self.Portfolio[i.b].Quantity == 0) and i not in self.trading_pairs:
                    if i.touch == 0:
                        if i.error < i.mean_error - self.open_size*i.sd and i.last_error > i.mean_error - self.open_size*i.sd:
                            i.touch += -1
                        elif i.error > i.mean_error + self.open_size*i.sd and i.last_error < i.mean_error + self.open_size*i.sd:
                            i.touch += 1
                        else:
                            pass
                    elif i.touch == -1:
                        if i.error > i.mean_error - self.open_size*i.sd and i.last_error < i.mean_error - self.open_size*i.sd:
                            self.Log('long %s and short %s'%(str(i.a),str(i.b)))
                            i.record_model = i.model
                            i.record_mean_error = i.mean_error
                            i.record_sd = i.sd
                            self.trading_pairs.append(i)
                            self.SetHoldings(i.a, 5.0/(len(self.selected_pair)))
                            self.SetHoldings(i.b, -5.0/(len(self.selected_pair)))
                            i.touch = 0
                    elif i.touch == 1:
                        if i.error < i.mean_error + self.open_size*i.sd and i.last_error > i.mean_error + self.open_size*i.sd:
                            self.Log('long %s and short %s'%(str(i.b),str(i.a)))
                            i.record_model = i.model
                            i.record_mean_error = i.mean_error
                            i.record_sd = i.sd
                            self.trading_pairs.append(i)
                            self.SetHoldings(i.b, 5.0/(len(self.selected_pair)))
                            self.SetHoldings(i.a, -5.0/(len(self.selected_pair)))
                            i.touch = 0
                    else:
                        pass
                else:
                    pass

            # close
            for i in self.trading_pairs:
                if data.ContainsKey(i.a) and data.ContainsKey(i.b):
                    price_a = float(data[i.a].Close)
                    price_b = float(data[i.b].Close)
                    i.error = price_a - (i.record_model.params[0] + i.record_model.params[1]*price_b)
                    if ((i.error < i.record_mean_error + self.close_size*i.record_sd and i.last_error >i.record_mean_error + self.close_size*i.record_sd)
                       or (i.error > i.record_mean_error - self.close_size*i.record_sd and i.last_error <i.record_mean_error - self.close_size*i.record_sd)):
                        self.Log('close %s'%str(i.name))
                        self.Liquidate(i.a)
                        self.Liquidate(i.b)
                        self.trading_pairs.remove(i)
                    elif i.error < i.record_mean_error - self.stop_loss*i.record_sd or i.error > i.record_mean_error + self.stop_loss*i.record_sd:
                        self.Log('close %s to stop loss'%str(i.name))
                        self.Liquidate(i.a)
                        self.Liquidate(i.b)
                        self.trading_pairs.remove(i)
                    else:
                        pass




            self.count +=1
            self.data_count = 0
            return

        if self.count == self.one_month:
            self.count = 0
            self.data_count = 0
            return
