# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2020 QuantConnect Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import statistics as stat
import pickle
from collections import deque

class DynamicCalibratedGearbox(QCAlgorithm):

    def Initialize(self):
        ### IMPORTANT: FOR USERS RUNNING THIS ALGORITHM IN LIVE TRADING,
        ### RUN THE BACKTEST ONCE

        self.tech_ROA_key = 'TECH_ROA'

        # we need 3 extra years to warmup our ROA values
        self.SetStartDate(2012, 9, 1)
        self.SetEndDate(2020, 9, 1)

        self.SetCash(100000)  # Set Strategy Cash

        self.SetBrokerageModel(AlphaStreamsBrokerageModel())
        self.SetAlpha(ConstantAlphaModel(InsightType.Price, InsightDirection.Up, timedelta(days=31)))
        self.SetExecution(ImmediateExecutionModel())
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel(lambda time:None))

        self.AddUniverseSelection(
            FineFundamentalUniverseSelectionModel(self.CoarseFilter, self.FineFilter)
        )
        self.UniverseSettings.Resolution = Resolution.Daily

        self.curr_month = -1

        # store ROA of tech stocks
        self.tech_ROA = {}

        self.symbols = None

        if self.LiveMode and not self.ObjectStore.ContainsKey(self.tech_ROA_key):
            self.Quit('QUITTING: USING LIVE MOVE WITHOUT TECH_ROA VALUES IN OBJECT STORE')

        self.quarters = 0

    def OnEndOfAlgorithm(self):
        self.Log('Algorithm End')

        self.SaveData()

    def SaveData(self):
        '''
        Saves the tech ROA data to ObjectStore
        '''

        # Symbol objects aren't picklable, hence why we use the ticker string
        tech_ROA = {symbol.Value:ROA for symbol, ROA in self.tech_ROA.items()}
        self.ObjectStore.SaveBytes(self.tech_ROA_key, pickle.dumps(tech_ROA))

    def CoarseFilter(self, coarse):

        # load data from ObjectStore
        if len(self.tech_ROA) == 0 and self.ObjectStore.ContainsKey(self.tech_ROA_key):
            tech_ROA = self.ObjectStore.ReadBytes(self.tech_ROA_key)
            tech_ROA = pickle.loads(bytearray(tech_ROA))
            self.tech_ROA = {Symbol.Create(ticker, SecurityType.Equity, Market.USA):ROA for ticker, ROA in tech_ROA.items()}
            return list(self.tech_ROA.keys())

        if self.curr_month == self.Time.month:
            return Universe.Unchanged

        self.curr_month = self.Time.month

        # we only want to update our ROA values every three months
        if self.Time.month % 3 != 1:
            return Universe.Unchanged

        self.quarters += 1

        return [c.Symbol for c in coarse if c.HasFundamentalData]

    def FineFilter(self, fine):
        # book value == FinancialStatements.BalanceSheet.NetTangibleAssets (book value and NTA are synonyms)
        # BM (Book-to-Market) == book value / MarketCap
        # ROA == OperationRatios.ROA
        # CFROA == FinancialStatements.CashFlowStatement.OperatingCashFlow / FinancialStatements.BalanceSheet.TotalAssets
        # R&D to MktCap == FinancialStatements.IncomeStatement.ResearchAndDevelopment / MarketCap
        # CapEx to MktCap == FinancialStatements.CashFlowStatement.CapExReported / MarketCap
        # Advertising to MktCap == FinancialStatements.IncomeStatement.SellingGeneralAndAdministration / MarketCap
        #   note: this parameter may be slightly higher than pure advertising costs

        tech_securities = [f for f in fine if f.AssetClassification.MorningstarSectorCode == MorningstarSectorCode.Technology and
                                                f.OperationRatios.ROA.ThreeMonths]

        for security in tech_securities:
            # we use deques instead of RWs since deques are picklable
            symbol = security.Symbol
            if symbol not in self.tech_ROA:
                # 3 years * 4 quarters = 12 quarters of data
                self.tech_ROA[symbol] = deque(maxlen=12)
            self.tech_ROA[symbol].append(security.OperationRatios.ROA.ThreeMonths)

        if self.LiveMode:
            # this ensures we don't lose new data from an algorithm outage
            self.SaveData()

        # we want to rebalance in the fourth month after the (fiscal) year ends
        #   so that we have the most recent quarter's data
        if self.Time.month != 4 or (self.quarters < 12 and not self.LiveMode):
            return Universe.Unchanged

        # make sure our stocks has these fundamentals
        tech_securities = [x for x in tech_securities if x.OperationRatios.ROA.OneYear and
                                                        x.FinancialStatements.CashFlowStatement.OperatingCashFlow.TwelveMonths and
                                                        x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths and
                                                        x.FinancialStatements.IncomeStatement.ResearchAndDevelopment.TwelveMonths and
                                                        x.FinancialStatements.CashFlowStatement.CapExReported.TwelveMonths and
                                                        x.FinancialStatements.IncomeStatement.SellingGeneralAndAdministration.TwelveMonths and
                                                        x.MarketCap]

        # compute the variance of the ROA for each tech stock
        tech_VARROA = {symbol:stat.variance(ROA) for symbol, ROA in self.tech_ROA.items() if len(ROA) == ROA.maxlen}

        if len(tech_VARROA) < 2:
            return Universe.Unchanged

        tech_VARROA_median = stat.median(tech_VARROA.values())

        # we will now map tech Symbols to various fundamental ratios,
        #   and compute the median for each ratio

        # ROA 1-year
        tech_ROA1Y = {x.Symbol:x.OperationRatios.ROA.OneYear for x in tech_securities}
        tech_ROA1Y_median = stat.median(tech_ROA1Y.values())

        # Cash Flow ROA
        tech_CFROA = {x.Symbol: (
            x.FinancialStatements.CashFlowStatement.OperatingCashFlow.TwelveMonths
            / x.FinancialStatements.BalanceSheet.TotalAssets.TwelveMonths
            ) for x in tech_securities}
        tech_CFROA_median = stat.median(tech_CFROA.values())

        # R&D to MktCap
        tech_RD2MktCap = {x.Symbol: (
            x.FinancialStatements.IncomeStatement.ResearchAndDevelopment.TwelveMonths / x.MarketCap
            ) for x in tech_securities}
        tech_RD2MktCap_median = stat.median(tech_RD2MktCap.values())

        # CapEx to MktCap
        tech_CaPex2MktCap = {x.Symbol: (
            x.FinancialStatements.CashFlowStatement.CapExReported.TwelveMonths / x.MarketCap
            ) for x in tech_securities}
        tech_CaPex2MktCap_median = stat.median(tech_CaPex2MktCap.values())

        # Advertising to MktCap
        tech_Ad2MktCap = {x.Symbol: (
            x.FinancialStatements.IncomeStatement.SellingGeneralAndAdministration.TwelveMonths / x.MarketCap
            ) for x in tech_securities}
        tech_Ad2MktCap_median = stat.median(tech_Ad2MktCap.values())

        # sort fine by book-to-market ratio, get lower quintile
        has_book = [f for f in fine if f.FinancialStatements.BalanceSheet.NetTangibleAssets.TwelveMonths and f.MarketCap]
        sorted_by_BM = sorted(has_book, key=lambda x: x.FinancialStatements.BalanceSheet.NetTangibleAssets.TwelveMonths / x.MarketCap)[:len(has_book)//4]
        # choose tech stocks from lower quintile
        tech_symbols = [f.Symbol for f in sorted_by_BM if f in tech_securities]

        ratioDicts_medians = [(tech_ROA1Y, tech_ROA1Y_median),
                                (tech_CFROA, tech_CFROA_median), (tech_RD2MktCap, tech_RD2MktCap_median),
                                (tech_CaPex2MktCap, tech_CaPex2MktCap_median), (tech_Ad2MktCap, tech_Ad2MktCap_median)]

        def compute_g_score(symbol):
            g_score = 0
            if tech_CFROA[symbol] > tech_ROA1Y[symbol]:
                g_score += 1
            if symbol in tech_VARROA and tech_VARROA[symbol] < tech_VARROA_median:
                g_score += 1
            for ratio_dict, median in ratioDicts_medians:
                if symbol in ratio_dict and ratio_dict[symbol] > median:
                    g_score += 1
            return g_score

        # compute g-scores for each symbol
        g_scores = {symbol:compute_g_score(symbol) for symbol in tech_symbols}

        return [symbol for symbol, g_score in g_scores.items() if g_score >= 5]
