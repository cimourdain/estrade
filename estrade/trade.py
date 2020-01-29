""" This module define the Trade class used to manage positions.
"""
import logging

from estrade.ref_mixin import RefMixin
from estrade.exceptions import TradeException
from estrade.observer import Observable
from estrade.stop_limit import StopLimitAbsolute, StopLimitRelative
from estrade.strategy import Strategy
from estrade.tick import Tick


logger = logging.getLogger(__name__)


class TradeClose:
    """
    Manage a trade close
    """

    def __init__(self, tick, quantity, result, reason):
        """
        Init a trade close
        :param tick: <estrade.tick.Tick> instance
        :param quantity: <int>
        :param result: <float>
        :param reason: <str>
        """
        self.tick = tick
        self.quantity = quantity
        self.result = result
        self.reason = reason

    def to_json(self):
        """
        Convert trade close to dict (mainly used for reporting)
        :return: <dict>
        """
        return {
            'tick': self.tick.to_json(True),
            'quantity': self.quantity,
            'reason': self.reason,
            'result': self.result
        }


class Trade(RefMixin, Observable):
    """
        The Trade class manage trades (=market positions)
    """
    def __init__(self, quantity, direction, tick=None, epic=None, trade_manager=None, strategy=None, ref=None,
                 stop_absolute=None, stop_relative=None, limit_absolute=None, limit_relative=None, meta=None):
        """
        Init a new trade
        :param tick: <estrade.tick.Tick> instance : trade open tick
        :param epic: <str> epic ref
        :param quantity: <int> opened quantity
        :param trade_manager: <estrade.trade_manager.TradeManager> trade manager managing this trade
        :param direction: <int> in [1, -1, 'BUY', 'SELL'] trade direction (buy or sell)
        :param strategy: <estrade.Astrategy.Astrategy> child instance => strategy that generated this trade
        :param ref: <str> trade reference
        :param stop_absolute: <int> absolute stop
        :param stop_relative: <int> relative stop
        :param limit_absolute: <int> absolute limit
        :param limit_relative: <int> relative limit
        :param meta: <dict> free of use dict to register provider events etc.
        """
        # set ref with parent class
        RefMixin.__init__(self, ref)
        # set class as observable so it can fire events
        # TODO : fire events on trade update
        Observable.__init__(self)

        self.trade_manager = trade_manager
        self.strategy = strategy
        self.direction = direction
        self.inital_quantities = abs(quantity)
        self.opened_quantity = abs(quantity)
        self.closed_quantity = 0
        self.closed = False

        # init empty list of ticks received by trade
        self.ticks = []

        self._add_new_tick(self._get_open_tick(tick, epic))

        # init empty list of closes
        self.closes = []

        # set max gain and max losses
        self.max_gain = float('inf') * -1
        self.max_loss = float('inf')
        self.update_max_loss_gains(self._calculate_result())

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

        self.meta = {} if not meta or not isinstance(meta, dict) else meta

        logger.info('%s' % repr(self))

    ##################################################
    # INIT HELPERS
    ##################################################
    def _get_open_tick(self, tick, epic):
        # add tick to list of ticks
        if tick is not None:
            logger.warning('It is highly disrecommended to specify tick on trade open. '
                           'A trade whould be opened with not specified tick (the last epic tick will be used)')
            # check that provided tick is valid
            Trade.is_open_tick_valid(tick)
            return tick
        elif epic is not None:
            epic = self.trade_manager.market.get_epic(epic)
            if not epic:
                raise TradeException('Impossible to find epic (to get the trade open tick)')
            return epic.current_tick

        raise TradeException('Provide epic ref to open trade')

    @staticmethod
    def is_open_tick_valid(tick):
        """
        Check that tick provided is valid
        :param tick: <estrade.tick.Tick> instance
        :return: <bool> True if tick valid and epic tradeable else False
        """
        if not Trade.is_tick_valid(tick):
            raise TradeException('Invalid tick')

        if not Trade.is_tick_tradeable(tick):
            raise TradeException('Tick epic {} is not tradeable, cannot open trade'.format(tick.epic.ref))

        return True

    @staticmethod
    def is_tick_valid(tick):
        """
        Check if a tick is a valid class instance
        :param tick: <estrade.tick.Tick> instance
        :return: <bool>
        """
        return isinstance(tick, Tick)

    @staticmethod
    def is_tick_tradeable(tick):
        """
        Check if tick epic is tradeable
        :param tick: <estrade.tick.Tick> instance
        :return: <bool>
        """
        return tick.epic.tradeable

    ##################################################
    # TRADE MANAGER GET/SET
    ##################################################
    @property
    def trade_manager(self):
        """
        return trade manager that holds this trade
        :return: <estrade.trade_manager.TradeManager>
        """
        return self._trade_manager

    @trade_manager.setter
    def trade_manager(self, trade_manager):
        """
        Set the trade manager that holds this trade
        :param trade_manager: <estrade.trade_manager.TradeManager>
        :return:
        """
        # import here to prevent import loop
        from estrade.trade_manager import TradeManager

        if trade_manager is None:
            self._trade_manager = None
            return

        if not isinstance(trade_manager, TradeManager):
            raise TradeException('Invalid trade manager: {}'.format(trade_manager))
        self._trade_manager = trade_manager

    ##################################################
    # DIRECTION GET/SET
    ##################################################
    @property
    def direction(self):
        """
        Return trade direction
        :return: <int> 1 if trade is a BUY, -1 if trade is a SELL
        """
        return self._direction

    @direction.setter
    def direction(self, direction):
        """
        Set trade direction
        :param direction: <int> in [-1, 1] or <str> in ['SELL', 'BUY']
        :return:
        """
        if direction:
            if direction == 1 or (isinstance(direction, str) and direction.upper() == 'BUY'):
                self._direction = 1
                return
            elif direction == -1 or (isinstance(direction, str) and direction.upper() == 'SELL'):
                self._direction = -1
                return
        raise TradeException('Invalid trade direction: {}'.format(direction))

    ##################################################
    # Strategy GET/SET
    ##################################################
    @property
    def strategy(self):
        """
        Returns the strategy that generated this trade
        :return: <estrade.strategy.Strategy> child instance or None
        """
        return self._strategy

    @strategy.setter
    def strategy(self, strategy):
        """
        Set trade strategy:
            - if strategy is provided in params, set this strategy
            - else if only one strategy is registered on market -> use this strategy
            - else raise error
        :param strategy: <estrade.strategy.Strategy> child instance or None
        :return:
        """
        if strategy is None:
            if self.trade_manager and self.trade_manager.market and len(self.trade_manager.market.strategies) == 1:
                logger.warning('Use market unique strategy to open trade, \
                               it is recommended to explicitly define \
                               strategy when opening trade')
                self._strategy = self.trade_manager.market.strategies[0]
                return
            self._strategy = None
            logger.warning('A trade was opened without a strategy defined')
            return

        if not isinstance(strategy, Strategy):
            raise TradeException('Invalid Strategy : {}'.format(strategy))

        self._strategy = strategy

    ##################################################
    # STOP/LIMIT HELPERS
    ##################################################
    def _set_stop_limit(self, type_, value, relative):
        """
        Set a stop or a limit on trade
        :param type_: <str> in ['STOP', 'LIMIT']
        :param value: <int> or <float>
        :param relative: <bool>
        :return: <estrade.stop_limit.AbstractStopLimit> child instance
        """
        if value is None:
            return None

        if relative:
            # set stop/limit as relative
            return StopLimitRelative(
                type_=type_,
                trade=self,
                value=value,
            )

        # set stop/limit as an absolute stop
        return StopLimitAbsolute(
            type_=type_.lower(),
            trade=self,
            value=value
        )

    ##################################################
    # STOP GET/SET
    ##################################################
    @property
    def stop(self):
        """
        Return trade stop
        :return: <estrade.stop_limit.AbstractStopLimit> Child
        """
        return self._stop

    @stop.setter
    def stop(self, stop):
        """
        Prevent set of stop directly as stop set requires to define if the stop is relative (use set_stop method)
        :param stop:
        :return:
        """
        raise NotImplementedError('Impossible to directly set stop on trade, use Trade.set_stop method')

    def set_stop(self, stop_value, relative=False):
        """
        Stop setter
        :param stop_value: <int> or <float>
        :param relative: <bool> : is the stop value provided is relative to trade open tick?
        :return:
        """
        self._stop = self._set_stop_limit(type_='stop', value=stop_value, relative=relative)

    ##################################################
    # LIMIT GET/SET
    ##################################################
    @property
    def limit(self):
        """
        return trade limit
        :return: <estrade.stop_limit.AbstractStopLimit> Child
        """
        return self._limit

    @limit.setter
    def limit(self, limit):
        """
        Prevent set of limit directly as limit set requires to define if the limit is relative (use set_limit method)
        :param limit:
        :return:
        """
        raise NotImplementedError('Impossible to directly set limit on trade, use Trade.set_limit method')

    def set_limit(self, limit_value, relative=False):
        """
        Limit setter
        :param limit_value: <int> or <float>
        :param relative: <bool> : is the stop value provided is relative to trade open tick?
        :return:
        """
        self._limit = self._set_stop_limit(type_='limit', value=limit_value, relative=relative)

    ##################################################
    # EPIC GETTERS
    ##################################################
    @property
    def epic(self):
        """
        get trade epic
        :return: <estrade.epic.Epic> instance
        """
        return self.ticks[0].epic

    ##################################################
    # OPEN GETTERS
    ##################################################
    @property
    def open_tick(self):
        """
        get trade open tick
        :return: <estrade.tick.Tick> instance
        """
        return self.ticks[0]

    @property
    def open(self):
        """
        Return trade open value (value of open tick)
        :return: <int>
        """
        if self.direction > 0:
            return self.open_tick.ask

        return self.open_tick.bid

    ##################################################
    # MIN/MAX GETTERS
    ##################################################
    @property
    def max(self):
        """
        Return upper value of ticks received during this trade
        # TODO: rename this property for clarity
        :return: <float>
        """
        return max([t.value for t in self.ticks])

    @property
    def min(self):
        """
        Return lower value of ticks received during this trade
        # TODO: rename this property for clarity
        :return: <float>
        """
        return min([t.value for t in self.ticks])

    ##################################################
    # QUANTITIES GETTERS
    ##################################################
    @property
    def quantity(self):
        """
        Return current opened quantities
        :return: <int>
        """
        return self.opened_quantity

    ##################################################
    # CLOSE
    ##################################################
    def close(self, tick=None, quantity=None, close_reason='manual'):
        """
        Total or partial close of trade.

        :param tick: <estrade.tick.Tick> instance -> tick to use for close
            (if not provided, last received tick will be used)
        :param quantity: <int> -> quantities to close
            (if not provided, all opened quantities will be closed)
        :param close_reason: <str> -> comment on trade close
        :return:
        """
        # define quantities to close
        if quantity and quantity > self.opened_quantity:
            raise TradeException(
                'Impossible to close {} (more than remaining quantity {}'.format(
                    quantity, self.opened_quantity
                )
            )
        if not quantity:
            quantity = self.opened_quantity

        # define tick to use for close
        if not tick:
            tick = self.ticks[-1]
        elif not Trade.is_tick_valid(tick):
            raise TradeException('Invalid tick provided to close trade')

        # prevent close when epic is not tradeable
        if not Trade.is_tick_tradeable(tick):
            logger.error('Impossible to close trade because epic %s is not tradeable.' % tick.epic.ref)
            return

        # calculate result of this close
        close_result = self._calculate_result(close_tick=tick, quantity=quantity)

        # add a new close object to list of closed.
        self.closes.append(TradeClose(
            tick=tick,
            quantity=quantity,
            result=close_result,
            reason=close_reason,
        ))
        self.closed_quantity += quantity
        self.opened_quantity -= quantity
        if self.opened_quantity <= 0:
            self.closed = True

        logger.info(
            '%s : Close %d @ %f > %f (max loss: %f, max_gain: %f)' % (
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
    def _calculate_result(self, close_tick=None, quantity=None):
        """
        Calculate trade result for close.
        :param sell_tick: <estrade.tick.Tick> instance -> tick to use to calculate close result
            (if not provided, the last tick received by trade will be used)
        :param quantity: <int> -> quantities to close
        :return:
        """
        if not close_tick:
            close_tick = self.ticks[-1]
        if not quantity:
            quantity = self.opened_quantity

        if self.direction > 0:
            return round((close_tick.bid - self.ticks[0].ask) * abs(quantity), 2)
        else:
            return round((self.ticks[0].bid - close_tick.ask) * abs(quantity), 2)

    @property
    def closed_result(self):
        """
        Result of closed quantities for this trade
        :return: <float>
        """
        result = 0
        for close in self.closes:
            result += close.result
        return result

    @property
    def opened_result(self):
        """
        Current result of opened quantities
        :return:
        """
        return self._calculate_result()

    @property
    def result(self):
        """
        Total trade result (opened quantities + closed quantities)
        :return:
        """
        return self.closed_result + self.opened_result

    ##################################################
    # HANDLE NEW TICK
    ##################################################
    def on_new_tick(self, tick):
        """
        Method triggered when a new tick is received by trade_manager.
        :param tick: <estrade.tick.Tick> instance
        :return:
        """
        if not self.closed:
            self._add_new_tick(tick)

            # update max gain and max loss
            self.update_max_loss_gains(self._calculate_result())

            # check stop/limit
            logger.debug('Check if tick value reached stop (%s) or limit (%s)' % (self.stop, self.limit))
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

    def _add_new_tick(self, tick):
        """
        Method to add a new tick to trade
        :param tick: <estrade.tick.Tick> instance
        :return:
        """
        if not Trade.is_tick_valid(tick):
            raise TradeException('Invalid tick provided to add on trade.')

        self.ticks.append(tick)

    def update_max_loss_gains(self, current_result):
        """
        Update trade max gain and max losses.
        :param current_result: <float>
        :return:
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
            'nb_ticks': len(self.ticks),
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
            'nb_ticks',
        ]
        base_headers.extend(list(self.meta.keys()))
        return base_headers

    def __repr__(self):
        repr_string = '{}: Trade for {} @ {} with ref: {} on strategy {}'.format(
            self.open_tick.datetime,
            self.inital_quantities,
            self.open,
            self.ref,
            self.strategy.ref if self.strategy else None
        )
        if self.stop:
            repr_string = '{}, stop absolute: {}, stop relative {}'.format(
                repr_string,
                self.stop.absolute_value,
                self.stop.relative_value,
            )
        if self.limit:
            repr_string = '{}, limit absolute: {}, limit relative {}'.format(
                repr_string,
                self.limit.absolute_value,
                self.limit.relative_value,
            )
        return repr_string
