from unittest.mock import call

import pytest

from estrade.enums import CandleType
from estrade.graph.base_indicator import BaseIndicator
from estrade.graph.indicators.candle_set import (
    HeikinAshiCandle,
    JapaneseCandle,
)
from tests.unit.factories import CandleSetFactory


class TestInheritance:
    def test_base_indicator(self):
        cs = CandleSetFactory()

        assert BaseIndicator in cs.__class__.__bases__

    @pytest.mark.parametrize(
        ["candle_type", "expected_value_class"],
        [
            (CandleType.CLASSIC, JapaneseCandle),
            (CandleType.HEIKIN_ASHI, HeikinAshiCandle),
        ],
    )
    def test_base_indicator_call(self, mocker, candle_type, expected_value_class):
        init_mock = mocker.patch.object(
            BaseIndicator, "__init__", wraps=BaseIndicator.__init__
        )

        cs = CandleSetFactory(ref="test_ref", candle_type=candle_type)

        assert init_mock.call_args_list == [
            call(cs, ref="test_ref", value_class=expected_value_class)
        ]
