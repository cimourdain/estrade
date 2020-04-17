import pytest

from estrade.graph.indicators.candle_set import BaseCandle, JapaneseCandle
from tests.unit.factories import JapaneseCandleFactory


CLASS_DEFINITION_PATH = "estrade.graph.indicators.candle_set.JapaneseCandle"


class TestInheritance:
    def test_base_indicator_value(self):
        jc = JapaneseCandleFactory()

        assert BaseCandle in jc.__class__.__bases__

    def test_init_not_written(self):
        assert JapaneseCandle.__init__ == BaseCandle.__init__


class TestOpen:
    def test_nominal(self, mocker):
        first_tick_mock = mocker.Mock()
        first_tick_mock.value = 45.679

        jc = JapaneseCandleFactory()
        jc.first_tick = first_tick_mock

        assert jc.open == 45.68


class TestHigh:
    def test_nominal(self, mocker):
        high_tick_mock = mocker.Mock()
        high_tick_mock.value = 65.345

        jc = JapaneseCandleFactory()
        jc.high_tick = high_tick_mock

        assert jc.high == 65.34


class TestLow:
    def test_nominal(self, mocker):
        low_tick_mock = mocker.Mock()
        low_tick_mock.value = 345.876

        jc = JapaneseCandleFactory()
        jc.low_tick = low_tick_mock

        assert jc.low == 345.88


class TestLast:
    def test_nominal(self, mocker):
        last_tick_mock = mocker.Mock()
        last_tick_mock.value = 45.679

        jc = JapaneseCandleFactory()
        jc.last_tick = last_tick_mock

        assert jc.last == 45.68


class TestClose:
    @pytest.mark.parametrize(
        ["closed", "expected_close"], [(True, 324.46), (False, None)]
    )
    def test_nominal(self, mocker, closed, expected_close):
        last_tick_mock = mocker.Mock()
        last_tick_mock.value = 324.456
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.closed",
            new_callable=lambda: closed,
        )
        jc = JapaneseCandleFactory()
        jc.last_tick = last_tick_mock

        assert jc.close == expected_close
