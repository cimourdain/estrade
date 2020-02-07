import logging

from estrade.ref_mixin import RefMixin
from estrade.mixins.reporting_mixin import ReportingMixin
from estrade.exceptions import MarketException
from estrade.observer import Observable
from estrade.strategy import Strategy
from estrade.tick import Tick
from estrade.trade_manager import TradeManager


logger = logging.getLogger(__name__)


class Market(RefMixin, Observable):
    """
    A market is the component wrapping provider and epics.
    """
    def __init__(self, strategies, provider, ref=None, reporting=None):
        """
        Init a new Market Instance
        :param provider: <estrade.provider.Provider> child
        :param ref: <str>
        :param reporting: <estrade.reporting.AReporting> child
        """
        logger.info('Create new Market')

        # init ref via parent
        RefMixin.__init__(self, ref)

        # set as observable so market can fire events.
        Observable.__init__(self)

        # init epics as an empty list (will be filled by strategies epics)
        self.epics = []
        self.strategies = strategies

        # Init new trade manager
        self.trade_manager = None

        self.provider = provider

        self.reporting = reporting
        logger.info('New market created with %d strategies and %d epics' % (len(self.strategies), len(self.epics)))

    ##################################################
    # TRADE MANAGER
    ##################################################
    @property
    def trade_manager(self):
        return self._trade_manager

    @trade_manager.setter
    def trade_manager(self, trade_manager):
        logger.debug('create new TradeManager on market')
        self._trade_manager = TradeManager(market=self)

    ##################################################
    # PROVIDER
    ##################################################
    @property
    def provider(self):
        """
        return market provider
        :return:
        """
        return self._provider

    @provider.setter
    def provider(self, provider):
        """
        Set Market Provider
        :param provider: <estrade.provider.Provider> child
        :return:
        """
        logger.debug('Set a new market provider')
        # import here to prevent import loop
        from estrade.provider import Provider
        if not isinstance(provider, Provider):
            raise MarketException('Invalid Provider')

        self._provider = provider
        # attach this instance to provider
        self._provider.market = self

    ##################################################
    # STRATEGIES
    ##################################################
    @property
    def strategies(self):
        """
        return this instance strategies
        :return: [<estrade.strategy.Strategy> children]
        """
        return self._strategies

    @strategies.setter
    def strategies(self, strategies):
        """
        Assign strategies to Market
        :param strategies: [<estrade.strategy.Strategy> children]
        :return:
        """
        self._strategies = []
        logger.debug('init market strategies')
        if not isinstance(strategies, list):
            raise MarketException('strategies must be a list')

        for strategy in strategies:
            if not isinstance(strategy, Strategy):
                raise MarketException('Strategy must be instance of Strategy')

            logger.debug('Set self as market for strategy %s' % strategy.ref)
            strategy.market = self

            logger.debug('Add strategy %s to market strategies' % strategy.ref)
            self._strategies.append(strategy)

            logger.debug('Add epics of strategy %s to market strategies' % strategy.ref)
            self.add_epics(strategy.epics)

        if not self._strategies:
            raise MarketException('Impossible to create a market without strategies')

    ##################################################
    # EPICS
    ##################################################
    def add_epics(self, epics):
        """
        Epics are not directly added to Market.
        Every time a strategy is added to Market, this method allow to add strategy epics to Market.
        :param epics: list of <Epic>
        :return:
        """
        for epic in epics:
            if epic not in self.epics:
                logger.debug('Add epic %s to market' % epic.ref)
                epic.market = self
                self.epics.append(epic)

    def get_epic(self, epic_ref):
        """
        Find an epic in list of epics by its ref.
        :param epic_ref: <str>
        :return: <estrade.epic.Epic> instance if found, else MarketException
        """
        for e in self.epics:
            if e.ref == epic_ref:
                return e
        raise MarketException('Epic with ref {} not found'.format(epic_ref))

    @property
    def epics_refs(self):
        """
        return list of ref of this instance epics
        :return: [<str>]
        """
        return [epic.ref for epic in self.epics]

    ##################################################
    # REPORTING
    ##################################################
    @property
    def reporting(self):
        """
        return current instance reporting
        :return: <estrade.reporting.AReporting> child
        """
        return self._reporting

    @reporting.setter
    def reporting(self, reporting):
        """
        Assign reporting to market
        :param reporting: <estrade.reporting.Reporting> child
        :return:
        """
        self._reporting = None
        if reporting and isinstance(reporting, ReportingMixin):
            self._reporting = reporting
            self._reporting.market = self

    ##################################################
    # RUNTIME
    ##################################################
    def _dispatch_tick_to_epic(self, tick):
        # dispatch tick to its epic to update candleset and indicators
        tick.epic.on_new_tick(tick=tick)

        # send tick to strategies attached to its epic
        for strategy in tick.epic.strategies:
            logger.debug('dispatch tick to strategy %s' % strategy.ref)
            strategy.on_new_tick(tick)

    def on_new_tick(self, tick):
        """
        This method is called every time a new tick is sent by provider.

        :param tick: :class:`estrade.tick.Tick`
        :return:
        """
        logger.debug('new tick received: %f' % tick.value)
        Tick.validate(tick)

        # update open trades with the new tick
        self.trade_manager.on_new_tick(tick=tick)

        self._dispatch_tick_to_epic(tick)

    def on_new_candle(self, candle):
        """
        This method is called every time a new candle is sent by self.provider.
        :param candle: :class:`estrade.candle.Candle`
        :return
        """
        candle_epic = candle.open_tick.epic

        # dispatch open tick to epic candle_sets
        self.on_new_tick(tick=candle.open_tick)

        # check that a new candle was created
        for candle_set in candle_epic.candle_sets:
            if candle_set.timeframe == candle.timeframe and not candle_set.new_candle_opened:
                raise MarketException(f'Error, the open tick provided did '
                                      f'not create a new candle in candle set {candle.timefame}')

        # dispatch high/low to trade_manager
        self.trade_manager.on_new_tick_high_low(
            epic=candle_epic,
            low=candle.low_tick,
            high=candle.high_tick,
        )
        # dispatch high/low to candle sets
        if candle.high_tick and candle.low_tick:
            if candle.high_tick.datetime < candle.low_tick.datetime:
                self._dispatch_tick_to_epic(candle.high_tick)
                self._dispatch_tick_to_epic(candle.low_tick)
            else:
                self._dispatch_tick_to_epic(candle.low_tick)
                self._dispatch_tick_to_epic(candle.high_tick)
        elif candle.high_tick:
            self._dispatch_tick_to_epic(candle.high_tick)
        elif candle.low_tick:
            self._dispatch_tick_to_epic(candle.low_tick)

        # dispatch candle close
        self.on_new_tick(candle.close_tick)

    def run(self):
        """
        This method run the data Provider.
            - check provided is logged
            - check that no open trade exists in provider
            - generate ticks from provider (for every tick, the provider call the above method on_new_tick)
        :return:
        """
        self.fire('market_before_run')

        logger.info('Check if provider is logged')
        if not self.provider.logged:
            raise MarketException('Cannot start because provider is not logged, '
                                  'please call the provider login function before running market.')

        logger.info('Check opened trades')
        if self.provider.get_open_trades():
            raise MarketException('Cannot start when trades are already opened')

        logger.info('Generate ticks from provider')
        self.provider.generate()

        self.fire('market_run_end')
