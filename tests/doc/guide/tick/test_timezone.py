import arrow

from estrade import Tick


def test_tick_timezone():
    now_tokyo = arrow.now("Asia/Tokyo")
    tick = Tick(datetime=now_tokyo, bid=99, ask=101)

    assert tick.datetime == now_tokyo
    assert tick.datetime_utc == now_tokyo.to("UTC")
