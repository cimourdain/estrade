from unittest.mock import PropertyMock, call

import arrow
import pytest

from estrade import TradeClose
from estrade.enums import TradeDirection, TransactionStatus
from estrade.mixins import MetaMixin, RefMixin, TimedMixin, TransactionMixin
from tests.unit.factories import TradeCloseFactory, TradeFactory


CLASS_TRADE_DEFINITION_PATH = "estrade.trade.Trade"
CLASS_TRADE_CLOSE_DEFINITION_PATH = "estrade.trade.TradeClose"


class TestInheritance:
    def test_inherit_ref(self):
        assert RefMixin in TradeClose.__bases__

    @pytest.mark.parametrize(
        ["ref"],
        [pytest.param(None, id="empty"), pytest.param("test", id="not empty")],
    )
    def test_refmixin_called(self, mocker, ref):
        mock_ref_mixin_init = mocker.patch("estrade.mixins.ref.RefMixin.__init__")
        trade_close = TradeCloseFactory(ref=ref)

        assert mock_ref_mixin_init.call_args_list == [call(trade_close, ref)]

    def test_inherit_timed(self):
        assert TimedMixin in TradeClose.__bases__

    def test_timed_mixin_called(self, mocker):
        mock_timed_mixin_init = mocker.patch("estrade.mixins.timed.TimedMixin.__init__")
        dt = arrow.get("2020-01-01 12:34:56")
        trade_close = TradeCloseFactory(datetime=dt)

        assert mock_timed_mixin_init.call_args_list == [call(trade_close, dt)]

    def test_inherit_meta(self):
        assert MetaMixin in TradeClose.__bases__

    def test_meta_mixin_called(self, mocker):
        mock_meta_mixin_init = mocker.patch("estrade.mixins.meta.MetaMixin.__init__")
        trade_close = TradeCloseFactory(meta={"test": "test"})

        assert mock_meta_mixin_init.call_args_list == [
            call(trade_close, {"test": "test"})
        ]

    def test_inherit_transaction(self):
        assert TransactionMixin in TradeClose.__bases__

    @pytest.mark.parametrize(
        ["close_params", "expected_status_call"],
        [
            pytest.param({}, TransactionStatus.CREATED, id="empty"),
            pytest.param(
                {"status": TransactionStatus.CONFIRMED},
                TransactionStatus.CONFIRMED,
                id="not empty",
            ),
        ],
    )
    def test_transaction_mixin_called(self, mocker, close_params, expected_status_call):
        mock_transaction_mixin_init = mocker.patch(
            "estrade.mixins.transaction.TransactionMixin.__init__"
        )
        trade_close = TradeCloseFactory(**close_params)

        assert mock_transaction_mixin_init.call_args_list == [
            call(trade_close, expected_status_call)
        ]


class TestInit:
    def test_trade(self):
        trade = TradeFactory()
        trade_close = TradeCloseFactory(trade=trade)

        assert trade_close.trade == trade

    def test_close_value(self):
        trade_close = TradeCloseFactory(close_value=12.67)

        assert trade_close.close_value == 12.67

    def test_quantity(self):
        trade_close = TradeCloseFactory(quantity=150)

        assert trade_close.quantity == 150


class TestResultAvg:
    @pytest.mark.parametrize(
        ["direction", "trade_open", "close_value", "expected_result_avg"],
        [
            pytest.param(TradeDirection.BUY, 10.34, 12.87, 2.53, id="BUY positive"),
            pytest.param(TradeDirection.BUY, 10.34, 6.91, -3.43, id="BUY negative"),
            pytest.param(TradeDirection.SELL, 10.34, 3.27, 7.07, id="SELL positive"),
            pytest.param(TradeDirection.SELL, 10.34, 18.38, -8.04, id="SELL negative"),
        ],
    )
    def test_nominal(self, direction, trade_open, close_value, expected_result_avg):
        trade = TradeFactory(direction=direction, open_value=trade_open)

        trade_close = TradeCloseFactory(trade=trade, close_value=close_value)

        assert trade_close.result_avg == expected_result_avg


class TestResult:
    def test_nominal(self, mocker):
        mocker.patch(
            f"{CLASS_TRADE_CLOSE_DEFINITION_PATH}.result_avg",
            new_callable=PropertyMock(return_value=23.56),
        )

        trade_close = TradeCloseFactory(quantity=3)

        assert trade_close.result == 70.68
