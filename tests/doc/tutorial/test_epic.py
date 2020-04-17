import arrow
from dateutil import tz

from estrade import Epic, Tick


def test_create_epic():
    # GIVEN an epic timezoned on Paris(France) holding a max of 3 ticks in memory
    epic = Epic(timezone="Europe/Paris")

    # WHEN I add a tick to this epic in UTC
    tick = Tick(
        datetime=arrow.utcnow(),
        bid=100,
        ask=101,
    )
    epic.on_new_tick(tick)

    # THEN the tick is set as the Epic last tick
    assert epic.last_tick == tick

    # THEN the tick date was converted from UTC to the Epic timezone (Europe/Paris)
    assert tick.datetime.tzinfo == tz.gettz(epic.timezone)
