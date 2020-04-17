from unittest.mock import call

from estrade.graph.base_indicator import BaseIndicator
from estrade.graph.indicators.simple_moving_average import (
    SimpleMovingAverageValue,
)
from tests.unit.factories import SimpleMovingAverageFactory


class TestInheritance:
    def test_base_indicator(self):
        sma = SimpleMovingAverageFactory()

        assert BaseIndicator in sma.__class__.__bases__

    def test_base_indicator_call(self, mocker):
        init_mock = mocker.patch.object(
            BaseIndicator, "__init__", wraps=BaseIndicator.__init__
        )

        sma = SimpleMovingAverageFactory(ref="test_ref")

        assert init_mock.call_args_list == [
            call(sma, ref="test_ref", value_class=SimpleMovingAverageValue)
        ]


class TestInit:
    def test_max_periods(self):
        sma = SimpleMovingAverageFactory(max_periods=245)

        assert sma.max_periods == 245
