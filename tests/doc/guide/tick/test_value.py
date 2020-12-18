import arrow

from estrade import Tick


def test_tick_value():
    now = arrow.utcnow()
    tick = Tick(datetime=now, bid=99, ask=101)

    assert tick.value == 100