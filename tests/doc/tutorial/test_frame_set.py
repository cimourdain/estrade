import arrow

from estrade import BaseTickProvider, Epic, Tick
from estrade.enums import Unit
from estrade.graph import FrameSet


class MyTickProvider(BaseTickProvider):
    def run(self):
        # Generate 10 ticks (1 tick every minute from 2020-01-01 00:00:12)
        dt = arrow.get("2020-01-01 00:00:12")
        for i in range(10):
            dt = dt.shift(minutes=1)
            # create a new tick
            new_tick = Tick(
                datetime=dt,
                bid=(i - 0.5),
                ask=(i + 0.5),
            )
            # find epic to attach the tick to
            tick_epic = self.get_epic_by_ref("MY_EPIC_CODE")
            # dispatch tick to epic
            tick_epic.on_new_tick(new_tick)


def test_frame_sets():
    # GIVEN A FrameSet grouping ticks by 5
    ut5ticks = FrameSet(ref="UT5TICKS", unit=Unit.TICK, unit_quantity=5)

    # GIVEN a FrameSet grouping ticks by 3 minutes
    ut3mn = FrameSet(ref="UT3MN", unit=Unit.MINUTE, unit_quantity=3)

    # GIVEN an Epic holding both frame sets
    epic = Epic(ref="MY_EPIC_CODE")
    epic.add_frame_set(ut5ticks)
    epic.add_frame_set(ut3mn)

    # GIVEN an instance of my provider
    provider = MyTickProvider(epics=[epic])

    # WHEN I run the tick provider
    provider.run()

    # THEN in UT 5 ticks
    # 2 frames were created
    assert len(epic.frame_sets["UT5TICKS"].frames) == 2

    # THEN in UT 3 minutes
    # 4 frames where created
    assert len(epic.frame_sets["UT3MN"].frames) == 4
    # the period_start of each frame is rounded properly
    assert [f.period_start for f in epic.frame_sets["UT3MN"].frames] == [
        arrow.get("2020-01-01 00:00:00"),
        arrow.get("2020-01-01 00:03:00"),
        arrow.get("2020-01-01 00:06:00"),
        arrow.get("2020-01-01 00:09:00"),
    ]
