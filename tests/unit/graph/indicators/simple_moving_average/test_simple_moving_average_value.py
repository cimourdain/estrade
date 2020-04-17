from unittest.mock import call

from estrade.graph.base_indicator import BaseIndicatorValue
from estrade.graph.indicators.simple_moving_average import (
    SimpleMovingAverageValue,
)
from tests.unit.factories import (
    SimpleMovingAverageFactory,
    SimpleMovingAverageValueFactory,
    TickFactory,
)


CLASS_DEFINITION_PATH = (
    "estrade.graph.indicators.simple_moving_average.SimpleMovingAverageValue"
)


class TestInheritance:
    def test_base_indicator_value(self):

        assert BaseIndicatorValue in SimpleMovingAverageValue.__bases__

    def test_base_indicator_value_call(self, mocker):
        init_mock = mocker.patch.object(
            BaseIndicatorValue, "__init__", wraps=BaseIndicatorValue.__init__
        )

        frame_mock = mocker.Mock()
        frame_mock.previous_frame.indicators = {}
        frame_mock.previous_frame.previous_frame = None
        indicator_mock = mocker.Mock()
        indicator_mock.max_periods = 100
        smav = SimpleMovingAverageValueFactory(
            frame=frame_mock, indicator=indicator_mock
        )

        assert init_mock.call_args_list == [
            call(smav, frame=frame_mock, indicator=indicator_mock)
        ]


class TestInit:
    def test_last_closes_first(self, mocker):
        frame_mock = mocker.Mock()
        frame_mock.previous_frame = None
        smav = SimpleMovingAverageValueFactory(frame=frame_mock)

        assert smav.last_closes == []

    def test_last_closes_with_previous(self, mocker):
        previous_value_mock = mocker.Mock()
        previous_value_mock.extended_closes = [1, 2, 3]
        frame_mock = mocker.Mock()
        frame_mock.previous_frame.indicators = {"sma": previous_value_mock}

        sma = SimpleMovingAverageFactory(ref="sma", max_periods=3)
        smav = SimpleMovingAverageValueFactory(frame=frame_mock, indicator=sma)

        assert smav.last_closes == [2, 3]

    def test_extended_closes_first(self, mocker):
        frame_mock = mocker.Mock()
        frame_mock.previous_frame = None
        frame_mock.last_tick.value = 1
        smav = SimpleMovingAverageValueFactory(frame=frame_mock)

        assert smav.extended_closes == [1]

    def test_extended_closes_with_previous(self, mocker):
        previous_value_mock = mocker.Mock()
        previous_value_mock.extended_closes = [1, 2, 3]
        frame_mock = mocker.Mock()
        frame_mock.previous_frame.indicators = {"sma": previous_value_mock}
        frame_mock.last_tick.value = 4

        sma = SimpleMovingAverageFactory(ref="sma", max_periods=3)
        smav = SimpleMovingAverageValueFactory(frame=frame_mock, indicator=sma)

        assert smav.extended_closes == [2, 3, 4]


class TestOnNewTick:
    def test_parent__call(self, mocker):
        parent_on_new_tick = mocker.patch(
            "estrade.graph.base_indicator.BaseIndicatorValue.on_new_tick"
        )
        smav = SimpleMovingAverageValueFactory()

        new_tick = TickFactory()

        smav.on_new_tick(new_tick, True)
        assert parent_on_new_tick.call_args_list == [call(new_tick, True)]

    def test_update_extended_closes(self):
        smav = SimpleMovingAverageValueFactory()
        smav.last_closes = [1, 2, 3]

        new_tick = TickFactory(bid=3, ask=5)

        smav.frame.last_tick = new_tick
        smav.on_new_tick(new_tick, True)

        assert smav.extended_closes == [1, 2, 3, 4]

    def test_last_closes_not_updated(self):
        smav = SimpleMovingAverageValueFactory()
        smav.last_closes = [1, 2, 3]

        new_tick = TickFactory(bid=3, ask=5)

        smav.frame.last_tick = new_tick
        smav.on_new_tick(new_tick, True)

        assert smav.last_closes == [1, 2, 3]


class TestGetValue:
    def test_nominal(self, mocker):
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.extended_closes",
            new_callable=lambda: [1, 2, 3],
        )

        smav = SimpleMovingAverageValueFactory()

        sma_value = smav.get_value(periods=2)

        assert sma_value == 2.5

    def test_exceed_closes_count(self, mocker):
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.extended_closes",
            new_callable=lambda: [1, 2, 3],
        )
        smav = SimpleMovingAverageValueFactory()

        sma_value = smav.get_value(periods=5)

        assert sma_value is None
