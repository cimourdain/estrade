import logging

from estrade.classes.abstract.Aref_class import ARefClass
from estrade.classes.abstract.Areporting import AReporting
from estrade.classes.exceptions import MarketException
from estrade.classes.observer import Observable
from estrade.classes.strategy import Strategy
from estrade.classes.trade_manager import TradeManager


logger = logging.getLogger(__name__)


class Market(ARefClass, Observable):
    """
    A market is the component wrapping provider and epics.
    """
    def __init__(self, strategies, provider, ref=None, reporting=None):
        """
        Init a new Market Instance
        :param provider: <estrade.classes.provider.Provider> child
        :param ref: <str>
        :param reporting: <estrade.classes.reporting.AReporting> child
        """
        logger.info('Create new Market')

        # init ref via parent
        ARefClass.__init__(self, ref)

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
        :param provider: <estrade.classes.provider.Provider> child
        :return:
        """
        logger.debug('Set a new market provider')
        # import here to prevent import loop
        from estrade.classes.abstract.Aprovider import AProvider
        if not isinstance(provider, AProvider):
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
        :return: [<estrade.classes.strategy.Strategy> children]
        """
        return self._strategies

    @strategies.setter
    def strategies(self, strategies):
        """
        Assign strategies to Market
        :param strategies: [<estrade.classes.strategy.Strategy> children]
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
        :return: <estrade.classes.epic.Epic> instance if found, else MarketException
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
        :return: <estrade.classes.reporting.AReporting> child
        """
        return self._reporting

    @reporting.setter
    def reporting(self, reporting):
        """
        Assign reporting to market
        :param reporting: <estrade.classes.reporting.Reporting> child
        :return:
        """
        self._reporting = None
        if reporting and isinstance(reporting, AReporting):
            self._reporting = reporting
            self._reporting.market = self

    ##################################################
    # RUNTIME
    ##################################################
    def on_new_tick(self, tick):
        """
        This method is called every time a new tick is sent by self.provider (see Provider.on_new_tick)
        :param tick: <estrade.classes.tick.Tick>
        :return:
        """
        logger.debug('new tick: %f' % tick.value)
        logger.debug('nb strategies : %d' % len(self.strategies))

        if tick.epic not in self.epics:
            raise MarketException('Tick epic received {}({}) not in market epics {}'.format(
                tick.epic.ref,
                id(tick.epic),
                [(e.ref, id(e)) for e in self.epics]
            ))
        tick.epic.on_new_tick(tick=tick)

        # update open trades with the new tick
        self.trade_manager.on_new_tick(tick=tick)

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
        self.provider.generate_ticks()

        self.fire('market_run_end')
