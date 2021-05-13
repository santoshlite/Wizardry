from datetime import timedelta, datetime

class SMAPairsTrading(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)

        symbols = [Symbol.Create("HZN", SecurityType.Equity, Market.USA), Symbol.Create("ISRG", SecurityType.Equity, Market.USA)]
        self.AddUniverseSelection(ManualUniverseSelectionModel(symbols))
        self.UniverseSettings.Resolution = Resolution.Hour
        self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
        self.AddAlpha(PairsTradingAlphaModel())
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())
        self.SetExecution(ImmediateExecutionModel())

    def OnEndOfDay(self, symbol):
        self.Log("Taking a position of " + str(self.Portfolio[symbol].Quantity) + " units of symbol " + str(symbol))

class PairsTradingAlphaModel(AlphaModel):

    def __init__(self):
        self.pair = [ ]
        self.spreadMean = SimpleMovingAverage(500)
        self.spreadStd = StandardDeviation(500)
        self.period = timedelta(hours=2)

    def Update(self, algorithm, data):
        spread = self.pair[1].Price - self.pair[0].Price
        self.spreadMean.Update(algorithm.Time, spread)
        self.spreadStd.Update(algorithm.Time, spread)

        upperthreshold = self.spreadMean.Current.Value + self.spreadStd.Current.Value
        lowerthreshold = self.spreadMean.Current.Value - self.spreadStd.Current.Value

        if spread > upperthreshold:
            return Insight.Group(
                [
                    Insight.Price(self.pair[0].Symbol, self.period, InsightDirection.Up),
                    Insight.Price(self.pair[1].Symbol, self.period, InsightDirection.Down)
                ])

        if spread < lowerthreshold:
            return Insight.Group(
                [
                    Insight.Price(self.pair[0].Symbol, self.period, InsightDirection.Down),
                    Insight.Price(self.pair[1].Symbol, self.period, InsightDirection.Up)
                ])

        return []

    def OnSecuritiesChanged(self, algorithm, changes):
        self.pair = [x for x in changes.AddedSecurities]

        #1. Call for 500 bars of history data for each symbol in the pair and save to the variable history
        history = algorithm.History([x.Symbol for x in self.pair], 500)
        #2. Unstack the Pandas data frame to reduce it to the history close price
        history = history = history.close.unstack(level=0)
        #3. Iterate through the history tuple and update the mean and standard deviation with historical data
        for tuple in history.itertuples():
            self.spreadMean.Update(tuple[0], tuple[2]-tuple[1])
            self.spreadStd.Update(tuple[0], tuple[2]-tuple[1])
