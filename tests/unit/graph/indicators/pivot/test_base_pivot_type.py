import pytest

from estrade.graph.base_indicator import BaseIndicatorValue
from estrade.graph.indicators.pivot import BasePivotType
from tests.unit.factories import FrameFactory


class TestInheritance:
    def test_base_indicator(self):
        assert BaseIndicatorValue in BasePivotType.__bases__


class TestProperties:
    def test_pivot(self):
        bpt = BasePivotType(indicator="test", frame=FrameFactory())

        with pytest.raises(NotImplementedError):
            bpt.pivot

    def test_support1(self):
        bpt = BasePivotType(indicator="test", frame=FrameFactory())

        with pytest.raises(NotImplementedError):
            bpt.support1

    def test_support2(self):
        bpt = BasePivotType(indicator="test", frame=FrameFactory())

        with pytest.raises(NotImplementedError):
            bpt.support2

    def test_support3(self):
        bpt = BasePivotType(indicator="test", frame=FrameFactory())

        with pytest.raises(NotImplementedError):
            bpt.support3

    def test_resistance1(self):
        bpt = BasePivotType(indicator="test", frame=FrameFactory())

        with pytest.raises(NotImplementedError):
            bpt.resistance1

    def test_resistance2(self):
        bpt = BasePivotType(indicator="test", frame=FrameFactory())

        with pytest.raises(NotImplementedError):
            bpt.resistance2

    def test_resistance3(self):
        bpt = BasePivotType(indicator="test", frame=FrameFactory())

        with pytest.raises(NotImplementedError):
            bpt.resistance3
