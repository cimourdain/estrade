import arrow

from estrade.trade import Trade, TradeClose, TradeDirection
from tests.unit.factories import EpicFactory
from tests.unit.factories.factory import Factory


class TradeFactory(Factory):
    class Meta:
        model = Trade

    epic = EpicFactory()
    direction = TradeDirection.BUY
    quantity = 1
    open_value = 101
    current_close_value = 99

    def open_datetime():
        return arrow.utcnow()


class TradeCloseFactory(Factory):
    class Meta:
        model = TradeClose

    trade = TradeFactory()
    close_value = 10
    quantity = 1

    def datetime():
        return arrow.utcnow()
