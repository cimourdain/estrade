from unittest.mock import PropertyMock, call

import arrow
import pytest

from estrade import Trade, TradeClose
from estrade.enums import TradeDirection, TransactionStatus
from estrade.exceptions import TradeException
from estrade.mixins import MetaMixin, RefMixin, TimedMixin, TransactionMixin
from tests.unit.factories import (
    EpicFactory,
    StrategyFactory,
    TickFactory,
    TradeFactory,
)


CLASS_TRADE_DEFINITION_PATH = "estrade.trade.Trade"
CLASS_TRADE_CLOSE_DEFINITION_PATH = "estrade.trade.TradeClose"


class TestInheritance:
    def test_inherit_ref(self):
        assert RefMixin in Trade.__bases__

    def test_ref_init_called__default(self, mocker):
        ref_init = mocker.patch.object(RefMixin, "__init__", wraps=RefMixin.__init__)
        trade = TradeFactory()

        ref_init.assert_called_once_with(trade, None)

    def test_ref_init_called__manual(self, mocker):
        ref_init = mocker.patch.object(RefMixin, "__init__", wraps=RefMixin.__init__)
        trade = TradeFactory(ref="test")

        ref_init.assert_called_once_with(trade, "test")

    def test_inherit_metadata(self):
        assert MetaMixin in Trade.__bases__

    def test_meta_init_called__default(self, mocker):
        meta_init = mocker.patch.object(MetaMixin, "__init__")
        trade = TradeFactory()

        meta_init.assert_called_once_with(trade, None)

    def test_meta_init_called__manual(self, mocker):
        meta_init = mocker.patch.object(MetaMixin, "__init__")
        trade = TradeFactory(meta="test")

        meta_init.assert_called_once_with(trade, "test")

    def test_inherit_timed(self):
        assert TimedMixin in Trade.__bases__

    def test_timed_init_called__manual(self, mocker):
        timed_init = mocker.patch.object(TimedMixin, "__init__")
        trade = TradeFactory(open_datetime="test")

        timed_init.assert_called_once_with(trade, "test")

    def test_inherit_transaction(self):
        assert TransactionMixin in Trade.__bases__

    def test_transaction_init_called__default(self, mocker):
        transaction_init = mocker.patch.object(TransactionMixin, "__init__")
        trade = TradeFactory()

        transaction_init.assert_called_once_with(trade, TransactionStatus.CREATED)

    def test_transaction_init_called__manual(self, mocker):
        transaction_init = mocker.patch.object(TransactionMixin, "__init__")
        trade = TradeFactory(status="test")

        transaction_init.assert_called_once_with(trade, "test")


class TestInit:
    @pytest.mark.parametrize(
        ["direction"],
        [
            pytest.param(TradeDirection.BUY, id="BUY"),
            pytest.param(TradeDirection.SELL, id="SELL"),
        ],
    )
    def test_direction__valid(self, direction):
        trade = TradeFactory(direction=direction)

        assert trade.direction == direction

    def test_quantity(self):
        trade = TradeFactory(quantity=12)
        assert trade.open_quantity == 12

    def test_open_value(self):
        trade = TradeFactory(open_value=555)
        assert trade.open_value == 555

    def test_open_datetime(self):
        open_datetime = arrow.get("2020-01-01 12:34:56")
        trade = TradeFactory(open_datetime=open_datetime)

        assert trade.datetime == open_datetime

    def test_current_close_value__default(self):
        trade = TradeFactory(open_value=777, current_close_value=None)

        assert trade.current_close_value == 777

    def test_current_close_value__manual(self):
        trade = TradeFactory(current_close_value=666)

        assert trade.current_close_value == 666

    @pytest.mark.parametrize(
        ["status"],
        [
            pytest.param(TransactionStatus.REQUIRED, id="required"),
            pytest.param(TransactionStatus.CREATED, id="created"),
            pytest.param(TransactionStatus.CONFIRMED, id="confirmed"),
        ],
    )
    def test_status(self, status):
        trade = TradeFactory(status=status)

        assert trade.status == status

    def test_epic__default(self):
        trade = TradeFactory(epic=None)

        assert trade.epic is None

    def test_epic__manual(self):
        epic = EpicFactory()
        trade = TradeFactory(epic=epic)

        assert trade.epic == epic

    def test_strategy__default(self):
        trade = TradeFactory(strategy=None)

        assert trade.strategy is None

    def test_strategy__manual(self):
        strategy = "test"
        trade = TradeFactory(strategy=strategy)

        assert trade.strategy == strategy

    def test_meta(self):
        trade = TradeFactory(meta={"test": "test"})
        assert trade.meta == {"test": "test"}


