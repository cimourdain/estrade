import arrow

from estrade import Epic, Tick
from estrade.enums import TradeDirection, TransactionStatus


def test_init_buy():
    now = arrow.utcnow()
    epic = Epic()
    tick = Tick(bid=54.3, ask=68.9, datetime=now)
    epic.on_new_tick(tick)
    trade = epic.open_trade(
        direction=TradeDirection.BUY,
        quantity=3,
        ref="MY_TRADE",
        meta={"my_trade_data": "data"},
    )

    assert trade.direction == TradeDirection.BUY
    assert trade.open_quantity == 3
    # for a BUY, open value is the input ask
    assert trade.open_value == 68.9
    # current represents the current market value to close this trade
    assert trade.current_close_value == 54.3
    assert trade.datetime == now

    assert trade.closes == []

    # max and min result are the opened result
    assert trade.max_result == round(54.3 - 68.9, 2) * 3
    assert trade.min_result == round(54.3 - 68.9, 2) * 3

    # by default a trade status in confirmed
    assert trade.status == TransactionStatus.CONFIRMED

    assert trade.ref == "MY_TRADE"
    assert trade.meta == {"my_trade_data": "data"}


def test_init_sell():
    now = arrow.utcnow()
    epic = Epic()
    tick = Tick(bid=34, ask=36, datetime=now)
    epic.on_new_tick(tick)
    trade = epic.open_trade(
        direction=TradeDirection.SELL,
        quantity=7,
    )

    assert trade.direction == TradeDirection.SELL
    assert trade.open_quantity == 7
    # for a SELL, open value is the input bid
    assert trade.open_value == 34
    # current represents the current market value to close this trade
    assert trade.current_close_value == 36
    assert trade.datetime == now

    assert trade.closes == []

    # max and min result are the opened result
    assert trade.max_result == (34 - 36) * 7
    assert trade.min_result == (34 - 36) * 7
