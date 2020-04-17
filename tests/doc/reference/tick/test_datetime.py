from datetime import datetime, timezone

import arrow

from estrade import Tick


def test_python_datetime():
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    tick = Tick(
        datetime=now,
        bid=49,
        ask=50,
    )

    assert tick.datetime == arrow.get(now)


def test_arrow_datetime():
    now = arrow.utcnow()
    tick = Tick(
        datetime=now,
        bid=49,
        ask=50,
    )

    assert tick.datetime == now