class TestInitStopLimit:
    def test_stop_default(self):
        trade = TradeFactory(stop_relative=None, stop_absolute=None)

        assert trade.absolute_stop is None

    def test_stop_absolute(self):
        trade = TradeFactory(open_value=100, stop_relative=None, stop_absolute=20.56)

        assert trade.absolute_stop == 20.56

    def test_stop_absolute__trade_provider_call(self, mocker):
        update_trade_stop = mocker.patch(
            "estrade.trade_provider.BaseTradeProvider.update_stop"
        )
        TradeFactory(open_value=100, stop_relative=None, stop_absolute=20.56)

        assert not update_trade_stop.called

    def test_stop_relative(self):
        trade = TradeFactory(open_value=100, stop_relative=5.67, stop_absolute=None)

        assert trade.absolute_stop == 94.33

    def test_stop_relative__trade_provider_call(self, mocker):
        update_trade_stop = mocker.patch(
            "estrade.trade_provider.BaseTradeProvider.update_stop"
        )
        TradeFactory(open_value=100, stop_relative=5.67, stop_absolute=None)

        assert not update_trade_stop.called

    def test_limit_default(self):
        trade = TradeFactory(limit_relative=None, limit_absolute=None)

        assert trade.absolute_limit is None

    def test_limit_absolute(self):
        trade = TradeFactory(open_value=100, limit_relative=None, limit_absolute=120.56)

        assert trade.absolute_limit == 120.56

    def test_limit_absolute__trade_provider_call(self, mocker):
        update_trade_limit = mocker.patch(
            "estrade.trade_provider.BaseTradeProvider.update_limit"
        )
        TradeFactory(open_value=100, limit_relative=None, limit_absolute=120.56)

        assert not update_trade_limit.called

    def test_limit_relative(self):
        trade = TradeFactory(open_value=100, limit_relative=5.67, limit_absolute=None)

        assert trade.absolute_limit == 105.67

    def test_limit_relative__trade_provider_call(self, mocker):
        update_trade_limit = mocker.patch(
            "estrade.trade_provider.BaseTradeProvider.update_limit"
        )
        TradeFactory(open_value=100, limit_relative=5.67, limit_absolute=None)

        assert not update_trade_limit.called


