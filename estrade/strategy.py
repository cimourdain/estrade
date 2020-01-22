import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import arrow

from estrade.candle_set import CandleSet
from estrade.candle import Candle
from estrade.mixins.ref_mixin import RefMixin
from estrade.mixins.candle_set_indicator_mixin import CandleSetIndicatorMixin
from estrade.epic import Epic
from estrade.tick import Tick
from estrade.trade import Trade
from estrade.exceptions import StrategyException

if TYPE_CHECKING:
    from estrade.market import Market

logger = logging.getLogger(__name__)


class Strategy(RefMixin):
    """
    This class define a strategy to apply on ticks/candles.t pu

    Arguments:
        epics: list of `estrade.Epic` instances
        meta: free of use dict of parameters you can re-use in your strategy methods
        ref: strategy name
        max_concurrent_trades: nb max of trades concurrently opened

    Define your custom strategies to define when to open/close trades. Your strategies
    are triggered by all new ticks received and all new candles created on the
    Epics attached to it.

    !!! example
        Example of a strategy that

         - open a BUY trade when the tick value is 1000
         - open a SELL trade when the last closed candle was red
         - close all opened BUY trades when the moving average on 50 periods is
         inferior to the current tick - 20
         - close all trades when the strategy result is > 200 when a new candle opens.

        ```python
        from estrade import CandleSet, Market, Provider, SimpleMovingAverage, Strategy

        class MyCustomStrategy(Strategy):
            def on_new_tick_opening_strategy(tick):
                if tick.value == 1000:
                    self.open_trade(
                        epic=tick.epic,
                        quantity=2,
                        direction='SELL',
                        stop_absolute=1010,
                        limit_absolute=990,
                    )

            def on_new_candle_opening_strategy(candle_set):
                last_candle = candle_set.last_closed_candle
                # check if is defined because on first candle in candle set,
                # it will be none.
                if last_candle:
                    if last_candle.color == 'red':
                        self.open_trade(
                            epic=candle_set.epic,
                            quantity=1,
                            direction='BUY',
                            stop_relative=30,
                        )

            def on_new_tick_closing_strategy(tick):
                sma50_15mn = self.get_indicator(
                    epic_ref='MY_EPIC',
                    timeframe='15minutes',
                    indicator_name='sma50'
                )
                # check if exists because for the 49 fist candles it will not be defined
                if sma50_15mn:
                    if sma50_15mn < (tick.value - 20):
                        self.close_all_buys()


            def on_new_candle_closing_strategy(tick):
                result = self.market.trade_manager.result(strategy=self)
                if result > 200:
                    self.close_all_trades()

        class MyProvider(Provider):
            # define your custom provider
            pass

        if __name__ == '__main__':
            market = Market()

            epic = Epic(ref='MY_EPIC', market=market)
            sma50 = SimpleMovingAverage(periods=50, ref='sma50')
            candle_set = CandleSet(epic=epic, timeframe='15minutes', indicators=[sma50])

            strategy = MyCustomStrategy(market=market, epics=[epic])
            provider = MyProvider(market=market)

            market.run()

        ```


    """

    def __init__(
        self,
        market: 'Market',
        epics: List[Epic],
        meta: Optional[Dict[str, Any]] = None,
        ref: str = None,
        max_concurrent_trades: int = 1,
    ):
        logger.info('Init new strategy creation')
        self.market: Market = market
        self.market.strategies.append(self)
        # init class ref attribute
        RefMixin.__init__(self, ref)

        self.epics = epics
        self.meta = meta or {}
        self.max_concurrent_trades = max_concurrent_trades
        self.status = "active"

        self.paused_until: Optional[arrow.Arrow] = None
        self.stopped = False

        logger.info('New strategy created %s' % self.ref)

    ##################################################
    # EPICS
    ##################################################
    @property
    def epics(self) -> List[Epic]:
        """
        Return:
            Returns list of epics attached to strategy
        """
        return self._epics

    @epics.setter
    def epics(self, epics: List[Epic]) -> None:
        """
        Attach epics on the current strategy.

        Raises:
            StrategyExeption: if input is not a list of `estrade.Epic` instances.


        """
        self._epics = []

        if not isinstance(epics, list):
            raise StrategyException('Invalid epics on strategy creation')

        for epic in epics:
            if not isinstance(epic, Epic):
                raise StrategyException('Invalid Epic')
            logger.debug('Add epic %s to strategy %s' % (epic.ref, self.ref))
            self._epics.append(epic)
            epic.strategies.append(self)

    ##################################################
    # GETTERS
    # Helpers to fetch elements in strategy execution methods
    ##################################################
    def get_epic(self, epic_ref: str) -> Epic:
        """
        Getter to find epic in strategies epic from its ref.

        Arguments:
            epic_ref: ref of an Epic in the current strategy epics.

        Raises:
            StrategyException: if epic not found in current strategy epics

        Returns:
            Epic instance

        """
        for epic in self.epics:
            if epic.ref == epic_ref:
                return epic
        raise StrategyException(f'Epic with ref {epic_ref} not found')

    def get_candle_set(self, epic_ref: str, timeframe: str) -> CandleSet:
        """
        Getter to find a candle set from epic_ref and timeframe.

        Arguments:
            epic_ref: reference of an epic attached to this strategy
            timeframe: timeframe of the `estrade.CandleSet` to return

        Raises:
            StrategyException : if epic not found on market
            EpicException : if no candle set with this timeframe found on this epic

        Return:
            A candle set object, see `estrade.CandleSet`

        """
        return self.get_epic(epic_ref).get_candle_set(timeframe)

    def get_candle(
        self, epic_ref: str, timeframe: str, offset: int = 0
    ) -> Optional[Candle]:
        """
        Getter to find a candle by its offset in a candleset

        Arguments:
            epic_ref: reference of an epic attached to this strategy
            timeframe: timeframe of the `estrade.CandleSet` to return
            offset: index of the candle to retrieve

        !!! info "Offset usage"
            - 0: returns the currently opened candle on candleset
            - 1 : returns the last closed candle
            - etc.

        !!! tip
            Reserve usage of this getter when you need to find candles that are not the
            current candle or the last closed candle.

            It is recommendend that you call the `Strategy.get_candle_set` method and
            retrieve its `last_closed_candle`, `current_candle` for these cases.

        Raises:
            StrategyException : if epic not found on market
            EpicException : if no candle set with this timeframe found on this epic

        Return:
            A candle object, see `estrade.Candle`

        """
        offset = abs(offset) + 1
        cs = self.get_candle_set(epic_ref, timeframe)
        if len(cs.candles) >= offset:
            return cs.candles[offset * -1]
        return None

    def get_indicator(
        self, epic_ref: str, timeframe: str, indicator_name: str, offset: int = 0
    ) -> Optional[CandleSetIndicatorMixin]:
        """
        Getter to find a candle indicator value.

        Arguments:
            epic_ref: ref of an epic in current strategy epics
            timeframe: matching a candleset.timeframe in epic
            indicator_name: matching an existing indicator on candle_set
            offset: offset of the candle to fetch indicator from
                (see `Strategy.get_candle` offset argument)

        Raise:
            StrategyException : if epic not found on market
            EpicException : if no candle set with this timeframe found on this epic

        Returns:
            Indicator value
        """
        candle = self.get_candle(epic_ref, timeframe, offset)
        if not candle:
            return None
        return candle.indicators.get(indicator_name)

    def get_trades(self, **kwargs) -> Optional[List[Trade]]:
        """
        Getter to find list of strategy trades.

        !!! seealso
            referer to `TradeManager.get_trades` to view the list of arguments

        Returns:
            List of trades attached to the current strategy
        """
        return self.market.trade_manager.get_trades(strategy=self, **kwargs)

    ##################################################
    # OPEN/CLOSE trade(s) helpers
    ##################################################
    def open_trade(self, **kwargs) -> None:
        """
        Use this method to open a trade.

        This method calls `estrade.trade_manager.TradeManager.open_trade` method
        and inject this strategy as an argument.

        As a result, a new `estrade.Trade` instance is created and attached to the
        TradeManager.

        for example, you can open a trade in your strategy event as following ::

        !!! example
            Example of trade open that you can use in opening strategies
            ```python
                from estrade import Strategy

                class MyCustomStrategy:
                    def on_new_tick_opening_strategy(self, tick):
                        if tick.value == 1000:
                            self.open_trade(
                                # mandatory params
                                epic=tick.epic,
                                quantity=5,
                                direction='SELL',
                                # optional params
                                ref='my_trade_ref',
                                stop_relative=10,
                                limit_relative=20,
                                meta={'data': 'my_data'},
                            )
            ```
        """
        self.market.trade_manager.open_trade(strategy=self, **kwargs)

    def close_trade_by_ref(self, ref: str, **kwargs) -> None:
        """
        Use this method in your closing strategy methods to close a trade by its
        reference.

        !!! info
            Closing strategy method where it is advised to call this method are:

            - `Strategy.on_new_tick_closing_strategy`
            - `Strategy.on_new_candle_closing_strategy`

        !!! seealso
            This method calls `estrade.TradeManager.close_trade_by_ref` method
            and inject this strategy as an argument.

        Arguments:
            ref: existing `estrade.trade.Trade` ref code attached to this strategy on
                current Market.trade_manager
            kwargs: args to close a trade
                (see `estrade.TradeManager.close_trade_by_ref`)
        hello
        """
        self.market.trade_manager.close_trade_by_ref(ref=ref, strategy=self, **kwargs)

    def close_all_trades(self, *args, **kwargs) -> None:
        """
        Use this method in your closing strategy methods to close all opened trades
        for strategy

        !!! info
            Closing strategy method where it is advised to call this method are:

            - `Strategy.on_new_tick_closing_strategy`
            - `Strategy.on_new_candle_closing_strategy`

        !!! seealso
            This method calls `estrade.TradeManager.close_all_trades` method and inject
            this strategy as an argument.

        Arguments:
            args: args to close a trade (see `estrade.TradeManager.close_all_trades`)
            kwargs: args to close a trade (see `estrade.TradeManager.close_all_trades`)
        """
        kwargs.pop('strategy', None)
        self.market.trade_manager.close_all_trades(*args, strategy=self, **kwargs)

    def close_all_buys(self, *args, **kwargs) -> None:
        """
        Use this method in closing strategy methods to close all opened buys for
        strategy

        !!! info
            Closing strategy method where it is advised to call this method are:

            - `Strategy.on_new_tick_closing_strategy`
            - `Strategy.on_new_candle_closing_strategy`

        !!! seealso
            This method calls `estrade.TradeManager.close_all_buys` method and inject
            this strategy as an argument.

        Arguments:
            args: args to close a trade (see `estrade.TradeManager.close_all_buys`)
            kwargs: args to close a trade (see `estrade.TradeManager.close_all_buys`)
        """
        kwargs.pop('strategy', None)
        self.market.trade_manager.close_all_buys(*args, strategy=self, **kwargs)

    def close_all_sells(self, *args, **kwargs) -> None:
        """
        Use this method in closing strategy methods to close all opened sells for
        strategy

        !!! info
            Closing strategy method where it is advised to call this method are:

            - `Strategy.on_new_tick_closing_strategy`
            - `Strategy.on_new_candle_closing_strategy`

        !!! seealso
            This method calls `estrade.TradeManager.close_all_sells` method and inject
            this strategy as an argument.

        Arguments:
            args: args to close a trade (see `estrade.TradeManager.close_all_sells`)
            kwargs: args to close a trade (see `estrade.TradeManager.close_all_sells`)
        """
        kwargs.pop('strategy', None)
        self.market.trade_manager.close_all_sells(*args, strategy=self, **kwargs)

    ##################################################
    # Check if strategy method has to be applied
    ##################################################
    def _apply_closing_strategy(self):
        """
        Check if closing strategy must be applied.
        Closing strategy is applied if trades are opened.
        :return: <bool> True if closing strategy have to be applied, else False
        """
        if self.market.trade_manager.strategy_trades[self.ref]["opened"]:
            return True
        return False

    def _apply_opening_strategy(self):
        """
        Check if opening strategy must be applied.
        Opening strategy have to be applied if the number of open trades is inferior to
        the max concurrent trades
        :return: <bool> True if opening strategy have to be applied, else False
        """
        if (
            len(self.market.trade_manager.strategy_trades[self.ref]["opened"])
            < self.max_concurrent_trades
        ):
            return True
        return False

    ##################################################
    # EVENTS
    ##################################################
    def _is_strategy_paused(self, current_datetime: arrow.Arrow) -> bool:
        """
        Check if strategy is paused for a given tick datetime.
        """
        if self.paused_until is None:
            return False
        elif self.paused_until <= current_datetime:
            logger.info('Un-pause strategy %s' % self.ref)
            self.paused_until = None
            return False
        return True

    def on_new_tick(self, tick: Tick) -> None:
        """
        Method triggered when a new tick is received by Market.
        This method check if opening and/or closing srategies have to be applied and
        then call the opening/closing
        methods.

        Arguments:
            tick: new tick instance received

        """
        logger.debug('check if any trade has to be open/closed on new tick')

        self.on_every_new_tick(tick)
        apply_closing_strategy = self._apply_closing_strategy()

        if apply_closing_strategy:
            self.on_new_tick_closing_strategy(tick)

        for candle_set in tick.epic.candle_sets:
            if candle_set.new_candle_opened:
                self.on_every_new_candle(candle_set)
                if apply_closing_strategy:
                    self.on_new_candle_closing_strategy(candle_set=candle_set)

        if self._is_strategy_paused(tick.datetime):
            logger.debug('Strategy %s is paused, do not apply tick.')
            return

        if self._apply_opening_strategy():
            logger.debug('apply opening strategy')
            self.on_new_tick_opening_strategy(tick)

            for candle_set in tick.epic.candle_sets:
                if candle_set.new_candle_opened:
                    logger.debug(
                        "call new candle opening strategy bc "
                        "a new candle was created in %s" % candle_set.timeframe
                    )
                    self.on_new_candle_opening_strategy(candle_set=candle_set)

    ##################################################
    # Strategy apply method to be implemented
    ##################################################
    def on_every_new_tick(self, tick: Tick) -> None:
        """
        This method is called on every new tick received, it should be reserved
        to pause strategy (set of `self.pause_until`) or stopping strategy
        (set of `self.stopped`).
        """
        pass

    def on_every_new_candle(self, candle_set: CandleSet) -> None:
        """
        This method is called on every new tick received, it should be reserved
        to pause strategy (set of `self.pause_until`) or stopping strategy
        (set of `self.stopped`).
        """
        pass

    def set_stop(self, current_datetime: arrow.Arrow) -> None:
        """
        This method is called before every opening and closing strategy methods
        execution. Its purpose is to update the `self.stopped` parameter
        with `True` when the strategy have to be totally stopped.

        Arguments:
            current_datetime: datetime of the last received tick


        !!! note
            When the `self.stopped` value is set to `True` the strategy is totally
            deactivated. No tick will every be sent again to this strategy.

        !!! note
            If all strategy are stopped, the market run will automatically end.

        """
        pass

    def on_new_tick_opening_strategy(self, tick: Tick) -> None:
        """
        This method is called on every tick received from provider when the number of
        open trades for this strategy
        is inferior to this instance `max_concurrent_trades` value.

        Arguments:
            tick: new tick received
        """
        pass

    def on_new_tick_closing_strategy(self, tick: Tick) -> None:
        """
        Method is called on every tick received from provider when at least one trade is
        opened for this strategy.

        Arguments:
            tick: new tick received

        """
        pass

    def on_new_candle_opening_strategy(self, candle_set: CandleSet) -> None:
        """
        Method called every time a new candle is created when the number of opened
        trades for this strategy is inferior to this instance `max_concurrent_trades`
        value.

        Use this method to open trades with `Strategy.open_trade` method.

        Arguments:
            candle_set: candle set that generated a new candle

        """
        pass

    def on_new_candle_closing_strategy(self, candle_set: CandleSet) -> None:
        """
        Method called every time a new candle is created and at least one trade is
        opened for this strategy.

        Arguments:
            candle_set: candle set that generated a new candle

        """
        pass

    ##################################################
    # Reporting
    ##################################################
    @property
    def to_json(self) -> Dict[str, Any]:
        """
        Generate a dictionary of strategy stats for reporting
        """
        strategy_stats = {
            "ref": self.ref,
            "max_concurrent_trades": self.max_concurrent_trades,
            "profit_factor": None,
            "result": None,
            "nb_trades": 0,
            "nb_win": 0,
            "nb_losses": 0,
            **self.meta,
        }
        if self.market and self.market.trade_manager:
            strategy_stats["profit_factor"] = self.market.trade_manager.profit_factor(
                strategy=self
            )
            strategy_stats["result"] = self.market.trade_manager.result(strategy=self)
            strategy_stats["nb_trades"] = self.market.trade_manager.nb_trades(
                strategy=self
            )
            strategy_stats["nb_win"] = self.market.trade_manager.nb_win(strategy=self)
            strategy_stats["nb_losses"] = self.market.trade_manager.nb_losses(
                strategy=self
            )
            strategy_stats["max_drawdown"] = self.market.trade_manager.max_drowdown(
                strategy=self
            )

        return strategy_stats

    @property
    def json_headers(self) -> List[str]:
        """
        Generate header of a dictionary of strategy stats for reporting
        """
        headers = [
            "ref",
            "profit_factor",
            "result",
            "nb_trades",
            "nb_win",
            "nb_losses",
            "max_drawdown",
            "max_concurrent_trades",
        ]
        headers.extend(list(self.meta.keys()))
        return headers
