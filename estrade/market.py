import logging

from typing import List, Optional, TYPE_CHECKING

from estrade.mixins.ref_mixin import RefMixin
from estrade.epic import Epic
from estrade.exceptions import MarketException
from estrade.observer import Observable
from estrade.strategy import Strategy
from estrade.tick import Tick
from estrade.trade_manager import TradeManager

if TYPE_CHECKING:
    from estrade.provider import Provider
    from estrade.mixins.reporting_mixin import ReportingMixin


logger = logging.getLogger(__name__)


class Market(RefMixin, Observable):
    """
    A market is the component wrapping provider and epics.

    Arguments:
        ref: name of the market

    !!! example
        ```python
        from estrade import Market

        market = Market(ref='MY_MARKET')
        ```
    """

    def __init__(self, ref: str = None) -> None:
        logger.info('Create new Market')

        # init ref via parent
        RefMixin.__init__(self, ref)

        # set as observable so market can fire events.
        Observable.__init__(self)

        # init epics as an empty list (will be filled by strategies epics)
        self.epics: List[Epic] = []
        self.strategies: List[Strategy] = []

        # Init new trade manager
        self.trade_manager: TradeManager = TradeManager(market=self)

        self.provider: Optional[Provider] = None

        self.reporting: Optional[ReportingMixin] = None

    ##################################################
    # EPICS
    ##################################################
    def get_epic(self, epic_ref: str) -> Epic:
        """
        Get an epic by its reference.

        Arguments:
            epic_ref: reference of epic to find

        Raises:
            MarketException: if no epic found with this reference

        Returns:
            epic instance
        """
        for e in self.epics:
            if e.ref == epic_ref:
                return e
        raise MarketException(f'Epic with ref {epic_ref} not found')

    @property
    def epics_refs(self) -> List[str]:
        """
        Get the list of epic references

        Returns:
            list of ref of this instance epics
        """
        return [epic.ref for epic in self.epics]

    ##################################################
    # STRATEGY
    ##################################################
    @property
    def one_strategy_still_active(self) -> bool:
        for strategy in self.strategies:
            if strategy.stopped is False:
                return True
        return False

    ##################################################
    # RUNTIME
    ##################################################
    def _dispatch_tick(self, tick: Tick) -> None:
        """
        Dispatch tick to :
         - epics (update of its candle sets & indicators)
         - strategies (open and close trades)

        """
        # dispatch tick to its epic to update candleset and indicators
        tick.epic.on_new_tick(tick=tick)

        # send tick to strategies attached to its epic
        for strategy in tick.epic.strategies:
            if strategy.stopped is False:
                logger.debug('dispatch tick to strategy %s' % strategy.ref)
                strategy.on_new_tick(tick=tick)

    def on_new_tick(self, tick: Tick) -> None:
        """
        This method is called every time a new tick is sent by provider.

        Its purpose is to:
         1. Update open trades with the new tick value
         2. Dispatch tick to epic (and update candle sets & indicators)
         3. Dispatch tick to strategies (to open and close trades)

        Arguments:
            tick: new tick to be dispatched to candle sets and strategies

        Raises:
            estrade.exceptions.TickException: if tick is not valid

        """
        logger.debug('new tick received: %s' % tick)

        Tick.validate(tick)

        # update open trades with the new tick
        self.trade_manager.on_new_tick(tick=tick)

        # dispatch tick to epics and strategies
        self._dispatch_tick(tick)

    def on_new_candle(self, candle):
        """
        This method is called every time a new candle is sent by self.provider.
        :param candle: :class:`estrade.candle.Candle`
        :return
        """
        candle_epic = candle.open_tick.epic
        epic_timeframes = [cs.timeframe for cs in candle_epic.candle_sets]
        if candle.timeframe not in epic_timeframes:
            raise MarketException(
                f'Impossible to add candle, Epic {candle_epic.ref} '
                f'has no CandleSet with timeframe {candle.timeframe}'
            )
        # dispatch open tick to epic candle_sets
        self.on_new_tick(tick=candle.open_tick)

        # dispatch high and low tick to ongoing trades
        # apply low first to open BUY and high first to open SELL
        self.trade_manager.on_new_ticks_high_low(
            epic=candle_epic, low=candle.low_tick, high=candle.high_tick,
        )
        # dispatch high/low to candle sets
        if candle.high_tick.datetime < candle.low_tick.datetime:
            self._dispatch_tick(candle.high_tick)
            self._dispatch_tick(candle.low_tick)
        else:
            self._dispatch_tick(candle.low_tick)
            self._dispatch_tick(candle.high_tick)

        # dispatch candle close
        self.on_new_tick(candle.ticks[-1])

    def run(self, mode: str = 'tick') -> None:
        """
        This method run the data Provider.
            - check provided is logged
            - check that no open trade exists in provider
            - generate ticks from provider (for every tick, the provider call the above
            method on_new_tick)
        """
        self.fire('market_before_run')

        if not self.provider:
            raise MarketException('Impossible to run Market without a provider')

        # add strategies to trade manager
        self.trade_manager.add_strategies()

        logger.info('Check if provider is logged')
        if self.provider.requires_login:
            if not self.provider.login():
                raise MarketException(
                    'Cannot start because provider is not logged, '
                    'please call the provider login function before running market.'
                )

        logger.info('Check opened trades')
        if self.provider.get_open_trades():
            raise MarketException('Cannot start when trades are already opened')

        logger.info('Generate ticks from provider')
        if mode == 'tick':
            for tick in self.provider.generate_ticks():
                self.on_new_tick(tick)
                if self.one_strategy_still_active is False:
                    break

        elif mode == 'candle':
            for candle in self.provider.generate_candles():
                self.on_new_candle(candle)
                if self.one_strategy_still_active is False:
                    break

        # trigger actions (reporting etc.) on market end
        self.fire('market_run_end')
