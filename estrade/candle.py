""" This file define the Candle class.
"""
import logging
from typing import Any, Dict, List, Optional

from estrade.exceptions import CandleException
from estrade.tick import Tick

logger = logging.getLogger(__name__)


class Candle:
    """
    Class used to represent a Candle (from a clandlesticks graph).
    This class is used in list of candles of `estrade.candle_set.CandleSet` instances.

    A candle holds a list of ticks happening between the time/nb defined in CandleSet.

    Arguments:
        timeframe: candle timeframe
        epic_ref: reference of epic
        meta: free of use dictionnary

    !!! note
        The `open_at` can be different from the open_tick datetime, for example in a
        `5minutes` timeframe, if the first tick has a time of 12:06:03, then the
        `open_at` should be 12:05:00.

    !!! note
        This class does not have a reference to a CandleSet because it can be created
        manually from a Provider (and not be attached to a candleset directly).

    """

    def __init__(
        self,
        timeframe: str,
        epic_ref: str,
        open_tick: Tick,
        meta: Dict[str, Any] = None,
    ) -> None:
        logger.debug('create new candle')

        # validate and set timeframe
        from estrade.candle_set import CandleSet

        CandleSet.validate_timeframe(timeframe)
        self.timeframe = timeframe

        # TODO: instanciate with open_tick.epic.ref
        if not isinstance(epic_ref, str):
            raise CandleException('Invalid Candle Epic ref')
        self.epic_ref = epic_ref

        if not isinstance(open_tick, Tick):
            raise CandleException('Invalid candle open tick')
        self.ticks: List[Tick] = [open_tick]
        self.low_tick = open_tick
        self.high_tick = open_tick

        self.closed = False

        # as the open tick is not necessarily on the timeframe lowest, set it with
        # the CandleSet static method
        nb, ut = CandleSet.split_timeframe(self.timeframe)
        self.open_at = CandleSet.round_candle_open_datetime(
            tick_datetime=open_tick.datetime, nb=nb, ut=ut,
        )

        self.indicators: Dict[str, Any] = {}
        self.meta = meta or {}

        logger.debug('new candle created: %s' % self.open_at)

    ##################################################
    # TICKS
    ##################################################
    @property
    def open(self) -> float:
        """
        Returns:
            The first tick of candle
        """
        return self.ticks[0].value

    @property
    def last(self) -> float:
        """
        Returns:
            The last tick of candle
        """
        return self.ticks[-1].value

    @property
    def close(self) -> Optional[float]:
        """
        Returns:
            When candle is closed, this method send the last tick of candle
        """
        if self.closed:
            return self.last
        return None

    @property
    def high(self) -> float:
        """
        Returns:
            The highest tick in candle
        """
        return self.high_tick.value

    @property
    def low(self) -> float:
        """
        Returns:
            The tick with the lowest value of candle

        """
        return self.low_tick.value

    @property
    def open_tick(self) -> Tick:
        """
        Returns:
            The fist tick of candle
        """
        return self.ticks[0]

    @property
    def last_tick(self) -> Tick:
        """
        Returns:
            The last tick in candle

        """
        return self.ticks[-1]

    ##################################################
    # CANDLE PARTS
    ##################################################
    @property
    def color(self) -> str:
        """
        Returns:
            This method return the "color" of the candle.

         - if open < close: returns `green`
         - elif open > close: returns `red`
         - else (open == close): returns `black` (doji)

        """
        if self.last > self.open:
            return 'green'
        elif self.last < self.open:
            return 'red'
        return 'black'

    @property
    def height(self) -> float:
        """
        Returns:
            Height of candle (high - low)

        ```
                |  ┐
                |  |
                ┴  |
               | | |
               | | |<-- height
               | | |
                ┬  |
                |  |
                |  ┘
        ```
        """
        return self.high - self.low

    @property
    def body(self) -> float:
        """
        Returns:
            the absolute difference between open and close of the candle

        ```
                |
                |
                ┴  ┐
               | | |
               | | |<-- body
               | | |
                ┬  ┘
                |
                |
        ```
        """
        return abs(self.open - self.last)

    @property
    def head(self) -> float:
        """
        Returns:
            distance between the highest value and the highest from (open/last)
        ```
                |  ┐
                |  | <-- head
                ┴  ┘
               | |
               | |
               | |
                ┬
                |
                |
        ```
        """
        return self.high - (max(self.open, self.last))

    @property
    def tail(self) -> float:
        """
        Returns:
            distance between the lowest value and the lowest from (open/last)

        ```
                |
                |
                ┴
               | |
               | |
               | |
                ┬  ┐
                |  | <-- tail
                |  ┘
        ```
        """
        return min(self.open, self.last) - self.low

    ##################################################
    # EVENTS
    ##################################################
    def on_new_tick(self, tick: Tick) -> None:
        """
        This method append a new tick to the candle.ticks and update candle low/high.

        Arguments:
            tick: tick to add to candle
        """
        if not isinstance(tick, Tick):
            raise CandleException('Can only add Tick objects to candle')

        self.ticks.append(tick)

        if not self.low_tick or tick.value < self.low_tick.value:
            self.low_tick = tick
        if not self.high_tick or tick.value > self.high_tick.value:
            self.high_tick = tick

    def close_candle(self) -> None:
        """
        This method set the candle as closed.

        A candle is closed when :

         - the max number of tick in candle is reached (max number defined in "parent"
         CandleSet)
         - the candle time range is reached (time ranched defined in "parent" CandleSet)
        """
        self.closed = True

    def __str__(self) -> str:
        return (
            f'Candle : open {self.open}@{self.open_at}, '
            f'{"close" if self.closed else "last"} {self.ticks[-1].value}@'
            f'{self.ticks[-1].datetime}'
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            'timeframe': self.timeframe,
            'epic': self.epic_ref,
            'nb_ticks': len(self.ticks),
            'open': self.open_tick.to_json(),
            'high': self.high_tick.to_json() if self.high_tick else None,
            'low': self.low_tick.to_json() if self.low_tick else None,
            'closed': self.closed,
            'close': self.ticks[-1].to_json() if self.closed else None,
            'indicators': self.indicators,
            'meta': self.meta,
        }
