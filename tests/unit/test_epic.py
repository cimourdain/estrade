from datetime import date, datetime, time
from unittest.mock import call

import arrow
import pytest
import pytz
from dateutil import tz

from estrade import BaseStrategy, BaseTradeProvider
from estrade.enums import TradeDirection
from estrade.exceptions import EpicException
from estrade.mixins import RefMixin
from estrade.trade_provider import TradeProviderBacktests
from tests.unit.factories import EpicFactory, TickFactory, TradeFactory


CLASS_DEFINITION_PATH = "estrade.epic.Epic"


class TestInheritance:
    def test_ref_mixin__call(self, mocker):
        ref_mock = mocker.patch.object(RefMixin, "__init__", wraps=RefMixin.__init__)
        epic = EpicFactory(ref="test_ref")

        assert call(epic, "test_ref") in ref_mock.call_args_list


class TestInit:
    class TestArguments:
        def test_timezone__default(self):
            epic = EpicFactory()

            assert epic.timezone == "UTC"

        def test_timezone_custom__valid(self):
            for timezone in pytz.all_timezones:
                epic = EpicFactory(timezone=timezone)

                assert epic.timezone == timezone

        @pytest.mark.parametrize(
            ["invalid_timezone"],
            [
                pytest.param(None, id="None timezone"),
                pytest.param("test", id="invalid string"),
            ],
        )
        def test_timezone_custom__invalid(self, invalid_timezone):
            with pytest.raises(EpicException):
                EpicFactory(timezone=invalid_timezone)

        def test_open_time__default(self):
            epic = EpicFactory()

            assert epic.open_time == time(9, 30)

        def test_open_time__custom(self):
            epic = EpicFactory(open_time=time(12, 45))

            assert epic.open_time == time(12, 45)

        def test_close_time__default(self):
            epic = EpicFactory()

            assert epic.close_time == time(17, 30)

        def test_close_time__custom(self):
            epic = EpicFactory(close_time=time(12, 45))

            assert epic.close_time == time(12, 45)

        def test_trade_days__default(self):
            epic = EpicFactory()

            assert epic.trade_days == [0, 1, 2, 3, 4]

        def test_trade_days__custom(self):
            epic = EpicFactory(trade_days=[2, 5, 6])

            assert epic.trade_days == [2, 5, 6]

        def test_holidays__default(self):
            epic = EpicFactory()

            assert epic.holidays == []

        def test_holidays__custom(self):
            epic = EpicFactory(holidays=[date(2020, 1, 3)])

            assert epic.holidays == [date(2020, 1, 3)]

        def test_trade_provider__default(self):
            epic = EpicFactory()

            assert isinstance(epic.trade_provider, TradeProviderBacktests)

        def test_trade_provider__custom(self):
            class MyCustomTradeProvider(BaseTradeProvider):
                def open_trade_request(self, trade):
                    pass

                def close_trade_request(self, trade_close):
                    pass

            custom_trade_provider = MyCustomTradeProvider(ref="MY_PROVIDER")
            epic = EpicFactory(trade_provider=custom_trade_provider)

            assert isinstance(epic.trade_provider, MyCustomTradeProvider)

    class TestAttributesDefaults:
        def test_last_tick(self):
            epic = EpicFactory()

            assert epic.last_tick is not None

        def test_framesets(self):
            epic = EpicFactory()

            assert epic.frame_sets == {}


class TestMarketOpenProperty:
    def test_nominal(self):
        tick = TickFactory(datetime=arrow.get("2020-01-01 12:00:00"))
        epic = EpicFactory()
        epic.on_new_tick(tick)

        assert epic.market_open is True

    def test_before_open(self):
        tick = TickFactory(datetime=arrow.get("2020-01-01 08:59:59"))
        epic = EpicFactory(open_time=time(9, 0))
        epic.on_new_tick(tick)

        assert epic.market_open is False

    def test_after_close(self):
        tick = TickFactory(datetime=arrow.get("2020-01-01 18:01:00"))
        epic = EpicFactory(close_time=time(18, 0))
        epic.on_new_tick(tick)

        assert epic.market_open is False

    def test_out_of_trade_days(self):
        tick = TickFactory(datetime=arrow.get("2020-01-01 12:00:00"))
        epic = EpicFactory(trade_days=[0, 1, 3, 4, 5])
        epic.on_new_tick(tick)

        assert epic.market_open is False

    def test_in_holidays(self):
        tick = TickFactory(datetime=arrow.get("2020-01-01 12:00:00"))
        epic = EpicFactory(holidays=[date(2020, 1, 1)])
        epic.on_new_tick(tick)

        assert epic.market_open is False


