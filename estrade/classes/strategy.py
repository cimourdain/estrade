import logging

from estrade.classes.abstract.Aref_class import ARefClass
from estrade.classes.abstract.Amarket_class import AMarketOptionalClass
from estrade.classes.epic import Epic
from estrade.classes.exceptions import StrategyException

logger = logging.getLogger(__name__)


class Strategy(AMarketOptionalClass, ARefClass):
    """
    This class define comportment of a trading bot strategy.
    """
    def __init__(self, epics, params=None, ref=None, max_concurrent_trades=1):
        """
        Init a new strategy
        :param epics: [<estrade.classes.epics.Epic>,]
        :param params: <dict> (only to use in strategy execution method)
        :param ref: <str> strategy name
        :param max_concurrent_trades: <int> nb max of trades concurrently opened
        :param log_level: <logging.LEVEL> or None
        """
        logger.info('Init new strategy creation')
        # init class ref attribute
        ARefClass.__init__(self, ref)

        # set market to None on init (will be set when strategy is attached to Market instance)
        AMarketOptionalClass.__init__(self, None)

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
        :return: [<estrade.classes.epic.Epic>,]
        """
        return self._epics

    @epics.setter
    def epics(self, epics):
        """
        Set instance epics
        :param epics: [<estrade.classes.epic.Epic>,] or None
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
        Helper method to find epic in strategies epic from ref
        :param epic_ref: <str>
        :return: <estrade.classes.epic.Epic> if found else <estrade.classes.exceptions.StrategyException>
        """
        for epic in self.epics:
            if epic.ref == epic_ref:
                return epic
        raise StrategyException('Epic with ref {} not found'.format(epic_ref))

    def get_candle_set(self, epic_ref, timeframe):
        """
        Helper to fetch a candle set from epic_ref and timeframe
        :param epic_ref: <str> (matching an epic in self.epics)
        :param timeframe: <str> (matching a candleset.timeframe in epic)
        :return: <estrade.classes.candle_set.CandleSet> instance
        """
        return self.get_epic(epic_ref).get_candle_set(timeframe)

    def get_candle(self, epic_ref, timeframe, offset=0):
        """
        Helper to get a candle from a candle set in self.epics
        :param epic_ref: <str> (matching an epic ref in self.epics)
        :param timeframe: <str> (matching an candle set timeframe in the above epic)
        :param offset: <int> nb of candles backward from the last candle in candle set found
        :return: <estrade.classes.candle.Candle> instance or None if not found
        """
        offset = abs(offset) + 1
        cs = self.get_candle_set(epic_ref, timeframe)
        if len(cs.candles) >= offset:
            return cs.candles[offset * -1]
        return None

    def get_indicator(self, epic_ref, timeframe, indicator_name, offset=0):
        """
        Helper to fetch an indicator
        :param epic_ref: <str> (matching an epic ref in self.epics)
        :param timeframe: <str> (matching an candle set timeframe in the above epic)
        :param indicator_name:
        :param offset: <int> nb of candles backward from the last candle in candle set found
        :return: <estrade.classes.Acandle_set_indicator.ACandleSetIndicator> child instance
        """
        candle = self.get_candle(epic_ref, timeframe, offset)
        if not candle:
            return None
        return candle.indicators.get(indicator_name)

    def get_trades(self, **kwargs):
        return self.market.trade_manager.get_trades(strategy=self, **kwargs)

    ##################################################
    # OPEN/CLOSE trade(s) helpers
    ##################################################
    def open_trade(self, **kwargs):
        """
        Helper to add strategy on open trade
        :param kwargs: args to open a trade (see <estrade.classes.trade_manager.TradeManager.open_trade>)
        :return:
        """
        self.market.trade_manager.open_trade(strategy=self, **kwargs)

    def close_trade_by_ref(self, *args, **kwargs):
        """
        Helper to add strategy in close trade call
        :param args/kwargs: args to close a trade (see <estrade.classes.trade_manager.TradeManager.close_trade_by_ref>)
        :return:
        """
        self.market.trade_manager.close_trade_by_ref(*args, strategy=self, **kwargs)

    def close_all_trades(self, *args, **kwargs):
        """
        Helper to add strategy on close all trade call
        :param args/kwargs: args to close all trade (see <estrade.classes.trade_manager.TradeManager.close_all_trades>)
        :return:
        """
        self.market.trade_manager.close_all_trades(*args, strategy=self, **kwargs)

    def close_all_buys(self, *args, **kwargs):
        """
        Helper to close all buys for the current strategy
        :param args/kwargs: args close all buys (see <estrade.classes.trade_manager.TradeManager.close_all_buys>)
        :return:
        """
        self.market.trade_manager.close_all_buys(*args, strategy=self, **kwargs)

    def close_all_sells(self, *args, **kwargs):
        """
        Helper to close all sells for the current strategy
        :param args/kwargs: args close all sells (see <estrade.classes.trade_manager.TradeManager.close_all_sells>)
        :return:
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

        WARNING: this method is called AFTER epics and candle set are updated (see subscriptions). As a consequence,
        if any epic candleset create a new candle for this tick.
        The `on_new_candle` method of this instance will be called BEFORE this method.

        :param tick: <estrade.classes.tick.Tick>
        :return:
        """
        if not self.market:
            raise StrategyException('Impossible to handle a new tick on strategy {} without market associated'.format(
                self.ref
            ))

        logger.debug('check if any trade has to be open/closed on new tick')
        if not self.check_tick_time(tick):
            if self.market.trade_manager.strategy_trades[self.ref]['opened']:
                logger.info('out of trading period > close %d trades' % len(
                    self.market.trade_manager.strategy_trades[self.ref]['opened']
                ))
                self.close_all_trades(close_reason='out of trading period for strategy {}'.format(self.ref))
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

    ##################################################
    # Strategy apply method to be implemented
    ##################################################
    def check_tick_time(self, tick):
        """
        Check if tick datetime is valid
        :return: <bool> True if valid else False
        """
        return True

    def on_new_tick_opening_strategy(self, tick):
        """
        method called to apply opening strategy for each tick where opening trade is allowed (see on_new_tick)
        :param tick: <estrade.classes.tick.Tick> instance
        """
        pass

    def on_new_tick_closing_strategy(self, tick):
        """
        method called to apply opening strategy for each tick where closing trade is allowed (see on_new_tick)
        :param tick: <estrade.classes.tick.Tick> instance
        """
        pass

    def on_new_candle_opening_strategy(self, candle_set):
        """
        method called every time a new candle is created
        :param candle_set: <estrade.classes.candle_set.CandleSet> instance
        """
        pass

    def on_new_candle_closing_strategy(self, candle_set):
        """
        method called every time a new candle is created
        :param candle_set: <estrade.classes.candle_set.CandleSet> instance
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
