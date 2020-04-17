import arrow

from estrade import Tick


def test_tick():
    now_tokyo = arrow.now("Asia/Tokyo")
    tick = Tick(datetime=now_tokyo, bid=99, ask=101, meta={"my_data": "data"})

    assert tick.bid == 99
    assert tick.ask == 101
    assert tick.datetime == now_tokyo
    assert tick.meta == {"my_data": "data"}

    assert tick.value == 100.0  # value represents the mean between bid and ask
    assert tick.spread == 2.0  # spread is the difference between bid and ask
    assert tick.datetime_utc == now_tokyo.to("UTC")