class TestAddFrameSet:
    def test_add_to_frame_sets(self, mocker):
        frame_set_mock = mocker.Mock()
        frame_set_mock.ref = "fs_ref"

        epic = EpicFactory()
        epic.add_frame_set(frame_set_mock)

        assert epic.frame_sets["fs_ref"] == frame_set_mock

    def test_update_frameset_epic(self, mocker):
        frame_set_mock = mocker.Mock()
        frame_set_mock.ref = "fs_ref"

        epic = EpicFactory()
        epic.add_frame_set(frame_set_mock)

        assert frame_set_mock.epic == epic

    def test_add_existing_ref(self, mocker):
        epic = EpicFactory()
        epic.frame_sets = {"MY_REF": "my_frame_set"}

        frame_set_mock = mocker.Mock()
        frame_set_mock.ref = "MY_REF"

        with pytest.raises(EpicException):
            epic.add_frame_set(frame_set_mock)


class TestAddStrategy:
    def test_add_strategy(self, mocker):
        strategy_mock = mocker.Mock()
        strategy_mock.ref = "strategy_ref"
        strategy_mock.epics = {}

        epic = EpicFactory()
        epic.add_strategy(strategy_mock)

        assert epic.strategies["strategy_ref"] == strategy_mock

    def test_update_strategy(self, mocker):
        strategy_mock = mocker.Mock()
        strategy_mock.ref = "strategy_ref"
        strategy_mock.epics = {}

        epic = EpicFactory()
        epic.add_strategy(strategy_mock)

        assert strategy_mock.epics[epic.ref] == epic

    def test_add_existing_ref(self, mocker):
        epic = EpicFactory()
        epic.strategies = {"MY_REF": "my_strategy"}

        strategy_mock = mocker.Mock()
        strategy_mock.ref = "MY_REF"

        with pytest.raises(EpicException):
            epic.add_strategy(strategy_mock)


