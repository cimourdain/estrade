from unittest.mock import call

import pytest

from estrade.exceptions import BaseIndicatorException
from estrade.graph.base_indicator import BaseIndicator
from estrade.graph.indicators.rsi import RSIValue
from tests.unit.factories import FrameSetFactory, RSIFactory


class TestInheritance:
    def test_base_indicator(self):
        rsi = RSIFactory()

        assert BaseIndicator in rsi.__class__.__bases__

    def test_base_indicator_call(self, mocker):
        init_mock = mocker.patch.object(
            BaseIndicator, "__init__", wraps=BaseIndicator.__init__
        )

        rsi = RSIFactory(ref="test_ref")

        assert init_mock.call_args_list == [
            call(rsi, ref="test_ref", value_class=RSIValue)
        ]


class TestInit:
    def test_periods(self):
        rsi = RSIFactory(periods=14)

        assert rsi.periods == 14

    def test_rsi_periods__default(self):
        rsi = RSIFactory(periods=14)

        assert rsi.rsi_periods is None


class TestSetFrameSet:
    def test_set_frame_set(self, mocker):
        parent_method = mocker.patch(
            "estrade.graph.base_indicator.BaseIndicator.set_frame_set",
            return_value=None,
        )
        rsi = RSIFactory(periods=7)
        frame_set = FrameSetFactory(unit_quantity=5, max_frames_in_memory=35)
        rsi.set_frame_set(frame_set)

        assert parent_method.call_args_list == [call(frame_set)]

    def test_rsi_periods(self):
        rsi = RSIFactory(periods=7)
        frame_set = FrameSetFactory(unit_quantity=5, max_frames_in_memory=35)
        rsi.set_frame_set(frame_set)

        assert rsi.rsi_periods == 35

    def test_rsi_period__insufficient(self):
        rsi = RSIFactory(periods=7)
        frame_set = FrameSetFactory(unit_quantity=5, max_frames_in_memory=34)

        with pytest.raises(BaseIndicatorException):
            rsi.set_frame_set(frame_set)
