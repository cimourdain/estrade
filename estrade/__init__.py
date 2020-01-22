__version__ = '0.0.1'

# classes
from estrade.strategy import Strategy  # noqa
from estrade.abstract.Areporting import AReporting  # noqa

from estrade.candle_set import CandleSet  # noqa
from estrade.epic import Epic  # noqa
from estrade.market import Market  # noqa
from estrade.tick import Tick  # noqa
from estrade.abstract.Aprovider import AProvider, ALiveProvider  # noqa

# indicators
from estrade.indicators.candle_set.moving_average import (  # noqa
    ExponentialMovingAverage,  # noqa
    SimpleMovingAverage,  # noqa
)  # noqa

# reporting
from estrade.reporting.csv import ReportingCSV  # noqa

# logging
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger(__name__).addHandler(logging.NullHandler())
