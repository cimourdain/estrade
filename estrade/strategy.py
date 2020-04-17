import logging
from typing import Dict, Generator, List, Optional, TYPE_CHECKING, Union

from estrade.mixins import RefMixin


if TYPE_CHECKING:  # pragma: no cover
    from arrow import Arrow  # type: ignore
    from estrade import Epic, Trade, TradeClose

logger = logging.getLogger(__name__)


class BaseStrategy(RefMixin):
    """
    Abstract representation of a strategy.

    Attributes:
        epics (Dict[str, estrade.epic.Epic]): [`Epics`][estrade.epic.Epic]
            that call this instance when they receive a
            new [`Tick`][estrade.tick.Tick].
        paused_until (Optional[arrow.Arrow]): Date to which the strategy is paused.
            When a strategy is paused it will not be called by any new tick
            update of its epics until this datetime is reached.
        stopped (bool): Is the strategy stopped. When a strategy is stopped it will
            never be called again by any new tick update of its epics.
        trades (List[estrade.trade.Trade]): List of trade of this instance.

        ref (str): reference of this instance
            (see `estrade.mixins.ref.RefMixin`)
    """

    def __init__(self, ref: str = None) -> None:
        """
        Create a new Strategy instance.

        Arguments:
            ref: reference of this Strategy
        """
        RefMixin.__init__(self, ref)
        self.epics: Dict[str, "Epic"] = {}
        self.paused_until: Optional["Arrow"] = None
        self.stopped = False
        self.trades: List["Trade"] = []

    def is_active(self, new_tick_date: "Arrow") -> bool:
        """
        Check if this strategy is either stopped or paused for the input datetime.

        Arguments:
            new_tick_date: date of the current tick

        Returns:
            Is the strategy active or not?
        """
        if self.stopped:
            return False

        is_paused = self._is_paused(new_tick_date)
        return not is_paused

    def _is_paused(self, new_tick_date: "Arrow") -> bool:
        if not self.paused_until:
            return False
        is_still_paused = new_tick_date < self.paused_until
        if not is_still_paused:
            self.paused_until = None
        return is_still_paused

    ##############
    # Open/Close trades
    ##############
    def open_trade(self, epic: "Epic", **kwargs) -> "Trade":
        """
        Open a trade for this Strategy.

        Arguments:
            epic: epic to open instance on.
            kwargs: see arguments of [`Trade`][estrade.trade.Trade]
        """
        new_trade = epic.open_trade(strategy=self, **kwargs)
        return new_trade

    def close_trade(self, trade: "Trade", **kwargs) -> "TradeClose":
        """
        Close a trade.

        Arguments:
            trade: Trade to close
            kwargs: see arguments of [`TradeClose`][estrade.trade.TradeClose]

        Returns:
            closing of trade.
        """
        trade_close = trade.epic.close_trade(trade=trade, **kwargs)
        return trade_close

    def close_opened_trades(self, **kwargs) -> None:
        """
        Close all opened trades of this Strategy.

        Arguments:
            kwargs: see arguments of [`TradeClose`][estrade.trade.TradeClose]
        """
        for trade in self.get_trades(open_only=True):
            self.close_trade(trade=trade, **kwargs)

    ##############
    # Get Trades status
    ##############
    def get_trades(
        self,
        epics: Optional[List["Epic"]] = None,
        open_only: bool = False,
        only_after: Optional["Arrow"] = None,
    ) -> Generator["Trade", None, None]:
        """
        Get list of trades attached to this Strategy.

        Arguments:
            epics: epic of trades
            open_only: only returns open trades

        Returns:
            List of trades.
        """
        for trade in reversed(self.trades):
            if (epics is None or trade.epic in epics) and (
                open_only is False or trade.closed is False
            ):
                if only_after is not None and trade.datetime < only_after:
                    break
                yield trade

    def result(
        self,
        trades: Optional[Union[Generator["Trade", None, None], List["Trade"]]] = None,
    ) -> float:
        """
        Return result of a list of trades.

        Arguments:
            trades: list of trades (default to list of trades of this strategy)

        Returns:
            Result of the input list of trades.
        """
        if not trades:
            trades = self.trades

        result = 0.0
        for trade in trades:
            result += trade.result

        return round(result, 2)

    def profit_factor(
        self,
        trades: Optional[Union[Generator["Trade", None, None], List["Trade"]]] = None,
    ) -> float:
        """
        Return profit factor of a list of trades.

        Arguments:
            trades: list of trades (default to list of trades of this strategy)

        Returns:
            Profit factor of the input list of trades.
        """
        if not trades:
            trades = self.trades

        sum_positive = 0.0
        sum_negative = 0.0
        for trade in trades:
            trade_result = trade.result
            if trade_result >= 0:
                sum_positive += trade_result
            else:
                sum_negative += trade_result

        if sum_negative == 0:
            return sum_positive
        if abs(sum_negative) < 1:
            sum_negative = 1
        return abs(round(sum_positive / sum_negative, 2))

    ##############
    # Handle epic update
    ##############
    def on_every_tick(self, epic: "Epic") -> None:
        """
        Handle every new tick received by Epic.

        Arguments:
            epic: updated [`Epic`][estrade.epic.Epic] instance.
        """
        pass

    def on_market_open(self, epic: "Epic") -> None:
        """
        Handle tick when market opens.

        Arguments:
            epic: updated [`Epic`][estrade.epic.Epic] instance.
        """
        pass

    def on_market_close(self, epic: "Epic") -> None:
        """
        Handle tick when market closes.

        Arguments:
            epic: updated [`Epic`][estrade.epic.Epic] instance.
        """
        pass

    def on_every_tick_market_open(self, epic: "Epic") -> None:
        """
        Handle every tick when market is open.

        Arguments:
            epic: updated [`Epic`][estrade.epic.Epic] instance.
        """
        pass
