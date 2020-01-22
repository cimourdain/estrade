""" This module define the Trade class used to manage positions.
"""
import logging
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from estrade.mixins.ref_mixin import RefMixin
from estrade.exceptions import TradeException
from estrade.observer import Observable
from estrade.stop_limit import StopLimitMixinAbsolute, StopLimitMixinRelative
from estrade.tick import Tick

if TYPE_CHECKING:
    from estrade.epic import Epic
    from estrade.strategy import Strategy
    from estrade.trade_manager import TradeManager


logger = logging.getLogger(__name__)


class TradeClose:
    """
    Manage a trade close

    Arguments:
        tick: tick to close trade with
        quantity: quantity to close on trade
        result: result of trade close
        reason: reason for closing
    """

    def __init__(self, tick: Tick, quantity: int, result: float, reason: str) -> None:
        self.tick = tick
        self.quantity = quantity
        self.result = result
        self.reason = reason

    def to_json(self) -> Dict[str, Any]:
        """
        Convert trade close to dict (mainly used for reporting)

        Returns:
            dictionary formatted close
        """
        return {
            'tick': self.tick.to_json(True),
            'quantity': self.quantity,
            'reason': self.reason,
            'result': self.result,
        }


class Trade(RefMixin, Observable):
    """
    The Trade class manage trades (=market positions)

    Arguments:
        quantity: open trade quantities
        direction: trade direction (`BUY`/`1` or `SELL`/`-1`)
        epic: trade epic to open trade on
        trade_manager: trade manager holding this trade
        strategy: strategy that generated this trade
        ref: trade name reference
        stop_absolute: trade stop in absolute value
        stop_relative: trade stop in relative value
        limit_absolute: trade target profit in absolute value
        limit_relative: trade target profit in relative value
        meta: free of use dictionary

    """

    def __init__(
        self,
        quantity: int,
        direction: Union[str, int],
        trade_manager: 'TradeManager',
        strategy: 'Strategy',
        epic: 'Epic',
        ref: Optional[str] = None,
        stop_absolute: Optional[Union[int, float]] = None,
        stop_relative: Optional[Union[int, float]] = None,
        limit_absolute: Optional[Union[int, float]] = None,
        limit_relative: Optional[Union[int, float]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        # set ref with parent class
        RefMixin.__init__(self, ref)

        # set class as observable so it can fire events
        # TODO : fire events on trade update
        Observable.__init__(self)

        # set trade manager
        self.trade_manager: 'TradeManager' = trade_manager

        # set strategy
        self.strategy: 'Strategy' = strategy

        self.direction = direction
        self.inital_quantities = abs(quantity)
        self.opened_quantity = abs(quantity)
        self.closed_quantity = 0
        self.closed = False

        # init empty list of ticks received by trade
        open_tick = epic.ticks[-1]

        if open_tick is None:
            raise TradeException('Impossible to define trade open tick.')
        elif not epic.tradeable:
            raise TradeException(
                'Open tick epic %s is not tradeable ' % open_tick.epic.ref
            )
        self.open_tick = open_tick
        self.last_tick = open_tick
        self.high_tick = open_tick
        self.low_tick = open_tick
        self.opened_result = open_tick.spread * -1
        self.closed_result = 0
        self.result = self.opened_result

        # init empty list of closes
        self.closes: List[TradeClose] = []

        # set max gain and max losses
        self.max_gain = float('inf') * -1
        self.max_loss = float('inf')

        # init stop/limit from params
        self._stop = None
        if stop_relative:
            self.set_stop(stop_value=stop_relative, relative=True)
        elif stop_absolute:
            self.set_stop(stop_value=stop_absolute, relative=False)

        self._limit = None
        if limit_relative:
            self.set_limit(limit_value=limit_relative, relative=True)
        elif limit_absolute:
            self.set_limit(limit_value=limit_absolute, relative=False)

        self.on_new_tick(open_tick)

        self.meta = {} if not meta or not isinstance(meta, dict) else meta

        logger.info('%s' % repr(self))

    ##################################################
    # DIRECTION GET/SET
    ##################################################
    @property
    def direction(self) -> int:
        """
        Returns:
            trade direction, `1` for a BUY and `-1` for a sell.
        """
        return self._direction

    @direction.setter
    def direction(self, direction: Union[str, int]) -> None:
        """
        Set trade direction

        Arguments:
            direction: value in `[1, 'BUY']` to open a buy or value in `[-1, 'SELL']`
                to open a sell
        """
        if direction:
            if direction == 1 or (
                isinstance(direction, str) and direction.upper() == 'BUY'
            ):
                self._direction = 1
                return
            elif direction == -1 or (
                isinstance(direction, str) and direction.upper() == 'SELL'
            ):
                self._direction = -1
                return
        raise TradeException(f'Invalid trade direction: {direction}')

    ##################################################
    # STOP/LIMIT HELPERS
    ##################################################
    def _set_stop_limit(
        self, type_: str, value: Union[int, float], relative: bool
    ) -> Union[StopLimitMixinAbsolute, StopLimitMixinRelative]:
        """
        Set a stop or a limit on trade

        Arguments:
            type_: `STOP` or `LIMIT`
            value: stop/limit value
            relative: is the stop/limit value is relative or absolute

        Returns:
            Stop/Limit object
        """
        if relative:
            # set stop/limit as relative
            return StopLimitMixinRelative(type_=type_, trade=self, value=value,)

        # set stop/limit as an absolute stop
        return StopLimitMixinAbsolute(type_=type_.lower(), trade=self, value=value)

    ##################################################
    # STOP GET/SET
    ##################################################
    @property
    def stop(self) -> Optional[Union[StopLimitMixinRelative, StopLimitMixinAbsolute]]:
        """
        Returns:
            Stop/Limit object
        """
        return self._stop

    @stop.setter
    def stop(self, stop: Any) -> None:
        """
        Prevent set of stop directly as stop set requires to define if the stop is
        relative (use set_stop method)

        Argument:
            Stop value

        !!! warning
            Do not use this method, use the set_stop

        """
        raise NotImplementedError(
            'Impossible to directly set stop on trade, use Trade.set_stop method'
        )

    def set_stop(self, stop_value: Union[int, float], relative: bool = False) -> None:
        """
        Stop setter

        Arguments:
            stop_value: stop value
            relative: is the stop value relative to trade open tick or absolute
        """
        self._stop = self._set_stop_limit(
            type_='stop', value=stop_value, relative=relative
        )

    ##################################################
    # LIMIT GET/SET
    ##################################################
    @property
    def limit(self) -> Optional[Union[StopLimitMixinAbsolute, StopLimitMixinRelative]]:
        """
        Returns:
            Trade Stop/Limit object
        """
        return self._limit

    @limit.setter
    def limit(self, limit: Any) -> None:
        """
        Prevent set of limit directly as limit set requires to define if the limit is
        relative (use set_limit method)

        Arguments:
            limit: limit value

        !!! warning
            Do not use this method, use `Trade.set_limit()`

        """
        raise NotImplementedError(
            'Impossible to directly set limit on trade, use Trade.set_limit method'
        )

    def set_limit(self, limit_value: Union[int, float], relative: bool = False) -> None:
        """
        Limit setter

        Arguments:
            limit_value: value of the target profit
            relative: is the value provided relative to trade open tick or absolute
        """
        self._limit = self._set_stop_limit(
            type_='limit', value=limit_value, relative=relative
        )

    ##################################################
    # EPIC GETTERS
    ##################################################
    @property
    def epic(self) -> 'Epic':
        """
        get trade epic

        Returns:
            Trade Epic
        """
        return self.open_tick.epic

    ##################################################
    # OPEN GETTERS
    ##################################################
    @property
    def open(self) -> float:
        """
        Returns:
            trade open value (value of open tick)
        """
        if self.direction > 0:
            return self.open_tick.ask

        return self.open_tick.bid

    @property
    def high(self) -> float:
        """
        Returns:
            trade higher tick value
        """
        return self.high_tick.bid if self.direction > 0 else self.high_tick.ask

    @property
    def low(self) -> float:
        """
        Returns:
            trade lower tick value
        """
        return self.high_tick.bid if self.direction > 0 else self.high_tick.ask

    ##################################################
    # QUANTITIES GETTERS
    ##################################################
    @property
    def quantity(self) -> int:
        """
        Returns:
            current opened quantities
        """
        return self.opened_quantity

    ##################################################
    # CLOSE
    ##################################################
    def close(
        self, tick: Tick = None, quantity: int = None, close_reason: str = 'manual'
    ) -> None:
        """
        Total or partial close of trade.

        Arguments:
            tick: tick to close trade with (last epic tick if not provided)
            quantity: quantity to close (all closed if not provided)
            close_reason: justification of the trade close (for reporting use)

        """
        # define quantities to close
        if quantity and quantity > self.opened_quantity:
            raise TradeException(
                f'Impossible to close {quantity} '
                f'(more than remaining quantity {self.opened_quantity}'
            )
        if not quantity:
            quantity = self.opened_quantity

        # define tick to use for close
        if not tick:
            tick = self.epic.ticks[-1]

        # prevent close when epic is not tradeable
        if not tick.epic.tradeable:
            logger.error(
                'Impossible to close trade because epic %s is not tradeable.'
                % tick.epic.ref
            )
            return

        # calculate result of this close
        close_result = self._calculate_result(close_tick=tick, quantity=quantity)
        self.closed_result += close_result

        # add a new close object to list of closed.
        self.closes.append(
            TradeClose(
                tick=tick, quantity=quantity, result=close_result, reason=close_reason,
            )
        )
        self.closed_quantity += quantity
        self.opened_quantity -= quantity
        if self.opened_quantity <= 0:
            self.result = self.closed_result
            self.closed = True
        else:
            self.result = self._calculate_result(tick) + self.closed_result

        logger.info(
            '%s : Close %d @ %f > %f (max loss: %f, max_gain: %f)'
            % (
                tick.datetime,
                quantity,
                tick.value,
                close_result,
                self.max_loss,
                self.max_gain,
            )
        )

    ##################################################
    # RESULT
    ##################################################
    def _calculate_result(self, close_tick: Tick = None, quantity: int = None) -> float:
        """
        Calculate trade result for close.

        Returns:
            The trade result
        """
        if not close_tick:
            close_tick = self.last_tick
        if not quantity:
            quantity = self.opened_quantity

        if self.direction > 0:
            return round((close_tick.bid - self.open_tick.ask) * abs(quantity), 2)
        else:
            return round((self.open_tick.bid - close_tick.ask) * abs(quantity), 2)

    ##################################################
    # HANDLE NEW TICK
    ##################################################
    def on_new_tick(self, tick: Tick):
        """
        Method triggered when a new tick is received by trade_manager.

        Arguments:
            tick: new tick received

        """
        if not self.closed:
            self.last_tick = tick
            if tick.value > self.high_tick.value:
                self.high_tick = tick
            if tick.value < self.low_tick.value:
                self.low_tick = tick

            # update max gain and max loss
            self.opened_result = self._calculate_result(tick)
            self.result = self.closed_result + self.opened_result

            self.update_max_loss_gains(self.result)

            # check stop/limit
            logger.debug(
                'Check if tick value reached stop (%s) or limit (%s)'
                % (self.stop, self.limit)
            )
            if self.stop and self.stop.check(tick):
                if self.trade_manager:
                    self.trade_manager.close_trade(trade=self, close_reason='stop')
                else:
                    self.close(close_reason='stop')
            elif self.limit and self.limit.check(tick):
                if self.trade_manager:
                    self.trade_manager.close_trade(trade=self, close_reason='limit')
                else:
                    self.close(close_reason='limit')

    def update_max_loss_gains(self, current_result: float) -> None:
        """
        Update trade max gain and max losses.

        Arguments:
            current_result: current trade result
        """
        if current_result < self.max_loss:
            self.max_loss = self.result
        elif current_result > self.max_gain:
            self.max_gain = self.result

    ##################################################
    # REPORTING
    ##################################################
    @property
    def to_json(self):
        return {
            'ref': self.ref,
            'open_at': self.open_tick.datetime,
            'open': self.open_tick.value,
            'open_quantity': abs(self.inital_quantities),
            'direction': self.direction,
            'stop_rel': self.stop.relative_value if self.stop else None,
            'stop_abs': self.stop.absolute_value if self.stop else None,
            'limit_rel': self.limit.relative_value if self.limit else None,
            'limit_abs': self.limit.absolute_value if self.limit else None,
            'closed_quantity': abs(self.closed_quantity),
            'closed': self.closed,
            'closes': [c.to_json() for c in self.closes],
            'result': self.result,
            'max_loss': self.max_loss,
            'max_gain': self.max_gain,
            **self.meta,
        }

    @property
    def json_headers(self):
        base_headers = [
            'ref',
            'open_at',
            'open',
            'open_quantity',
            'direction',
            'stop_rel',
            'stop_abs',
            'limit_rel',
            'limit_abs',
            'closed_quantity',
            'closed',
            'closes',
            'result',
            'max_loss',
            'max_gain',
        ]
        base_headers.extend(list(self.meta.keys()))
        return base_headers

    def __repr__(self):
        repr_string = (
            f'{self.open_tick.datetime}: '
            f'Trade for {self.inital_quantities} @ {self.open} '
            f'with ref: {self.ref} '
            f'on strategy {self.strategy.ref if self.strategy else None}'
        )
        if self.stop:
            repr_string = (
                f'{repr_string}, '
                f'stop absolute: {self.stop.absolute_value}, '
                f'stop relative {self.stop.relative_value}'
            )
        if self.limit:
            repr_string = (
                f'{repr_string}, '
                f'limit absolute: {self.limit.absolute_value}, '
                f'limit relative {self.limit.relative_value}'
            )
        return repr_string
