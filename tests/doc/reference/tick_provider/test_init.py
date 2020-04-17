from datetime import datetime, timezone

from estrade import BaseTickProvider, Epic, Tick


class MyTickProvider(BaseTickProvider):
    """Basic tick provider generating 10 ticks."""

    def run(self):
        for i in range(10):
            # create a new tick
            new_tick = Tick(
                datetime=datetime.utcnow().replace(tzinfo=timezone.utc),
                bid=(i - 0.5),
                ask=(i + 0.5),
            )
            # find epic to attach the tick to
            tick_epic = self.get_epic_by_ref("MY_EPIC_CODE")
            # attach tick to epic
            tick_epic.on_new_tick(new_tick)


def test_basic_tick_provider():
    # GIVEN AN EPIC
    epic = Epic(ref="MY_EPIC_CODE")
    # GIVEN an instance of my provider
    provider = MyTickProvider(epics=[epic])

    # WHEN I run the tick provider
    provider.run()

    # THEN 10 ticks are generated
    assert epic.last_tick.value == 9
