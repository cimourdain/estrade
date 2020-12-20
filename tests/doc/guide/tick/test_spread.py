import arrow

from estrade import Tick


def test_tick_spread():
    now = arrow.utcnow()
    tick = Tick(datetime=now, bid=99, ask=101)

    assert tick.spread == 2
