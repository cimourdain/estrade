import pytest

from estrade.exceptions import MarketException

from estrade.epic import Epic
from estrade.strategy import Strategy
from tests.factories import (
    EpicFactory,
    LiveProviderFactory,
    MarketFactory,
    ProviderFactory,
    ReportingFactory,
    StrategyFactory,
    TickFactory,
)


class TestMarket:

    def test_base(self):
        market = MarketFactory()
        assert market
        assert len(market.strategies) == 1
        assert len(market.epics) == 1
        assert len(market.epics[0].strategies) == 1


class TestMarketRef:

    def test_ref(self):
        market = MarketFactory()
        assert market.ref
        assert market.ref[:7] == 'market_'


class TestMarketProvider:

    def test_base(self):
        provider = ProviderFactory()
        market = MarketFactory(provider=provider)
        assert market.provider == provider

    @pytest.mark.parametrize('invalid_provider', [
        pytest.param('string', id='provider string'),
        pytest.param(1, id='provider int'),
        pytest.param([], id='provider list'),
        pytest.param({}, id='provider dict'),
    ])
    def test_invalid_provider(self, invalid_provider):
        with pytest.raises(MarketException):
            MarketFactory(provider=invalid_provider)


class TestMarketTradeManager:

    def test_base(self):
        market = MarketFactory()
        assert market.trade_manager

    def test_auto_create(self):
        market = MarketFactory()
        assert market.trade_manager


class TestOnNewTick:

    def test_base(self, mocker):
        trade_manager_mocker = mocker.patch('estrade.trade_manager.TradeManager.on_new_tick')
        epic_mocker = mocker.spy(Epic, 'on_new_tick')
        strategy_mocker = mocker.spy(Strategy, 'on_new_tick')

        epic1 = EpicFactory(ref='epic1')
        epic2 = EpicFactory(ref='epic2')

        s1 = StrategyFactory(ref='strategy1', epics=[epic1])
        s2 = StrategyFactory(ref='strategy2', epics=[epic2])
        s3 = StrategyFactory(ref='strategy3', epics=[epic1, epic2])

        market = MarketFactory(strategies=[s1, s2, s3])

        tick = TickFactory(epic=epic1)
        market.on_new_tick(tick)
        assert trade_manager_mocker.called_once
        # on new tick was only called for epic1
        assert epic_mocker.call_count == 1
        # on new tick was only called for strategies using epic1
        assert strategy_mocker.call_count == 2


class TestReporting:

    def test_reporting(self):
        market = MarketFactory()
        assert not market.reporting

        market = MarketFactory(reporting=ReportingFactory())
        assert market.reporting


class TestMarketRun:

    def test_base(self, mocker):
        market = MarketFactory()
        provider_generate = mocker.patch.object(market.provider, 'generate_ticks')
        market.run()
        assert provider_generate.called

    def test_run_not_logged(self, mocker):
        # GIVEN a live provider (with a login function that does nothing ==> is not logged)
        provider = LiveProviderFactory()
        mocker.patch.object(provider, 'login', return_value=True)

        # WHEN I add this provider to this function and call the run function
        market = MarketFactory(provider=provider)
        with pytest.raises(MarketException, match=r'.*provider is not logged.*'):
            # THEN an exception is raised because provider is not logged
            market.run()

    def test_run_with_existing_trades(self, mocker):
        # GIVEN a provider returning True to the get_open_trades method
        provider = ProviderFactory()
        mocker.patch.object(provider, 'get_open_trades', return_value=True)

        # WHEN i attach this provider to a market and call the run method
        market = MarketFactory(provider=provider)

        with pytest.raises(MarketException, match=r'.*trades are already open.*'):
            # THEN an exception is raised because trades are already opened
            market.run()
