from unittest.mock import call

import pytest

from estrade.exceptions import BaseIndicatorException
from estrade.graph.base_indicator import BaseIndicatorValue
from estrade.graph.indicators.rsi import RSIValue
from tests.unit.factories import (
    FrameFactory,
    RSIFactory,
    RSIValueFactory,
    TickFactory,
)


class TestInheritance:
    def test_base_indicator_value(self):

        assert BaseIndicatorValue in RSIValue.__bases__

    def test_base_indicator_value_call(self, mocker):
        init_mock = mocker.patch.object(
            BaseIndicatorValue, "__init__", wraps=BaseIndicatorValue.__init__
        )

        frame_mock = FrameFactory()
        rsi = RSIFactory()
        rsi.rsi_periods = 5
        rsiv = RSIValue(frame=frame_mock, indicator=rsi)

        assert init_mock.call_args_list == [call(rsiv, frame=frame_mock, indicator=rsi)]


class TestInit:
    def test_no_rsi_periods(self):
        rsi = RSIFactory()
        rsi.rsi_periods = None

        with pytest.raises(BaseIndicatorException):
            RSIValueFactory(indicator=rsi)

    def test_last_changes__no_previous_indicator(self):
        rsiv = RSIValueFactory()

        assert rsiv.last_changes == []

    def test_last_changes__nominal(self, mocker):
        previous_mock = mocker.Mock()
        previous_mock.extended_changes = [1, 2, 3]
        mocker.patch(
            "estrade.graph.indicators.rsi.RSIValue.previous",
            new_callable=lambda: previous_mock,
        )
        indicator = RSIFactory()
        indicator.rsi_periods = 3
        rsiv = RSIValueFactory(indicator=indicator)

        assert rsiv.last_changes == [2, 3]

    @pytest.mark.parametrize(
        ["extended_changes", "expected_rsi"],
        [
            pytest.param([1, 2, 3], None, id="not enough value"),
            pytest.param([1, 2, 3, 4], 100, id="only_positive"),
            pytest.param([-1, -2, -3, -4], 0, id="only_negative"),
            # sum_pos_avg = 3 => ((8 + 4) / 4),
            # sum_neg_avg = 6 => abs((-18 -6) / 4)
            # rsi = 100 - (100 / (1 + (3 / 6))) = 90
            pytest.param([-18, 8, -6, 4], 33.33, id="mixed positive negatives"),
        ],
    )
    def test_value__nominal(self, mocker, extended_changes, expected_rsi):
        mocker.patch(
            "estrade.graph.indicators.rsi.RSIValue.extended_changes",
            new_callable=lambda: extended_changes,
        )

        rsi = RSIFactory()
        rsi.rsi_periods = 4
        rsiv = RSIValueFactory(indicator=rsi)

        assert rsiv.value == expected_rsi, rsiv._build_rs()


class TestExtendedChanges:
    def test_no_previous_frame(self, mocker):
        rsiv = RSIValueFactory()

        frame_mock = mocker.Mock()
        frame_mock.previous_frame = None
        rsiv.frame = frame_mock

        assert rsiv.extended_changes == []

    @pytest.mark.parametrize(
        ["last_tick_value", "previous_frame_last_tick_value", "expected"],
        [(1, 2, [1, 2, -1]), (2, 1, [1, 2, 1])],
    )
    def test_previous_frame(
        self, mocker, last_tick_value, previous_frame_last_tick_value, expected
    ):
        rsiv = RSIValueFactory()

        frame_mock = mocker.Mock()
        frame_mock.last_tick.value = last_tick_value
        frame_mock.previous_frame.last_tick.value = previous_frame_last_tick_value
        rsiv.frame = frame_mock
        rsiv.last_changes = [1, 2]

        assert rsiv.extended_changes == expected


class TestOnNewTick:
    def test_parent__call(self, mocker):
        parent_on_new_tick = mocker.patch(
            "estrade.graph.base_indicator.BaseIndicatorValue.on_new_tick"
        )
        rsiv = RSIValueFactory()

        new_tick = TickFactory()

        rsiv.on_new_tick(new_tick, True)
        assert parent_on_new_tick.call_args_list == [call(new_tick, True)]

    @pytest.mark.parametrize(
        ["extended_changes", "expected_rsi"],
        [
            pytest.param([1, 2, 3], None, id="not enough value"),
            pytest.param([1, 2, 3, 4], 100, id="only_positive"),
            pytest.param([-1, -2, -3, -4], 0, id="only_negative"),
            # sum_pos_avg = 3 => ((8 + 4) / 4),
            # sum_neg_avg = 6 => abs((-18 -6) / 4)
            # rsi = 100 - (100 / (1 + (3 / 6))) = 90
            pytest.param([-18, 8, -6, 4], 33.33, id="mixed positive negatives"),
        ],
    )
    def test_value__nominal(self, mocker, extended_changes, expected_rsi):
        mocker.patch(
            "estrade.graph.indicators.rsi.RSIValue.extended_changes",
            new_callable=lambda: extended_changes,
        )

        rsi = RSIFactory()
        rsi.rsi_periods = 4
        rsiv = RSIValueFactory(indicator=rsi)

        assert rsiv.value == expected_rsi, rsiv._build_rs()