class TestTradeOpen:
    class TestOpenFromTick:
        @pytest.fixture
        def mock_init_trade(self, mocker):
            mock = mocker.patch(f"{CLASS_TRADE_DEFINITION_PATH}")
            return mock

        def test_epic(self, mock_init_trade):
            tick = TickFactory()
            default_trade_args, _ = TradeFactory.get_default_args()

            Trade.open_from_tick(tick=tick, **default_trade_args)

            assert mock_init_trade.call_count == 1
            assert (
                mock_init_trade.call_args_list[0][1]["epic"]
                == default_trade_args["epic"]
            )

        def test_open_datetime(self, mock_init_trade):
            tick_datetime = arrow.get("2020-01-01 12:34:56")
            tick = TickFactory(datetime=tick_datetime)

            default_trade_args, _ = TradeFactory.get_default_args()
            Trade.open_from_tick(tick=tick, **default_trade_args)

            assert mock_init_trade.call_count == 1
            assert (
                mock_init_trade.call_args_list[0][1]["open_datetime"] == tick_datetime
            )

        def test_kwargs(self, mock_init_trade):
            default_trade_args, _ = TradeFactory.get_default_args()
            Trade.open_from_tick(tick=TickFactory(), ref="test", **default_trade_args)

            assert mock_init_trade.call_count == 1
            assert mock_init_trade.call_args_list[0][1]["ref"] == "test"

        @pytest.mark.parametrize(
            ["direction", "bid", "ask", "expected_open", "expected_current"],
            [
                pytest.param(TradeDirection.BUY, 99, 100, 100, 99, id="buy"),
                pytest.param(TradeDirection.SELL, 99, 100, 99, 100, id="sell"),
            ],
        )
        def test_direction(
            self,
            mock_init_trade,
            direction,
            bid,
            ask,
            expected_open,
            expected_current,
        ):

            tick_datetime = arrow.get("2020-01-01 12:34:56")
            tick = TickFactory(bid=bid, ask=ask, datetime=tick_datetime)
            default_trade_args, _ = TradeFactory.get_default_args()
            default_trade_args["direction"] = direction
            Trade.open_from_tick(tick=tick, **default_trade_args)

            assert mock_init_trade.call_count == 1
            assert mock_init_trade.call_args_list[0][1]["direction"] == direction
            assert mock_init_trade.call_args_list[0][1]["open_value"] == expected_open
            assert (
                mock_init_trade.call_args_list[0][1]["current_close_value"]
                == expected_current
            )

        def test_invalid_direction(self):
            tick = TickFactory()
            default_trade_args, _ = TradeFactory.get_default_args()
            default_trade_args["direction"] = "invalid"
            with pytest.raises(TradeException):
                Trade.open_from_tick(tick=tick, **default_trade_args)

    class TestOpenFromEpic:
        @pytest.fixture
        def mock_trade_open_from_tick(self, mocker):
            mock = mocker.patch(f"{CLASS_TRADE_DEFINITION_PATH}.open_from_tick")
            return mock

        def test_valid_epic(self, mock_trade_open_from_tick):
            epic = EpicFactory()

            default_trade_args, _ = TradeFactory.get_default_args()
            default_trade_args["epic"] = epic

            Trade.open_from_epic(**default_trade_args)

            assert mock_trade_open_from_tick.call_args_list == [
                call(tick=epic.last_tick, **default_trade_args)
            ]


class TestTradeUpdate:
    class TestUpdateMinMax:
        @pytest.fixture(autouse=True)
        def mock_result(self, mocker):
            # mock property result of Trade
            mock_property = mocker.Mock(return_value=150)
            mock = mocker.patch(
                f"{CLASS_TRADE_DEFINITION_PATH}.result", new_callable=mock_property
            )
            return mock

        @pytest.mark.parametrize(
            ["current_max_result", "expected_max_result"],
            [
                pytest.param(100, 150, id="update max result"),
                pytest.param(200, 200, id="no update max result"),
            ],
        )
        def test_update_max_result(self, current_max_result, expected_max_result):
            trade = TradeFactory()
            trade.max_result = current_max_result

            trade._update_min_max()

            assert trade.max_result == expected_max_result

        @pytest.mark.parametrize(
            ["current_min_result", "expected_min_result"],
            [
                pytest.param(200, 150, id="update min result"),
                pytest.param(100, 100, id="no update min result"),
            ],
        )
        def test_update_min_result(self, current_min_result, expected_min_result):
            trade = TradeFactory()
            trade.min_result = current_min_result

            trade._update_min_max()

            assert trade.min_result == expected_min_result

    class TestUpdateFromTick:
        @pytest.fixture
        def mock_update(self, mocker):
            mock = mocker.patch(f"{CLASS_TRADE_DEFINITION_PATH}.update")
            return mock

        @pytest.mark.parametrize(
            ["direction", "expected_current"],
            [
                pytest.param(TradeDirection.BUY, 99, id="update buy"),
                pytest.param(TradeDirection.SELL, 100, id="update sell"),
            ],
        )
        def test_nominal(self, mock_update, direction, expected_current):
            trade: Trade = TradeFactory(direction=direction)
            tick = TickFactory(bid=99, ask=100)

            trade.update_from_tick(tick)

            mock_update.assert_called_once_with(expected_current)

    class TestUpdateFromEpic:
        @pytest.fixture
        def mock_update_from_tick(self, mocker):
            mock = mocker.patch(f"{CLASS_TRADE_DEFINITION_PATH}.update_from_tick")
            return mock

        def test_nominal_epic(self, mock_update_from_tick):
            epic = EpicFactory()
            trade = TradeFactory(epic=epic)
            trade.update_from_epic()

            mock_update_from_tick.assert_called_once_with(epic.last_tick)

    class TestUpdateTrade:
        @pytest.fixture(autouse=True)
        def mock_update_mix_max(self, mocker):
            mock = mocker.patch(f"{CLASS_TRADE_DEFINITION_PATH}._update_min_max")
            return mock

        def test_closed(self, mocker, mock_update_mix_max):
            # mock property closed of Trade
            closed_mock = PropertyMock(return_value=True)
            mocker.patch(
                f"{CLASS_TRADE_DEFINITION_PATH}.closed", new_callable=closed_mock
            )

            trade = TradeFactory()

            trade.update(34.5)

            assert mock_update_mix_max.not_called

        def test_set_current_close(self):
            trade = TradeFactory()

            trade.update(34.9)

            assert trade.current_close_value == 34.9

        def test_call_update_min_max(self, mock_update_mix_max):
            trade = TradeFactory()

            trade.update(34.9)

            assert mock_update_mix_max.call_args_list == [call()]


