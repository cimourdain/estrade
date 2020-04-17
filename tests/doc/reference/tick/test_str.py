import arrow

from estrade import Tick


def test_convert_to_string():
    now = arrow.utcnow()
    tick = Tick(datetime=now, bid=999, ask=1001)

    assert (
        str(tick) == f"{now.strftime('%Y-%m-%d %H:%M:%S')} : 1000.0 "
        f"(bid: 999.0, ask: 1001.0, spread: 2.0)"
    )
