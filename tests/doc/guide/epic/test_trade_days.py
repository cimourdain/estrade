import arrow

from estrade import Epic, Tick


def test_open_periods():
    # WHEN I create an epic tradeable only on Tuesday and Thursday
    epic = Epic(ref="MY_EPIC_REF", trade_days=[1, 3])

    # WHEN a tick is received on Monday
    fmt = r"ddd[\s+]DD[\s+]MMM[\s+]YYYY[\s+]HH:mm:ss"
    tick = Tick(datetime=arrow.get("Mon 13 Jan 2020 12:00:00", fmt), bid=99, ask=100)
    epic.on_new_tick(tick)

    # THEN the epic is not open
    assert epic.market_open is False

    # WHEN a tick is received on Tuesday
    tick = Tick(datetime=arrow.get("Tue 14 Jan 2020 12:00:00", fmt), bid=99, ask=100)
    epic.on_new_tick(tick)

    # THEN the epic is not open
    assert epic.market_open is True, epic.last_tick.datetime.weekday()

    # WHEN a tick is received on Wednesday
    tick = Tick(datetime=arrow.get("Wed 15 Jan 2020 12:00:00", fmt), bid=99, ask=100)
    epic.on_new_tick(tick)

    # THEN the epic is not open
    assert epic.market_open is False

    # WHEN a tick is received on Tuesday
    tick = Tick(datetime=arrow.get("Tue 16 Jan 2020 12:00:00", fmt), bid=99, ask=100)
    epic.on_new_tick(tick)

    # THEN the epic is open
    assert epic.market_open is True

    # WHEN a tick is received on Friday
    tick = Tick(datetime=arrow.get("Fri 17 Jan 2020 12:00:00", fmt), bid=99, ask=100)
    epic.on_new_tick(tick)

    # THEN the epic is not open
    assert epic.market_open is False