class TestTradeClose:
    class TestClose:
        @pytest.fixture(autouse=True)
        def mock_trade_close_init(self, mocker):
            mock = mocker.patch(f"{CLASS_TRADE_DEFINITION_PATH}Close")
            return mock

        @pytest.mark.parametrize(
            ["quantity", "expected_quantity"],
            [
                pytest.param(3, 3, id="explicit quantity"),
                pytest.param(None, 5, id="all quantity"),
                pytest.param(6, 5, id="exceding opened quantity"),
            ],
        )
        def test_quantities(self, mock_trade_close_init, quantity, expected_quantity):
            trade = TradeFactory(quantity=5)

            trade.close(close_value=100, datetime=arrow.utcnow(), quantity=quantity)

            assert mock_trade_close_init.call_count == 1
            assert (
                mock_trade_close_init.call_args_list[0][1]["quantity"]
                == expected_quantity
            )

        def test_close_value(self, mock_trade_close_init):
            trade = TradeFactory(quantity=2)

            trade.close(close_value=100, datetime=arrow.utcnow())

            assert mock_trade_close_init.call_count == 1
            assert mock_trade_close_init.call_args_list[0][1]["close_value"] == 100

        def test_datetime(self, mock_trade_close_init):
            trade = TradeFactory()

            trade.close(close_value=100, datetime="test")

            assert mock_trade_close_init.call_count == 1
            assert mock_trade_close_init.call_args_list[0][1]["datetime"] == "test"

        def test_append_to_closes(self, mocker):
            mocker.patch(
                f"{CLASS_TRADE_CLOSE_DEFINITION_PATH}", return_value="new_close"
            )

            trade = TradeFactory()

            trade.close(close_value=100, datetime="test")

            assert trade.closes == ["new_close"]

        def test_return_close(self, mocker):
            mocker.patch(
                f"{CLASS_TRADE_CLOSE_DEFINITION_PATH}", return_value="new_close"
            )

            trade = TradeFactory()

            response = trade.close(close_value=100, datetime="test")

            assert response == "new_close"

        def test_kwargs(self, mock_trade_close_init):
            trade = TradeFactory(quantity=2)

            trade.close(close_value=100, datetime=arrow.utcnow(), random_arg="test")

            assert mock_trade_close_init.call_args_list[0][1]["random_arg"] == "test"

    class TestCloseFromTick:
        @pytest.fixture(autouse=True)
        def mock_trade_close(self, mocker):
            mock = mocker.patch(f"{CLASS_TRADE_DEFINITION_PATH}.close")
            return mock

        @pytest.fixture(autouse=True)
        def mock_update_from_tick(self, mocker):
            mock = mocker.patch(f"{CLASS_TRADE_DEFINITION_PATH}.update_from_tick")
            return mock

        def test_call_update_from_tick(self, mock_update_from_tick):
            tick = TickFactory()
            trade = TradeFactory()
            trade.close_from_tick(tick)

            assert mock_update_from_tick.call_args_list == [call(tick)]

        def test_close_value(self, mock_trade_close):
            tick = TickFactory()
            trade = TradeFactory()
            trade.current_close_value = 87.9
            trade.close_from_tick(tick)

            assert mock_trade_close.call_count == 1
            assert mock_trade_close.call_args_list[0][1]["close_value"] == 87.9

        def test_datetime(self, mock_trade_close):
            dt = arrow.get("2020-01-01 12:34:56")
            tick = TickFactory(datetime=dt)
            trade = TradeFactory()
            trade.close_from_tick(tick)

            assert mock_trade_close.call_count == 1
            assert mock_trade_close.call_args_list[0][1]["datetime"] == dt

        def test_kwargs(self, mock_trade_close):
            tick = TickFactory()
            trade = TradeFactory()
            trade.close_from_tick(tick, test_arg="test_value")

            assert mock_trade_close.call_count == 1
            assert mock_trade_close.call_args_list[0][1]["test_arg"] == "test_value"

        def test_response(self, mocker):
            mocker.patch(
                f"{CLASS_TRADE_DEFINITION_PATH}.close", return_value="test_close"
            )

            tick = TickFactory()
            trade = TradeFactory()
            response = trade.close_from_tick(tick)

            assert response == "test_close"

    class TestCloseFromEpic:
        @pytest.fixture(autouse=True)
        def mock_close_from_tick(self, mocker):
            mock = mocker.patch(f"{CLASS_TRADE_DEFINITION_PATH}.close_from_tick")
            return mock

        def test_call_close_from_tick(self, mock_close_from_tick):
            epic = EpicFactory()
            trade = TradeFactory(epic=epic)

            last_tick = TickFactory()
            epic.last_tick = last_tick

            trade.close_from_epic()

            assert mock_close_from_tick.call_args_list == [call(last_tick)]

        def test_return(self, mocker):
            mocker.patch(
                f"{CLASS_TRADE_DEFINITION_PATH}.close_from_tick",
                return_value="test_close",
            )
            trade = TradeFactory(epic=EpicFactory())

            result = trade.close_from_epic()

            assert result == "test_close"


