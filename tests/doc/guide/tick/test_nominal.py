import arrow

from estrade import Tick


def test_tick_nominal():
    now = arrow.utcnow()
    tick = Tick(datetime=now, bid=99, ask=101)

    assert tick.bid == 99
    assert tick.ask == 101
    assert tick.datetime == now

    assert tick.value == 100.0  # value represents the mean between bid and ask
    assert tick.spread == 2.0  # spread is the difference between bid and ask
