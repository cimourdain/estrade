from unittest.mock import call

import arrow
import pytest

from tests.unit.factories import FrameFactory, FrameSetFactory, TickFactory


CLASS_DEFINITION_PATH = "estrade.graph.frame_set.Frame"


class TestInit:
    def test_first_tick(self):
        tick = TickFactory()

        fr = FrameFactory(first_tick=tick)

        assert fr.first_tick == tick

    def test_period_start(self):
        period_start = arrow.utcnow()

        fr = FrameFactory(period_start=period_start)

        assert fr.period_start == period_start

    def test_period_end__default(self):
        fr = FrameFactory()

        assert fr.period_end is None

    def test_period_end__manual(self):
        period_end = arrow.utcnow()

        fr = FrameFactory(period_end=period_end)

        assert fr.period_end == period_end

    def test_previous_frame__default(self):
        fr = FrameFactory()

        assert fr.previous_frame is None

    def test_previous_frame__manual(self):
        previous_frame = FrameFactory()

        fr = FrameFactory(previous_frame=previous_frame)

        assert fr.previous_frame == previous_frame

    def test_nb_ticks__default(self):
        fr = FrameFactory()

        assert fr.nb_ticks == 1

    def test_last_tick__default(self):
        tick = TickFactory()

        fr = FrameFactory(first_tick=tick)

        assert fr.last_tick == tick

    def test_high_tick__default(self):
        tick = TickFactory()

        fr = FrameFactory(first_tick=tick)

        assert fr.high_tick == tick

    def test_low_tick__default(self):
        tick = TickFactory()

        fr = FrameFactory(first_tick=tick)

        assert fr.low_tick == tick

    def test_indicators__no_indicators(self):
        fr = FrameFactory()

        assert fr.indicators == {}

    def test_indicators_not_empty(self, mocker):
        epic_mock = mocker.Mock()
        epic_mock.market_open = True
        parent_framset = FrameSetFactory()
        indicator_mock = mocker.Mock()
        indicator_mock.ref = "my_indicator_ref"
        indicator_mock.build_value_from_frame.return_value = "indicator_value"
        parent_framset.epic = epic_mock
        parent_framset.add_indicator(indicator_mock)
        fr = FrameFactory(parent_frameset=parent_framset)

        assert fr.indicators == {"my_indicator_ref": "indicator_value"}


class TestClosed:
    def test_not_closed(self):
        fr = FrameFactory()

        assert fr.closed is False

    def test_closed(self):
        fr = FrameFactory()

        next_frame = FrameFactory()
        fr.next_frame = next_frame

        assert fr.closed is True


class TestOnNewTick:
    def test_nb_ticks_update(self):
        fr = FrameFactory()

        fr.on_new_tick(TickFactory())

        assert fr.nb_ticks == 2

    def test_update_last_tick(self):
        tick = TickFactory()
        fr = FrameFactory()

        fr.on_new_tick(tick)

        assert fr.last_tick == tick

    def test_update_high_tick(self):
        fr = FrameFactory()
        fr.high_tick = TickFactory(bid=99, ask=101)

        new_high = TickFactory(bid=100, ask=102)
        fr.on_new_tick(new_high)

        assert fr.high_tick == new_high

    def test_update_low_tick(self):
        fr = FrameFactory()
        fr.low_tick = TickFactory(bid=99, ask=101)

        new_low = TickFactory(bid=98, ask=100)
        fr.on_new_tick(new_low)

        assert fr.low_tick == new_low

    @pytest.mark.parametrize(["market_open"], [(True,), (False,)])
    def test_indicators_on_new_tick_called__indicator_not_none(
        self, mocker, market_open
    ):
        epic_mock = mocker.Mock()
        epic_mock.market_open = market_open
        parent_framset = FrameSetFactory()
        indicator_mock = mocker.Mock()
        indicator_mock.ref = "my_indicator_ref"
        parent_framset.epic = epic_mock
        parent_framset.add_indicator(indicator_mock)
        fr = FrameFactory(parent_frameset=parent_framset)

        indicator_value_mock = mocker.Mock()
        fr.indicators = {"my_indicator_ref": indicator_value_mock}

        tick = TickFactory()
        fr.on_new_tick(tick)

        assert indicator_value_mock.on_new_tick.call_args_list == [
            call(tick, market_open)
        ]

    @pytest.mark.parametrize(["market_open"], [(True,), (False,)])
    def test_indicators_on_new_tick_called__indicator_none(self, mocker, market_open):
        epic_mock = mocker.Mock()
        epic_mock.market_open = market_open
        parent_framset = FrameSetFactory()
        indicator_mock = mocker.Mock()
        indicator_mock.ref = "my_indicator_ref"
        parent_framset.epic = epic_mock
        parent_framset.add_indicator(indicator_mock)
        fr = FrameFactory(parent_frameset=parent_framset)
        fr.indicators = {"my_indicator_ref": None}

        tick = TickFactory()
        fr.on_new_tick(tick)

        assert indicator_mock.build_value_from_frame.call_args_list == [
            call(fr, market_open),  # call on Frame Init
            call(fr, market_open),
        ]


class TestGetItem:
    def test_get_not_existing(self):
        fr = FrameFactory()

        assert fr["undefined"] is None

    def test_existing(self):
        fr = FrameFactory()

        fr.indicators["test_indicator"] = "test"

        assert fr["test_indicator"] == "test"