class TestOnNewTick:
    def test_anterior_tick(self):
        epic = EpicFactory()
        last_tick = TickFactory(datetime=arrow.get("2020-01-01 12:34:56"))
        epic.last_tick = last_tick

        new_tick = TickFactory(datetime=arrow.get("2020-01-01 12:34:55"))

        with pytest.raises(EpicException):
            epic.on_new_tick(new_tick)

    def test_update_last_tick(self):
        epic = EpicFactory()
        tick = TickFactory()
        epic.on_new_tick(tick)

        assert epic.last_tick == tick

    def test_convert_tick_datetime(self):
        epic = EpicFactory(timezone="Asia/Tokyo")

        tz_NY = pytz.timezone("America/New_York")
        datetime_NY = datetime.now(tz_NY)
        tick = TickFactory(datetime=datetime_NY)

        epic.on_new_tick(tick)

        # datetime is converted to epic timezone
        assert epic.last_tick.datetime.tzinfo == tz.gettz(epic.timezone)

    def test_update_trades(self, mocker):
        epic = EpicFactory()

        trade = TradeFactory(direction=TradeDirection.BUY, quantity=4, epic=epic)
        epic.trade_provider.open_trade(trade)
        trade_update_mock = mocker.patch.object(trade, "update_from_tick")

        new_tick = TickFactory()
        epic.on_new_tick(new_tick)

        assert trade_update_mock.call_args_list == [call(new_tick)]

    def test_update_frame_sets(self, mocker):
        epic = EpicFactory()

        frame_set_mock = mocker.Mock()
        epic.frame_sets["test"] = frame_set_mock

        new_tick = TickFactory()

        epic.on_new_tick(new_tick)

        assert frame_set_mock.on_new_tick.call_args_list == [call(new_tick)]

    def test_update_strategies_call_on_every_tick__nominal(self, mocker):
        epic = EpicFactory()

        strategy_mock = mocker.Mock(spec=BaseStrategy)
        strategy_mock.is_active.return_value = True
        epic.strategies["test"] = strategy_mock

        new_tick = TickFactory()

        epic.on_new_tick(new_tick)

        assert strategy_mock.on_every_tick.call_args_list == [call(epic)]

    def test_update_strategies_call_on_every_tick__inactive_strategy(self, mocker):
        epic = EpicFactory()

        strategy_mock = mocker.Mock(spec=BaseStrategy)
        strategy_mock.is_active.return_value = False
        epic.strategies["test"] = strategy_mock

        new_tick = TickFactory()

        epic.on_new_tick(new_tick)

        assert strategy_mock.on_every_tick.call_args_list == []

    def test_update_strategies_call_on_market_close__nominal(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.is_market_open", return_value=False)
        epic = EpicFactory()
        epic.market_open = True

        strategy_mock = mocker.Mock(spec=BaseStrategy)
        strategy_mock.is_active.return_value = True
        epic.strategies["test"] = strategy_mock

        new_tick = TickFactory()

        epic.on_new_tick(new_tick)

        assert strategy_mock.on_market_close.call_args_list == [call(epic)]

    @pytest.mark.parametrize(
        ["strategy_is_active", "market_open_before_tick", "market_open_after_tick"],
        [
            pytest.param(True, False, False, id="strategy active, market closed"),
            pytest.param(True, False, True, id="strategy active, market opening"),
            pytest.param(
                True, True, True, id="strategy active, market open before and after"
            ),
            pytest.param(False, False, False, id="strategy inactive, market closed"),
            pytest.param(False, False, True, id="strategy inactive, market opening"),
            pytest.param(
                False, True, True, id="strategy inactive, market open before and after"
            ),
            pytest.param(False, True, False, id="strategy inactive, market closing"),
        ],
    )
    def test_update_strategies_call_on_market_close__no_call_expected(
        self,
        mocker,
        market_open_before_tick,
        market_open_after_tick,
        strategy_is_active,
    ):
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.is_market_open",
            return_value=market_open_after_tick,
        )
        epic = EpicFactory()
        epic.market_open = market_open_before_tick

        strategy_mock = mocker.Mock(spec=BaseStrategy)
        strategy_mock.is_active.return_value = strategy_is_active
        epic.strategies["test"] = strategy_mock

        new_tick = TickFactory()

        epic.on_new_tick(new_tick)

        assert strategy_mock.on_market_close.call_args_list == []

    def test_update_strategies_call_on_market_open__nominal(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.is_market_open", return_value=True)
        epic = EpicFactory()
        epic.market_open = False

        strategy_mock = mocker.Mock(spec=BaseStrategy)
        strategy_mock.is_active.return_value = True
        epic.strategies["test"] = strategy_mock

        new_tick = TickFactory()

        epic.on_new_tick(new_tick)

        assert strategy_mock.on_market_open.call_args_list == [call(epic)]

    @pytest.mark.parametrize(
        ["strategy_is_active", "market_open_before_tick", "market_open_after_tick"],
        [
            pytest.param(True, False, False, id="strategy active, market closed"),
            pytest.param(
                True, True, True, id="strategy active, market open before and after"
            ),
            pytest.param(True, True, False, id="strategy active, market closing"),
            pytest.param(False, False, False, id="strategy inactive, market closed"),
            pytest.param(False, False, True, id="strategy inactive, market opening"),
            pytest.param(
                False, True, True, id="strategy inactive, market open before and after"
            ),
            pytest.param(False, True, False, id="strategy inactive, market closing"),
        ],
    )
    def test_update_strategies_call_on_market_open__no_call_expected(
        self,
        mocker,
        market_open_before_tick,
        market_open_after_tick,
        strategy_is_active,
    ):
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.is_market_open",
            return_value=market_open_after_tick,
        )
        epic = EpicFactory()
        epic.market_open = market_open_before_tick

        strategy_mock = mocker.Mock(spec=BaseStrategy)
        strategy_mock.is_active.return_value = strategy_is_active
        epic.strategies["test"] = strategy_mock

        new_tick = TickFactory()

        epic.on_new_tick(new_tick)

        assert strategy_mock.on_market_open.call_args_list == []