class TestStop:
    @pytest.fixture
    def mock_trade_provider_update_stop(self, mocker):
        mock = mocker.patch("estrade.trade_provider.BaseTradeProvider.update_stop")

        return mock

    @pytest.mark.parametrize(
        ["direction", "open", "current_close", "stop"],
        [(TradeDirection.BUY, 100, 99, 98.9), (TradeDirection.SELL, 100, 101, 101.1)],
    )
    def test_stop_absolute__valid(
        self, mock_trade_provider_update_stop, direction, open, current_close, stop
    ):
        trade = TradeFactory(
            direction=direction, open_value=open, current_close_value=current_close
        )
        trade.set_stop_absolute(stop)

        assert trade.absolute_stop == stop
        assert mock_trade_provider_update_stop.call_args_list == [call(trade=trade)]

    @pytest.mark.parametrize(
        ["direction", "open", "current_close", "stop"],
        [
            (TradeDirection.BUY, 100, 99, 100),
            (TradeDirection.BUY, 100, 99, 100.1),
            (TradeDirection.SELL, 100, 101, 100),
            (TradeDirection.SELL, 100, 101, 99.9),
        ],
    )
    def test_stop_absolute__invalid(self, direction, open, current_close, stop):
        trade = TradeFactory(
            direction=direction, open_value=open, current_close_value=current_close
        )
        with pytest.raises(TradeException):
            trade.set_stop_absolute(stop)

    @pytest.mark.parametrize(
        ["direction", "open", "current_close", "stop_relative", "expected_absolute"],
        [
            (TradeDirection.BUY, 100, 99, 1.2, 98.8),
            (TradeDirection.SELL, 100, 101, 0.4, 100.4),
        ],
    )
    def test_stop_relative__valid(
        self,
        mock_trade_provider_update_stop,
        direction,
        open,
        current_close,
        stop_relative,
        expected_absolute,
    ):
        trade = TradeFactory(
            direction=direction, open_value=open, current_close_value=current_close
        )
        trade.set_stop_relative(stop_relative)

        assert trade.absolute_stop == expected_absolute
        assert mock_trade_provider_update_stop.call_args_list == [call(trade=trade)]

    @pytest.mark.parametrize(
        ["direction", "stop_absolute", "current_value"],
        [
            (TradeDirection.BUY, 95, 99),
            (TradeDirection.BUY, 95, 95.1),
            (TradeDirection.SELL, 105, 101),
            (TradeDirection.SELL, 105, 104.9),
        ],
    )
    def test_no_close_before_stop(
        self, mocker, direction, stop_absolute, current_value
    ):
        close_mock = mocker.patch("estrade.trade.Trade.close")
        trade = TradeFactory(
            direction=direction, open_value=100, stop_absolute=stop_absolute
        )

        trade.update(current_close_value=current_value)
        assert close_mock.call_args_list == []

    @pytest.mark.parametrize(
        ["direction", "stop_absolute", "current_value"],
        [
            (TradeDirection.BUY, 95, 95),
            (TradeDirection.BUY, 95, 94.9),
            (TradeDirection.BUY, 95, 80.4),
            (TradeDirection.SELL, 105, 105),
            (TradeDirection.SELL, 105, 105.1),
            (TradeDirection.SELL, 105, 125.5),
        ],
    )
    def test_close_on_stop(self, mocker, direction, stop_absolute, current_value):
        close_mock = mocker.patch("estrade.trade.Trade.close")
        trade = TradeFactory(
            direction=direction, open_value=100, stop_absolute=stop_absolute
        )

        trade.update(current_close_value=current_value)
        assert close_mock.call_args_list == [
            call(
                close_value=current_value,
                meta={"close_reason": "stop_limit_reached"},
            )
        ]


