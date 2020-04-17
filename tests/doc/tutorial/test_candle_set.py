import arrow

from estrade import BaseTickProvider, Epic, Tick
from estrade.enums import CandleType, Unit
from estrade.graph import CandleSet, FrameSet


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


def test_indicator_candle_set():
    # GIVEN A FrameSet in UT4 minutes
    ut4mn = FrameSet(ref="UT4MN", unit=Unit.MINUTE, unit_quantity=4)

    # GIVEN a Classic candle set indicator set on the UT4MN FrameSet
    candle_set_classic = CandleSet(ref="UT4CS", candle_type=CandleType.CLASSIC)
    ut4mn.add_indicator(candle_set_classic)

    # GIVEN a HEIKIN ASHI candle set indicator set on the UT4MN FrameSet
    candle_set_ha = CandleSet(ref="UT4HA", candle_type=CandleType.HEIKIN_ASHI)
    ut4mn.add_indicator(candle_set_ha)

    # GIVEN an Epic holding the UT4MN FrameSet
    epic = Epic(ref="MY_EPIC_CODE")
    epic.add_frame_set(ut4mn)

    # GIVEN an instance of my provider
    provider = MyTickProvider(epics=[epic])

    # WHEN I run the tick provider
    provider.run()

    # THEN the last classic candle values match the input ticks
    first_frame_candle_classic = epic.get_indicator_value(
        frame_set_ref="UT4MN", indicator_ref="UT4CS", offset=1
    )
    assert first_frame_candle_classic.open == 12
    assert first_frame_candle_classic.low == 8.2
    assert first_frame_candle_classic.high == 13.4
    assert first_frame_candle_classic.last == 10

    last_frame_candle_classic = epic.get_indicator_value(
        frame_set_ref="UT4MN", indicator_ref="UT4CS"
    )
    assert last_frame_candle_classic.open == 12.6
    assert last_frame_candle_classic.low == 9.4
    assert last_frame_candle_classic.high == 14.7
    assert last_frame_candle_classic.last == 11.8

    # THEN the HEIKIN ASHI candle values match the input ticks
    first_frame_candle_ha = epic.get_indicator_value(
        frame_set_ref="UT4MN", indicator_ref="UT4HA", offset=1
    )
    assert first_frame_candle_ha.open == 12
    assert first_frame_candle_ha.low == 8.2
    assert first_frame_candle_ha.high == 13.4
    assert first_frame_candle_ha.last == 10.9

    last_frame_candle_ha = epic.get_indicator_value(
        frame_set_ref="UT4MN", indicator_ref="UT4HA"
    )
    assert last_frame_candle_ha.open == 11.45
    assert last_frame_candle_ha.low == 9.4
    assert last_frame_candle_ha.high == 14.7
    assert last_frame_candle_ha.last == 12.12
