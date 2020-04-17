import arrow

from estrade import Epic, Tick
from estrade.enums import TradeDirection


def test_close_buy():
    now = arrow.utcnow()
    epic = Epic()
    tick = Tick(bid=64.6, ask=68.2, datetime=now)
    epic.on_new_tick(tick)

    trade = epic.open_trade(
        direction=TradeDirection.BUY,
        quantity=6,
        ref="MY_TRADE",
        meta={"my_trade_data": "data"},
    )

    # close 4 @ 54.3
    tick = Tick(bid=54.3, ask=55.6, datetime=now)
    epic.on_new_tick(tick)
    epic.close_trade(
        trade=trade,
        quantity=4,
        ref="MY_CLOSE_ID",
        meta={"data": "data"},
    )
    assert trade.closed_quantities == 4
    assert trade.opened_quantities == 2
    assert trade.closed_result_avg == round(54.3 - 68.2, 2)
    assert trade.closed_result == round(54.3 - 68.2, 2) * 4
    assert trade.opened_result_avg == round(54.3 - 68.2, 2)
    assert trade.opened_result == round(54.3 - 68.2, 2) * 2
    assert trade.result_avg == round(54.3 - 68.2, 2)
    assert trade.result == round(54.3 - 68.2, 2) * 6

    assert trade.closed is False

    # close 2 @ 72.3
    tick = Tick(bid=72.3, ask=73.4, datetime=now)
    epic.on_new_tick(tick)
    epic.close_trade(
        trade=trade,
        quantity=2,
    )
    assert trade.closed_quantities == 6
    assert trade.opened_quantities == 0
    assert trade.closed_result_avg == round(
        (round(54.3 - 68.2, 2) * 4 + round(72.3 - 68.2, 2) * 2) / 6, 2
    )
    assert trade.closed_result == round(54.3 - 68.2, 2) * 4 + round(72.3 - 68.2, 2) * 2
    assert trade.opened_result_avg == 0
    assert trade.opened_result == 0
    assert trade.result_avg == round(
        (round(54.3 - 68.2, 2) * 4 + round(72.3 - 68.2, 2) * 2) / 6, 2
    )
    assert trade.result == round(54.3 - 68.2, 2) * 4 + round(72.3 - 68.2, 2) * 2

    assert trade.closed is True


def test_close_sell():
    now = arrow.utcnow()
    epic = Epic()
    tick = Tick(bid=33.3, ask=34.5, datetime=now)
    epic.on_new_tick(tick)

    trade = epic.open_trade(
        direction=TradeDirection.SELL,
        quantity=7,
        ref="MY_TRADE",
        meta={"my_trade_data": "data"},
    )

    # close 3 @ 45.8
    tick = Tick(bid=44.2, ask=45.8, datetime=now)
    epic.on_new_tick(tick)
    epic.close_trade(
        trade=trade,
        quantity=3,
        ref="MY_CLOSE_ID",
        meta={"data": "data"},
    )
    assert trade.closed_quantities == 3
    assert trade.opened_quantities == 4
    assert trade.closed_result_avg == round(33.3 - 45.8, 2)
    assert trade.closed_result == round(33.3 - 45.8, 2) * 3
    assert trade.opened_result_avg == round(33.3 - 45.8, 2)
    assert trade.opened_result == round(33.3 - 45.8, 2) * 4
    assert trade.result_avg == round(33.3 - 45.8, 2)
    assert trade.result == round(33.3 - 45.8, 2) * 7

    assert trade.closed is False

    # close 4 @ 12.4
    tick = Tick(bid=11.1, ask=12.4, datetime=now)
    epic.on_new_tick(tick)
    epic.close_trade(
        trade=trade,
        quantity=4,
    )
    assert trade.closed_quantities == 7
    assert trade.opened_quantities == 0
    assert trade.closed_result_avg == round(
        (round(33.3 - 45.8, 2) * 3 + round(33.3 - 12.4, 2) * 4) / 7, 2
    )
    assert trade.closed_result == round(33.3 - 45.8, 2) * 3 + round(33.3 - 12.4, 2) * 4
    assert trade.opened_result_avg == 0
    assert trade.opened_result == 0
    assert trade.result_avg == round(
        (round(33.3 - 45.8, 2) * 3 + round(33.3 - 12.4, 2) * 4) / 7, 2
    )
    assert trade.result == round(33.3 - 45.8, 2) * 3 + round(33.3 - 12.4, 2) * 4

    assert trade.closed is True
