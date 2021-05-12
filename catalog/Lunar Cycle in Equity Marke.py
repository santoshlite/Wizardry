# https://quantpedia.com/Screener/Details/61
from QuantConnect.Data import SubscriptionDataSource
from QuantConnect.Python import PythonData
from datetime import date, timedelta, datetime
from decimal import Decimal
import numpy as np
import pandas as pd


class TradeWtiBrentSpreadAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2004, 1, 1)
        self.SetEndDate(2018, 8, 1)
        self.SetCash(100000)
        # import the custom data
        self.AddData(MoonPhase, "phase", Resolution.Daily)
        self.AddEquity("EEM", Resolution.Daily)
        self.SetBenchmark("EEM")

    def OnData(self, data):
        # long in emerging market index ETF 7 days before the new moon (It's the Last Quarter)
        if self.Securities["phase"].Price == 3 and not self.Portfolio["EEM"].IsLong:
            self.SetHoldings("EEM", 1)
        # short on emerging market index ETF 7 days before the full moon (It's the First Quarter)
        elif self.Securities["phase"].Price == 1 and not self.Portfolio["EEM"].IsShort:
            self.SetHoldings("EEM", -1)


class MoonPhase(PythonData):
    "Class to import Phases of the Moon data from Dropbox"

    def GetSource(self, config, date, isLiveMode):
        return SubscriptionDataSource("https://www.dropbox.com/s/q9rt06tpfjlvymt/MoonPhase.csv?dl=1", SubscriptionTransportMedium.RemoteFile)

    def Reader(self, config, line, date, isLiveMode):
        index = MoonPhase()
        index.Symbol = config.Symbol
        try:
            # Example File Format: (Data starts from 01/07/2004)
            # date                 phase
            # 2004 Jan 07 15:40    Full Moon
            data = line.split(',')
            if data[0] == "date": return None
            index.Time = datetime.strptime(data[0], "%Y %b %d %H:%M").replace(hour=0, minute=0)
            if data[1] == "New Moon":
                index.Value = 0
            elif data[1] == "First Quarter":
                index.Value = 1
            elif data[1] == "Full Moon":
                index.Value = 2
            elif data[1] == "Last Quarter":
                index.Value = 3
        except:
            return None

        return index
