import logging

from estrade.classes.abstract.Amarket_class import AMarketMandatoryClass
from estrade.classes.abstract.Atrade_class import ATradeClassUser
from estrade.classes.exceptions import TradeManagerException
from estrade.classes.observer import Observable

logger = logging.getLogger(__name__)


class TradeManager(AMarketMandatoryClass, ATradeClassUser, Observable):
    """
    A trade manager handle a list of trades.
    """
    def __init__(self, market=None, trades=None):
        """
        Init a new trade manager
        :param market: <estrade.classes.market.Market> instance
        :param trades: [<self.trade_class>,]
        """
        # init list of trades
        self.trades = trades
        self.open_trades = []
        self.closed_trades = []
        self.strategy_trades = {}

        # init market
        AMarketMandatoryClass.__init__(self, market)

        # init trade_manager with the default trade class <estrade.classes.trade.Trade>
        ATradeClassUser.__init__(self, trade_class=None)

        # set trade manager as observable so it can fire events
        Observable.__init__(self)
        logger.debug('New trade manager created with %d open trades and %d closed trades' % (
            len(self.open_trades),
            len(self.closed_trades)
        ))
        logger.debug('strategy trades: {}'.format(self.strategy_trades))

    ##################################################
    # Market
    ##################################################
    def _post_set_market(self):
        for strategy in self.market.strategies:
            if strategy.ref not in self.strategy_trades:
                self.strategy_trades[strategy.ref] = {'opened': [], 'closed': []}

    ##################################################
    # Trades
    ##################################################
    @property
    def trades(self):
        """
        Retur list of trades
        :return: [<self.trade_class>,]
        """
        return self._trades

    @trades.setter
    def trades(self, trades):
        """
        Set list of trades
        :param trades: None or [<self.trade_class>,]
        :return:
        """
        self._trades = []
        if not trades:
            return

        if not isinstance(trades, list):
            raise TradeManagerException('Trades must be a list')

        for trade in trades:
            if not isinstance(trade, self.trade_class):
                raise TradeManagerException('Trades list must only contains instance of Trades')
            self._trades.append(trade)

    def get_trade_by_ref(self, ref):
        """
        Find a trade by its ref
        :param ref: <str>
        :return: <self.trade_class> instance or None
        """
        for trade in reversed(self.trades):
            if trade.ref == ref:
                return trade
        return None

    ##################################################
    # OPEN TRADE
    ##################################################
    def open_trade_api_call(self, trade):
        """
        Call API to open a new trade
        :param trade: <self.trade_class>
        :return: None or <self.trade_class>
        """
        return trade

    def open_trade(self, *args, **kwargs):
        """
        Open a new trade
        :param args/kwargs: agrs/kwargs required to open a trade (see <self.trade_class.__init__> )
        :return: <self.trade_class> instance
        """
        logger.debug('Open new trade')
        self.fire('trade_manager_before_new_trade', *args, **kwargs)

        new_trade = self.trade_class(*args, trade_manager=self, **kwargs)
        new_trade = self.open_trade_api_call(new_trade)
        if not new_trade:
            logger.error('New trade creation failed, do not add it to trade manager trades.')
            return None

        self.trades.append(new_trade)
        self.open_trades.append(new_trade)
        if new_trade.strategy:
            self.strategy_trades[new_trade.strategy.ref]['opened'].append(new_trade)

        self.fire('trade_manager_after_open_trade', trade=new_trade)

        return new_trade

    @property
    def open_buys(self):
        """
        List all opened buy trades
        :return: [<self.trade_class>,]
        """
        return [trade for trade in self.open_trades if trade.direction > 0]

    @property
    def open_sells(self):
        """
        List all opened sell trades
        :return: [<self.trade_class>,]
        """
        return [trade for trade in self.open_trades if trade.direction < 0]

    ##################################################
    # ON NEW TICK EVENT
    ##################################################
    def on_new_tick(self, tick):
        """
        On new tick, dispatch tick to all opened trades
        :param tick: <estrade.classes.tick.Tick>
        :return:
        """
        from estrade.classes.tick import Tick
        if not isinstance(tick, Tick):
            raise TradeManagerException('Invalid tick received')

        for trade in reversed(self.open_trades):
            if tick.epic == trade.epic:
                trade.on_new_tick(tick)

    ##################################################
    # CLOSE TRADE
    ##################################################
    def close_trade_api_call(self, trade, quantity):
        """
        Method used by providers trade manager to close trade by api.
        :param trade: <self.trade_class> instance
        :param quantity: <int>
        :return: <self.trade_class> instance or None if api call failed
        """

        return trade

    def _close_trade(self, trade, quantity=None, close_reason='close unique trade', tick=None):
        """
        method to close a trade.

        This method fire the following events:
            - trade_manager_before_close_trade
            - trade_manager_after_close_trade

        :param trade: <self.trade_class> instance
        :param quantity: <int> quantity to close on trade
        :param close_reason: <str> closing reason
        :param tick: <estrade.classes.tick.Tick> instance : tick to use for trade close
        :return:
        """
        logger.info('close unique trade %s', trade)
        quantity = quantity if quantity and quantity <= trade.opened_quantity else trade.opened_quantity

        self.fire('trade_manager_before_close_trade', trade=trade, quantity=quantity, close_reason=close_reason)

        updated_trade = self.close_trade_api_call(trade, quantity)
        if not updated_trade:
            logger.error('Impossible to close %d on trade because api call failed for %s' % (quantity, trade.ref))
            return None

        updated_trade.close(quantity=quantity, close_reason=close_reason, tick=tick)

        # drop trade from open_trades and add it to closed trades
        self.open_trades.remove(updated_trade)
        self.closed_trades.append(updated_trade)

        if updated_trade.strategy:
            self.strategy_trades[updated_trade.strategy.ref]['opened'].remove(updated_trade)
            self.strategy_trades[updated_trade.strategy.ref]['closed'].append(updated_trade)

        self.fire('trade_manager_after_close_trade', trade=updated_trade)

    def close_trade_by_ref(self, ref, close_reason='close trade by ref', quantity=None, strategy=None, tick=None):
        """
        Close a trade by its reference
        :param ref: <str> ref of a trade in self.trades
        :param close_reason: <str>
        :param quantity: <int> quantity to close
        :param strategy: <estrade.classes.strategy.Strategy> strategy to restrict search for trade on
        :param tick: <estrade.classes.tick.Tick> instance : tick to use for trade close
        :return:
        """
        for trade in reversed(self.get_trades(only_opened=True, strategy=strategy)):
            if not trade.closed and trade.ref == ref and (not strategy or trade.strategy == strategy):
                self._close_trade(trade, quantity=quantity, close_reason=close_reason, tick=tick)
                return
        raise TradeManagerException(
            'impossible to find trade to close with ref {} in {}'.format(
                ref,
                [trade.ref for trade in self.trades if not trade.closed]
            )
        )

    def close_all_trades(self, close_reason='close all trades', strategy=None, tick=None):
        """
        Close all open trades (for a specific strategy if prrovided)
        :param close_reason: <str>
        :param strategy: <estrade.classes.strategy.Strategy> child instance
        :param tick: <estrade.classes.tick.Tick> instance : tick to use for trade close
        :return:
        """
        logger.debug('close all trades')
        for trade in reversed(self.trades):
            if not trade.closed and (not strategy or trade.strategy == strategy):
                self._close_trade(trade, close_reason=close_reason, tick=tick)

    def close_all_buys(self, close_reason='close all buys', strategy=None, tick=None):
        """
        Close all opened buy trades (for a specific strategy if provided)
        :param close_reason: <str>
        :param strategy: <estrade.classes.strategy.Strategy> child instance
        :param tick: <estrade.classes.tick.Tick> instance : tick to use for trade close
        :return:
        """
        for trade in reversed(self.trades):
            if not trade.closed and trade.direction > 0 and (not strategy or trade.strategy == strategy):
                self._close_trade(trade, close_reason=close_reason, tick=tick)

    def close_all_sells(self, close_reason='close all sells', strategy=None, tick=None):
        """
        Close all opened sell trades (for a specific strategy if provided)
        :param close_reason: <str>
        :param strategy: <estrade.classes.strategy.Strategy> child instance
        :param tick: <estrade.classes.tick.Tick> instance : tick to use for trade close
        :return:
        """
        for trade in reversed(self.trades):
            if not trade.closed and trade.direction < 0 and (not strategy or trade.strategy == strategy):
                self._close_trade(trade, close_reason=close_reason, tick=tick)

    ##################################################
    # STATS
    ##################################################
    def get_trades(self, only_opened=False, only_closed=False, strategy=None):
        """
        get a list of trade based on search input params
        :param only_opened: <bool> only return opened trades
        :param only_closed: <bool> only return closed trades
        :param strategy: <estrade.classes.strategy.Strategy> child instance
        :return: [<self.trade_class>,]
        """
        if strategy:
            if only_closed:
                return self.strategy_trades[strategy.ref]['closed']
            elif only_opened:
                return self.strategy_trades[strategy.ref]['opened']
            else:
                return self.strategy_trades[strategy.ref]['opened'] + self.strategy_trades[strategy.ref]['closed']

        if only_closed:
            return self.closed_trades
        elif only_opened:
            return self.open_trades
        return self.trades

    def won_trades(self, **kwargs):
        """
        Return list of trade with a positive (or zero) result
        :param kwargs: (same arguments as TradeManager.get_trades method)
        :return: [<self.trade_class>,]
        """
        return [trade for trade in self.get_trades(**kwargs) if trade.result >= 0]

    def lost_trades(self, **kwargs):
        """
        Return list of trade with a negative result
        :param kwargs: (same arguments as TradeManager.get_trades method)
        :return: [<self.trade_class>,]
        """
        return [trade for trade in self.get_trades(**kwargs) if trade.result < 0]

    def nb_trades(self, **kwargs):
        """
        Count number of trade matching input argements
        :param kwargs: (same arguments as TradeManager.get_trades method)
        :return: [<self.trade_class>,]
        """
        return len(self.get_trades(**kwargs))

    def nb_win(self, **kwargs):
        """
        Count number of trade with a positive result and matching input parameters
        :param kwargs: (same arguments as TradeManager.get_trades method)
        :return: <int>
        """
        return len(self.won_trades(**kwargs))

    def nb_losses(self, **kwargs):
        """
        Count number of trade with a negative result and matching input parameters
        :param kwargs: (same arguments as TradeManager.get_trades method)
        :return: <int>
        """
        return len(self.lost_trades(**kwargs))

    def total_win(self, **kwargs):
        """
        Return the total result of trades with a positive result
        :param kwargs: (same arguments as TradeManager.get_trades method)
        :return: <int>
        """
        return sum([trade.result for trade in self.won_trades(**kwargs)])

    def total_losses(self, **kwargs):
        """
        Return the total result of trades with a negative result
        :param kwargs: (same arguments as TradeManager.get_trades method)
        :return: <int>
        """
        return sum([trade.result for trade in self.lost_trades(**kwargs)])

    def result(self, **kwargs):
        """
        Return the total result of trades matching input arguments
        :param kwargs: (same arguments as TradeManager.get_trades method)
        :return: <int>
        """
        return sum([trade.result for trade in self.get_trades(**kwargs)])

    def profit_factor(self, **kwargs):
        """
        Return the profit factor of trades matching input arguments

        Note:
            profit factor is absolute value of (
                sum of result of trades with positive result /
                sum of results of trades with negative results
            )
        :param kwargs: (same arguments as TradeManager.get_trades method)
        :return: <float>
        """
        total_win = self.total_win(**kwargs)
        total_losses = self.total_losses(**kwargs)

        if total_losses == 0:
            return total_win
        return total_win / abs(total_losses)

    def max_drowdown(self, **kwargs):
        """
        return the max drowdown of a list of trades
        :param kwargs:
        :return:
        """
        max_dd = 0
        min = 0
        max = 0
        result = 0
        for trade in self.get_trades(**kwargs):
            result += trade.result
            if result > max:
                max = result
                min = result
            elif result < min:
                min = max - result
                if min > max_dd:
                    max_dd = min
        return max_dd
