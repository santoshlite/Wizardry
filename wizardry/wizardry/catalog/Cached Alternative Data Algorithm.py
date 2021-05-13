from datetime import datetime, timedelta

from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Data import *
from QuantConnect.Data.Custom.CBOE import *
from QuantConnect.Data.Custom.Fred import *
from QuantConnect.Data.Custom.USEnergy import *

class CachedAlternativeDataAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2003, 1, 1)
        self.SetEndDate(2019, 10, 11)
        self.SetCash(100000)

        # QuantConnect caches a small subset of alternative data for easy consumption for the community.
        # You can use this in your algorithm as demonstrated below:

        self.cboeVix = self.AddData(CBOE, "VIX", Resolution.Daily).Symbol
        # United States EIA data: https://eia.gov/
        self.usEnergy = self.AddData(USEnergy, USEnergy.Petroleum.UnitedStates.WeeklyGrossInputsIntoRefineries, Resolution.Daily).Symbol
        # FRED data
        self.fredPeakToTrough = self.AddData(Fred, Fred.OECDRecessionIndicators.UnitedStatesFromPeakThroughTheTrough, Resolution.Daily).Symbol

    def OnData(self, data):
        if data.ContainsKey(self.cboeVix):
            vix = data.Get(CBOE, self.cboeVix)
            self.Log(f"VIX: {vix}")

        if data.ContainsKey(self.usEnergy):
            inputIntoRefineries = data.Get(USEnergy, self.usEnergy)
            self.Log(f"U.S. Input Into Refineries: {inputIntoRefineries}")

        if data.ContainsKey(self.fredPeakToTrough):
            peakToTrough = data.Get(Fred, self.fredPeakToTrough)
            self.Log(f"OECD based Recession Indicator for the United States from the Peak through the Trough: {peakToTrough}")
