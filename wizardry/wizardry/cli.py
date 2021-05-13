from __future__ import print_function, unicode_literals, with_statement
import typer
import textwrap
from contextlib import contextmanager
try:
    from StringIO import StringIO ## for Python 2
except ImportError:
    from io import StringIO ## for Python 3
from PyInquirer import style_from_dict, Token, prompt, Separator
from pprint import pprint
from pathlib import*
import os.path
import requests
import re

import os
import shutil
import sys
from colorama import init
init(strip=not sys.stdout.isatty())
from termcolor import cprint
from pyfiglet import figlet_format

def urlify(s):

    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)

    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '%20', s)

    return s

INDENT = ' ' * 4

class IndentManager(object):
    """
    A context manager for indentation. Used internally by the source manager
    to provide the indent context manager. And the indent and dedent methods.
    """
    def __init__(self, indent_with=INDENT):
        self.indent_with = indent_with
        self.level = 0

    def __call__(self):
        """
        Raise the indentation level if this instance is called like a method.
        """
        self.indent()

    def __str__(self):
        """
        self.indent_with multiplied by the current indentation level.
        Used to indent strings to the correct depth.
        """
        return self.indent_with * self.level

    def __enter__(self):
        """
        Start of an indentation context.
        """
        self.indent()
        return self

    def __exit__(self, *exc_info):
        """
        Ends of an indentation context, so dedent.
        """
        self.dedent()

    def indent(self):
        """Raise the indentation level by 1."""
        self.level = self.level + 1
        return self

    def dedent(self):
        """
        Decrease the indentation level by one. If the indentation level is
        already at zero a ``DedentException`` is raised.
        """
        if self.level == 0:
            raise DedentException('Indent level is already at zero.')
        self.level = self.level - 1

    def reset(self):
        """
        Reset the indentation level to zero.
        """
        self.level = 0


class SourceBuilder(object):
    """
    A basic source code writer.
    Usage
    -----
    Create a SourceBuilder instance  and write code to it to line by line.
    By using the ``indent`` context manager each line gets correctly indented
    and the input indentation will resemble the output::
      >>> sb = SourceBuilder()
      >>> sb.writeln()
      >>> sb.writeln('def hello_world():')
      >>> with sb.indent:
      ...     sb.writeln('print \'Hello World\'')
      ...
      ...
      >>> sb.writeln()
      >>> sb.writeln('hello_world()')
      >>> source = sb.end()
      >>> print source
      def hello_world():
          print 'Hello World'
      hello_world()
    If for some reason context managers can't be used ``indent`` also works
    as a method. Combined with the ``dedent`` method code indentation levels
    can be controlled manually.::
      >>> sb = SourceBuilder()
      >>> sb.writeln()
      >>> sb.writeln('def hello_world():')
      >>> sb.indent()
      >>> sb.writeln('print \'Hello World\'')
      >>> sb.dedent()
      >>> sb.writeln()
      >>> sb.writeln('hello_world()')
      >>> source = sb.end()
      >>> print source
      def hello_world():
           print 'Hello World'
      hello_world()
    It's not advised to use ``sb.indent`` in ``with`` statements in combination
    with calls to ``sb.dedent()`` or ``sb.indent()``.
    """
    def __init__(self, indent_with=INDENT):
        """
        Initialize SourceBuilder, ``indent_with`` is set to 4 spaces
        by default.
        """
        self._out = StringIO()
        self.indent = IndentManager(indent_with=indent_with)

    def write(self, code):
        """
        Write code at the current indentation level.
        """
        self._out.write(str(self.indent))
        self._out.write(code)

    def writeln(self, code=''):
        """
        Write a line at the current indentation level.
        If no code is given only a newline is written.
        """
        if code:
            self.write(code)
        self._out.write('\n')

    def dedent(self):
        """
        Decrease the current indentation level. Should only be used if
        the indent context manager is not used.
        Raises a ``DedentException`` if decreasing indentation level is not
        possible.
        """
        self.indent.dedent()

    def end(self):
        """
        Get the generated source and resets the indent level.
        """
        self.indent.reset()
        return self._out.getvalue()

    def truncate(self):
        '''
        Discard generated source and memory buffer and resets the indent level.
        '''
        if not self._out.closed:
            self._out.close()
        self._out = StringIO()
        self.indent.reset()

    def close(self):
        '''
        Convenience method for use with ``contextlib.closing``.
        Calls ``self.truncate()``.
        '''
        self.truncate()


