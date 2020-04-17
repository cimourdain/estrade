from unittest.mock import call

import arrow
import pytest

from tests.unit.factories import EpicFactory, StrategyFactory


CLASS_DEFINITION_PATH = "estrade.strategy.BaseStrategy"


class TestStrategyInit:
    def test_epics(self):
        epic = EpicFactory()
        strategy = StrategyFactory()
        epic.add_strategy(strategy)

        assert strategy.epics == {epic.ref: epic}

    def test_paused_until(self):
        strategy = StrategyFactory()

        assert strategy.paused_until is None

    def test_stopped(self):
        strategy = StrategyFactory()

        assert strategy.stopped is False

    def test_trades(self):
        strategy = StrategyFactory()

        assert strategy.trades == []


class TestIsActive:
    @pytest.mark.parametrize(
        ["paused_until"],
        [
            pytest.param(None, id="paused_until not set"),
            pytest.param(arrow.get("2020-01-01 12:34:56"), id="paused until elapsed"),
        ],
    )
    def test_active(self, paused_until):
        strategy = StrategyFactory()
        strategy.stopped = False
        strategy.paused_until = paused_until

        assert strategy.is_active(new_tick_date=arrow.get("2020-01-01 12:34:57"))

    def test_stopped(self):
        strategy = StrategyFactory()
        strategy.stopped = True

        assert strategy.is_active("test") is False

    def test_paused(self):
        strategy = StrategyFactory()
        strategy.stopped = False
        strategy.paused_until = arrow.get("2020-01-01 12:34:56")

        assert (
            strategy.is_active(new_tick_date=arrow.get("2020-01-01 12:34:55")) is False
        )

    def test_paused_until_reset(self):
        strategy = StrategyFactory()
        strategy.stopped = False
        strategy.paused_until = arrow.get("2020-01-01 12:34:56")

        strategy.is_active(new_tick_date=arrow.get("2020-01-01 12:34:57"))

        assert strategy.paused_until is None


class TestOpenTrade:
    def test_epic_open_trade_call(self, mocker):
        epic = mocker.Mock()
        strategy = StrategyFactory()
        strategy.open_trade(epic=epic, test_arg="test_value")

        assert epic.open_trade.call_args_list == [
            call(strategy=strategy, test_arg="test_value")
        ]

    def test_return_trade(self, mocker):
        epic = mocker.Mock()
        epic.open_trade.return_value = "my_new_trade"

        strategy = StrategyFactory()
        response = strategy.open_trade(epic=epic)

        assert response == "my_new_trade"


class TestCloseTrade:
    def test_close_trade_call(self, mocker):
        trade = mocker.Mock()

        strategy = StrategyFactory()
        strategy.close_trade(trade=trade, test_arg="test_value")

        assert trade.epic.close_trade.call_args_list == [
            call(trade=trade, test_arg="test_value")
        ]

    def test_return_trade_close(self, mocker):
        trade = mocker.Mock()
        trade.epic.close_trade.return_value = "my_trade_close"

        strategy = StrategyFactory()
        response = strategy.close_trade(trade=trade, test_arg="test_value")

        assert response == "my_trade_close"


class TestCloseOpenedTrades:
    def test_get_trade_call(self, mocker):
        trade1_mock = mocker.Mock()
        trade2_mock = mocker.Mock()
        get_trade_mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.get_trades",
            return_value=[trade1_mock, trade2_mock],
        )

        strategy = StrategyFactory()
        strategy.close_opened_trades()

        assert get_trade_mock.call_args_list == [call(open_only=True)]

    def test_trade_close_call(self, mocker):
        strategy_close_trade_mock = mocker.patch(f"{CLASS_DEFINITION_PATH}.close_trade")
        trade1_mock = mocker.Mock()
        trade2_mock = mocker.Mock()
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.get_trades",
            return_value=[trade1_mock, trade2_mock],
        )

        strategy = StrategyFactory()
        strategy.close_opened_trades(test_arg="test_value")

        assert strategy_close_trade_mock.call_args_list == [
            call(trade=trade1_mock, test_arg="test_value"),
            call(trade=trade2_mock, test_arg="test_value"),
        ]


