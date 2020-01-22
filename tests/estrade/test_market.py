from unittest.mock import call

import pytest

from estrade.exceptions import (
    MarketException,
    TickException,
)
from estrade.trade_manager import TradeManager
from tests.factories import (
    CandleGreenFactory,
    CandleRedFactory,
    CandleSetFactory,
    EpicFactory,
    MarketFactory,
    ProviderFactory,
    StrategyFactory,
    TickFactory,
)


class TestReference:
    def test_creation(self):
        market = MarketFactory()
        assert market.ref is not None

    def test_explicit_ref(self):
        market = MarketFactory(ref='test_market')
        assert market.ref == 'test_market'


class TestEpics:
    def test_creation(self):
        market = MarketFactory()
        assert len(market.epics) == 0

    def test_add_epic(self):
        market = MarketFactory()
        epic = EpicFactory(market=market)
        market.epics.append(epic)

        assert market.epics[0] == epic
        assert epic.market == market

    def test_add_multiple_epics(self):
        market = MarketFactory()

        epics = [EpicFactory(market=market) for _ in range(0, 10)]

        assert market.epics == epics
        for e in epics:
            assert e.market == market

    def test_get_epic__ok(self):
        market = MarketFactory()
        epics = [EpicFactory(market=market) for _ in range(0, 10)]

        for e in epics:
            assert market.get_epic(e.ref) == e

    def test_get_epic__nok(self):
        market = MarketFactory()
        [EpicFactory(market=market) for _ in range(0, 3)]

        with pytest.raises(MarketException):
            market.get_epic('undefined')

    def test_epics_ref(self):
        market = MarketFactory()
        epics = [EpicFactory(market=market) for _ in range(0, 10)]

        assert market.epics_refs == [e.ref for e in epics]


class TestStrategies:
    def test_creation(self):
        market = MarketFactory()
        assert market.strategies == []

    def test_add_unique_strategy(self):
        market = MarketFactory()
        strategy = StrategyFactory(market=market)

        assert market.strategies == [strategy]

    def test_add_multiple_strategies(self):
        market = MarketFactory()
        strategies = [StrategyFactory(market=market) for _ in range(10)]

        assert market.strategies == strategies


class TestTradeManager:
    def test_creation(self):
        market = MarketFactory()

        assert isinstance(market.trade_manager, TradeManager)

        assert market.trade_manager.market == market


class TestProvider:
    def test_creation(self):
        market = MarketFactory()
        assert market.provider is None

    def test_association(self):
        market = MarketFactory()
        provider = ProviderFactory(market=market)

        assert market.provider == provider
        assert provider.market == market


class TestOnNewTick:
    @pytest.fixture(autouse=True)
    def update_trades_mock(self, mocker):
        return mocker.patch(
            'estrade.trade_manager.TradeManager.on_new_tick',
            return_value=None,
        )

    @pytest.fixture(autouse=True)
    def update_epic_mock(self, mocker):
        return mocker.patch(
            'estrade.epic.Epic.on_new_tick',
            return_value=None,
        )

    @pytest.fixture(autouse=True)
    def update_strategy_mock(self, mocker):
        return mocker.patch(
            'estrade.strategy.Strategy.on_new_tick',
            return_value=None,
        )

    @pytest.mark.parametrize(
        ['invalid_tick'],
        [
            pytest.param(None, id='None tick'),
            pytest.param({}, id='empty dict tick'),
            pytest.param(object(), id='object tick'),
        ]
    )
    def test_invalid_tick(self, invalid_tick):
        market = MarketFactory()
        with pytest.raises(TickException):
            market.on_new_tick(invalid_tick)

    def test_update_trades(self, update_trades_mock):
        market = MarketFactory()

        tick = TickFactory()
        market.on_new_tick(tick)
        assert update_trades_mock.call_args_list == [call(tick=tick)]

    def test_update_only_tick_epic(self, mocker):
        market = MarketFactory()
        epic1 = EpicFactory(market=market)
        epic2 = EpicFactory(market=market)

        update_epic1_mock = mocker.patch.object(epic1, 'on_new_tick')
        update_epic2_mock = mocker.patch.object(epic2, 'on_new_tick')

        tick = TickFactory(epic=epic2)
        market.on_new_tick(tick)

        assert update_epic1_mock.call_args_list == []
        assert update_epic2_mock.call_args_list == [call(tick=tick)]

    def test_update_only_strategy(self, mocker):
        market = MarketFactory()
        epic1 = EpicFactory(market=market)
        epic2 = EpicFactory(market=market)

        strategy1 = StrategyFactory(market=market, epics=[epic1])
        strategy2 = StrategyFactory(market=market, epics=[epic2])
        strategy3 = StrategyFactory(market=market, epics=[epic1, epic2])

        update_strategy1_mock = mocker.patch.object(strategy1, 'on_new_tick')
        update_strategy2_mock = mocker.patch.object(strategy2, 'on_new_tick')
        update_strategy3_mock = mocker.patch.object(strategy3, 'on_new_tick')

        tick = TickFactory(epic=epic2)
        market.on_new_tick(tick)

        assert update_strategy1_mock.call_args_list == []
        assert update_strategy2_mock.call_args_list == [call(tick=tick)]
        assert update_strategy3_mock.call_args_list == [call(tick=tick)]