INDENT = ' ' * 4
TRIPLE_QUOTES = '"' * 3
DOCSTRING_WIDTH = 72


class PySourceBuilder(SourceBuilder):
    """
    A special SourceBuilder that provides some convenience context managers
    for writing well formatted Python code.
    """
    def __init__(self, indent_with=INDENT):
        super(PySourceBuilder, self).__init__(indent_with=indent_with)

    @contextmanager
    def block(self, code, lines_before=0):
        """
        A context manager for block structures. It's a generic way to start a
        control structure (if, try, while, for etc.) or a class, function or
        method definition.
        The given ``code`` will be printed preceded by 0 or more blank lines,
        controlled by the ``lines_before`` parameter. An indent context is
        then started.
        Example::
            sb = PySourceBuilder()
            >>>
            >>> with sb.block('class Hello(object):', 2):
            ...     with sb.block('def __init__(self, what=\'World\'):', 1):
            ...         sb.writeln('pass')
            ...
            >>> print sb.end()
            class Hello(object):
                def __init__(self, what='World'):
                    pass
        """
        for i in range(lines_before):
            self.writeln()
        self.writeln(code)
        with self.indent:
            yield

    def docstring(self, doc, delimiter=TRIPLE_QUOTES, width=DOCSTRING_WIDTH):
        """
        Write a docstring. The given ``doc`` is surrounded by triple double
        quotes (\"\"\"). This can be changed by passing a different
        ``delimiter`` (e.g. triple single quotes).
        The docstring is formatted to not run past 72 characters per line
        (including indentation). This can be changed by passing a different
        ``width`` parameter.
        """
        doc = textwrap.dedent(doc).strip()
        max_width = width - len(str(self.indent))
        lines = doc.splitlines()
        if len(lines) == 1 and len(doc) < max_width - len(delimiter) * 2:
            self.writeln(u'%s%s%s' % (delimiter, doc, delimiter))
        else:
            self.writeln(delimiter)
            for line in lines:
                if not line.strip():
                    self.writeln()
                for wrap in textwrap.wrap(line, max_width):
                    self.writeln(wrap)
            self.writeln()
            self.writeln(delimiter)


app = typer.Typer()

