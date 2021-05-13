from QuantConnect.Python import PythonQuandl
from datetime import timedelta
import numpy as np
import pandas as pd

class ImprovedCommodityMomentumTrading(QCAlgorithm):
    '''
    Demystifying Time-Series Momentum Strategies: Volatility Estimators, Trading Rules and Pairwise Correlations

    This paper proposed 3 modifications to the basic time-series momentum strategies in order to reduce portfolio turnover and improve portfolio performance.

        1. Volatility Estimator: Yang and Zhang (2000) range-based estimator, which replaces the traditional estimator (standard deviation of past daily returns)
        2. Trading Rules: Trading positions takes a continuum of values between -1 and +1 to reflect the statistical strength of price trend, which replaces the traditional trading rules (binary +1 or -1 based on the sign of historical mean return)
        3. Pairwise Correlations: Incorporate signed pairwise correlations in the weighing scheme of portfolio construction

    Reference:
    [1] Baltas, Nick and Kosowski, Robert, "Demystifying Time-Series Momentum Strategies: Volatility Estimators, Trading Rules and Pairwise Correlations", May 8, 2017.
        URL: https://pdfs.semanticscholar.org/a2e9/df201d4b4774fda84a961cc804f2450988c5.pdf
    [2] Yang, Dennis, and Qiang Zhang, "Drift‐Independent Volatility Estimation Based on High, Low, Open, and Close Prices", The Journal of Business, vol. 73, no. 3, 2000, pp. 477–492.
        URL: www.jstor.org/stable/10.1086/209650.'''

    def Initialize(self):

        self.SetStartDate(2008,1, 1)
        self.SetEndDate(2019, 9, 1)
        self.SetCash(25000)

        tickers = ["CHRIS/CME_S1",  # Soybean Futures, Continuous Contract #1
                   "CHRIS/CME_W1",  # Wheat Futures, Continuous Contract #1
                   "CHRIS/CME_SM1", # Soybean Meal Futures, Continuous Contract #1
                   "CHRIS/CME_BO1", # Soybean Oil Futures, Continuous Contract #1
                   "CHRIS/CME_C1",  # Corn Futures, Continuous Contract #1
                   "CHRIS/CME_O1",  # Oats Futures, Continuous Contract #1
                   "CHRIS/CME_LC1", # Live Cattle Futures, Continuous Contract #1
                   "CHRIS/CME_FC1", # Feeder Cattle Futures, Continuous Contract #1
                   "CHRIS/CME_LN1", # Lean Hog Futures, Continuous Contract #1
                   "CHRIS/CME_GC1", # Gold Futures, Continuous Contract #1
                   "CHRIS/CME_SI1", # Silver Futures, Continuous Contract #1
                   "CHRIS/CME_PL1", # Platinum Futures, Continuous Contract #1
                   "CHRIS/ICE_B1",  # Brent Crude Futures, Continuous Contract
                   "CHRIS/ICE_O1",  # Heating Oil Futures, Continuous Contract #1
                   "CHRIS/ICE_M1",  # UK Natural Gas Futures, Continuous Contract #1
                   "CHRIS/ICE_CT1", # Cotton No. 2 Futures, Continuous Contract
                   "CHRIS/ICE_OJ1", # Orange Juice Futures, Continuous Contract
                   "CHRIS/ICE_KC1", # Coffee C Futures, Continuous Contract
                   "CHRIS/ICE_CC1", # Cocoa Futures, Continuous Contract
                   "CHRIS/ICE_G1",  # Gas Oil Futures, Continuous Contract
                   "CHRIS/ICE_RS1"] # Canola Futures, Continuous Contract

        for ticker in tickers:
            data = self.AddData(QuandlFutures, ticker, Resolution.Daily)
            data.SetLeverage(3) # Leverage was set to 3 for each of the futures contract

        self.OneYear = 365      # time period for trading rule calculation
        self.OneMonth = 30      # time period for YZ volatility estimator
        self.ThreeMonths = 90   # time period for pairwise correlation calculation

        # Last trading date tracker to achieve rebalancing the portfolio every month
        self.nextRebalance = self.Time

        # Set portfolio target level of volatility, set to 12%
        self.portfolio_target_sigma = 0.12


    def OnData(self, data):
        '''
        Monthly rebalance at the beginning of each month.
        Portfolio weights for each constituents are calculated based on Baltas and Kosowski weights.
        '''

        # skip if less than 30 days passed since the last trading date
        if self.Time < self.nextRebalance:
            return

        '''Monthly Rebalance Execution'''
        # dataframe that contains the historical data for all securities
        history = self.History(self.Securities.Keys, self.OneYear, Resolution.Daily)
        history.replace(0, np.nan, inplace = True)

        # Get the security symbols are are in the history dataframe
        available_symbols = list(set(history.index.get_level_values(level = 0)))

        # Liquidate symbols that are not in the history dataframe anymore
        for security in self.Securities.Keys:
            if security.Value not in available_symbols:
                self.Liquidate(security, 'Not found in history request')

        # Get the trade signals and YZ volatility for all securities
        trade_signals = self.GetTradingSignal(history)
        volatility = self.GetYZVolatility(history, available_symbols)

        # Get the correlation factor
        CF_rho_bar = self.GetCorrelationFactor(history, trade_signals, available_symbols)

        #Rebalance the portfolio according to Baltas and Kosowski suggested weights
        N_assets = len(available_symbols)
        for symbol, signal, vol in zip(available_symbols, trade_signals, volatility):
            # Baltas and Kosowski weights (Equation 19 in [1])
            weight = (signal*self.portfolio_target_sigma*CF_rho_bar)/(N_assets*vol)
            self.SetHoldings(symbol, weight)

        # Set next rebalance time
        self.nextRebalance = Expiry.EndOfMonth(self.Time)


    def GetCorrelationFactor(self, history, trade_signals, available_symbols):
        '''
        Calculate the Correlation Factor, which is a function of the average pairwise correlation of all portfolio contituents
        - the calculation is based on past three month pairwise correlation
        - Notations:
            rho_bar - average pairwise correlation of all portfolio constituents
            CF_rho_bar - the correlation factor as a function of rho_bar'''

        # Get the past three month simple daily returns for all securities
        settle = history.settle.unstack(level = 0)
        past_three_month_returns = settle.pct_change().loc[settle.index[-1]-timedelta(self.ThreeMonths):]

        # Get number of assets
        N_assets = len(available_symbols)

        # Get the pairwise signed correlation matrix for all assets
        correlation_matrix = past_three_month_returns.corr()

        # Calculate rho_bar
        summation = 0
        for i in range(N_assets-1):
            for temp in range(N_assets - 1 - i):
                j = i + temp + 1
                x_i = trade_signals[i]
                x_j = trade_signals[j]
                rho_i_j = correlation_matrix.iloc[i,j]
                summation += x_i * x_j * rho_i_j

        # Equation 14 in [1]
        rho_bar = (2 * summation) / (N_assets * (N_assets - 1))

        # Calculate the correlation factor (CF_rho_bar)
        # Equation 18 in [1]
        return np.sqrt(N_assets / (1 + (N_assets - 1) * rho_bar))


    def GetTradingSignal(self, history):
        '''
        TREND Trading Signal
        - Uses the t-statistics of historical daily log-returns to reflect the strength of price movement trend
        - TREND Signal Conditions:
            t-stat > 1 => TREND Signal = 1
            t-stat < 1 => TREND Signal = -1
            -1 < t-stat < 1 => TREND Signal = t-stat
            '''
        settle = history.settle.unstack(level = 0)

        # daily futures log-returns based on close-to-close
        log_returns = np.log(settle/settle.shift(1)).dropna()

        # Calculate the t-statistics as
        # (mean-0)/(stdev/sqrt(n)), where n is sample size
        mean = np.mean(log_returns)
        std = np.std(log_returns)
        n = len(log_returns)
        t_stat = mean/(std/np.sqrt(n))

        # cap holding at 1 and -1
        return np.clip(t_stat, a_max=1, a_min=-1)

    def GetYZVolatility(self, history, available_symbols):
        '''
        Yang and Zhang 'Drift-Independent Volatility Estimation'

        Formula: sigma_YZ^2 = sigma_OJ^2 + self.k * sigma_SD^2 + (1-self.k)*sigma_RS^2 (Equation 20 in [1])
            where,  sigma_OJ - (Overnight Jump Volitility estimator)
                    sigma_SD - (Standard Volitility estimator)
                    sigma_RS - (Rogers and Satchell Range Volatility estimator)'''
        YZ_volatility = []

        time_index = history.loc[available_symbols[0]].index
        today = time_index[-1]

        #Calculate YZ volatility for each security and append to list
        for ticker in available_symbols:
            past_month_ohlc = history.loc[ticker].loc[today-timedelta(self.OneMonth):today]
            open, high, low, close = past_month_ohlc.open, past_month_ohlc.high, past_month_ohlc.low, past_month_ohlc.settle
            estimation_period = past_month_ohlc.shape[0]

            # Calculate constant parameter k for Yang and Zhang volatility estimator
            # using the formula found in Yang and Zhang (2000)
            k = 0.34 / (1.34 + (estimation_period + 1) / (estimation_period - 1))

            # sigma_OJ (overnight jump => stdev of close-to-open log returns)
            open_to_close_log_returns = np.log(open/close.shift(1))
            open_to_close_log_returns = open_to_close_log_returns[np.isfinite(open_to_close_log_returns)]
            sigma_OJ = np.std(open_to_close_log_returns)

            # sigma_SD (standard deviation of close-to-close log returns)
            close_to_close_log_returns = np.log(close/close.shift(1))
            close_to_close_log_returns = close_to_close_log_returns[np.isfinite(close_to_close_log_returns)]
            sigma_SD = np.std(close_to_close_log_returns)

            # sigma_RS (Rogers and Satchell (1991))
            h = np.log(high/open)
            l = np.log(low/open)
            c = np.log(close/open)
            sigma_RS_daily = (h * (h - c) + l * (l - c))**0.5
            sigma_RS_daily = sigma_RS_daily[np.isfinite(sigma_RS_daily)]
            sigma_RS = np.mean(sigma_RS_daily)

            # daily Yang and Zhang volatility
            sigma_YZ = np.sqrt(sigma_OJ**2 + k * sigma_SD**2 + (1 - k) * sigma_RS**2)

            # append annualized volatility to the list
            YZ_volatility.append(sigma_YZ*np.sqrt(252))

        return YZ_volatility


class QuandlFutures(PythonQuandl):
    def __init__(self):
        self.ValueColumnName = "Settle"