class TestOnNewCandle:
    @pytest.fixture(autouse=True)
    def mock_trade_manager_on_new_tick(self, mocker):
        return mocker.patch('estrade.trade_manager.TradeManager.on_new_tick')

    @pytest.fixture(autouse=True)
    def mock_trade_manager_on_new_candle(self, mocker):
        return mocker.patch('estrade.trade_manager.TradeManager.on_new_ticks_high_low')

    @pytest.fixture(autouse=True)
    def mock_epic_on_new_tick(self, mocker):
        return mocker.patch('estrade.epic.Epic.on_new_tick')

    def test_epic_updated_with_all_ticks(self, mocker):
        market = MarketFactory()

        epic = EpicFactory(market=market)
        CandleSetFactory(timeframe='5minutes', epic=epic)

        epic_on_new_tick_mock = mocker.patch.object(epic, 'on_new_tick')
        candle = CandleGreenFactory(
            timeframe='5minutes',
            epic=epic,
        )
        market.on_new_candle(candle)
        assert epic_on_new_tick_mock.call_args_list == \
               [call(tick=tick) for tick in candle.ticks]

    @pytest.mark.parametrize(
        ['candle_factory'],
        [
            pytest.param(CandleGreenFactory, id='green'),
            pytest.param(CandleRedFactory, id='red'),
        ]
    )
    def test_call_trade_manager_on_green_candle(
            self,
            candle_factory,
            mock_trade_manager_on_new_tick,
            mock_trade_manager_on_new_candle
    ):
        market = MarketFactory()
        epic = EpicFactory(market=market)
        CandleSetFactory(timeframe='5minutes', epic=epic)

        candle = candle_factory(
            timeframe='5minutes',
            epic=epic,
        )
        market.on_new_candle(candle)
        assert mock_trade_manager_on_new_tick.call_args_list == [
            call(tick=candle.ticks[0]),
            call(tick=candle.ticks[-1])
        ]
        assert mock_trade_manager_on_new_candle.call_args_list == [
            call(epic=epic, low=candle.low_tick, high=candle.high_tick)
        ]

    def test_invalid_candle(self):
        market = MarketFactory()
        epic = EpicFactory(market=market)
        CandleSetFactory(timeframe='5minutes', epic=epic)

        candle = CandleGreenFactory(timeframe='21ticks', epic=epic)
        with pytest.raises(MarketException):
            market.on_new_candle(candle)


class TestRun:
    @pytest.fixture(autouse=True)
    def mock_trade_manager_add_strategies(self, mocker):
        return mocker.patch('estrade.trade_manager.TradeManager.add_strategies')

    @pytest.fixture(autouse=True)
    def mock_provider_login(self, mocker):
        return mocker.patch('estrade.provider.Provider.login', return_value=True)

    @pytest.fixture(autouse=True)
    def mock_provider_get_opened_trades(self, mocker):
        return mocker.patch(
            'estrade.provider.Provider.get_open_trades',
            return_value=[]
        )

    @pytest.fixture(autouse=True)
    def mock_provider_generate(self, mocker):
        return mocker.patch('estrade.provider.Provider.generate_ticks')

    @pytest.fixture(autouse=True)
    def mock_fire_events(self, mocker):
        return mocker.patch('estrade.market.Market.fire')

    def test_missing_provider(self):
        market = MarketFactory()
        with pytest.raises(MarketException):
            market.run()

    def test_add_strategy_called(self, mock_trade_manager_add_strategies):
        market = MarketFactory()
        ProviderFactory(market=market)
        market.run()

        assert mock_trade_manager_add_strategies.call_args_list == [call()]

    def test_login__ok(self, mock_provider_login):
        market = MarketFactory()
        ProviderFactory(market=market, requires_login=True)
        market.run()

        assert mock_provider_login.call_args_list == [call()]

    def test_login__nok(self, mocker):
        market = MarketFactory()
        provider = ProviderFactory(market=market, requires_login=True)
        mock_provider_login_false = mocker.patch.object(
            provider,
            'login',
            return_value=False
        )
        with pytest.raises(MarketException):
            market.run()

        assert mock_provider_login_false.call_args_list == [call()]

    def test_generate_called(self, mock_provider_generate):
        market = MarketFactory()
        ProviderFactory(market=market)

        market.run()

        assert mock_provider_generate.call_args_list == [call()]

    def test_call_get_open_trades__ok(self, mock_provider_get_opened_trades):
        market = MarketFactory()
        ProviderFactory(market=market)

        market.run()

        assert mock_provider_get_opened_trades.call_args_list == [call()]

    def test_call_get_open_trades__nok(self, mocker):
        market = MarketFactory()
        provider = ProviderFactory(market=market)
        mock_provider_get_opened_trades = mocker.patch.object(
            provider,
            'get_open_trades',
            return_value=[1, 2, 3]
        )

        with pytest.raises(MarketException):
            market.run()

        assert mock_provider_get_opened_trades.call_args_list == [call()]
