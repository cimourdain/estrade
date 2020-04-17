from unittest.mock import call

import pytest

from estrade.enums import PivotType
from estrade.graph.base_indicator import BaseIndicator
from estrade.graph.indicators.pivot import PivotTypeClassic, PivotTypeOLHC
from tests.unit.factories import PivotFactory


class TestInheritance:
    def test_base_indicator(self):
        piv = PivotFactory()

        assert BaseIndicator in piv.__class__.__bases__

    def test_base_indicator_call(self, mocker):
        init_mock = mocker.patch.object(
            BaseIndicator, "__init__", wraps=BaseIndicator.__init__
        )

        piv = PivotFactory(ref="test_ref", pivot_type=PivotType.CLASSIC)

        assert init_mock.call_args_list == [
            call(piv, ref="test_ref", value_class=PivotTypeClassic)
        ]


class TestInit:
    @pytest.mark.parametrize(
        ["pivot_type", "expected_class"],
        [
            (PivotType.CLASSIC, PivotTypeClassic),
            (PivotType.OLHC, PivotTypeOLHC),
        ],
    )
    def test_pivot_type(self, pivot_type, expected_class):
        piv = PivotFactory(pivot_type=pivot_type)

        assert piv.value_class == expected_class
