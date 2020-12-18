import arrow

from estrade import Epic, Tick


def test_create_epic():
    epic = Epic()
    tick = Tick(datetime=arrow.utcnow(), bid=99, ask=101)

    epic.on_new_tick(tick)

    assert epic.last_tick == tick