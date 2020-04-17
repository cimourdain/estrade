import arrow

from estrade import BaseTickProvider, Epic, Tick


class MyTickProvider(BaseTickProvider):
    def run(self):
        # Generates 9 ticks
        for i in range(10):
            # create a new tick
            new_tick = Tick(
                datetime=arrow.utcnow(),
                bid=(i - 0.5),
                ask=(i + 0.5),
            )
            # find epic to attach the tick to
            tick_epic = self.get_epic_by_ref("MY_EPIC_CODE")
            # dispatch tick to epic
            tick_epic.on_new_tick(new_tick)


def test_tick_provider():
    # GIVEN an Epic
    epic = Epic(ref="MY_EPIC_CODE")

    # GIVEN an instance of the tick provider
    provider = MyTickProvider(epics=[epic])

    # WHEN I run the tick provider
    provider.run()

    # THEN 9 ticks are registered on epic
    assert epic.last_tick.value == 9
