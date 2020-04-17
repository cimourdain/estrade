import arrow

from estrade import Epic, Tick
from estrade.enums import TradeDirection, TransactionStatus


def test_trade_provider_backtest():
    # GIVEN an instance of our custom trade provider attached to an Epic
    epic = Epic(ref="MY_EPIC")

    # Add a tick to the epic
    tick = Tick(datetime=arrow.utcnow(), bid=99, ask=101)
    epic.on_new_tick(tick)

    # WHEN I create a new trade add open it with the Trade Provider
    trade = epic.open_trade(direction=TradeDirection.SELL, quantity=2)

    # THEN a new trade is created
    assert len(epic.trade_provider.trades) == 1

    # THEN the trade status is automatically set to CONFIRMED
    trade_in_provider = epic.trade_provider.trades[0]
    assert trade_in_provider.status == TransactionStatus.CONFIRMED

    # WHEN I close the trade
    epic.close_trade(trade=trade, quantity=1)

    # THEN a close of one quantity was created on the opened trade
    assert len(trade_in_provider.closes) == 1

    # THEN the trade close attributes where set
    trade_close_in_provider = trade_in_provider.closes[0]
    assert trade_close_in_provider.status == TransactionStatus.CONFIRMED
