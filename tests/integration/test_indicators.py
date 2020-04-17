from datetime import time

import arrow

from estrade import Epic, Tick
from estrade.enums import Unit
from estrade.graph import FrameSet
from estrade.graph.base_indicator import BaseIndicator, BaseIndicatorValue


def test_indicator_market_open_gaps():
    my_indicator = BaseIndicator(
        ref="MY_IND", value_class=BaseIndicatorValue, market_open_only=True
    )
    daily_frameset = FrameSet(ref="UT1D", unit=Unit.DAY, unit_quantity=1)
    daily_frameset.add_indicator(my_indicator)

    # GIVEN an epic open between 9 and 18 on Tuesday and Thursday
    epic = Epic(open_time=time(9, 0), close_time=time(18, 0), trade_days=[1, 3])
    epic.add_frame_set(daily_frameset)

    # Add ticks on Monday: Market is closed, the indicator value stays to None
    tick1 = Tick(datetime=arrow.get("2020-01-06 08:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick1)

    last_frame = epic.frame_sets["UT1D"].current
    assert last_frame.period_start == arrow.get("2020-01-06 00:00:00")
    assert last_frame.indicators["MY_IND"] is None

    tick2 = Tick(datetime=arrow.get("2020-01-06 10:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick2)
    assert last_frame.indicators["MY_IND"] is None

    tick3 = Tick(datetime=arrow.get("2020-01-06 19:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick3)
    assert last_frame.indicators["MY_IND"] is None

    # Add ticks on Tuesday: Market is opened, the indicator value is updated
    tick4 = Tick(datetime=arrow.get("2020-01-07 08:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick4)

    last_frame = epic.frame_sets["UT1D"].current
    assert last_frame.period_start == arrow.get("2020-01-07 00:00:00")
    assert last_frame.indicators["MY_IND"] is None

    tick5 = Tick(datetime=arrow.get("2020-01-07 10:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick5)
    assert last_frame.indicators["MY_IND"].first_tick == tick5

    tick6 = Tick(datetime=arrow.get("2020-01-07 11:00:00"), bid=1005, ask=1007)
    epic.on_new_tick(tick6)
    assert last_frame.indicators["MY_IND"].high_tick == tick6

    tick7 = Tick(datetime=arrow.get("2020-01-07 12:00:00"), bid=997, ask=999)
    epic.on_new_tick(tick7)
    assert last_frame.indicators["MY_IND"].low_tick == tick7

    tick8 = Tick(datetime=arrow.get("2020-01-07 17:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick8)
    assert last_frame.indicators["MY_IND"].last_tick == tick8

    tick9 = Tick(datetime=arrow.get("2020-01-07 19:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick9)
    assert last_frame.indicators["MY_IND"].first_tick == tick5
    assert last_frame.indicators["MY_IND"].high_tick == tick6
    assert last_frame.indicators["MY_IND"].low_tick == tick7
    assert last_frame.indicators["MY_IND"].last_tick == tick8

    # Add ticks on Wednesday: Market is closed, the indicator value stays to None
    tick10 = Tick(datetime=arrow.get("2020-01-08 08:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick10)

    last_frame = epic.frame_sets["UT1D"].current
    assert last_frame.period_start == arrow.get("2020-01-08 00:00:00")
    assert last_frame.indicators["MY_IND"] is None
    assert last_frame.previous_frame.indicators["MY_IND"].last_tick == tick8

    tick11 = Tick(datetime=arrow.get("2020-01-08 12:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick11)
    assert last_frame.indicators["MY_IND"] is None

    tick12 = Tick(datetime=arrow.get("2020-01-08 19:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick12)
    assert last_frame.indicators["MY_IND"] is None

    # Add ticks on Thursday: Market is opened, the indicator value is updated
    tick13 = Tick(datetime=arrow.get("2020-01-09 08:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick13)

    last_frame = epic.frame_sets["UT1D"].current
    assert last_frame.period_start == arrow.get("2020-01-09 00:00:00")
    assert last_frame.indicators["MY_IND"] is None

    tick14 = Tick(datetime=arrow.get("2020-01-09 10:00:00"), bid=999, ask=1001)
    epic.on_new_tick(tick14)
    assert last_frame.indicators["MY_IND"].first_tick == tick14
    assert last_frame.indicators["MY_IND"].previous.last_tick == tick8