class TestLimit:
    @pytest.fixture
    def mock_trade_provider_update_limit(self, mocker):
        mock = mocker.patch("estrade.trade_provider.BaseTradeProvider.update_limit")

        return mock

    @pytest.mark.parametrize(
        ["direction", "open", "current_close", "limit"],
        [(TradeDirection.BUY, 100, 99, 100.3), (TradeDirection.SELL, 100, 101, 99.8)],
    )
    def test_limit_absolute__valid(
        self, mock_trade_provider_update_limit, direction, open, current_close, limit
    ):
        trade = TradeFactory(
            direction=direction, open_value=open, current_close_value=current_close
        )
        trade.set_limit_absolute(limit)

        assert trade.absolute_limit == limit
        assert mock_trade_provider_update_limit.call_args_list == [call(trade=trade)]

    @pytest.mark.parametrize(
        ["direction", "open", "current_close", "limit"],
        [
            (TradeDirection.BUY, 100, 99, 99),
            (TradeDirection.BUY, 100, 99, 98.99),
            (TradeDirection.SELL, 100, 101, 101),
            (TradeDirection.SELL, 100, 101, 101.01),
        ],
    )
    def test_limit_absolute__invalid(self, direction, open, current_close, limit):
        trade = TradeFactory(
            direction=direction, open_value=open, current_close_value=current_close
        )
        with pytest.raises(TradeException):
            trade.set_limit_absolute(limit)

    @pytest.mark.parametrize(
        ["direction", "open", "current_close", "limit_relative", "expected_absolute"],
        [
            (TradeDirection.BUY, 100, 99, 0.6, 100.6),
            (TradeDirection.SELL, 100, 101, 0.4, 99.6),
        ],
    )
    def test_limit_relative__valid(
        self,
        mock_trade_provider_update_limit,
        direction,
        open,
        current_close,
        limit_relative,
        expected_absolute,
    ):
        trade = TradeFactory(
            direction=direction, open_value=open, current_close_value=current_close
        )
        trade.set_limit_relative(limit_relative)

        assert trade.absolute_limit == expected_absolute
        assert mock_trade_provider_update_limit.call_args_list == [call(trade=trade)]

    @pytest.mark.parametrize(
        ["direction", "limit_absolute", "current_value"],
        [
            (TradeDirection.SELL, 95, 99),
            (TradeDirection.SELL, 95, 95.1),
            (TradeDirection.BUY, 105, 101),
            (TradeDirection.BUY, 105, 104.9),
        ],
    )
    def test_no_close_before_limit(
        self, mocker, direction, limit_absolute, current_value
    ):
        close_mock = mocker.patch("estrade.trade.Trade.close")
        trade = TradeFactory(
            direction=direction, open_value=100, limit_absolute=limit_absolute
        )

        trade.update(current_close_value=current_value)
        assert close_mock.call_args_list == []

    @pytest.mark.parametrize(
        ["direction", "limit_absolute", "current_value"],
        [
            (TradeDirection.SELL, 95, 95),
            (TradeDirection.SELL, 95, 94.9),
            (TradeDirection.SELL, 95, 80.4),
            (TradeDirection.BUY, 105, 105),
            (TradeDirection.BUY, 105, 105.1),
            (TradeDirection.BUY, 105, 125.5),
        ],
    )
    def test_close_on_limit(self, mocker, direction, limit_absolute, current_value):
        close_mock = mocker.patch("estrade.trade.Trade.close")
        trade = TradeFactory(
            direction=direction, open_value=100, limit_absolute=limit_absolute
        )

        trade.update(current_close_value=current_value)
        assert close_mock.call_args_list == [
            call(
                close_value=current_value,
                meta={"close_reason": "stop_limit_reached"},
            )
        ]


