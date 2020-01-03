""" This file define the Candle class.
"""
import logging

from estrade.classes.exceptions import CandleException
from estrade.classes.tick import Tick

logger = logging.getLogger(__name__)


class Candle:
    """
    Class used to represent a Candle (from a clandlesticks graph).
    This class is used in list of candles of <estrade.classes.candle_set.CandleSet> instances.

    A candle holds a list of ticks happening between the time/nb defined in CandleSet.
    """
    def __init__(self, open_tick, open_at=None):
        """
        Create a new Candle
        :param open_tick: <estrade.classes.tick.Tick>
        :param open_at: <datetime.datetime>
        """
        logger.debug('create new candle')
        self.ticks = []
        self.low = float('inf')
        self.high = -1
        self.closed = False
        self.on_new_tick(open_tick)
        self.open_at = open_at if open_at else open_tick.datetime
        self.indicators = {}
        logger.debug('new candle created: %s' % self.open_at)

    ##################################################
    # TICKS
    ##################################################
    @property
    def open(self):
        """
        get candle open/first tick value
        :return: <float>
        """
        return self.ticks[0].value

    @property
    def last(self):
        """
        get candle last tick value
        :return: <float>
        """
        return self.ticks[-1].value

    @property
    def close(self):
        """
        When candle is closed, this method send the last tick of candle
        :return: <None>/<float>
        """
        if self.closed:
            return self.last
        return None

    ##################################################
    # CANDLE PARTS
    ##################################################
    @property
    def color(self):
        """
        This method return the color of the candle.
        if open < close: green
        elif open > close: red
        else (open == close): black (doji)
        :return: <str> in ['green', 'red', 'black']
        """
        if self.last > self.open:
            return 'green'
        elif self.last < self.open:
            return 'red'
        return 'black'

    @property
    def height(self):
        """
        Height of a candle (max - min)
                |  ┐
                |  |
                ┴  |
               | | |
               | | |<-- height
               | | |
                ┬  |
                |  |
                |  ┘
        :return: <float>
        """
        return self.high - self.low

    @property
    def body(self):
        """
        Body of a candle : distance between open value and last tick value
                |
                |
                ┴  ┐
               | | |
               | | |<-- body
               | | |
                ┬  ┘
                |
                |
        :return: <float>
        """
        return abs(self.open - self.last)

    @property
    def head(self):
        """
        Head of a candle : distance between the highest value and the highest from (open/last)
                |  ┐
                |  | <-- head
                ┴  ┘
               | |
               | |
               | |
                ┬
                |
                |
        :return: <float>
        """
        return self.high - (max(self.open, self.last))

    @property
    def tail(self):
        """
        Tail of a candle : distance between the lowest value and the lowest from (open/last)
                |
                |
                ┴
               | |
               | |
               | |
                ┬  ┐
                |  | <-- tail
                |  ┘
        :return: <float>
        """
        return min(self.open, self.last) - self.low

    ##################################################
    # EVENTS
    ##################################################
    def on_new_tick(self, tick):
        """
        This method append a new tick to the candle.ticks and update candle low/high.
        :param tick: <estrade.classes.tick.Tick>
        :return:
        """
        if not isinstance(tick, Tick):
            raise CandleException('Can only add Tick objects to candle')

        self.ticks.append(tick)

        if tick.value < self.low:
            self.low = tick.value
        if tick.value > self.high:
            self.high = tick.value

    def close_candle(self):
        """
        This method set the candle as closed.
        A candle is closed when :
            - the max number of tick in candle is reached (max number defined in "parent" CandleSet)
            - the candle time range is reached (time ranched defined in "parent" CandleSet)
        :return:
        """
        self.closed = True