class TestGetTrades:
    def test_nominal(self, mocker):
        strategy = StrategyFactory()
        trade1_mock = mocker.Mock()
        trade2_mock = mocker.Mock()
        strategy.trades = [trade1_mock, trade2_mock]

        assert list(strategy.get_trades()) == [trade2_mock, trade1_mock]

    def test_epic_filter(self, mocker):
        strategy = StrategyFactory()
        trade1_mock = mocker.Mock()
        trade1_mock.epic = "epic1"
        trade2_mock = mocker.Mock()
        trade2_mock.epic = "epic2"
        trade3_mock = mocker.Mock()
        trade3_mock.epic = "epic1"
        strategy.trades = [trade1_mock, trade2_mock, trade3_mock]

        assert list(strategy.get_trades(epics=["epic1"])) == [trade3_mock, trade1_mock]

    def test_open_only_filter(self, mocker):
        strategy = StrategyFactory()
        trade1_mock = mocker.Mock()
        trade1_mock.closed = True
        trade2_mock = mocker.Mock()
        trade2_mock.closed = False
        trade3_mock = mocker.Mock()
        trade3_mock.closed = True
        strategy.trades = [trade1_mock, trade2_mock, trade3_mock]

        assert list(strategy.get_trades(open_only=True)) == [trade2_mock]

    def test_only_after_mock(self, mocker):
        strategy = StrategyFactory()
        trade0_mock = mocker.Mock()
        trade0_mock.datetime = arrow.get("2020-01-01 14:00:00")
        trade1_mock = mocker.Mock()
        trade1_mock.datetime = arrow.get("2020-01-01 10:00:00")
        trade2_mock = mocker.Mock()
        trade2_mock.datetime = arrow.get("2020-01-01 12:00:00")
        trade3_mock = mocker.Mock()
        trade3_mock.datetime = arrow.get("2020-01-01 14:00:00")
        strategy.trades = [trade0_mock, trade1_mock, trade2_mock, trade3_mock]

        assert list(
            strategy.get_trades(only_after=arrow.get("2020-01-01 12:00:00"))
        ) == [trade3_mock, trade2_mock]


class TestResult:
    def test_no_trades(self):
        strategy = StrategyFactory()
        strategy.trades = []

        assert strategy.result() == 0

    @pytest.mark.parametrize(
        ["trades_results", "expected_result"],
        [
            ([123.456, -98.76], 24.70),
        ],
    )
    def test_trades(self, mocker, trades_results, expected_result):
        strategy = StrategyFactory()
        for trade_result in trades_results:
            trade_mock = mocker.Mock()
            trade_mock.result = trade_result
            strategy.trades.append(trade_mock)

        assert strategy.result() == expected_result

    @pytest.mark.parametrize(
        ["trades_results", "expected_result"],
        [
            ([123.456, -98.76], 24.70),
        ],
    )
    def test_trades__argument(self, mocker, trades_results, expected_result):
        strategy = StrategyFactory()
        input_trades = []
        for trade_result in trades_results:
            trade_mock = mocker.Mock()
            trade_mock.result = trade_result
            input_trades.append(trade_mock)

        assert strategy.result(input_trades) == expected_result


class TestProfitFactor:
    def test_no_trades(self):
        strategy = StrategyFactory()
        strategy.trades = []

        assert strategy.profit_factor() == 0

    @pytest.mark.parametrize(
        ["trades_results", "expected_profit_factor"],
        [
            ([123.456, -98.76, 56.87, -34.87], 1.35),
            ([123.456, -98.76, -100.34, -34.87], 0.53),
            ([123.456, -0.01], 123.46),
        ],
    )
    def test_trades(self, mocker, trades_results, expected_profit_factor):
        strategy = StrategyFactory()
        for trade_result in trades_results:
            trade_mock = mocker.Mock()
            trade_mock.result = trade_result
            strategy.trades.append(trade_mock)

        assert strategy.profit_factor() == expected_profit_factor

    @pytest.mark.parametrize(
        ["trades_results", "expected_profit_factor"],
        [
            ([123.456, -98.76, 56.87, -34.87], 1.35),
            ([123.456, -98.76, -100.34, -34.87], 0.53),
            ([123.456, -0.01], 123.46),
        ],
    )
    def test_trades__argument(self, mocker, trades_results, expected_profit_factor):
        strategy = StrategyFactory()
        input_trades = []
        for trade_result in trades_results:
            trade_mock = mocker.Mock()
            trade_mock.result = trade_result
            input_trades.append(trade_mock)

        assert strategy.profit_factor(input_trades) == expected_profit_factor


class TestEventMethods:
    def test_on_every_tick(self):
        strategy = StrategyFactory()
        epic = EpicFactory()

        assert strategy.on_every_tick(epic) is None

    def test_on_every_tick_market_open(self):
        strategy = StrategyFactory()
        epic = EpicFactory()

        assert strategy.on_every_tick_market_open(epic) is None

    def test_on_market_open(self):
        strategy = StrategyFactory()
        epic = EpicFactory()

        assert strategy.on_market_open(epic) is None

    def test_on_market_close(self):
        strategy = StrategyFactory()
        epic = EpicFactory()

        assert strategy.on_market_close(epic) is None
