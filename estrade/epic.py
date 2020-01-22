import logging
import pytz
from dateutil import tz
from typing import List, TYPE_CHECKING

from estrade.mixins.ref_mixin import RefMixin
from estrade.exceptions import EpicException

if TYPE_CHECKING:
    from estrade.candle_set import CandleSet
    from estrade.market import Market
    from estrade.strategy import Strategy
    from estrade.tick import Tick

logger = logging.getLogger(__name__)


class Epic(RefMixin):
    """
    Class used to define an Epic

    Arguments:
        ref: reference/name of the epic
        market: Market instance
        timezone: epic timezone
        ticks_in_memory: nb ticks kept in the `ticks` attribute

    !!! example
        ```python
        from estrade import Epic, Market

        market = Market()
        epic = Epic(
            ref='MY_EPIC',
            market=market,
            timezone='Europe/Paris',
            ticks_in_memory=50
        )
        ```

    """

    def __init__(
        self,
        market: 'Market',
        ref: str = None,
        timezone: str = 'UTC',
        ticks_in_memory: int = 1,
    ):
        RefMixin.__init__(self, ref)
        logger.info('Init new Epic %s' % self.ref)

        self.timezone = timezone
        self.strategies: List[Strategy] = []

        # init a market to None
        self.market = market
        self.market.epics.append(self)

        # TODO: check that elements appened to this list are CandleSet objects
        self.candle_sets = []
        self.tradeable = True
        self.meta = {}
        self.ticks_in_memory = ticks_in_memory
        self.ticks = []
        logger.info(
            'New epic created with ref %s and %d strategies'
            % (self.ref, len(self.strategies))
        )

    ##################################################
    # CANDLE SETS
    ##################################################
    def get_candle_set(self, timeframe: str) -> 'CandleSet':
        """
        Get candle_set by timeframe in this instance candle_set

        Arguments:
            timeframe: timeframe of CandleSet to find in epic

        Returns:
            CandleSet associated with the required timeframe

        """
        for cs in self.candle_sets:
            if cs.timeframe == timeframe:
                return cs
        raise EpicException(
            'No candleSet found with timeframe %s in epic %s' % (timeframe, self.ref)
        )

    ##################################################
    # TICKS
    ##################################################
    @property
    def current_tick(self):
        return self.ticks[-1] if self.ticks else None

    def _add_tick(self, tick):
        """
        Add a new tick to list of epic ticks
        :param tick: <estrade.tick.Tick> instance
        :return:
        """
        self.ticks.append(tick)
        self.ticks = self.ticks[(self.ticks_in_memory * -1) :]

    ##################################################
    # TIMEZONE
    ##################################################
    @property
    def timezone(self) -> str:
        """
        Returns:
            epic timezone (see `pytz.all_timezones`)
        """
        return self._timezone

    @timezone.setter
    def timezone(self, timezone: str) -> None:
        """
        Set Epic timezone

        Timezone is used to update tick date when a new `estrade.tick.Tick`
        instance is created.

        :param timezone: <str> that should be a valid pytz timezone.
        :return: EpicException if timezone is invalid
        """
        if timezone in pytz.all_timezones:
            self._timezone = timezone
        else:
            raise EpicException(f'Invalid timezone : {timezone}')

    ##################################################
    # EVENTS
    ##################################################
    def _check_timezone(self, tick: 'Tick') -> bool:
        """Check that epic timezone matches the epic timezone."""
        if (
            self.timezone != 'UTC' and tick.datetime.tzinfo != tz.gettz(self.timezone)
        ) or (self.timezone == 'UTC' and tick.datetime.tzinfo != tz.tzutc()):
            raise EpicException(
                f'Invalid tick timezone, found {tick.datetime.tzinfo} when'
                f' expected {tz.gettz(self.timezone)}'
            )
        return True

    def on_new_tick(self, tick: 'Tick') -> None:
        """
        Method used to handle every new tick received by market.

        Its purpose is to:

         - check the tick received
         - update the epic/max min
         - dispatch tick to CandleSets

        Arguments:
            tick: tick received by epic

        """
        if tick.epic != self:
            raise EpicException(
                f'Invalid tick epic: cannot update epic {self.ref}({id(self)}) with '
                f'tick attached to epic {tick.epic.ref}({id(tick.epic)})'
            )

        logger.debug(
            'Add new tick to epic %s (%s): %f' % (self.ref, id(self), tick.value)
        )
        self._check_timezone(tick)

        # set tick as the current tick
        self._add_tick(tick)

        # dispatch tick to all candle sets
        for candle_set in self.candle_sets:
            logger.debug('dispatch tick to candle set %s' % candle_set.timeframe)
            candle_set.on_new_tick(tick)
