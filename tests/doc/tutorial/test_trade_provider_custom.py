import arrow

from estrade import BaseTradeProvider, Epic, Tick
from estrade.enums import TradeDirection, TransactionStatus


class MyTradeProvider(BaseTradeProvider):
    def open_trade_request(self, trade):
        # call your api to open a new trade
        # eg: response = requests.get("http://my_provider.com/open_trade", params={
        #     "epic": trade.epic.ref,
        #     "direction": trade.direction,
        #     "quantity": trade.quantity,
        #     ...
        # })

        # update trade with your provider response
        trade.meta["provider_id"] = 123
        trade.status = TransactionStatus.PENDING

        return trade

    def close_trade_request(self, trade_close):
        # call your api to close a trade.
        # eg: response = requests.get("http://my_provider.com/close_trade", params={
        #     "epic": trade_close.trade.epic.ref,
        #     "quantity": trade_close.quantity,
        #     ...
        # })

        # update trade with your provider response
        trade_close.meta["provider_close_id"] = 123
        trade_close.status = TransactionStatus.REQUIRED

        return trade_close


def test_trade_provider_custom():
    # GIVEN an instance of our custom trade provider attached to an Epic
    trade_provider = MyTradeProvider()
    epic = Epic(ref="MY_EPIC", trade_provider=trade_provider)

    # Add a tick to the epic
    tick = Tick(datetime=arrow.utcnow(), bid=99, ask=101)
    epic.on_new_tick(tick)

    # WHEN I create a new trade add open it with the Trade Provider
    trade = epic.open_trade(direction=TradeDirection.SELL, quantity=2)

    # THEN a new trade is created
    assert len(epic.trade_provider.trades) == 1

    # THEN the trade attribute were updated by the trade provider
    trade_in_provider = epic.trade_provider.trades[0]
    assert trade_in_provider.status == TransactionStatus.PENDING
    assert trade_in_provider.meta["provider_id"] == 123

    # WHEN I close the trade
    epic.close_trade(trade=trade, quantity=1)

    # THEN a close of one quantity was created on the opened trade
    assert len(trade_in_provider.closes) == 1

    # THEN the trade close attributes where set
    trade_close_in_provider = trade_in_provider.closes[0]
    assert trade_close_in_provider.status == TransactionStatus.REQUIRED
    assert trade_close_in_provider.meta["provider_close_id"] == 123
