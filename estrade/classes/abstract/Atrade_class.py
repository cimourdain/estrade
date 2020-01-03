import logging

from estrade.classes.abstract import get_exception
from estrade.classes.trade import Trade

logger = logging.getLogger(__name__)


class ATradeClassUser:

    def __init__(self, trade_class=None):
        self.trade_class = trade_class

    ##################################################
    # TRADE CLASS
    ##################################################
    @property
    def trade_class(self):
        return self._trade_class

    @trade_class.setter
    def trade_class(self, trade_class):
        if trade_class is None:
            self._trade_class = Trade
            return

        if not isinstance(trade_class, type) or not issubclass(trade_class, Trade):
            raise get_exception(self)('Trade class must be a sub class of <estrade.classes.trade.Trade>.')

        self._trade_class = trade_class
