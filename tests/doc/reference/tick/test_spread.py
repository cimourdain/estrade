from datetime import datetime, timezone

from estrade import Tick


def test_value():
    tick = Tick(
        datetime.utcnow().replace(tzinfo=timezone.utc),
        bid=99,
        ask=101,
    )

    assert tick.spread == 2
