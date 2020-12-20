import arrow

from estrade import Tick


def test_tick_meta():
    now = arrow.utcnow()
    tick = Tick(datetime=now, bid=99, ask=101, meta={"test": "test"})

    assert tick.meta == {"test": "test"}
