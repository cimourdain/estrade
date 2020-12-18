import arrow
from dateutil import tz

from estrade import Epic, Tick


def test_tick_timezone_comversion():
    # GIVEN an epic timezoned on London
    epic = Epic(timezone="Europe/London")

    # WHEN I add a tick to this epic in UTC
    tick = Tick(
        datetime=arrow.get("2020-01-01 12:34:56").replace(tzinfo="US/Pacific"),
        bid=100,
        ask=101,
    )
    epic.on_new_tick(tick)

    # THEN the tick date was converted from US/Pacific to the Epic timezone (GMT)
    assert tick.datetime.format("YYYY-MM-DD HH:mm:ss ZZZ") == "2020-01-01 20:34:56 GMT"
