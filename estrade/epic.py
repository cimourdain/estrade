import logging
from datetime import date, time
from typing import Dict, List, Optional, TYPE_CHECKING

import arrow  # type: ignore
import pytz

from estrade.exceptions import EpicException
from estrade.mixins import RefMixin
from estrade.tick import Tick
from estrade.trade import Trade, TradeClose
from estrade.trade_provider import BaseTradeProvider, TradeProviderBacktests


if TYPE_CHECKING:  # pragma: no cover
    from datetime import time as datetime_time
    from estrade.strategy import BaseStrategy
    from estrade.graph.frame_set import FrameSet, Frame
    from estrade.graph.base_indicator import BaseIndicatorValue


logger = logging.getLogger(__name__)


class Epic(RefMixin):
    """
    An [`Epic`][estrade.epic.Epic] is a financial instrument.

    Attributes:
        trade_provider (BaseTradeProvider): trade provider of this instance
        timezone (str): timezone to apply to all received ticks
        open_time (datetime.time): Epic open time
        close_time (datetime.time): current instance close time
        trade_days (List[int]): List of trading days for this Epic (monday=0)
        holidays (List[datetime.date]): List of holidays for this instance.
        frame_sets (Dict[str, "FrameSet"]): Dict of frame sets indexed by
            their reference.
        strategies (Dict[str, "BaseStrategy"]): Dict of strategies indexed by
            their reference.

        ref (str): reference of this instance
            (see `estrade.mixins.ref.RefMixin`)
    """

    def __init__(
        self,
        timezone: str = "UTC",
        open_time: time = time(9, 30),
        close_time: time = time(17, 30),
        trade_days: Optional[List[int]] = None,
        holidays: Optional[List[date]] = None,
        trade_provider: Optional["BaseTradeProvider"] = None,
        ref: Optional[str] = None,
    ) -> None:
        """
        Create a new Epic instance.

        Arguments:
            trade_provider: instance inheriting from
                [`TradeProvider`][estrade.trade_provider.BaseTradeProvider]. Defaults to
                [`TradeProviderBacktests`][estrade.trade_provider.TradeProviderBacktests]
                if not provided
            timezone: timezone string from `pytz.all_timezones`, it is applied on tick
                on association with Epic.
            open_time: Instance open_time
            close_time: Instance close_time
            trade_days: List of weekdays when the market is open (Monday=0).
            holidays: List of dates where the Epic is open.
            ref: epic code name

        Raises:
            estrade.EpicException: if timezone is invalid

        """
        # call parent mixins
        RefMixin.__init__(self, ref)

        # handle arguments to set attributes
        self.timezone: str = timezone
        self.open_time = open_time
        self.close_time = close_time
        self.trade_days = trade_days or [0, 1, 2, 3, 4]
        self.holidays = holidays or []
        self.trade_provider = trade_provider or TradeProviderBacktests()

        # create a fake tick to init last_tick attribute
        self.last_tick: Tick = Tick(
            datetime=arrow.get("1900-01-01 00:00:00"),
            bid=0,
            ask=0,
        )
        self.frame_sets: Dict[str, "FrameSet"] = {}
        self.strategies: Dict[str, "BaseStrategy"] = {}
        self.market_open: bool = False
        logger.info(f"New Epic created: {self}")

    def __str__(self) -> str:
        """
        Return a string representation of the current instance.

        Returns:
            string representation of current [`Epic`][estrade.epic.Epic] instance.
        """
        return f"Epic: {self.ref} on timezone {self.timezone}"

    @property
    def timezone(self) -> str:
        """
        Return the current instance timezone.

        Returns:
            epic timezone (see `pytz.all_timezones`)
        """
        return self._timezone

    @timezone.setter
    def timezone(self, timezone: str) -> None:
        """
        Set timezone of current instance.

        Timezone is used to update tick datetime when associated to epic.

        Arguments:
            timezone: timezone from `pytz.all_timezones`

        Raises:
            estrade.EpicException: if timezone is invalid
        """
        if timezone in pytz.all_timezones:
            self._timezone = timezone
        else:
            raise EpicException(f"Invalid timezone : {timezone}")

    def add_frame_set(self, frame_set: "FrameSet") -> None:
        if self.frame_sets.get(frame_set.ref):
            raise EpicException(
                f"Cannot add 2 FrameSet with the same ref ({frame_set.ref}) to epic."
            )
        logger.info("Add frame set %s to epic %s", frame_set.ref, self.ref)
        frame_set.epic = self
        self.frame_sets[frame_set.ref] = frame_set

    def add_strategy(self, strategy: "BaseStrategy") -> None:
        if self.strategies.get(strategy.ref):
            raise EpicException(
                f"Cannot add 2 Strategies with the same ref ({strategy.ref}) to epic."
            )
        logger.info("Add strategy %s to epic %s", strategy.ref, self.ref)
        self.strategies[strategy.ref] = strategy
        strategy.epics[self.ref] = self

    def _in_market_hours(self, tick_datetime_time: "datetime_time") -> bool:
        """
        Check if a Tick is in Epic market hours.

        Arguments:
            tick_datetime_time: datetime of a tick

        Returns:
            Is the datetime provided in this instance trading hours?
        """
        if tick_datetime_time < self.open_time:
            logger.debug(
                "Tick is before Market hours: %s < %s",
                tick_datetime_time,
                self.open_time,
            )
            return False
        elif tick_datetime_time > self.close_time:
            logger.debug(
                "Tick is after Market hours: %s > %s",
                tick_datetime_time,
                self.open_time,
            )
            return False
        logger.debug("Tick is in Market hours")
        return True

    def is_market_open(self) -> bool:
        """
        Check if the market is currently opened.

        This method compare the last received tick datetime to the current instance
        `open_time` and `close_time`.

        Returns:
            - `None` when the epic contains no Tick
            - `True` if the last received tick datetime
                - datetime is between `open_time` and `close_time`
                - day is not a holiday
                - weekday is a trade_days
            - `False` in other cases
        """
        if not self._in_market_hours(self.last_tick.datetime.time()):
            logger.debug("Tick is not in Market hours")
            return False
        elif self.last_tick.datetime.weekday() not in self.trade_days:
            logger.debug("Tick is not in a valid weekday")
            return False
        elif self.last_tick.datetime.date() in self.holidays:
            logger.debug("Tick is not in a holiday")
            return False

        return True

    def _update_frame_sets(self, new_tick: "Tick") -> None:
        for _, fs in self.frame_sets.items():
            fs.on_new_tick(new_tick)

    def _update_open_trades(self, new_tick: "Tick") -> None:
        for trade in self.trade_provider.opened_trades:
            trade.update_from_tick(new_tick)

    def _execute_strategies(self, market_open_before_new_tick: bool) -> None:
        for _, strategy in self.strategies.items():
            if strategy.is_active(self.last_tick.datetime):
                if market_open_before_new_tick != self.market_open:
                    if market_open_before_new_tick is True:
                        strategy.on_market_close(self)
                    else:
                        strategy.on_market_open(self)
                if self.market_open:
                    strategy.on_every_tick_market_open(self)

                strategy.on_every_tick(self)

    def on_new_tick(self, tick: "Tick") -> None:
        """
        Add a new tick to Epic.

        The purpose of this method is to:

          1. Apply Epic timezone to the received Tick datetime
          3. Update frames sets
          4. Update opened trades result
          4. Trigger strategies

        Use this method in your TickProvider to propagate every new received Tick.

        Arguments:
            tick: new tick
        """
        # set tick timezone
        tick.datetime = tick.datetime.to(self.timezone)
        if tick.datetime < self.last_tick.datetime:
            raise EpicException(
                "Cannot handle a tick anterior to the last received tick."
            )

        # update last tick
        self.last_tick = tick
        market_open_before_new_tick = self.market_open
        self.market_open = self.is_market_open()

        self._update_frame_sets(tick)

        self._update_open_trades(tick)

        self._execute_strategies(market_open_before_new_tick)

    def open_trade(self, **kwargs) -> Trade:
        """
        Open a new trade on this Epic.

        Arguments:
            kwargs: see arguments of [`Trade`][estrade.trade.Trade]
        """
        logger.debug("Open a new trade for epic %s: %s", self.ref, kwargs)
        new_trade = Trade.open_from_epic(epic=self, **kwargs)
        self.trade_provider.open_trade(new_trade)
        return new_trade

    def close_trade(self, trade: Trade, **kwargs) -> TradeClose:
        """
        Close a new trade on this Epic.

        Arguments:
            trade: Trade to close
            kwargs: see arguments of [`TradeClose`][estrade.trade.TradeClose]
        """
        logger.debug("Close a trade for epic %s", self.ref)
        trade_close = trade.close_from_epic(**kwargs)
        self.trade_provider.close_trade(trade_close)

        return trade_close

    def get_frame(self, frame_set_ref: str, offset: int = 0) -> Optional["Frame"]:
        """
        Get a frame from a FrameSet.

        Arguments:
            frame_set_ref: reference of the
                [`FrameSet`][estrade.graph.frame_set.FrameSet]
            offset: number of frames backwards
                (eg: 0 = current frame,  1 = last closed frame)

        Returns:
            frame
        """
        offset = (offset + 1) * -1
        frame_set = self.frame_sets[frame_set_ref]
        try:
            frame = frame_set[offset]
        except IndexError:
            return None

        return frame

    def get_indicator_value(
        self, frame_set_ref: str, indicator_ref: str, offset: int = 0
    ) -> Optional["BaseIndicatorValue"]:
        """
        Get indicator value for a FrameSet.

        Arguments:
            frame_set_ref: reference of the
                [`FrameSet`][estrade.graph.frame_set.FrameSet]
            indicator_ref: indicator reference
            offset: number of frames backwards
                (eg: 0 = current frame,  1 = last closed frame)

        Returns:
            Indicator value
        """
        frame = self.get_frame(frame_set_ref=frame_set_ref, offset=offset)
        if frame is None:
            return None

        indicator_value = frame[indicator_ref]
        return indicator_value
