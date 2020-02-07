import logging

from estrade.ref_mixin import RefMixin
from estrade.market_mixin import MarketOptionalMixin
from estrade.epic import Epic
from estrade.exceptions import StrategyException

logger = logging.getLogger(__name__)


class Strategy(MarketOptionalMixin, RefMixin):
    """
    This class define a strategy to apply on ticks/candles.

    Add instances of this class to your :class:`estrade.Market` to apply strategies on your data.

    :param estrade.Epic epic: epic instance
    :param dict params: dict of parameters you can re-use in your strategy methods
    :param str ref: it is the strategy name
    :param int max_concurrent_trades: nb max of trades concurrently opened
    """

    def __init__(self, epics, params=None, ref=None, max_concurrent_trades=1):
        logger.info('Init new strategy creation')
        # init class ref attribute
        RefMixin.__init__(self, ref)

        # set market to None on init (will be set when strategy is attached to Market instance)
        MarketOptionalMixin.__init__(self, None)

        self.epics = epics
        self.params = params
        self.max_concurrent_trades = max_concurrent_trades
        self.status = 'active'

        logger.info('New strategy created %s' % self.ref)

    ##################################################
    # EPICS
    ##################################################
    @property
    def epics(self):
        """
        Returns instance epics
        :return: [<estrade.epic.Epic>,]
        """
        return self._epics

    @epics.setter
    def epics(self, epics):
        """
        Set instance epics
        :param epics: [<estrade.epic.Epic>,] or None
        :return:
        """
        self._epics = []
        # TODO: check if necessary to allow empty epics on strategy init
        if epics is None or epics == []:
            return

        if not isinstance(epics, list):
            raise StrategyException('Invalid epics on strategy creation')

        for epic in epics:
            if not isinstance(epic, Epic):
                raise StrategyException('Invalid Epic')
            logger.debug('Add epic %s to strategy %s' % (epic.ref, self.ref))
            self._epics.append(epic)

            if self not in epic.strategies:
                epic.add_strategy(strategy=self)

    ##################################################
    # MARKET
    ##################################################
    def _post_set_market(self):
        pass

    ##################################################
    # PARAMS
    ##################################################
    @property
    def params(self):
        """
        Returns strategy params
        :return: <dict>
        """
        return self._params

    @params.setter
    def params(self, params):
        """
        Set strategy params.
        Strategy params are not used in Strategy Class, they are only set to be used in your strategy implementation.
        :param params: <dict>
        :return:
        """
        self._params = {}
        if params:
            if not isinstance(params, dict):
                raise StrategyException('Invalid params')
            self._params = params

    ##################################################
    # GETTERS
    # Helpers to fetch elements in strategy execution methods
    ##################################################
    def get_epic(self, epic_ref):
        """
        Getter to find epic in strategies epic from ref.

        :param epic_ref: (str)
        :raises: :class:`estrade.exeptions.StrategyException` : if epic not found on market
        :return: :class:`estrade.epic.Epic`: epic instance
        """
        for epic in self.epics:
            if epic.ref == epic_ref:
                return epic
        raise StrategyException('Epic with ref {} not found'.format(epic_ref))

    def get_candle_set(self, epic_ref, timeframe):
        """
        Getter to find a candle set from epic_ref and timeframe

        :param epic_ref: (str) (matching an epic current strategy epics)
        :param timeframe: (str) (matching a candleset.timeframe in epic)
        :raises: :class:`estrade.exeptions.StrategyException` : if epic not found on market
        :raises: :class:`estrade.exeptions.EpicException` : if no candle set with this timeframe found on this epic
        :return: :class:`estrade.candle_set.CandleSet` instance
        """
        return self.get_epic(epic_ref).get_candle_set(timeframe)

    def get_candle(self, epic_ref, timeframe, offset=0):
        """
        Getter to find a candle by its offset in a candleset

        Offset usage example:
            - 0: returns the currently opened candle on candleset
            - 1 : returns the last closed candle
            - etc.

        .. note ::
            Reserve usage of this getter when you need to find candles that are not the
            current candle or the last closed candle.

            It is recommendend to use the :class:`estrade.CandleSet` attributes
            (`last_closed_candle`, `current_candle`) for these cases.

        :param epic_ref: (str) (matching an epic current strategy epics)
        :param timeframe: (str) (matching a candleset.timeframe in epic)
        :param offset: (int)
        :raises:
            - :class:`estrade.exeptions.StrategyException` : if epic not found on market
            - :class:`estrade.exeptions.EpicException` : if no candle set with this timeframe found on this epic
        :return:
            - :class:`estrade.candle.Candle` instance : if candle matching this offset found
            - None: if no candle matching this offset found
        """
        offset = abs(offset) + 1
        cs = self.get_candle_set(epic_ref, timeframe)
        if len(cs.candles) >= offset:
            return cs.candles[offset * -1]
        return None

    def get_indicator(self, epic_ref, timeframe, indicator_name, offset=0):
        """
        Getter to find a candle indicator value.

        :param epic_ref: (str) (matching an epic current strategy epics)
        :param timeframe: (str) (matching a candleset.timeframe in epic)
        :param indicator_name: (str) (matching an existing indicator on candle_set)
        :param offset: (int)
        :raises:
            - :class:`estrade.exeptions.StrategyException` : if epic not found on market
            - :class:`estrade.exeptions.EpicException` : if no candle set with this timeframe found on this epic
        :return:
            - :class:`estrade.candle.Candle` instance : if candle matching this offset found
            - None: if no candle matching this offset found or if indicator not found on candle
        """
        candle = self.get_candle(epic_ref, timeframe, offset)
        if not candle:
            return None
        return candle.indicators.get(indicator_name)

    def get_trades(self, **kwargs):
        """
        Getter to find list of strategy trades

        :param kwargs: see :func:`estrade.trade_manager.TradeManager.get_trades` params
        :return: [:class:`estrade.trade.Trade`,] list of trades
        """
        return self.market.trade_manager.get_trades(strategy=self, **kwargs)

    ##################################################
    # OPEN/CLOSE trade(s) helpers
    ##################################################
    def open_trade(self, **kwargs):
        """
        Use this method to open a trade.

        This method calls :func:`estrade.trade_manager.TradeManager.open_trade` method and inject
        this strategy as an argument.

        for example, you can open a trade in your strategy event as following ::

            self.open_trade(
                # mandatory params
                epic=self.get_epic('MY_EPIC_CODE'),
                quantity=5,
                direction='SELL',
                # optional params
                ref='my_trade_ref',
                stop_relative=10,
                limit_relative=20,
                meta={'data': 'my_data'},
            )


        :param kwargs: arguments to create a :class:`estrade.trade.Trade` instance
        """
        self.market.trade_manager.open_trade(strategy=self, **kwargs)

    def close_trade_by_ref(self, *args, **kwargs):
        """
        Use this method to close a trade by its reference.

        This method calls :func:`estrade.TradeManager.close_trade_by_ref` method and inject
        this strategy as an argument.

        :param kwargs: args to close a trade (see :func:`estrade.TradeManager.close_trade_by_ref`)
        """
        self.market.trade_manager.close_trade_by_ref(*args, strategy=self, **kwargs)

    def close_all_trades(self, *args, **kwargs):
        """
        Use this method to close all opened trades for strategy

        This method calls :func:`estrade.TradeManager.close_all_trades` method and inject
        this strategy as an argument.

        :param kwargs: args to close a trade (see :func:`estrade.TradeManager.close_all_trades`)
        """
        self.market.trade_manager.close_all_trades(*args, strategy=self, **kwargs)

    def close_all_buys(self, *args, **kwargs):
        """
        Use this method to close all opened buys for strategy

        This method calls :func:`estrade.TradeManager.close_all_buys` method and inject
        this strategy as an argument.

        :param kwargs: args to close a trade (see :func:`estrade.TradeManager.close_all_buys`)
        """
        self.market.trade_manager.close_all_buys(*args, strategy=self, **kwargs)

    def close_all_sells(self, *args, **kwargs):
        """
        Use this method to close all opened sells for strategy

        This method calls :func:`estrade.TradeManager.close_all_sells` method and inject
        this strategy as an argument.

        :param kwargs: args to close a trade (see :func:`estrade.TradeManager.close_all_sells`)
        """
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
        if self.market.trade_manager.strategy_trades[self.ref]['opened']:
            return True
        return False

    def _apply_opening_strategy(self):
        """
        Check if opening strategy must be applied.
        Opening strategy have to be applied if the number of open trades is inferior to the max concurrent trades
        :return: <bool> True if opening strategy have to be applied, else False
        """
        if len(self.market.trade_manager.strategy_trades[self.ref]['opened']) < self.max_concurrent_trades:
            return True
        return False

    ##################################################
    # EVENTS
    ##################################################
    def on_new_tick(self, tick):
        """
        Method triggered when a new tick is received by Market.
        This method check if opening and/or closing srategies have to be applied and then call the opening/closing
        methods.

        :param tick: <estrade.tick.Tick>
        :return:
        """
        if not self.market:
            raise StrategyException('Impossible to handle a new tick on strategy {} without market associated'.format(
                self.ref
            ))

        logger.debug('check if any trade has to be open/closed on new tick')
        if not self.check_tick_time(tick):
            if len(self.market.trade_manager.strategy_trades[self.ref]['opened']) > 0:
                logger.info('%s out of trading period > close %s' % (
                    tick.datetime,
                    self.market.trade_manager.strategy_trades[self.ref]['opened'][0]
                ))
                self.close_all_trades(close_reason='out of trading period for strategy {}'.format(self.ref))

                if len(self.market.trade_manager.strategy_trades[self.ref]['opened']) > 0:
                    exit()
            # close all trades
            return

        if self._apply_closing_strategy():
            logger.debug('apply closing strategy')
            self.on_new_tick_closing_strategy(tick)

            for candle_set in tick.epic.candle_sets:
                if candle_set.new_candle_opened:
                    self.on_new_candle_closing_strategy(candle_set=candle_set)

        if self._apply_opening_strategy():
            logger.debug('apply opening strategy')
            self.on_new_tick_opening_strategy(tick)

            for candle_set in tick.epic.candle_sets:
                if candle_set.new_candle_opened:
                    logger.debug('call new candle opening strategy bc '
                                 'a new candle was created in %s' % candle_set.timeframe)
                    self.on_new_candle_opening_strategy(candle_set=candle_set)

    def on_new_candle(self, candle):
        # check market
        # check close time
        # closing strategy on all 4 ticks
        pass

    ##################################################
    # Strategy apply method to be implemented
    ##################################################
    def check_tick_time(self, tick):
        """
        This method is executed on every tick and allow to restrict the date/time where the strategy applies.
        If this method return False, no opening strategy will be applied.

        Notes:
            - tick.datetime is an Arrow instance (see arrow lib: https://arrow.readthedocs.io)
            - if this method is not defined, it will always return True (no date/time restriction)

        :param estrade.Tick tick: tick instance
        :return: bool
        """
        return True

    def on_new_tick_opening_strategy(self, tick):
        """
        This method is called on every tick received from provider when the number of open trades for this strategy
        is inferior to this instance `max_concurrent_trades` value.

        :param estrade.Tick tick: tick instance
        :return: None
        """
        pass

    def on_new_tick_closing_strategy(self, tick):
        """
        this method is called on every tick received from provider when at least one trade is
        opened for this strategy.

        :param estrade.Tick tick: tick instance
        :return: None
        """
        pass

    def on_new_candle_opening_strategy(self, candle_set):
        """
        method called every time a new candle is created when the number of opened trades for this strategy
        is inferior to this instance `max_concurrent_trades` value.

        :param estrade.CandleSet candle_set: candle set instance
        :return: None
        """
        pass

    def on_new_candle_closing_strategy(self, candle_set):
        """
        method called every time a new candle is created and at least one trade is
        opened for this strategy.

        :param estrade.CandleSet candle_set: candle set instance
        :return: None
        """
        pass

    ##################################################
    # Reporting
    ##################################################
    @property
    def to_json(self):
        """
        Generate a dictionary of strategy stats for reporting
        :return:
        """
        strategy_stats = {
            'ref': self.ref,
            'max_concurrent_trades': self.max_concurrent_trades,
            'profit_factor': None,
            'result': None,
            'nb_trades': 0,
            'nb_win': 0,
            'nb_losses': 0,
            **self.params,
        }
        if self.market and self.market.trade_manager:
            strategy_stats['profit_factor'] = self.market.trade_manager.profit_factor(strategy=self)
            strategy_stats['result'] = self.market.trade_manager.result(strategy=self)
            strategy_stats['nb_trades'] = self.market.trade_manager.nb_trades(strategy=self)
            strategy_stats['nb_win'] = self.market.trade_manager.nb_win(strategy=self)
            strategy_stats['nb_losses'] = self.market.trade_manager.nb_losses(strategy=self)
            strategy_stats['max_drawdown'] = self.market.trade_manager.max_drowdown(strategy=self)

        return strategy_stats

    @property
    def json_headers(self):
        """
        Generate header of a dictionary of strategy stats for reporting
        :return:
        """
        headers = [
            'ref',
            'profit_factor',
            'result',
            'nb_trades',
            'nb_win',
            'nb_losses',
            'max_drawdown',
            'max_concurrent_trades',
        ]
        headers.extend(list(self.params.keys()))
        return headers
