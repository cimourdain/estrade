import threading
from unittest.mock import call

import pytest

from estrade import BaseTradeProvider, Trade
from estrade.enums import TransactionStatus
from estrade.mixins import RefMixin
from tests.unit.factories import (
    StrategyFactory,
    TradeFactory,
    TradeProviderFactory,
)


CLASS_BASE_DEFINITION_PATH = "estrade.trade_provider.BaseTradeProvider"


class TestInheritance:
    def test_ref_mixin(self):
        assert RefMixin in BaseTradeProvider.__bases__

    def test_ref_mixin_usage(self, mocker):
        mock_mixin_init = mocker.patch("estrade.mixins.ref.RefMixin.__init__")
        trade_provider = TradeProviderFactory(ref="test")

        assert mock_mixin_init.call_args_list == [call(trade_provider, "test")]


class TestInit:
    def test_trades(self):
        trade_provider = TradeProviderFactory()

        assert trade_provider.trades == []

    def test_threads(self):
        trade_provider = TradeProviderFactory()

        assert trade_provider.threads == []

    def test_default_transaction_status(self):
        trade_provider = TradeProviderFactory()

        assert trade_provider.default_transaction_status == TransactionStatus.REQUIRED


class TestOpenTradeRequest:
    def test_unimplemented(self):
        trade_provider = TradeProviderFactory()

        with pytest.raises(NotImplementedError):
            trade_provider.open_trade_request("test")


class TestOpenTrade:
    @pytest.fixture(autouse=True)
    def mock_init_thread(self, mocker):
        thread_mocker = mocker.Mock(spec=threading.Thread)
        mock = mocker.patch("threading.Thread", return_value=thread_mocker)

        return mock

    def test_add_to_trades(self):
        trade_provider = TradeProviderFactory()
        trade = TradeFactory()
        trade_provider.open_trade(trade)

        assert trade_provider.trades == [trade]

    def test_add_to_strategy(self):
        trade_provider = TradeProviderFactory()
        strategy = StrategyFactory()
        trade = TradeFactory(strategy=strategy)
        trade_provider.open_trade(trade)

        assert strategy.trades == [trade]

    def test_open_thread(self, mock_init_thread):
        trade_provider = TradeProviderFactory()
        trade = TradeFactory()
        trade_provider.open_trade(trade)

        assert mock_init_thread.call_args_list == [
            call(
                target=trade_provider.open_trade_request,
                args=(),
                kwargs={"trade": trade},
            )
        ]

    def test_start_thread(self, mock_init_thread):
        mock_thread_start = mock_init_thread.return_value.start
        trade_provider = TradeProviderFactory()
        trade = TradeFactory()
        trade_provider.open_trade(trade)

        assert mock_thread_start.call_args_list == [call()]


class TestUpdateStopRequest:
    def test_unimplemented(self):
        trade_provider = TradeProviderFactory()

        with pytest.raises(NotImplementedError):
            trade_provider.update_trade_stop_request("trade")


class TestUpdateStop:
    @pytest.fixture(autouse=True)
    def mock_init_thread(self, mocker):
        thread_mocker = mocker.Mock(spec=threading.Thread)
        mock = mocker.patch("threading.Thread", return_value=thread_mocker)

        return mock

    def test_open_thread(self, mock_init_thread):
        trade_provider = TradeProviderFactory()
        trade = TradeFactory()
        trade_provider.update_stop(trade)

        assert mock_init_thread.call_args_list == [
            call(
                target=trade_provider.update_trade_stop_request,
                args=(),
                kwargs={"trade": trade},
            )
        ]

    def test_start_thread(self, mock_init_thread):
        mock_thread_start = mock_init_thread.return_value.start
        trade_provider = TradeProviderFactory()
        trade = TradeFactory()
        trade_provider.update_stop(trade)

        assert mock_thread_start.call_args_list == [call()]