@app.command()
def framework():
    print("\n")
    text="Quantconnect"
    cprint(figlet_format(text, font="slant"), "yellow")
    print("\n")
    style = style_from_dict({
        Token.Separator: '#cc5454',
        Token.QuestionMark: '#673ab7 bold',
        Token.Selected: '#ffba26',  # default
        Token.Pointer: '#673ab7 bold',
        Token.Instruction: '',  # default
        Token.Answer: '#ffba26 bold',
        Token.Question: '',
    })

    print("Let's build a strategy!")

    questions = [
        {
            'type': 'checkbox',
            'message': 'Choose one or several alpha',
            'name': 'alpha',
            'choices': [
                Separator('\n= Alpha ='),
                {
                    'name': 'RSI'
                },
                {
                    'name': 'EMA Cross'
                },
                {
                    'name': 'MACD'
                },
                {
                    'name': 'Historical Returns'
                },
                {
                    'name': 'Pairs Trading'
                },
                {
                    'name': 'Mean Reversion IBS'
                },
                {
                    'name': 'Greenblatt Magic Formula'
                },
                {
                    'name': 'Mortgage Rate Volatility'
                },
                {
                    'name': 'Intraday Reversal'
                },
                {
                    'name': 'Triangular Arbitrage'
                },
                {
                    'name': 'Dual Thrust'
                },
                {
                    'name': 'None'
                }
            ],

            'validate': lambda answer: 'You must choose one of these' \
                if len(answer) == 0 else True

        },
        {
            'type': 'list',
            'message': 'Choose an universe',
            'name': 'universe',
            'choices': [
                Separator('\n= Universe ='),

                {
                    'name': 'Large Cap Equities'
                },
                {
                    'name': 'EMA Cross Universe'
                },
                {
                    'name': 'Coarse Universe'
                },
                {
                    'name': 'Coarse-Fine Universe'
                },
                {
                    'name': 'Uncorrelated Universe'
                },
                {
                    'name': 'Options Universe'
                },
                {
                    'name': 'Future Universe'
                },
                {
                    'name': 'Scheduled Universe'
                },
                {
                    'name': 'Manual Selection'
                },
                {
                    'name': 'None'
                }
            ],
            'validate': lambda answer: 'You must choose at least one of these' \
                if len(answer) == 0 else True
        },

        {
            'type': 'list',
            'message': 'Choose the construction of your portfolio',
            'name': 'portfolio',
            'choices': [
                Separator('\n= Portfolio ='),
                #self.SetPortfolioConstruction(ConfidenceWeightedPortfolioConstructionModel())
                {
                    'name': 'Equal Weighting'
                },
                {
                    'name': 'Mean-Variance'
                },
                {
                    'name': 'Black Litterman'
                },
                {
                    'name': 'Confidence Weighted Portfolio'
                },
                {
                    'name': 'None'
                } #optimizer unconstrained, sharpe, min variance
            ],
            'validate': lambda answer: 'You must choose at least one of these' \
                if len(answer) == 0 else True
        },
        {
                'type': 'list',
                'message': 'Choose the type of execution',
                'name': 'execution',
                'choices': [
                    Separator('\n= Execution ='),
                    {
                        'name': 'Immediate'
                    },
                    {
                        'name': 'VWAP'
                    },
                    {
                        'name': 'Standard deviation'
                    },
                    {
                        'name': 'None'
                    }
                ],
                'validate': lambda answer: 'You must choose at least one of these' \
                    if len(answer) == 0 else True
            },
                {
                        'type': 'list',
                        'message': 'Choose the type of risk management',
                        'name': 'risk',
                        'choices': [
                            Separator('\n= Risk ='),
                            {
                                'name': 'Maximum Drawdown'
                            },
                            {
                                'name': 'Sector Exposure'
                            },
                            {
                                'name': 'Maximum Unrealized Profit Percent Per Security'
                            },
                            {
                                'name': 'Trailing Stop Risk Management Model'
                            },
                            {
                                'name': 'None'
                            }
                        ],
                        'validate': lambda answer: 'You must choose at least one of these' \
                            if len(answer) == 0 else True
                    },
                {
                        'type': 'input',
                        'message': 'Type the start date in this format YYYY, MM, DD (e.g : 2017, 1, 1)',
                        'name': 'start',
                        'validate': lambda answer: 'You must choose at least one of these' \
                            if len(answer) == 0 else True
                    },
                {
                        'type': 'input',
                        'message': 'Set Strategy cash (e.g : 100000)',
                        'name': 'cash',
                        'validate': lambda answer: 'You must choose at least one of these' \
                            if len(answer) == 0 else True
                    },
                {
                        'type': 'confirm',
                        'message': 'Build the strategy? (make sure there is no main.py file in this directory)',
                        'name': 'build',
                        'validate': lambda answer: 'You must choose at least one of these' \
                            if len(answer) == 0 else True
                    }
    ]

    answers = prompt(questions, style=style)

    factors = []
    for n in answers:
        list = answers[n]
        factors.append(list)


    #code generation
    sb = SourceBuilder()
    sb.writeln('from System import *')
    sb.writeln('from QuantConnect import *')
    sb.writeln('from QuantConnect.Algorithm import *')
    sb.writeln('from QuantConnect.Indicators import *')
    sb.writeln('from QuantConnect.Algorithm.Framework import *')
    sb.writeln('from QuantConnect.Algorithm.Framework.Risk import *')
    sb.writeln('from QuantConnect.Algorithm.Framework.Alphas import *')
    sb.writeln('from QuantConnect.Algorithm.Framework.Selection import *')
    sb.writeln('from QuantConnect.Algorithm.Framework.Execution import *')
    sb.writeln('from QuantConnect.Algorithm.Framework.Portfolio import *')
    sb.writeln()


    klasses = ['DancingBlueOwl']
    for klass in klasses:
         sb.writeln('class {0}(QCAlgorithm):'.format(klass))

         sb.writeln()
         with sb.indent:
             sb.writeln('def Initialize(self):')
             with sb.indent:

                 sb.writeln('self.SetStartDate('+factors[5]+') # Set Start Date')
                 sb.writeln('self.SetCash('+factors[6]+') # Set Strategy Cash')
                 sb.writeln('#self.AddEquity("SPY", Resolution.Minute)')
                 sb.writeln()

                  #alpha
                 if "RSI" in factors[0]:
                   sb.writeln('self.AddAlpha(RsiAlphaModel(60, Resolution.Minute))')

                 if "EMA Cross" in factors[0]:
                   sb.writeln('self.AddAlpha(EmaCrossAlphaModel(50, 200, Resolution.Minute))')

                 if "MACD" in factors[0]:
                   sb.writeln('self.AddAlpha(MacdAlphaModel(12, 26, 9, MovingAverageType.Simple, Resolution.Daily))')

                 if "Historical Returns" in factors[0]:
                   sb.writeln('self.AddAlpha(HistoricalReturnsAlphaModel(14, Resolution.Daily))')

                 if "Pairs Trading" in factors[0]:
                   sb.writeln('self.AddAlpha(PearsonCorrelationPairsTradingAlphaModel(252, Resolution.Daily))')

                 if "Mean Reversion IBS" in factors[0]:
                   sb.writeln('self.SetAlpha(MeanReversionIBSAlphaModel())')

                 if "Greenblatt Magic Formula" in factors[0]:
                   sb.writeln('self.SetAlpha(RateOfChangeAlphaModel())')

                 if "Mortgage Rate Volatility" in factors[0]:
                   sb.writeln('self.SetAlpha(MortgageRateVolatilityAlphaModel(self))')

                 if "Intraday Reversal" in factors[0]:
                   sb.writeln('self.SetAlpha(IntradayReversalAlphaModel(5, resolution))')

                 if "Triangular Arbitrage" in factors[0]:
                   sb.writeln('self.SetAlpha(ForexTriangleArbitrageAlphaModel(Resolution.Minute, symbols))')

                 if "Dual Thrust" in factors[0]:
                   sb.writeln('self.SetAlpha(DualThrustAlphaModel(self.k1, self.k2, self.rangePeriod, self.UniverseSettings.Resolution, self.consolidatorBars))')

                 if factors[0] == "None":
                   pass

                 sb.writeln()

                 #execution
                 if factors[3] == "Immediate":
                   sb.writeln('self.SetExecution(ImmediateExecutionModel())')

                 if factors[3] == "VWAP":
                   sb.writeln('self.SetExecution(VolumeWeightedAveragePriceExecutionModel())')

                 if factors[3] == "Standard deviation":
                   sb.writeln('self.SetExecution(StandardDeviationExecutionModel(60, 2, Resolution.Minute))')

                 if factors[3] == "None":
                     pass

                 sb.writeln()

                 #portfolio

                 if factors[2] == "Equal Weighting":
                   sb.writeln('self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())')

                 if factors[2] == "Mean-Variance":
                   sb.writeln('self.SetPortfolioConstruction(MeanVarianceOptimizationPortfolioConstructionModel())')

                 if factors[2] == "Black Litterman":
                   sb.writeln('self.SetPortfolioConstruction(BlackLittermanOptimizationPortfolioConstructionModel())')

                 if factors[2] == "Confidence Weighted Portfolio":
                   sb.writeln('self.SetPortfolioConstruction(ConfidenceWeightedPortfolioConstructionModel())')


                 if factors[2] == "None":
                     pass

                 sb.writeln()

                 #risk management

                 if factors[4] == "Maximum Drawdown":
                   sb.writeln('self.SetRiskManagement(MaximumDrawdownPercentPerSecurity(0.01))')

                 if factors[4] == "Sector Exposure":
                   sb.writeln('self.SetRiskManagement(MaximumSectorExposureRiskManagementModel())')

                 if factors[4] == "Maximum Unrealized Profit Percent Per Security":
                   sb.writeln('self.SetRiskManagement(MaximumUnrealizedProfitPercentPerSecurity(maximumUnrealizedProfitPercent = 0.1))')

                 if factors[4] == "Trailing Stop Risk Management Model":
                   sb.writeln('self.SetRiskManagement(TrailingStopRiskManagementModel(0.01))')



                 if factors[4] == "None":
                     pass

                 sb.writeln()




                 #universe

                 if factors[1] == "Large Cap Equities":
                   sb.writeln('self.SetUniverseSelection(QC500UniverseSelectionModel())')

                 if factors[1] == "Uncorrelated Universe":
                   sb.writeln('self.SetUniverseSelection(UncorrelatedUniverseSelectionModel())')

                 if factors[1] == "Options Universe":
                   sb.writeln('self.SetUniverseSelection(OptionsUniverseSelectionModel())')

                 if factors[1] == "Future Universe":
                   sb.writeln('self.SetUniverseSelection(FutureUniverseSelectionModel())')

                 if factors[1] == "EMA Cross Universe":
                   sb.writeln('fastPeriod = 10')
                   sb.writeln('slowPeriod = 30')
                   sb.writeln('count = 10')
                   sb.writeln('self.SetUniverseSelection(EmaCrossUniverseSelectionModel(fastPeriod, slowPeriod, count))')

                 if factors[1] == "Coarse Universe":
                   sb.writeln('self.SetUniverseSelection(CoarseFundamentalUniverseSelectionModel(self.CoarseSelectionFunction))')

                 if factors[1] == "Coarse-Fine Universe":
                   sb.writeln('self.__numberOfSymbols = 100')
                   sb.writeln('self.__numberOfSymbolsFine = 5')
                   sb.writeln('self.SetUniverseSelection(FineFundamentalUniverseSelectionModel(self.CoarseSelectionFunction, self.FineSelectionFunction, None, None))')

                 if factors[1] == "Scheduled Universe":
                   sb.writeln('# selection will run on mon/tues/thurs at 00:00/06:00/12:00/18:00')
                   sb.writeln('self.SetUniverseSelection(ScheduledUniverseSelectionModel(')
                   with sb.indent:
                              sb.writeln('self.DateRules.Every(DayOfWeek.Monday, DayOfWeek.Tuesday, DayOfWeek.Thursday),')
                              sb.writeln('self.TimeRules.Every(timedelta(hours = 12)),')
                              sb.writeln('self.SelectSymbols')
                   sb.writeln('))')

                 if factors[1] == "Manual Selection":
                   sb.writeln('symbols = [ Symbol.Create("SPY", SecurityType.Equity, Market.USA) ]')
                   sb.writeln('self.SetUniverseSelection( ManualUniverseSelectionModel(symbols) )')

                 if factors[1] == "None":
                     pass


                 sb.writeln()
                 sb.writeln()
         with sb.indent:
          sb.writeln('def OnData(self, data):')
          with sb.indent:
                 sb.writeln('# if not self.Portfolio.Invested:')
                 sb.writeln('#    self.SetHoldings("SPY", 1)')


    source = sb.end()

    with open('main.py', 'a') as file:
        print(source, file=file)
    print("Just created the main.py file!")


