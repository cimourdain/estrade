import arrow

from estrade import BaseTickProvider, Epic, Tick
from estrade.enums import Unit
from estrade.graph import FrameSet, SimpleMovingAverage


class MyTickProvider(BaseTickProvider):
    def run(self):
        # Generate 8 ticks (1 tick every minute from 2020-01-01 00:00:12)
        dt = arrow.get("2020-01-01 00:00:00")
        for i in [12, 13.4, 8.2, 10, 12.6, 9.4, 14.7, 11.8]:
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
            dt = dt.shift(minutes=1)


def test_simple_moving_average():
    # GIVEN A FrameSet in UT1 minutes
    ut1mn = FrameSet(ref="UT1MN", unit=Unit.MINUTE, unit_quantity=1)

    # GIVEN a SMA with a max number of periods of 10
    sma = SimpleMovingAverage(ref="SMA", max_periods=10)
    ut1mn.add_indicator(sma)

    # GIVEN an Epic holding the UT4MN FrameSet
    epic = Epic(ref="MY_EPIC_CODE")
    epic.add_frame_set(ut1mn)

    # GIVEN an instance of my provider
    provider = MyTickProvider(epics=[epic])

    # WHEN I run the tick provider
    provider.run()

    # THEN the SMA on the last 3 periods is properly calculated
    sma3 = epic.get_indicator_value(
        frame_set_ref="UT1MN",
        indicator_ref="SMA",
    ).get_value(periods=3)
    assert sma3 == round((9.4 + 14.7 + 11.8) / 3, 2)

    # WHEN I update the epic with a new tick, the SMA is updated
    new_tick = Tick(datetime=epic.last_tick.datetime, bid=15.6, ask=17.6)
    epic.on_new_tick(new_tick)

    # THEN the SMA on the last 3 periods is properly updated
    sma3 = epic.get_indicator_value(
        frame_set_ref="UT1MN",
        indicator_ref="SMA",
    ).get_value(periods=3)
    assert sma3 == round((9.4 + 14.7 + 16.6) / 3, 2)
