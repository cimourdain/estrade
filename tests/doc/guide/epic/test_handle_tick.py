import arrow

from estrade import Epic, Tick


def test_minimal_handle_tick():
    epic = Epic()
    tick = Tick(datetime=arrow.utcnow(), bid=99, ask=101)

    epic.on_new_tick(tick)

    assert epic.last_tick == tick