class TestClosedQuantities:
    def test_no_close(self):
        trade = TradeFactory()

        assert trade.closed_quantities == 0

    def test_some_closes(self, mocker):
        trade = TradeFactory()
        close_mock1 = mocker.Mock(spec=TradeClose)
        close_mock1.quantity = 3
        close_mock2 = mocker.Mock(spec=TradeClose)
        close_mock2.quantity = 2
        trade.closes = [close_mock2, close_mock1]

        assert trade.closed_quantities == 5


class TestOpenedQuantities:
    @pytest.fixture(autouse=True)
    def mock_closed_quantities(self, mocker):
        mock = mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.closed_quantities",
            new_callable=PropertyMock(return_value=3),
        )
        return mock

    def test_nominal(self):
        trade = TradeFactory(quantity=10)
        assert trade.opened_quantities == 7


class TestClosed:
    @pytest.mark.parametrize(
        ["opened_quantities", "expected_close"],
        [
            pytest.param(1, False, id="not closed"),
            pytest.param(0, True, id="closed"),
        ],
    )
    def test_nominal(self, mocker, opened_quantities, expected_close):
        mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.opened_quantities",
            new_callable=PropertyMock(return_value=opened_quantities),
        )
        trade = TradeFactory()

        assert trade.closed == expected_close


class TestOpenedResultAvg:
    @pytest.fixture(autouse=True)
    def mock_closed(self, mocker):
        mock = mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.closed",
            new_callable=PropertyMock(return_value=False),
        )
        return mock

    def test_closed(self, mocker):
        mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.closed",
            new_callable=PropertyMock(return_value=True),
        )

        trade = TradeFactory()

        assert trade.opened_result_avg == 0

    @pytest.mark.parametrize(
        ["direction", "open", "current", "expected_result"],
        [
            pytest.param(TradeDirection.BUY, 12.5, 20.8, 8.3, id="BUY positive"),
            pytest.param(TradeDirection.BUY, 4.6, 2.7, -1.9, id="BUY negative"),
            pytest.param(TradeDirection.SELL, 4.6, 2.7, 1.9, id="SELL postive"),
            pytest.param(TradeDirection.SELL, 12.5, 20.8, -8.3, id="SELL negative"),
            pytest.param(TradeDirection.SELL, 4.64567, 2.78768, 1.86, id="round"),
        ],
    )
    def test_nominal(self, direction, open, current, expected_result):
        trade = TradeFactory(direction=direction)
        trade.open_value = open
        trade.current_close_value = current

        assert trade.opened_result_avg == expected_result