class TestToString:
    def test_base(self):
        epic = EpicFactory(ref="MY_EPIC", timezone="Europe/Paris")
        assert str(epic) == "Epic: MY_EPIC on timezone Europe/Paris"


class TestOpenTrade:
    @pytest.fixture(autouse=True)
    def trade_open_from_epic_mock(self, mocker):
        mock = mocker.patch(
            "estrade.trade.Trade.open_from_epic", return_value="my_new_trade"
        )
        return mock

    def test_call_open_trade(self, mocker, trade_open_from_epic_mock):
        trade_provider_mock = mocker.Mock()

        epic = EpicFactory(trade_provider=trade_provider_mock)

        epic.open_trade(test="test")

        assert trade_open_from_epic_mock.call_args_list == [
            call(epic=epic, test="test")
        ]

    def test_call_trade_provider(self, mocker):
        trade_provider_mock = mocker.Mock()

        epic = EpicFactory(trade_provider=trade_provider_mock)

        epic.open_trade(test="test")

        assert trade_provider_mock.open_trade.call_args_list == [call("my_new_trade")]

    def test_response(self, mocker):
        trade_provider_mock = mocker.Mock()

        epic = EpicFactory(trade_provider=trade_provider_mock)

        response = epic.open_trade(test="test")

        assert response == "my_new_trade"


class TestCloseTrade:
    def test_call_open_trade(self, mocker):
        trade_provider_mock = mocker.Mock()
        trade_mock = mocker.Mock()
        trade_mock.close_from_epic.return_value = "my_trade_close"

        epic = EpicFactory(trade_provider=trade_provider_mock)

        epic.close_trade(trade=trade_mock, test="test")

        assert trade_mock.close_from_epic.call_args_list == [call(test="test")]

    def test_call_trade_provider(self, mocker):
        trade_provider_mock = mocker.Mock()
        trade_mock = mocker.Mock()
        trade_mock.close_from_epic.return_value = "my_trade_close"

        epic = EpicFactory(trade_provider=trade_provider_mock)

        epic.close_trade(trade=trade_mock, test="test")

        assert trade_provider_mock.close_trade.call_args_list == [
            call("my_trade_close")
        ]

    def test_response(self, mocker):
        trade_provider_mock = mocker.Mock()
        trade_mock = mocker.Mock()
        trade_mock.close_from_epic.return_value = "my_trade_close"

        epic = EpicFactory(trade_provider=trade_provider_mock)

        response = epic.close_trade(trade=trade_mock, test="test")

        assert response == "my_trade_close"


class TestGetFrame:
    def test_nominal(self):
        epic = EpicFactory()
        frame_set_mock = ["frame1", "frame2"]
        epic.frame_sets = {"my_fs": frame_set_mock}

        assert epic.get_frame("my_fs") == "frame2"

    def test_offset(self):
        epic = EpicFactory()
        frame_set_mock = ["frame1", "frame2"]
        epic.frame_sets = {"my_fs": frame_set_mock}

        assert epic.get_frame("my_fs", 1) == "frame1"

    def test_offset__invalid(self):
        epic = EpicFactory()
        frame_set_mock = ["frame1", "frame2"]
        epic.frame_sets = {"my_fs": frame_set_mock}

        assert epic.get_frame("my_fs", 2) is None


class TestGetIndicator:
    def test_no_frame(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.get_frame", return_value=None)
        epic = EpicFactory()

        assert epic.get_indicator_value("my_fs", "my_indicator") is None

    def test_get_frame_call(self, mocker):
        get_frame_mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.get_frame", return_value=None
        )
        epic = EpicFactory()

        epic.get_indicator_value("my_fs", "my_indicator", 55)

        assert get_frame_mock.call_args_list == [call(frame_set_ref="my_fs", offset=55)]

    def test_nominal(self, mocker):
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.get_frame",
            return_value={"my_indicator": "indicator_value"},
        )
        epic = EpicFactory()

        assert epic.get_indicator_value("my_fs", "my_indicator") == "indicator_value"