class TestUpdateLimitRequest:
    def test_unimplemented(self):
        trade_provider = TradeProviderFactory()

        with pytest.raises(NotImplementedError):
            trade_provider.update_trade_limit_request("trade")


class TestUpdatelimit:
    @pytest.fixture(autouse=True)
    def mock_init_thread(self, mocker):
        thread_mocker = mocker.Mock(spec=threading.Thread)
        mock = mocker.patch("threading.Thread", return_value=thread_mocker)

        return mock

    def test_open_thread(self, mock_init_thread):
        trade_provider = TradeProviderFactory()
        trade = TradeFactory()
        trade_provider.update_limit(trade)

        assert mock_init_thread.call_args_list == [
            call(
                target=trade_provider.update_trade_limit_request,
                args=(),
                kwargs={"trade": trade},
            )
        ]

    def test_start_thread(self, mock_init_thread):
        mock_thread_start = mock_init_thread.return_value.start
        trade_provider = TradeProviderFactory()
        trade = TradeFactory()
        trade_provider.update_limit(trade)

        assert mock_thread_start.call_args_list == [call()]


class TestCloseRequest:
    def test_unimplemented(self):
        trade_provider = TradeProviderFactory()

        with pytest.raises(NotImplementedError):
            trade_provider.close_trade_request("test_close")


class TestClose:
    @pytest.fixture(autouse=True)
    def mock_init_thread(self, mocker):
        thread_mocker = mocker.Mock(spec=threading.Thread)
        mock = mocker.patch("threading.Thread", return_value=thread_mocker)

        return mock

    def test_close_thread(self, mock_init_thread):
        trade_provider = TradeProviderFactory()
        trade_provider.close_trade("test_trade_close")

        assert mock_init_thread.call_args_list == [
            call(
                target=trade_provider.close_trade_request,
                args=(),
                kwargs={"trade_close": "test_trade_close"},
            )
        ]

    def test_start_thread(self, mock_init_thread):
        mock_thread_start = mock_init_thread.return_value.start
        trade_provider = TradeProviderFactory()
        trade_provider.close_trade("test_trade_close")

        assert mock_thread_start.call_args_list == [call()]


class TestIsAlive:
    def test_is_alive(self, mocker):
        thread_mock = mocker.Mock(spec=threading.Thread)
        thread_mock.is_alive.return_value = True

        trade_provider = TradeProviderFactory()
        trade_provider.threads = [thread_mock]

        assert trade_provider.is_alive is True

    def test_not_alive(self, mocker):
        thread_mock = mocker.Mock(spec=threading.Thread)
        thread_mock.is_alive.return_value = False

        trade_provider = TradeProviderFactory()
        trade_provider.threads = [thread_mock]

        assert trade_provider.is_alive is False

    def test_no_threads(self):
        trade_provider = TradeProviderFactory()

        assert trade_provider.is_alive is False


class TestOpenedTrades:
    @pytest.fixture
    def open_trade_mock(self, mocker):
        open_trade_mock = mocker.Mock(spec=Trade)
        open_trade_mock.closed = False

        return open_trade_mock

    @pytest.fixture
    def closed_trade_mock(self, mocker):
        open_trade_mock = mocker.Mock(spec=Trade)
        open_trade_mock.closed = True

        return open_trade_mock

    def test_no_trades(self):
        trade_provider = TradeProviderFactory()

        assert trade_provider.opened_trades == []

    def test_only_opened(self, open_trade_mock):
        trade_provider = TradeProviderFactory()
        trade_provider.trades = [open_trade_mock]

        assert trade_provider.opened_trades == [open_trade_mock]

    def test_mixed(self, open_trade_mock, closed_trade_mock):
        trade_provider = TradeProviderFactory()
        trade_provider.trades = [open_trade_mock, closed_trade_mock]

        assert trade_provider.opened_trades == [open_trade_mock]

    def test_only_closed(self, closed_trade_mock):
        trade_provider = TradeProviderFactory()
        trade_provider.trades = [closed_trade_mock]

        assert trade_provider.opened_trades == []
