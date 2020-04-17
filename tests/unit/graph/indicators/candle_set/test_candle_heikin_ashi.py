import pytest

from estrade.graph.indicators.candle_set import BaseCandle, HeikinAshiCandle
from tests.unit.factories import HeikinAshiCandleFactory


CLASS_DEFINITION_PATH = "estrade.graph.indicators.candle_set.HeikinAshiCandle"


class TestInheritance:
    def test_base_indicator_value(self):
        jc = HeikinAshiCandleFactory()

        assert BaseCandle in jc.__class__.__bases__

    def test_init_not_written(self):
        assert HeikinAshiCandle.__init__ == BaseCandle.__init__


class TestOpen:
    @pytest.fixture(autouse=True)
    def mock_previous(self, mocker):
        previous_mock = mocker.Mock()
        previous_mock.open = 100
        previous_mock.last = 110
        mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.previous",
            new_callable=lambda: previous_mock,
        )
        return mock

    def test_no_previous(self, mocker):
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.previous",
            new_callable=lambda: None,
        )

        hc = HeikinAshiCandleFactory()
        first_tick_mock = mocker.Mock()
        first_tick_mock.value = 5643.456
        hc.first_tick = first_tick_mock

        assert hc.open == 5643.46

    def test_with_previous(self, mocker):
        previous_mock = mocker.Mock()
        previous_mock.open = 435.6546
        previous_mock.last = 876.4355
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.previous",
            new_callable=lambda: previous_mock,
        )

        hc = HeikinAshiCandleFactory()

        assert hc.open == round((435.6546 + 876.4355) / 2, 2)


class TestHigh:
    @pytest.fixture(autouse=True)
    def mock_open(self, mocker):
        mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.open",
            new_callable=lambda: 100,
        )
        return mock

    @pytest.fixture(autouse=True)
    def mock_last(self, mocker):
        mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.last",
            new_callable=lambda: 50,
        )
        return mock

    @pytest.mark.parametrize(
        ["open", "high", "last", "expected_high"],
        [
            (1.234, 2.345, 3.456, 3.46),
            (3.456, 1.234, 2.345, 3.46),
            (1.234, 3.456, 2.345, 3.46),
        ],
    )
    def test_nominal(self, mocker, open, high, last, expected_high):
        high_tick_mock = mocker.Mock()
        high_tick_mock.value = high

        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.open",
            new_callable=lambda: open,
        )
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.last",
            new_callable=lambda: last,
        )

        hc = HeikinAshiCandleFactory()
        hc.high_tick = high_tick_mock

        assert hc.high == expected_high


class TestLow:
    @pytest.fixture(autouse=True)
    def mock_open(self, mocker):
        mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.open",
            new_callable=lambda: 100,
        )
        return mock

    @pytest.fixture(autouse=True)
    def mock_last(self, mocker):
        mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.last",
            new_callable=lambda: 50,
        )
        return mock

    @pytest.mark.parametrize(
        ["open", "low", "last", "expected_low"],
        [
            (1.234, 2.345, 3.456, 1.23),
            (3.456, 1.234, 2.345, 1.23),
            (2.345, 3.456, 1.234, 1.23),
        ],
    )
    def test_nominal(self, mocker, open, low, last, expected_low):
        low_tick_mock = mocker.Mock()
        low_tick_mock.value = low

        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.open",
            new_callable=lambda: open,
        )
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.last",
            new_callable=lambda: last,
        )

        hc = HeikinAshiCandleFactory()
        hc.low_tick = low_tick_mock

        assert hc.low == expected_low


class TestLast:
    @pytest.mark.parametrize(
        ["first", "high", "low", "last", "expected_last"],
        [
            (1.234, 2.345, 3.456, 4.567, 2.90),
            (4.567, 1.234, 2.345, 3.456, 2.90),
            (3.456, 4.567, 1.234, 2.345, 2.90),
            (2.345, 3.456, 4.567, 1.234, 2.90),
        ],
    )
    def test_nominal(self, mocker, first, high, low, last, expected_last):
        first_tick_mock = mocker.Mock()
        first_tick_mock.value = first

        low_tick_mock = mocker.Mock()
        low_tick_mock.value = low

        high_tick_mock = mocker.Mock()
        high_tick_mock.value = high

        last_tick_mock = mocker.Mock()
        last_tick_mock.value = last

        hc = HeikinAshiCandleFactory()
        hc.first_tick = first_tick_mock
        hc.last_tick = last_tick_mock
        hc.low_tick = low_tick_mock
        hc.high_tick = high_tick_mock

        assert hc.last == expected_last


class TestClose:
    @pytest.fixture(autouse=True)
    def mock_closed(self, mocker):
        mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.closed",
            new_callable=lambda: False,
        )
        return mock

    @pytest.fixture(autouse=True)
    def mock_last_tick(self, mocker):
        mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.last",
            new_callable=lambda: 100,
        )
        return mock

    @pytest.mark.parametrize(
        ["closed", "expected_close"],
        [
            (True, 12.35),
            (False, None),
        ],
    )
    def test_nominal(self, mocker, closed, expected_close):
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.last",
            new_callable=lambda: 12.35,
        )

        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.closed",
            new_callable=lambda: closed,
        )

        hc = HeikinAshiCandleFactory()

        assert hc.close == expected_close