class TestOpenedResult:
    def test_nominal(self, mocker):
        mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.opened_result_avg",
            new_callable=PropertyMock(return_value=87.36),
        )
        mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.opened_quantities",
            new_callable=PropertyMock(return_value=6),
        )

        trade = TradeFactory()

        assert trade.opened_result == 524.16


class TestClosedResultAvg:
    @pytest.fixture(autouse=True)
    def mock_closed(self, mocker):
        mock = mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.closed",
            new_callable=PropertyMock(return_value=False),
        )
        return mock

    def test_closed(self, mocker):
        mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.closed",
            new_callable=PropertyMock(return_value=True),
        )

        trade = TradeFactory()

        assert trade.closed_result_avg == 0

    def test_nominal(self, mocker):
        mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.closed_quantities",
            new_callable=PropertyMock(return_value=3),
        )

        trade = TradeFactory()

        close_mock1 = mocker.Mock(spec=TradeClose)
        close_mock1.result = 65.89
        close_mock2 = mocker.Mock(spec=TradeClose)
        close_mock2.result = -34.91
        trade.closes = [close_mock2, close_mock1]

        assert trade.closed_result_avg == round((65.89 - 34.91) / 3, 2)


class TestClosedResult:
    @pytest.fixture(autouse=True)
    def mock_closed(self, mocker):
        mock = mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.closed",
            new_callable=PropertyMock(return_value=False),
        )
        return mock

    def test_closed(self, mocker):
        mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.closed",
            new_callable=PropertyMock(return_value=True),
        )

        trade = TradeFactory()

        assert trade.closed_result == 0

    def test_nominal(self, mocker):

        trade = TradeFactory()

        close_mock1 = mocker.Mock(spec=TradeClose)
        close_mock1.result = 65.89
        close_mock2 = mocker.Mock(spec=TradeClose)
        close_mock2.result = -34.91
        trade.closes = [close_mock2, close_mock1]

        assert trade.closed_result == (65.89 - 34.91)


class TestResult:
    def test_nominal(self, mocker):
        mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.opened_result",
            new_callable=PropertyMock(return_value=12.56),
        )
        mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.closed_result",
            new_callable=PropertyMock(return_value=-45.82),
        )

        trade = TradeFactory()
        assert trade.result == 12.56 - 45.82


class TestResultAvg:
    def test_nominal(self, mocker):
        mocker.patch(
            f"{CLASS_TRADE_DEFINITION_PATH}.result",
            new_callable=PropertyMock(return_value=82.767),
        )
        trade = TradeFactory(quantity=4)

        assert trade.result_avg == 20.69


class TestAsDict:
    def test_nominal(self):
        epic = EpicFactory(ref="MY_EPIC_REF")
        strategy = StrategyFactory(ref="MY_STRATEGY")
        trade = TradeFactory(
            ref="MY_TRADE",
            epic=epic,
            direction=TradeDirection.BUY,
            open_datetime=arrow.get("2020-01-01 12:34:56"),
            quantity=5,
            status=TransactionStatus.REFUSED,
            strategy=strategy,
        )

        assert trade.asdict() == {
            "closed_quantities": 0,
            "direction": TradeDirection.BUY,
            "epic": "MY_EPIC_REF",
            "open_date": "2020-01-01 12:34:56",
            "open_quantity": 5,
            "open_value": 101,
            "ref": "MY_TRADE",
            "result": -10,
            "status": TransactionStatus.REFUSED,
            "strategy": "MY_STRATEGY",
        }

    def test_no_strategy(self):
        trade = TradeFactory(strategy=None)
        assert trade.asdict()["strategy"] == "undefined" ""
