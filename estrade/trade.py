import logging
from datetime import datetime as pydatetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

import arrow  # type: ignore

from estrade.enums import TradeDirection, TransactionStatus
from estrade.exceptions import TradeException
from estrade.mixins import MetaMixin, RefMixin, TimedMixin, TransactionMixin


if TYPE_CHECKING:  # pragma: no cover
    from estrade import Epic, BaseStrategy, Tick


logger = logging.getLogger(__name__)


class StopLimitMixin:
    def __init__(
        self,
        stop_absolute: Optional[float],
        stop_relative: Optional[float],
        limit_absolute: Optional[float],
        limit_relative: Optional[float],
    ) -> None:
        self.direction: TradeDirection
        self.epic: Epic
        self.open_value: float
        self.current_close_value: float

        self.stop_absolute = stop_absolute
        self.stop_relative = stop_relative
        self.limit_absolute = limit_absolute
        self.limit_relative = limit_relative

    @property
    def stop_absolute(self):
        """
        Stop value of the current trade.

        Returns:
            stop value.
        """
        return self._stop_absolute

    @stop_absolute.setter
    def stop_absolute(self, stop_absolute: Optional[float]) -> None:
        self._stop_absolute = None

        if stop_absolute is None:
            return

        if self.direction == TradeDirection.BUY and stop_absolute >= self.open_value:
            raise TradeException(
                f"Impossible to set a stop ({stop_absolute}) "
                f">= current value ({self.current_close_value})"
            )
        elif self.direction == TradeDirection.SELL and stop_absolute <= self.open_value:
            raise TradeException(
                f"Impossible to set a stop ({stop_absolute}) "
                f"<= current value ({self.current_close_value})"
            )

        self._stop_absolute = stop_absolute

    @property
    def stop_relative(self) -> Optional[float]:
        """
        Stop value of the current trade relative to open value.

        Returns:
            stop value.
        """
        if self.stop_absolute:
            return abs(self.open_value - self.stop_absolute)
        return None

    @stop_relative.setter
    def stop_relative(self, stop_relative: Optional[float]):
        if stop_relative is None:
            return

        if self.direction == TradeDirection.BUY:
            self.stop_absolute = self.open_value - stop_relative
        else:
            self.stop_absolute = self.open_value + stop_relative

    @property
    def limit_absolute(self):
        """
        Limit value of the current trade.

        Returns:
            limit value.
        """
        return self._limit_absolute

    @limit_absolute.setter
    def limit_absolute(self, limit_absolute: Optional[float]) -> None:
        self._limit_absolute = None

        if limit_absolute is None:
            return

        if self.direction == TradeDirection.BUY and limit_absolute <= self.open_value:
            raise TradeException(
                f"Impossible to set a limit ({limit_absolute}) "
                f"<= current value ({self.current_close_value})"
            )
        elif (
            self.direction == TradeDirection.SELL and limit_absolute >= self.open_value
        ):
            raise TradeException(
                f"Impossible to set a limit ({limit_absolute}) "
                f">= current value ({self.current_close_value})"
            )

        self._limit_absolute = limit_absolute

    @property
    def limit_relative(self) -> Optional[float]:
        """
        Limit value of the current trade relative to open value.

        Returns:
            limit value.
        """
        if self.limit_absolute:
            return abs(self.open_value - self.limit_absolute)
        return None

    @limit_relative.setter
    def limit_relative(self, limit_relative: Optional[float]) -> None:
        if limit_relative is None:
            return

        if self.direction == TradeDirection.BUY:
            self.limit_absolute = self.open_value + limit_relative
        else:
            self.limit_absolute = self.open_value - limit_relative

    def update_stop_absolute(self, stop_absolute: float) -> None:
        """
        Add a stop by its absolute value on the current instance.

        Arguments:
            stop_absolute: stop absolute value
        """
        self.stop_absolute = stop_absolute
        self.epic.trade_provider.update_stop(trade=self)  # type: ignore

    def update_stop_relative(self, stop_relative: float) -> None:
        """
        Add a stop by its relative value on the current instance.

        Arguments:
            stop_relative: stop absolute value

        !!! note

            stop is relative to the trade open value.
        """
        self.stop_relative = stop_relative
        self.epic.trade_provider.update_stop(trade=self)  # type: ignore

    def update_limit_absolute(self, limit_absolute: float) -> None:
        """
        Add a limit by its absolute value on the current instance.

        Arguments:
            limit_absolute: limit absolute value
        """
        self.limit_absolute = limit_absolute
        self.epic.trade_provider.update_limit(trade=self)  # type: ignore

    def update_limit_relative(self, limit_relative: float) -> None:
        """
        Add a limit by its relative value on the current instance.

        Arguments:
            limit_relative: limit absolute value

        !!! note

            limit is relative to the trade open value.
        """
        self.limit_relative = limit_relative
        self.epic.trade_provider.update_limit(trade=self)  # type: ignore

    def _stop_limit_reached(self) -> bool:
        if self.direction == TradeDirection.BUY:
            if self.stop_absolute and self.current_close_value <= self.stop_absolute:
                return True
            elif (
                self.limit_absolute and self.current_close_value >= self.limit_absolute
            ):
                return True
        else:
            if self.stop_absolute and self.current_close_value >= self.stop_absolute:
                return True
            elif (
                self.limit_absolute and self.current_close_value <= self.limit_absolute
            ):
                return True
        return False


