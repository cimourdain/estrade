import logging
import threading
from typing import List, Optional, TYPE_CHECKING

from estrade.enums import TradeDirection, TransactionStatus
from estrade.mixins import RefMixin


if TYPE_CHECKING:  # pragma: no cover
    from estrade.trade import Trade, TradeClose


logger = logging.getLogger(__name__)


class BaseTradeProvider(RefMixin):
    """
    Abstract object to create, update and close Trades.

    Attributes:
        trades (List[estrade.trade.Trade]): List of [`Trades`][estrade.trade.Trade]
            managed by this instance.
        threads (List[threading.Thread]): List of opened Threads (used to call provider)
        default_transaction_status (estrade.enums.TransactionStatus): default status
            to assign to new received [`Trades`][estrade.trade.Trade] .
        ref (str): reference of this instance
            (see `estrade.mixins.ref.RefMixin`)
    """

    def __init__(self, ref: Optional[str] = None) -> None:
        """
        Create a new TradeProvider.

        Arguments:
            ref: trade provider identifier.
        """
        self.trades: List["Trade"] = []
        self.threads: List[threading.Thread] = []
        self.default_transaction_status = TransactionStatus.REQUIRED
        RefMixin.__init__(self, ref)

        logger.info("New trade provider created.")

    def open_trade_request(self, trade: "Trade") -> "Trade":
        """
        Call an external Trade Provider to open a new Trade.

        !!! note
            after sending request to provider, it is recommened to update the
            trade object:

             - `trade.status` to set to pending or confirmed.
             - `trade.meta` to update with the provider transaction details.

        Arguments:
            trade: [`Trade`][estrade.trade.Trade] instance to open

        Returns:
            updated [`Trade`][estrade.trade.Trade] instance
        """
        raise NotImplementedError()

    def open_trade(self, trade: "Trade") -> None:
        """
        Open a trade.

        Create a thread to perform the provider request (so the thread request does
        not bock the rest of the program)

        Arguments:
            trade: New trade to create.
        """
        self.trades.append(trade)
        if trade.strategy:
            trade.strategy.trades.append(trade)

        thr = threading.Thread(
            target=self.open_trade_request,
            args=(),
            kwargs={"trade": trade},
        )
        self.threads.append(thr)
        thr.start()

    def close_trade_request(self, trade_close: "TradeClose") -> "TradeClose":
        """
        Call an external Trade Provider to close a Trade.

        !!! note
            after sending request to provider, it is recommened to update the
            TradeClose object:

             - `trade_close.status` to set to pending or confirmed.
             - `trade_close.meta` to update with the provider transaction details.

        Arguments:
            trade_close: [`TradeClose`][estrade.trade.TradeClose] instance.

        Returns:
            updated [`TradeClose`][estrade.trade.TradeClose] instance
        """
        raise NotImplementedError()

    def close_trade(self, trade_close: "TradeClose") -> None:
        """
        Close a trade.

        Arguments:
            trade_close: Close to register
        """
        thr = threading.Thread(
            target=self.close_trade_request,
            args=(),
            kwargs={"trade_close": trade_close},
        )
        self.threads.append(thr)
        thr.start()

    @property
    def is_alive(self) -> bool:
        """
        Check if some threads are still running.

        Returns:
            Are some threads still running?
        """
        for thread in self.threads:
            if thread.is_alive():
                return True
        return False

    @property
    def opened_trades(self) -> List["Trade"]:
        """
        List all opened trades for this instance.

        Returns:
            List of opened trades
        """
        opened_trades = [trade for trade in reversed(self.trades) if not trade.closed]
        return opened_trades


class TradeProviderBacktests(BaseTradeProvider):
    """Trade Provider that does not perform any external call to open/close trades."""

    def open_trade(self, trade: "Trade") -> None:
        """
        Open a trade in backtests.

        !!! warning
            This function checks if a trade is currently opened in the opposite
            direction. In this case, the currently opened trade is partially closed
            with the input trade quantity.

        Arguments:
            trade: New trade to open

        """
        opposite_direction = (
            TradeDirection.BUY
            if trade.direction == TradeDirection.SELL
            else TradeDirection.SELL
        )

        for open_trade in self.opened_trades:
            if open_trade.direction == opposite_direction:
                logger.info(
                    "A trade was opened when another is still open in "
                    "the opposite direction."
                )
                if open_trade.strategy != trade.strategy:
                    logger.info(
                        "As both trades does not belongs to the same strategy, "
                        "the existing trade will not be closed. Be warned that in "
                        "a live environement, this behaviour will not be applied."
                    )
                    continue
                logger.warning("It will be closed before opening a new position")
                quantities_to_close = min(
                    open_trade.opened_quantities, trade.open_quantity
                )
                trade_close = open_trade.close_from_epic(quantity=quantities_to_close)
                self.close_trade(trade_close=trade_close)

                trade.open_quantity -= quantities_to_close

        # if after decrement, the trade to open has a zero quantity, stop
        if trade.open_quantity <= 0:
            logger.warning("Do not open trade.")
            return

        BaseTradeProvider.open_trade(self, trade)

    def open_trade_request(self, trade: "Trade") -> "Trade":
        """
        Automatically set trade as confirmed.

        Arguments:
            trade: trade to open.
        """
        trade.status = TransactionStatus.CONFIRMED
        return trade

    def close_trade_request(self, trade_close: "TradeClose") -> "TradeClose":
        """
        Automatically set trade_close as confirmed.

        Arguments:
            trade_close: close to perform on trade.
        """
        trade_close.status = TransactionStatus.CONFIRMED
        return trade_close
