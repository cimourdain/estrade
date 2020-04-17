from datetime import datetime, timezone

from estrade import Tick


def test_value():
    tick = Tick(
        datetime.utcnow().replace(tzinfo=timezone.utc),
        bid=49,
        ask=50,
    )

    assert tick.value == 49.5
