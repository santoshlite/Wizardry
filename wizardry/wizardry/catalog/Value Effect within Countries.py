# https://quantpedia.com/Screener/Details/207
from QuantConnect.Data import SubscriptionDataSource
from QuantConnect.Python import PythonData
import numpy as np
from datetime import datetime
from decimal import Decimal


class ValueEffectWithinCountries(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2000, 1, 8)   # Set Start Date
        self.SetEndDate(2018, 9, 1)     # Set End Date
        self.SetCash(100000)            # Set Strategy Cash
        self.AddData(CAPE, "CAPE", Resolution.Daily, TimeZones.NewYork, True)
        self.symbols = Symbols().tickers
        for key, value in self.symbols.items():
            self.AddEquity(value[1], Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.Rebalance)
        self.slice = None

    def OnData(self, data):
        if data.ContainsKey("CAPE"):
            self.slice = data

    def Rebalance(self):
        self.cape = {}
        for key, value in self.symbols.items():
            cape = getattr(self.slice["CAPE"], key)
            if cape is not None:
                self.cape[value[1]] = cape
        sorted_cape = sorted(self.cape, key = lambda x: self.cape[x])
        # invests the cheapest 33% of countries if those countries have a CAPE below 15
        lowest_cape = sorted_cape[:int(1/3*len(sorted_cape))]
        long_list = [i for i in lowest_cape if self.cape[i]<15]
        invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        for i in invested:
            if i.Value not in long_list:
                self.Liquidate(i)
        for i in long_list:
            self.SetHoldings(i, 1/len(long_list))


class CAPE(PythonData):

    def GetSource(self, config, date, isLiveMode):
        return SubscriptionDataSource("https://www.dropbox.com/s/fcv8x1xeqamg5lx/CAPERatio.csv?dl=1", SubscriptionTransportMedium.RemoteFile)

    def Reader(self, config, line, date, isLiveMode):
        if not (line.strip() and line[1].isdigit()): return None
        index = CAPE()
        index.Symbol = config.Symbol
        # data format
        # Date       Canada  UK     United States  France    Germany   Italy    Spain ...
        # 1/31/00    45.7    25.08  42.18          55.94     51.35     54.34    32.16 ...
        data = line.split(',')
        index.Time = datetime.strptime(data[0], "%m/%d/%y")
        symbols = Symbols().tickers
        for key, value in symbols.items():
            index[key] = float(data[value[0]]) if data[value[0]] else None
        return index


class Symbols:
    def __init__(self):
        # the indiex is the country name
        # the first element of the value is the column number of CAPE ratio value in custom dataset
        # the second element of the value is the corresponding country ETF

        self.tickers = {"Canada":[1, "XIC"],          # S&P/TSX Composite Index: iShares S&P TSX Capped Cmpst Indx Fnd
                        "Uk":[2, "EWU"],              # FTSE 100 Index: iShares MSCI United Kingdom ETF
                        "Us":[3, "SPY"],              # S&P 500 Index: SPDR S&P 500 ETF
                        "France":[4, "EWQ"],          # CAC 40 Index: iShares MSCI France ETF
                        "Germany":[5, "EWG"],         # HDAX Index: iShares MSCI Germany ETF
                        "Italy":[6, "EWI"],           # FTSE MIB Index: iShares MSCI Italy ETF
                        "Spain":[7, "EWP"],           # IBEX 35 Index: iShares MSCI Spain ETF
                        "Russia":[8, "ERUS"],         # RTS Index: iShares MSCI Russia ETF
                        "India":[9, "INDY"],          # NIFTY 50 Index: iShares India 50 ETF
                        "Japan":[10, "EWJ"],          # All Public Companies: iShares MSCI Japan ETF
                        "Singapore":[11, "EWS"],      # STI Index:  iShares MSCI Singapore ETF
                        "Korea":[12,"EWY"],           # KOSPI Index: iShares MSCI South Korea ETF
                        "China":[13, "MCHI"],         # SSE Composite: iShares MSCI China Index Fund
                        "Hongkong":[14, "EWH"],       # Hang Seng Index: iShares MSCI Hong Kong Index Fund
                        "Brazil":[15, "EWZ"],         # Indice Bovespa (Ibovespa): iShares MSCI Brazil ETF
                        "Mexico":[16, "EWW"],         # &P/BMV IPC Index: iShares MSCI Mexico ETF
                        "Southafrica":[17, "EZA"],    # FTSE/JSE CAP Top 40 Index: iShares MSCI South Africa ETF
                        "Australia":[18, "EWA"],      # ASX All Ordinaries Index: iShares MSCI Australia ETF
                        "Turkey":[19, "TUR"],         # BIST 100: iShares MSCI Turkey ETF
                        "Poland":[20, "EPOL"],        # WIG Index: iShares MSCI Poland ETF
                        "Indonesia":[21, "EIDO"],     # IDX Composite: iShares MSCI Indonesia ETF
                        "Philippines":[22, "EPHE"]}   # PSE Composite:  iShares MSCI Philippines Investable
