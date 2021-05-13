from QuantConnect.Python import PythonQuandl
from datetime import datetime, timedelta
from QuantConnect.Python import PythonData
from decimal import Decimal
from datetime import timedelta
from QuantConnect.Data import SubscriptionDataSource
from collections import deque

class ShortTermReversalWithFutures(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2013, 2, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(10000000)

        self.tickers = ["CME_SF1_EF", "CME_MP1_FF",  "CME_CD1_EF", "CME_ED8_FF",               # Currencies
                        "CME_NQ1_EF", "CME_MD1_EF", "CME_ES1_EF", "CME_YM1_EF", "CME_NK1_EF",  # Financial indices
                        "CME_C1_EF", "CME_SM1_EF",  "ICE_CC1_EF",  "CME_LC1_EF",               # Agricultural product
                        "CME_KW1_EF", "CME_S1_EF", "ICE_KC1_EF", "CME_LC1_EF",
                        "CME_HG1_FF",  "CME_GC1_EF", "SHFE_AL1_EF",  "SHFE_CU1_EF",            # Commodities
                        "CME_CL1_EF", "ICE_T1_FR", "CME_HO1_EF"]
        self.length = len(self.tickers)
        for ticker in self.tickers:
            self.AddData(Futures, ticker)
        # create the deque list to save the weekly history dataframe
        self.window = deque(maxlen=2)
        # rebalance the portfolio every week on Wednesday
        self.Schedule.On(self.DateRules.Every(DayOfWeek.Wednesday, DayOfWeek.Wednesday), self.TimeRules.At(0, 0), self.WeeklyTrade)

    def WeeklyTrade(self):
        hist = self.History(self.tickers, self.Time-timedelta(days=7), self.Time,Resolution.Daily)
        self.window.append(hist)
        if len(self.window) == self.window.maxlen:
            hist_t2 = self.window[0] # the weekly history dataframe two week ago
            hist_t1 = self.window[1] # the weekly history dataframe a week ago
            top_vol, bottom_vol = self.CalculateChange("volume", hist_t2, hist_t1)
            top_OI, bottom_OI = self.CalculateChange("open_interest", hist_t2, hist_t1)
            # the intersection of top volume group and bottom open interest group
            trade_group = list(set(top_vol) & set(bottom_OI))
            returns = {}
            for ticker in trade_group:
                res = (hist_t1.loc[ticker]["settle"][-1] - hist_t2.loc[ticker]["settle"][-1]) / hist_t2.loc[ticker]["settle"][-1]
                returns[ticker] = res

            sortedByReturn = sorted(returns, key = lambda x: returns[x])

            if len(sortedByReturn) >= 2:
                if self.Portfolio.Invested:
                    self.Liquidate()
                self.SetHoldings(sortedByReturn[-1], -0.3)
                self.SetHoldings(sortedByReturn[0], 0.3)

    def CalculateChange(self, column_name, hist_t2, hist_t1):
        # calculate the weekly change and sort by the colume value
        value_t2 = hist_t2[column_name].unstack(level=0).sum(axis=0)
        value_t1 = hist_t1[column_name].unstack(level=0).sum(axis=0)
        delta = (value_t1 - value_t2).sort_values(ascending=True)
        top = list(delta[:int(self.length*0.5)].index)
        bottom = list(delta[-int(self.length*0.5):].index)
        return top, bottom


class Futures(PythonData):
    # import the futures custom data from dropbox

    def GetSource(self, config, date, isLiveMode):
        key = { "CME_C1_EF": "ptqr9mlbwmrwmha",
                "CME_CL1_EF": "pjwn2f1ym3030ql",
                "CME_ED8_FF": "kqmfgzlp4mljrmx",
                "CME_ES1_EF": "g88576n8n3y8fn9",
                "CME_GC1_EF": "ub1bdrukz02v820",
                "CME_HG1_FF": "nlm5ws5zxucdjg2",
                "CME_HO1_EF": "fsu70u9b7oxcirm",
                "CME_CD1_EF": "23cn1u489voxwr0",
                "CME_KW1_EF": "c5omhcfkfzt9x6b",
                "CME_LC1_EF": "slslbez9yw3763w",
                "CME_MD1_EF": "afb2p8urj99hg5p",
                "CME_MP1_FF": "zm13mpkyphtts2p",
                "CME_NG1_EF": "7y6c4wfgxyhq9eg",
                "CME_NK1_EF": "ufer5ypdn9dfehj",
                "CME_NQ1_EF": "fzqkino0ao3bm7y",
                "ICE_KC1_EF": "nl7ax33p05x7esz",
                "CME_S1_EF": "w00ryar0c8mxfmz",
                "CME_SF1_EF": "s0lqt3j8edyhp9c",
                "CME_SM1_EF": "zdt4okvkk6hxojb",
                "ICE_CC1_EF": "3n51khfd6nzkcqx",
                "CME_YM1_EF": "tyh0csc8q236bv5",
                "SHFE_CU1_EF": "uhrezib2dx2z2xd",
                "SHFE_AL1_EF": "u9xbkh5seja5f69",
                "ICE_T1_FR": "lxkcewy0jh8qw5o"}
        source = "https://www.dropbox.com/s/"+ key[config.Symbol.Value] +"/" + config.Symbol.Value +".csv?dl=1"
        return SubscriptionDataSource(source, SubscriptionTransportMedium.RemoteFile)

    def Reader(self, config, line, date, isLiveMode):
        futures = Futures()
        futures.Symbol = config.Symbol
        data = line.split(',')
        if data[0] == "date": return None
        futures.Time = datetime.strptime(data[0], "%m/%d/%y")
        futures.Value = float(data[4])
        futures["settle"] = float(data[4])
        futures["volume"] = float(data[5])
        futures["open_interest"] = float(data[6])

        return futures
