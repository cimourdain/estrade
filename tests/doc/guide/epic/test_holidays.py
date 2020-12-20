from datetime import time

import arrow

from estrade import Epic, Tick


def test_open_periods():
    epic = Epic(
        ref="MY_EPIC_REF",
        open_time=time(8, 30),
        close_time=time(17, 0),
    )

    # WHEN a tick is received before the opening time
    tick = Tick(datetime=arrow.get("2020-01-01 07:30:00"), bid=99, ask=100)
    epic.on_new_tick(tick)