@app.command()
def library():
        style = style_from_dict({
            Token.Separator: '#cc5454',
            Token.QuestionMark: '#673ab7 bold',
            Token.Selected: '#ffba26',  # default
            Token.Pointer: '#673ab7 bold',
            Token.Instruction: '',  # default
            Token.Answer: '#ffba26 bold',
            Token.Question: '',
        })

        questions = [
            {
                'type': 'list',
                'message': 'Choose one of these algorithm from Quantconnect library (new stuff coming soon!)',
                'name': 'catalog',
                'choices': [
                    Separator('\n= Our Super Catalog ='),
                    {
                        'name': 'Simple RSI Strategy'
                    },
                    {
                        'name': 'Sentiment analysis'
                    },
                    {
                        'name': 'Combining Mean Reversion and Momentum in Forex Market'
                    },
                    {
                        'name': 'CAPM Alpha Ranking Strategy on Dow 30 Companies'
                    },
                    {
                        'name': 'Pairs Trading Copula Method'
                    },
                    {
                        'name': 'Pairs Trading Cointegration Method'
                    },
                    {
                        'name': 'Dynamic Breakout II'
                    },
                    {
                        'name': 'Dual Thrust'
                    },
                    {
                        'name': 'Use Crude Oil to Predict Equity Returns'
                    },
                    {
                        'name': 'Intraday Dynamic Pairs Trading using Correlation and Cointegration Approach'
                    },
                    {
                        'name': 'Momentum Strategy Based on the Low Frequency Component of Forex Market'
                    },
                    {
                        'name': 'Stock Selection Strategy Based on Fundamental Factors'
                    },
                    {
                        'name': 'Fundamental Factor Long Short Strategy'
                    },
                    {
                        'name': 'Short-Term Reversal Strategy in Stocks'
                    },
                    {
                        'name': 'Asset Class Trend Following'
                    },
                    {
                        'name': 'Asset Class Momentum'
                    },
                    {
                        'name': 'Sector Momentum'
                    },
                    {
                        'name': 'Overnight Anomaly'
                    },
                    {
                        'name': 'Forex Carry Trade'
                    },
                    {
                        'name': 'Volatility Effect in Stocks'
                    },
                    {
                        'name': 'Forex Momentum'
                    },
                    {
                        'name': 'Pairs Trading with Stocks'
                    },
                    {
                        'name': 'Short Term Reversal'
                    },
                    {
                        'name': 'Momentum Effects in Stocks'
                    },
                    {
                        'name': 'Momentum Effect in Country Equity Indexes'
                    },
                    {
                        'name': 'Mean Reversion Effect in Country Equity Indexes'
                    },
                    {
                        'name': 'Paired Switching'
                    },
                    {
                        'name': 'Small Capitalization Stocks Premium Anomaly'
                    },
                    {
                        'name': 'Liquidity Effect in Stocks'
                    },
                    {
                        'name': 'Volatility Risk Premium Effect'
                    },
                    {
                        'name': 'Momentum Effect in Commodities Futures'
                    },
                    {
                        'name': 'Book-to-Market Value Anomaly'
                    },
                    {
                        'name': 'Term Structure Effect in Commodities'
                    },
                    {
                        'name': 'Gold Market Timing'
                    },
                    {
                        'name': 'Turn of the Month in Equity Indexes'
                    },
                    {
                        'name': 'Momentum-Short Term Reversal Strategy'
                    },
                    {
                        'name': 'Pairs Trading with Country ETFs'
                    },
                    {
                        'name': 'Accrual Anomaly'
                    },
                    {
                        'name': 'Asset Growth Effect'
                    },
                    {
                        'name': 'Momentum and State of Market Filters'
                    },
                    {
                        'name': 'Sentiment and Style Rotation Effect in Stocks'
                    },
                    {
                        'name': 'Momentum and Style Rotation Effect'
                    },
                    {
                        'name': 'Trading with WTI BRENT Spread'
                    },
                    {
                        'name': 'ROA Effect within Stocks'
                    },
                    {
                        'name': 'Momentum Effect in REITs'
                    },
                    {
                        'name': 'Option Expiration Week Effect'
                    },
                    {
                        'name': 'January Effect in Stocks'
                    },
                    {
                        'name': 'Momentum and Reversal Combined with Volatility Effect in Stock'
                    },
                    {
                        'name': 'Earnings Quality Factor'
                    },
                    {
                        'name': 'January Barometer'
                    },
                    {
                        'name': 'Lunar Cycle in Equity Market'
                    },
                    {
                        'name': 'VIX Predicts Stock Index Returns'
                    },
                    {
                        'name': 'Combining Momentum Effect with Volume'
                    },
                    {
                        'name': 'Short Term Reversal with Futures'
                    },
                    {
                        'name': 'Pre-Holiday Effect'
                    },
                    {
                        'name': 'Beta Factors in Stocks'
                    },
                    {
                        'name': 'Price Earnings Anomaly'
                    },
                    {
                        'name': 'Exploiting Term Structure of VIX Futures'
                    },
                    {
                        'name': '12 Month Cycle in Cross-Section of Stocks Returns'
                    },
                    {
                        'name': 'Momentum Effect in Stocks in Small Portfolios'
                    },
                    {
                        'name': 'Value Effect within Countries'
                    },
                    {
                        'name': 'Standardized Unexpected Earnings'
                    },
                    {
                        'name': 'Seasonality Effect based on Same-Calendar Month Returns'
                    },
                    {
                        'name': 'Risk Premia in Forex Markets'
                    },
                    {
                        'name': 'Expected Idiosyncratic Skewness'
                    },
                    {
                        'name': 'Mean-Reversion Statistical Arbitrage Strategy in Stocks'
                    },
                    {
                        'name': 'Fama French Five Factors'
                    },
                    {
                        'name': 'Improved Momentum Strategy on Commodities Futures'
                    },
                    {
                        'name': 'Commodities Futures Trend Following'
                    },
                    {
                        'name': 'G-Score Investing'
                    },
                    {
                        'name': 'Benzinga News Algorithm'
                    },
                    {
                        'name': 'Cached Alternative Data Algorithm'
                    },
                    {
                        'name': 'SEC Report 8K Algorithm'
                    },
                    {
                        'name': 'Smart Insider Transaction Algorithm'
                    },
                    {
                        'name': 'Tiingo News Algorithm'
                    },
                    {
                        'name': 'Trading Economics Algorithm'
                    },
                    {
                        'name': 'US Treasury Yield Curve Rate Algorithm'
                    },
                ],



                'validate': lambda answer: 'You must choose one of these' \
                    if len(answer) == 0 else True

            }]
        answers = prompt(questions, style=style)
        for n in answers:
            strategy = answers[n]

        strategy = urlify(strategy)
        filename = "%s.py" % strategy
        url = "https://raw.githubusercontent.com/ssantoshp/StrategyLibraryQC/main/"+filename
        response = requests.get(url)
        with open('main.py', 'a') as file:
            print(response.text, file=file)
        print("Just created the main.py file!")
        print("\n")
        print("You can also find the code here: "+url)



@app.command()
def backtest():
    print("For the moment, you can't directly backtest your strategy from here, so to backtest your strategy you can follow these instructions :")
    print("\n")
    print('1) run pip install lean in an empty directory')
    print('2) run lean login and give your QuantConnect ID and API token')
    print('3) run lean create-project "Project Name" in the same directory with your command prompt')
    print('4) Replace the main.py file in the "Project Name" folder by your main.py')
    print('5) Run lean cloud push --project "Project Name"')
    print('6) Finally, run lean cloud backtest "Project Name" --open --push')
    print("7) And you're done!")


