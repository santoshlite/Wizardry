from EtfSmaAlphaModel import EtfSmaAlphaModel
class ParticleQuantumChamber(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2015, 6, 15)
        self.SetEndDate(2020, 6, 15)
        self.SetCash(100000)

        self.sso = Symbol.Create('SSO', SecurityType.Equity, Market.USA)  # SSO = 2x levered SPX
        self.shy = Symbol.Create('SHY', SecurityType.Equity, Market.USA)  # SHY = short term Treasury ETF

        self.SetWarmup(200)

        self.SetBenchmark('SPY')

        self.UniverseSettings.Resolution = Resolution.Hour
        self.SetAlpha(EtfSmaAlphaModel(self.sso, self.shy))
        self.SetUniverseSelection(ManualUniverseSelectionModel([self.sso, self.shy]))
        self.SetExecution(ImmediateExecutionModel())
        self.SetBrokerageModel(AlphaStreamsBrokerageModel())
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())
