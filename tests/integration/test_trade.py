import arrow

from estrade import Epic, Tick
from estrade.enums import TradeDirection


def test_trade():
    # GIVEN an Epic
    epic = Epic(ref="MY_EPIC_CODE")

    # GIVEN a tick added to this epic (to set the epic last value to 100)
    tick1 = Tick(
        datetime=arrow.get("2020-01-01 12:34:56"),
        bid=99,
        ask=101,
    )
    epic.on_new_tick(tick1)

    # WHEN I open a BUY Trade with a quantity of 3 from the current epic value.
    trade = epic.open_trade(
        direction=TradeDirection.BUY,
        quantity=3,
    )

    # THEN the trade result is the current spread
    assert trade.result == -6

    # WHEN a new tick is received by the epic
    tick2 = Tick(
        datetime=arrow.get("2020-01-01 12:34:57"),
        bid=109,
        ask=111,
    )
    epic.on_new_tick(tick2)

    # THEN the trade result is updated
    assert trade.result == 24

    # WHEN I close 2 quantities on this trade
    epic.close_trade(trade=trade, quantity=2)

    assert trade.closed_quantities == 2

    # WHEN a new tick is received by the epic
    tick3 = Tick(
        datetime=arrow.get("2020-01-01 12:34:57"),
        bid=89,
        ask=91,
    )
    epic.on_new_tick(tick3)

    # THEN the trade result is updated and take account that one quantity is closed.
    assert trade.result == 4
