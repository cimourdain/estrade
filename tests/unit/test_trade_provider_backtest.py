from unittest.mock import PropertyMock, call

import pytest

from estrade import BaseTradeProvider, Trade
from estrade.enums import TradeDirection
from estrade.trade_provider import TradeProviderBacktests
from tests.unit.factories import TradeProviderBacktestsFactory


CLASS_BASE_DEFINITION_PATH = "estrade.trade_provider.BaseTradeProvider"


class TestInheritance:
    def test_inherit_trade_provider(self):
        assert BaseTradeProvider in TradeProviderBacktests.__bases__


class TestOpen:
    @pytest.fixture(autouse=True)
    def mock_open_trade(self, mocker):
        mock = mocker.patch(f"{CLASS_BASE_DEFINITION_PATH}.open_trade")
        return mock

    def test_open_new_trade(self, mocker, mock_open_trade):
        mocker.patch(
            f"{CLASS_BASE_DEFINITION_PATH}.opened_trades",
            new_callable=PropertyMock(return_value=[]),
        )
        trade_provider = TradeProviderBacktestsFactory()

        trade_mock = mocker.Mock(spec=Trade)
        trade_mock.direction = TradeDirection.BUY
        trade_mock.open_quantity = 3
        trade_provider.open_trade(trade_mock)

        assert mock_open_trade.call_args_list == [call(trade_provider, trade_mock)]

    def test_already_opened_trade__open(self, mocker):
        existing_trade_mock = mocker.Mock(spec=Trade)
        existing_trade_mock.direction = TradeDirection.SELL
        existing_trade_mock.strategy = "strategy1"
        existing_trade_mock.opened_quantities = 2
        mocker.patch(
            f"{CLASS_BASE_DEFINITION_PATH}.opened_trades",
            new_callable=PropertyMock(return_value=[existing_trade_mock]),
        )

        trade_mock = mocker.Mock(spec=Trade)
        trade_mock.direction = TradeDirection.BUY
        trade_mock.strategy = "strategy1"
        trade_mock.open_quantity = 3

        trade_provider = TradeProviderBacktestsFactory()
        trade_provider.open_trade(trade_mock)

        assert trade_mock.open_quantity == 1

    def test_already_opened_trade__open_other_strategy(self, mocker):
        existing_trade_mock = mocker.Mock(spec=Trade)
        existing_trade_mock.direction = TradeDirection.SELL
        existing_trade_mock.strategy = "strategy1"
        existing_trade_mock.opened_quantities = 2
        mocker.patch(
            f"{CLASS_BASE_DEFINITION_PATH}.opened_trades",
            new_callable=PropertyMock(return_value=[existing_trade_mock]),
        )

        trade_mock = mocker.Mock(spec=Trade)
        trade_mock.direction = TradeDirection.BUY
        trade_mock.strategy = "strategy2"
        trade_mock.open_quantity = 3

        trade_provider = TradeProviderBacktestsFactory()
        trade_provider.open_trade(trade_mock)

        assert trade_mock.open_quantity == 3

    def test_already_opened_trade__no_open(self, mocker, mock_open_trade):
        existing_trade_mock = mocker.Mock(spec=Trade)
        existing_trade_mock.direction = TradeDirection.SELL
        existing_trade_mock.strategy = "strategy1"
        existing_trade_mock.opened_quantities = 3
        mocker.patch(
            f"{CLASS_BASE_DEFINITION_PATH}.opened_trades",
            new_callable=PropertyMock(return_value=[existing_trade_mock]),
        )

        trade_mock = mocker.Mock(spec=Trade)
        trade_mock.direction = TradeDirection.BUY
        trade_mock.strategy = "strategy1"
        trade_mock.open_quantity = 2

        trade_provider = TradeProviderBacktestsFactory()
        trade_provider.open_trade(trade_mock)

        assert mock_open_trade.call_args_list == []
