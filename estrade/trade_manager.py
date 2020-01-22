import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, TYPE_CHECKING

import arrow

from estrade.exceptions import TradeManagerException
from estrade.observer import Observable
from estrade.trade import Trade

if TYPE_CHECKING:
    from estrade.epic import Epic
    from estrade.market import Market
    from estrade.tick import Tick
    from estrade.strategy import Strategy

logger = logging.getLogger(__name__)


class TradeManager(Observable):
    """
    A trade manager handle trades created by strategies. A trade Manager is
    attached to a Market object.

    Arguments:
        market: Parent market object

    """

    def __init__(self, market=None):
        # init list of trades
        self.trades: List[Trade] = []
        self.open_trades: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.strategy_trades: Dict[str, Dict[str : List[Trade]]] = {}

        # init market
        self.market: Market = market

        # set trade manager as observable so it can fire events
        Observable.__init__(self)
        logger.debug(
            'New trade manager created with %d open trades and %d closed trades'
            % (len(self.open_trades), len(self.closed_trades))
        )
        logger.debug('strategy trades: %s' % self.strategy_trades)

    ##################################################
    # Market
    ##################################################
    def add_strategies(self):
        logger.debug('add strategies to trade manager')
        for strategy in self.market.strategies:
            if strategy.ref not in self.strategy_trades:
                logger.debug('add strategy %s to trade manager' % strategy.ref)
                self.strategy_trades[strategy.ref] = {'opened': [], 'closed': []}

    ##################################################
    # Trades
    ##################################################
    def get_trade_by_ref(self, ref: str) -> Optional[Trade]:
        """
        Find a trade by its ref

        Arguments:
            ref: reference of the trade to fetch

        Returns:
            Trade with this reference
        """
        for trade in reversed(self.trades):
            if trade.ref == ref:
                return trade
        return None

    ##################################################
    # OPEN TRADE
    ##################################################
    def open_trade(self, *args, **kwargs) -> Optional[Trade]:
        """
        This method create a new Trade object.

        Arguments:
            args: see `estrade.Trade.open_trade` arguments
            kwargs: see `estrade.Trade.open_trade` arguments

        """
        logger.debug('Open new trade')
        self.fire('trade_manager_before_new_trade', *args, **kwargs)

        new_trade = Trade(*args, trade_manager=self, **kwargs)
        new_trade = self.market.provider.open_trade(new_trade)
        if not new_trade:
            logger.error(
                'New trade creation failed, do not add it to trade manager trades.'
            )
            return None

        self.trades.append(new_trade)
        self.open_trades.append(new_trade)
        if new_trade.strategy:
            self.strategy_trades[new_trade.strategy.ref]['opened'].append(new_trade)

        self.fire('trade_manager_after_open_trade', trade=new_trade)

        return new_trade

    @property
    def open_buys(self) -> List[Trade]:
        """
        Returns:
            List of all opened buy trades
        """
        return [trade for trade in self.open_trades if trade.direction > 0]

    @property
    def open_sells(self) -> List[Trade]:
        """
        Returns:
            List all opened sell trades
        """
        return [trade for trade in self.open_trades if trade.direction < 0]

    ##################################################
    # ON NEW TICK EVENT
    ##################################################
    def on_new_tick(self, tick: 'Tick') -> None:
        """
        On new tick, dispatch tick to all opened trades (to update their result)

        Arguments:
            tick: new tick received.
        """
        for trade in reversed(self.open_trades):
            if tick.epic == trade.epic:
                trade.on_new_tick(tick)

    def on_new_ticks_high_low(self, epic: 'Epic', high: 'Tick', low: 'Tick') -> None:
        """
        This method is used in candle mode to apply :

         - candle high to open SELL positions before candle low
         - candle low to open BUY positions before candle high

        Arguments:
            epic: Epic to search trades
            high: candle highest tick
            low: candle lowest tick

        """
        for trade in reversed(self.open_trades):
            if trade.epic == epic:
                if trade.direction > 0:
                    trade.on_new_tick(low)
                    trade.on_new_tick(high)
                else:
                    trade.on_new_tick(high)
                    trade.on_new_tick(low)

    ##################################################
    # CLOSE TRADE
    ##################################################
    def close_trade_api_call(self, trade: Trade, quantity: int) -> Trade:
        """
        Method used by providers trade manager to close trade by api.

        Arguments:
            trade: trade to close
            quantity: quantity to close on trade

        Returns:
            trade: updated trade after API call
        """

        return trade

    def close_trade(
        self,
        trade: Trade,
        quantity: int = None,
        close_reason: str = 'close unique trade',
        tick=None,
    ) -> None:
        """
        method to close a trade.

        This method fire the following events:

         - trade_manager_before_close_trade
         - trade_manager_after_close_trade

        Arguments:
            trade: trade to close
            quantity: quantity to close on trade (if not filled, the trade will be
            totally closed)
            close_reason: closing trade motivation (free string)
            tick: `estrade.Tick` to close the trade with (if not provided, the
                last tick received by epic will be applied)

        """
        logger.info('close unique trade %s', trade)
        quantity = (
            quantity
            if quantity and quantity <= trade.opened_quantity
            else trade.opened_quantity
        )

        self.fire(
            'trade_manager_before_close_trade',
            trade=trade,
            quantity=quantity,
            close_reason=close_reason,
        )

        updated_trade = self.market.provider.close_trade(trade, quantity)
        if not updated_trade:
            logger.error(
                'Impossible to close %d on trade because api call failed for %s'
                % (quantity, trade.ref)
            )
            return None

        updated_trade.close(quantity=quantity, close_reason=close_reason, tick=tick)

        # drop trade from open_trades and add it to closed trades
        self.open_trades.remove(updated_trade)
        self.closed_trades.append(updated_trade)

        if updated_trade.strategy:
            self.strategy_trades[updated_trade.strategy.ref]['opened'].remove(
                updated_trade
            )
            self.strategy_trades[updated_trade.strategy.ref]['closed'].append(
                updated_trade
            )

        self.fire('trade_manager_after_close_trade', trade=updated_trade)

    def close_trade_by_ref(
        self,
        ref: str,
        close_reason: str = 'close trade by ref',
        quantity: int = None,
        strategy: 'Strategy' = None,
        tick: 'Tick' = None,
    ) -> None:
        """
        Close a trade by its reference

        Arguments:
            ref: reference of the `estrade.Trade` to close
            quantity: quantity to close on trade (if not filled, the trade will be
            totally closed)
            close_reason: motivation of the trade close (free of use)
            strategy: Strategy to restrict trade search on
            tick: `estrade.Tick` to close the trade with (if not provided, the
                last tick received by epic will be applied)
        """
        for trade in reversed(self.get_trades(only_opened=True, strategy=strategy)):
            if (
                not trade.closed
                and trade.ref == ref
                and (not strategy or trade.strategy == strategy)
            ):
                self.close_trade(
                    trade, quantity=quantity, close_reason=close_reason, tick=tick
                )
                return
        raise TradeManagerException(
            f'impossible to find trade to close with ref {ref} '
            f'in {[trade.ref for trade in self.trades if not trade.closed]}'
        )

    def close_all_trades(
        self,
        close_reason: str = 'close all trades',
        strategy: 'Strategy' = None,
        tick: 'Tick' = None,
    ) -> None:
        """
        Close all open trades

        Arguments:
            close_reason: motivation of the trade close (free of use)
            strategy: Strategy to restrict trade search on
            tick: `estrade.Tick` to close the trade with (if not provided, the
                last tick received by epic will be applied)
        """
        logger.info(
            'close all (%d) trades for strategy %s'
            % (len(self.open_trades), strategy.ref if strategy else None)
        )
        for trade in self.open_trades[:]:
            if not strategy or trade.strategy == strategy:
                self.close_trade(trade, close_reason=close_reason, tick=tick)
                logger.debug('after close trade %s' % trade)
            else:
                logger.debug('do not close trade %s' % trade)

        logger.debug('%d trades remaining in open_trades' % len(self.open_trades))

    def close_all_buys(self, close_reason='close all buys', strategy=None, tick=None):
        """
        Close all opened buy trades.

        Arguments:
            close_reason: motivation of the trade close (free of use)
            strategy: Strategy to restrict trade search on
            tick: `estrade.Tick` to close the trade with (if not provided, the
                last tick received by epic will be applied)
        """
        for trade in self.open_trades[:]:
            if (
                not trade.closed
                and trade.direction > 0
                and (not strategy or trade.strategy == strategy)
            ):
                self.close_trade(trade, close_reason=close_reason, tick=tick)

    def close_all_sells(self, close_reason='close all sells', strategy=None, tick=None):
        """
        Close all opened SELL trades.

        Arguments:
            close_reason: motivation of the trade close (free of use)
            strategy: Strategy to restrict trade search on
            tick: `estrade.Tick` to close the trade with (if not provided, the
                last tick received by epic will be applied)
        """
        for trade in self.open_trades[:]:
            if (
                not trade.closed
                and trade.direction < 0
                and (not strategy or trade.strategy == strategy)
            ):
                self.close_trade(trade, close_reason=close_reason, tick=tick)

    ##################################################
    # STATS
    ##################################################
    def get_trades(
        self,
        only_opened: Optional[bool] = False,
        only_closed: Optional[bool] = False,
        strategy: Optional['Strategy'] = None,
        open_from: Optional[Union[datetime, arrow.Arrow]] = None,
        open_to: Optional[Union[datetime, arrow.Arrow]] = None,
    ) -> List[Trade]:
        """
        Get a list of trade based on search input params

        Arguments:
            only_closed: only return closed trades
            only_opened: only return opened trades
            strategy: only return trades for this strategy
            open_from: only return trades opened after this date
            open_to: only return trades before this date

        Returns:
            List of trades

        """
        trades = []
        if strategy:
            if only_closed:
                trades = self.strategy_trades[strategy.ref]['closed']
            elif only_opened:
                trades = self.strategy_trades[strategy.ref]['opened']
            else:
                trades = (
                    self.strategy_trades[strategy.ref]['opened']
                    + self.strategy_trades[strategy.ref]['closed']
                )
        else:
            if only_closed:
                trades = self.closed_trades
            elif only_opened:
                trades = self.open_trades
            else:
                trades = self.trades

        result_trades = []
        for trade in trades:
            if (open_from is None or open_from <= trade.open_tick.datetime) and (
                open_to is None or open_to >= trade.open_tick.datetime
            ):
                result_trades.append(trade)

        return result_trades

    def won_trades(self, **kwargs) -> List[Trade]:
        """
        Return list of trade with a positive (or zero) result

        Arguments:
            kwargs: see `estrade.TradeManager.get_trades` arguments.

        Returns:
            list of trade with a positive result.

        """
        return [trade for trade in self.get_trades(**kwargs) if trade.result >= 0]

    def lost_trades(self, **kwargs) -> List[Trade]:
        """
        Return list of trade with a negative result

        Arguments:
            kwargs: see `estrade.TradeManager.get_trades` arguments.

        Returns:
            list of trades with a negative result

        """
        return [trade for trade in self.get_trades(**kwargs) if trade.result < 0]

    def nb_trades(self, **kwargs) -> int:
        """
        Count number of trade matching input arguments

        Arguments:
            kwargs: see `estrade.TradeManager.get_trades` arguments.

        Returns:
            Count of trades matching input arguments.
        """
        return len(self.get_trades(**kwargs))

    def nb_win(self, **kwargs) -> int:
        """
        Count number of trade with a positive result and matching input parameters

        Arguments:
            kwargs: see `estrade.TradeManager.get_trades` arguments.

        Returns:
            Count of trades matching input arguments and having a positive result.
        """
        return len(self.won_trades(**kwargs))

    def nb_losses(self, **kwargs) -> int:
        """
        Count number of trade with a negative result and matching input parameters

        Arguments:
            kwargs: see `estrade.TradeManager.get_trades` arguments.

        Returns:
            Count of trades matching input arguments and having a positive result.
        """
        return len(self.lost_trades(**kwargs))

    def total_win(self, **kwargs) -> float:
        """
        Return the total result of trades with a positive result

        Arguments:
            kwargs: see `estrade.TradeManager.get_trades` arguments.

        Returns:
            Sum of results of trades having a positive result and matching input
                arguments.
        """
        return sum([trade.result for trade in self.won_trades(**kwargs)])

    def total_losses(self, **kwargs) -> float:
        """
        Return the total result of trades with a negative result

        Arguments:
            kwargs: see `estrade.TradeManager.get_trades` arguments.

        Returns:
            Sum of results of trades having a negative result and matching input
                arguments.
        """
        return sum([trade.result for trade in self.lost_trades(**kwargs)])

    def result(self, **kwargs) -> float:
        """
        Return the total result of trades matching input arguments

        Arguments:
            kwargs: see `estrade.TradeManager.get_trades` arguments.

        Returns:
            Sum of results of trades matching input arguments.
        """
        return sum([trade.result for trade in self.get_trades(**kwargs)])

    def profit_factor(self, **kwargs) -> float:
        """
        Return the profit factor of trades matching input arguments

        Arguments:
            kwargs: see `estrade.TradeManager.get_trades` arguments.

        Returns:
            Profit factor of the trades matching the input arguments.

        Note:
            profit factor is absolute value of (
                sum of result of trades with positive result /
                sum of results of trades with negative results
            )
        """
        total_win = self.total_win(**kwargs)
        total_losses = self.total_losses(**kwargs)

        if total_losses == 0:
            return total_win
        return total_win / abs(total_losses)

    def max_drowdown(self, **kwargs) -> float:
        """
        Max Drowdown of a list of trades

        Arguments:
            kwargs: see `estrade.TradeManager.get_trades` arguments.

        Returns:
            Max Drawdown of the trades matching the input arguments.
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
