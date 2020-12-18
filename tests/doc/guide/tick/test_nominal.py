from datetime import datetime, timezone

from estrade import Tick


def test_tick_nominal():
    now = datetime.now(tz=timezone.utc)
    tick = Tick(datetime=now, bid=99, ask=101)

    assert tick.bid == 99
    assert tick.ask == 101
    assert tick.datetime == now
