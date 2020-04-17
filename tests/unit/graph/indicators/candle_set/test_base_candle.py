from unittest.mock import call

import pytest

from estrade.enums import CandleColor
from estrade.graph.base_indicator import BaseIndicatorValue
from estrade.graph.indicators.candle_set import BaseCandle
from tests.unit.factories import TickFactory
from tests.unit.factories.graph.indicators.candle_set import BaseCandleFactory


CLASS_DEFINITION_PATH = "estrade.graph.indicators.candle_set.BaseCandle"


class TestInheritance:
    def test_base_indicator_value(self):

        assert BaseIndicatorValue in BaseCandle.__bases__

    def test_base_indicator_value_call(self, mocker):
        init_mock = mocker.patch.object(
            BaseIndicatorValue, "__init__", wraps=BaseIndicatorValue.__init__
        )

        frame_mock = mocker.Mock()
        frame_mock.first_tick = "first_tick"
        frame_mock.last_tick = "last_tick"
        indicator_mock = mocker.Mock()
        bc = BaseCandleFactory(frame=frame_mock, indicator=indicator_mock)

        assert init_mock.call_args_list == [
            call(bc, frame=frame_mock, indicator=indicator_mock)
        ]


class TestNotImplemented:
    def test_open(self):
        bc = BaseCandleFactory()

        with pytest.raises(NotImplementedError):
            bc.open

    def test_high(self):
        bc = BaseCandleFactory()

        with pytest.raises(NotImplementedError):
            bc.high

    def test_low(self):
        bc = BaseCandleFactory()

        with pytest.raises(NotImplementedError):
            bc.low

    def test_last(self):
        bc = BaseCandleFactory()

        with pytest.raises(NotImplementedError):
            bc.last

    def test_close(self):
        bc = BaseCandleFactory()

        with pytest.raises(NotImplementedError):
            bc.close


class TestColor:
    @pytest.fixture(autouse=True)
    def mock_open(self, mocker):
        mock = mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: 100)
        return mock

    @pytest.fixture(autouse=True)
    def mock_last(self, mocker):
        mock = mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: 100)
        return mock

    def test_no_open(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: None)
        bc = BaseCandleFactory()

        assert bc.color is None

    def test_no_last(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: None)
        bc = BaseCandleFactory()

        assert bc.color is None

    def test_green(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: 99)
        mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: 100)
        bc = BaseCandleFactory()
        assert bc.color == CandleColor.GREEN

    def test_red(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: 100)
        mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: 99)
        bc = BaseCandleFactory()
        assert bc.color == CandleColor.RED

    def test_black(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: 100)
        mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: 100)
        bc = BaseCandleFactory()
        assert bc.color == CandleColor.BLACK


class TestHeight:
    @pytest.mark.parametrize(
        ["high", "low", "expected_height"], [(100, 98.5, 1.5), (44.67, 44.67, 0)]
    )
    def test_nominal(self, mocker, high, low, expected_height):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.high", new_callable=lambda: high)
        mocker.patch(f"{CLASS_DEFINITION_PATH}.low", new_callable=lambda: low)
        bc = BaseCandleFactory()
        assert bc.height == expected_height


class TestBody:
    @pytest.fixture(autouse=True)
    def mock_open(self, mocker):
        mock = mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: 100)
        return mock

    @pytest.fixture(autouse=True)
    def mock_last(self, mocker):
        mock = mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: 100)
        return mock

    def test_no_open(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: None)
        bc = BaseCandleFactory()

        assert bc.body is None

    def test_no_last(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: None)
        bc = BaseCandleFactory()

        assert bc.body is None

    @pytest.mark.parametrize(
        ["open", "last", "expected_body"],
        [
            (100, 98.5, 1.5),
            (44.67, 44.67, 0),
            (33, 40.89, 7.89),
        ],
    )
    def test_nominal(self, mocker, open, last, expected_body):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: open)
        mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: last)
        bc = BaseCandleFactory()
        assert bc.body == expected_body


class TestHead:
    @pytest.fixture(autouse=True)
    def mock_open(self, mocker):
        mock = mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: 100)
        return mock

    @pytest.fixture(autouse=True)
    def mock_last(self, mocker):
        mock = mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: 100)
        return mock

    def test_no_open(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: None)
        bc = BaseCandleFactory()

        assert bc.head is None

    def test_no_last(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: None)
        bc = BaseCandleFactory()

        assert bc.head is None

    @pytest.mark.parametrize(
        ["high", "open", "last", "expected_head"],
        [
            (100, 98.5, 97, 1.5),
            (45.2, 40, 42.2, 3),
        ],
    )
    def test_nominal(self, mocker, high, open, last, expected_head):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.high", new_callable=lambda: high)
        mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: open)
        mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: last)
        bc = BaseCandleFactory()
        assert bc.head == expected_head


class TestTail:
    @pytest.fixture(autouse=True)
    def mock_open(self, mocker):
        mock = mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: 100)
        return mock

    @pytest.fixture(autouse=True)
    def mock_last(self, mocker):
        mock = mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: 100)
        return mock

    def test_no_open(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: None)
        bc = BaseCandleFactory()

        assert bc.tail is None

    def test_no_last(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: None)
        bc = BaseCandleFactory()

        assert bc.tail is None

    @pytest.mark.parametrize(
        ["low", "open", "last", "expected_tail"],
        [
            (90, 98.5, 97, 7),
            (30.33, 33.33, 34.78, 3),
        ],
    )
    def test_nominal(self, mocker, low, open, last, expected_tail):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.low", new_callable=lambda: low)
        mocker.patch(f"{CLASS_DEFINITION_PATH}.open", new_callable=lambda: open)
        mocker.patch(f"{CLASS_DEFINITION_PATH}.last", new_callable=lambda: last)
        bc = BaseCandleFactory()
        assert bc.tail == expected_tail


class TestOnNewTick:
    def test_parent__call(self, mocker):
        parent_on_new_tick = mocker.patch(
            "estrade.graph.base_indicator.BaseIndicatorValue.on_new_tick"
        )
        bc = BaseCandleFactory()

        new_tick = TickFactory()

        bc.on_new_tick(new_tick)
        assert parent_on_new_tick.call_args_list == [call(new_tick)]
