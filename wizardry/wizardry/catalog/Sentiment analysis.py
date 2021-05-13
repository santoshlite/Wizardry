from QuantConnect.Data.Custom.Tiingo import *
from datetime import datetime, timedelta
import numpy as np

class TiingoNewsSentimentAlgorithm(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2021, 1, 1)
        symbols = [Symbol.Create("PYPL", SecurityType.Equity, Market.USA),
        Symbol.Create("BABA", SecurityType.Equity, Market.USA)]
        self.SetUniverseSelection(ManualUniverseSelectionModel(symbols))
        self.SetAlpha(NewsSentimentAlphaModel())
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())
        self.SetExecution(ImmediateExecutionModel())
        self.SetRiskManagement(NullRiskManagementModel())

class NewsData():
    def __init__(self, symbol):
        self.Symbol = symbol
        self.Window = RollingWindow[float](100)

class NewsSentimentAlphaModel(AlphaModel):

    def __init__(self):
        self.newsData = {}

        self.wordScores = {
            "bad": -0.5, "good": 0.5, "negative": -0.5,
            "great": 0.5, "growth": 0.5, "fail": -0.5,
            "failed": -0.5, "success": 0.5, "nailed": 0.5,
            "beat": 0.5, "missed": -0.5, "profitable": 0.5,
            "beneficial": 0.5, "right": 0.5, "positive": 0.5,
            "large":0.5, "attractive": 0.5, "sound": 0.5,
            "excellent": 0.5, "wrong": -0.5, "unproductive": -0.5,
            "lose": -0.5, "missing": -0.5, "mishandled": -0.5,
            "un_lucrative": -0.5, "up": 0.5, "down": -0.5,
            "unproductive": -0.5, "poor": -0.5, "wrong": -0.5,
            "worthwhile": 0.5, "lucrative": 0.5, "solid": 0.5
        }

    def Update(self, algorithm, data):

        insights = []
        news = data.Get(TiingoNews)

        for article in news.Values:
            words = article.Description.lower().split(" ")
            score = sum([self.wordScores[word] for word in words
                if word in self.wordScores])

            #1. Get the underlying symbol and save to the variable symbol
            symbol = article.Symbol.Underlying

            #2. Add scores to the rolling window associated with its newsData symbol
            self.newsData[symbol].Window.Add(score)
            #3. Sum the rolling window scores, save to sentiment
            # If sentiment aggregate score for the time period is greater than 5, emit an up insight
            sentiment = sum(self.newsData[symbol].Window)

            if sentiment > 5:
                insights.append(Insight.Price(symbol, timedelta(1), InsightDirection.Up, None, None))

        return insights

    def OnSecuritiesChanged(self, algorithm, changes):

        for security in changes.AddedSecurities:
            symbol = security.Symbol
            newsAsset = algorithm.AddData(TiingoNews, symbol)
            self.newsData[symbol] = NewsData(newsAsset.Symbol)

        for security in changes.RemovedSecurities:
            newsData = self.newsData.pop(security.Symbol, None)
            if newsData is not None:
                algorithm.RemoveSecurity(newsData.Symbol)