class Trade(MetaMixin, TimedMixin, RefMixin, TransactionMixin, StopLimitMixin):
    """
    Trade object representation.

    Attributes:
        epic (estrade.epic.Epic): epic of this trade
        strategy (estrade.strategy.BaseStrategy): strategy that generated this trade
        direction (estrade.enums.TradeDirection): direction of this trade
        open_quantity (int): Quantities opened on trade initialisation.
        closes (List[estrade.trade.TradeClose]): List of closes of this trade.
        open_value (float): open tick value of the current instance
        current_close_value (float): current market value to close this trade.
        max_result (float): max result of this instance
        min_result (float): min result of this instance
        stop_absolute (Optional[float]): stop value for this trade
        limit_absolute (Optional[float]): limit value for this trade

        ref (str): reference of this instance
            (see `estrade.mixins.ref.RefMixin`)
        datetime (arrow.Arrow): datetime of open
            (see `estrade.mixins.timed.TimedMixin`)
        meta (Dict[str, Any]): Dictionary free of use
            (see `estrade.mixins.meta.MetaMixin`)
        status (estrade.enums.TransactionStatus): Transaction status of this trade
            (see [`TransactionStatus`][estrade.enums.TransactionStatus])
    """

    def __init__(
        self,
        direction: TradeDirection,
        quantity: int,
        open_value: float,
        open_datetime: arrow.Arrow,
        epic: "Epic",
        current_close_value: Optional[float] = None,
        status: Optional[TransactionStatus] = TransactionStatus.CREATED,
        strategy: Optional["BaseStrategy"] = None,
        stop_absolute: Optional[float] = None,
        limit_absolute: Optional[float] = None,
        stop_relative: Optional[float] = None,
        limit_relative: Optional[float] = None,
        ref: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Create a new trade instance.

        Arguments:
            direction: trade direction (buy or sell)
            quantity: quantity of the trade.
            open_value: market value to open the Trade with
            open_datetime: datetime of the trade open
            status: operation status
            epic: [`Epic`][estrade.epic.Epic] instance having at least one tick.
            strategy: [`Strategy`][estrade.strategy.BaseStrategy] instance
            stop_absolute (Optional[float]): stop value for this trade
            stop_relative (Optional[float]): stop value relative to open for this trade
            limit_absolute (Optional[float]): limit value for this trade
            limit_relative (Optional[float]): limit value relative to open for
                this trade
            ref: trade reference
            meta: trade metadata
        """
        self.epic = epic
        self.strategy = strategy  # TODO: test Strategy type
        self.direction = direction  # TODO: check invalid direction
        self.open_quantity = quantity  # TODO: check positive
        self.closes: List[TradeClose] = []

        self.open_value = open_value
        self.current_close_value = current_close_value or open_value

        self.max_result: float = self.result
        self.min_result: float = self.result

        StopLimitMixin.__init__(
            self,
            stop_absolute=stop_absolute,
            stop_relative=stop_relative,
            limit_absolute=limit_absolute,
            limit_relative=limit_relative,
        )

        RefMixin.__init__(self, ref)
        TimedMixin.__init__(self, open_datetime)
        MetaMixin.__init__(self, meta)
        TransactionMixin.__init__(self, status)

        # self.epic.trade_provider.open_trade(self)
        logger.info(
            "New %s trade created: %s @ %s", self.direction, self.ref, self.open_value
        )

    def asdict(self) -> Dict[str, Any]:
        dict_representation = {
            "ref": self.ref,
            "status": self.status,
            "epic": self.epic.ref,
            "strategy": self.strategy.ref if self.strategy else "undefined",
            "open_date": self.datetime.format("YYYY-MM-DD HH:mm:ss"),
            "direction": self.direction,
            "open_quantity": self.open_quantity,
            "open_value": self.open_value,
            "closed_quantities": self.closed_quantities,
            "result": self.result,
        }
        return dict_representation

    ####################
    # OPEN
    ####################
    @staticmethod
    def open_from_tick(tick: "Tick", epic: "Epic", **kwargs: Any) -> "Trade":
        """
        Open a [`Trade`][estrade.trade.Trade] from a [`Tick`][estrade.tick.Tick].

        Arguments:
            tick: [`Tick`][estrade.tick.Tick] instance.
            kwargs: Arguments with the same constraints as the
                [`Trade`][estrade.trade.Trade.__init__]
        """
        if kwargs["direction"] == TradeDirection.BUY:
            kwargs["open_value"] = tick.ask
            kwargs["current_close_value"] = tick.bid
        elif kwargs["direction"] == TradeDirection.SELL:
            kwargs["open_value"] = tick.bid
            kwargs["current_close_value"] = tick.ask
        else:
            raise TradeException("Invalid direction")

        kwargs["open_datetime"] = tick.datetime

        trade = Trade(
            epic=epic,
            **kwargs,
        )
        return trade

    @staticmethod
    def open_from_epic(epic: "Epic", **kwargs: Any) -> "Trade":
        """
        Open a trade from an Epic current last tick.

        Arguments:
            epic: Epic instance to open the Trade from
            kwargs: see [`Trade`][estrade.trade.Trade] `__init__` method arguments

        Returns:
            opened trade instance.
        """
        new_trade = Trade.open_from_tick(
            tick=epic.last_tick,
            epic=epic,
            **kwargs,
        )

        return new_trade

    ####################
    # Update
    ####################
    def _update_min_max(self) -> None:
        """Update trade min and max result."""
        if self.result > self.max_result:
            self.max_result = self.result
        if self.result < self.min_result:
            self.min_result = self.result

    def update(self, current_close_value: float) -> None:
        """
        Update trade with the current market value.

        Arguments:
            current_close_value: the current market value to close this Trade.

        !!! example

            ```python
            --8<-- "tests/doc/reference/trade/test_update.py"
            ```
        """
        if self.closed:
            logger.error("Cannot update a closed trade.")
            return

        self.current_close_value = current_close_value

        if self._stop_limit_reached():
            self.close(
                close_value=self.current_close_value,
                meta={"close_reason": "stop_limit_reached"},
            )

        self._update_min_max()

    def update_from_tick(self, tick: "Tick") -> None:
        """
        Update current trade from the input Tick.

        Arguments:
            tick: Tick instance to use to update the trade result.
        """
        if self.direction == TradeDirection.BUY:
            current_close_value = tick.bid
        else:
            current_close_value = tick.ask

        self.update(current_close_value)

    def update_from_epic(self) -> None:
        """Update current trade from its Epic current value."""
        self.update_from_tick(self.epic.last_tick)

    ####################
    # Close
    ####################
    def close(
        self,
        close_value: float,
        datetime: Optional[Union[pydatetime, arrow.Arrow]] = None,
        quantity: Optional[int] = None,
        **kwargs,
    ) -> "TradeClose":
        """
        Close (totally or partially) a trade.

        This method create a new instance of [`TradeClose`][estrade.trade.TradeClose]
        and adds it to this instance `closes`.

        Arguments:
            close_value: the market value at which the close is performed.
            datetime: datetime of the closing.
            quantity: quantity to close, default to the remaining open quantities if
                not provided.

        Returns:
            The [`TradeClose`][estrade.trade.TradeClose] instance created.

        """
        quantity = quantity or self.opened_quantities
        datetime = datetime or self.epic.last_tick.datetime

        if quantity > self.opened_quantities:
            logger.error(
                f"Impossible to close {quantity} when only "
                f"{self.opened_quantities} are opened."
            )
            quantity = self.opened_quantities

        logger.info(
            "Close %s quantities of trade %s @ %s", quantity, self.ref, close_value
        )
        new_close = TradeClose(
            trade=self,
            close_value=close_value,
            quantity=quantity,
            datetime=datetime,
            **kwargs,
        )
        self.closes.append(new_close)
        return new_close

    def close_from_tick(self, tick: "Tick", **kwargs) -> "TradeClose":
        """
        Close current Trade from a Tick instance.

        Arguments:
            tick: Tick instance to use to close the current trade.

        Returns:
            The [`TradeClose`][estrade.trade.TradeClose] instance created.
        """
        # update current trade with tick to set self.current_close_value
        self.update_from_tick(tick)

        trade_close = self.close(
            datetime=tick.datetime,
            close_value=self.current_close_value,
            **kwargs,
        )
        return trade_close

    def close_from_epic(self, **kwargs) -> "TradeClose":
        """
        Close Trade with its Epic last tick.

        Arguments:
            kwargs: see [`TradeClose`][estrade.trade.TradeClose] arguments

        Returns:
            The [`TradeClose`][estrade.trade.TradeClose] instance created.
        """
        trade_close = self.close_from_tick(self.epic.last_tick, **kwargs)

        return trade_close

    ####################
    # Properties
    ####################
    @property
    def closed_quantities(self) -> int:
        """
        Return closed quantities of the trade.

        return:
            Sum of closed quantities.
        """
        return sum(c.quantity for c in self.closes) if self.closes else 0

    @property
    def opened_quantities(self) -> int:
        """
        Return opened quantities of the trade.

        return:
            Sum of opened quantities.
        """
        return self.open_quantity - self.closed_quantities

    @property
    def closed(self) -> bool:
        """
        Check if the trade is closed.

        return:
            `True` if all the open quantities closed.
        """
        return self.opened_quantities == 0

    @property
    def opened_result_avg(self) -> float:
        """
        Average result per opened quantity.

        return:
            difference between open and last value.
        """
        if self.closed:
            return 0.0

        if self.direction == TradeDirection.BUY:
            avg_result = self.current_close_value - self.open_value
        else:
            avg_result = self.open_value - self.current_close_value
        return round(avg_result, 2)

    @property
    def opened_result(self) -> float:
        """
        Return result of the opened quantities.

        return:
            difference between open and last value multiplied by open quantities.
        """
        return self.opened_result_avg * self.opened_quantities

    @property
    def closed_result_avg(self) -> float:
        """
        Average result of the closed quantities.

        return:
            sum of closes average result (does not takes quantities into
            account).
        """
        return round(
            sum(close.result for close in self.closes) / self.closed_quantities
            if self.closes
            else 0,
            2,
        )

    @property
    def closed_result(self) -> float:
        """
        Return closed result of the current trade.

        return:
            sum of closes result.
        """
        return sum(close.result for close in self.closes) if self.closes else 0

    @property
    def result(self) -> float:
        """
        Trade current result.

        return:
            trade result
        """
        return self.opened_result + self.closed_result

    @property
    def result_avg(self) -> float:
        """
        Trade average result per quantity.

        return:
            trade average result (does not takes quantities into account)
        """
        return round(self.result / self.open_quantity, 2)


class TradeClose(MetaMixin, TimedMixin, RefMixin, TransactionMixin):
    """Partial close of a [`Trade`][estrade.trade.Trade]."""

    def __init__(
        self,
        trade: Trade,
        close_value: float,
        quantity: int,
        datetime: Union[pydatetime, arrow.Arrow],
        status: Optional[TransactionStatus] = TransactionStatus.CREATED,
        ref: Optional[str] = None,
        meta: Optional[Dict[Any, Any]] = None,
    ) -> None:
        """
        Create a new partial close of a trade.

        Arguments:
            trade: [`Trade`][estrade.trade.Trade] instance.
            close_value: current market value at close time.
            quantity: closed quantities
            datetime: close datetime
            ref: an optional name for this close
            meta: trade close metadata
        """
        self.trade = trade
        self.close_value = close_value
        self.quantity = quantity

        TransactionMixin.__init__(self, status)
        TimedMixin.__init__(self, datetime)
        MetaMixin.__init__(self, meta)
        RefMixin.__init__(self, ref)

    @property
    def result_avg(self) -> float:
        """
        Trade average result.

        Average result per quantity.

        Returns:
            Average result of this close per quantity.
        """
        if self.trade.direction == TradeDirection.BUY:
            return round(self.close_value - self.trade.open_value, 2)
        return round(self.trade.open_value - self.close_value, 2)

    @property
    def result(self) -> float:
        """
        Trade total result.

        Returns:
            Total result of this close per quantity.
        """
        return round(self.result_avg * self.quantity, 2)
