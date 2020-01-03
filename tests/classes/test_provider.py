from datetime import datetime

import arrow

from tests.factories import (
    LiveProviderFactory,
    MarketFactory,
    ProviderFactory
)


class TestProvider:

    def test_generate_ticks(self, mocker):
        # GIVEN a provider attached to a market
        provider = ProviderFactory()
        market = MarketFactory(provider=provider)
        assert len(market.strategies) == 1
        assert len(market.epics) == 1
        assert len(market.epics[0].strategies) == 1

        # GIVEN a mocker to spy if market.on_new_tick is called
        market_on_new_tick = mocker.spy(market, 'on_new_tick')

        # WHEN i generate ticks from provider
        provider.generate_ticks(ticks_dicts=[
            {
                'epic_ref': market.epics[0].ref,
                'bid': 999,
                'ask': 1000,
                'datetime': arrow.get(datetime(year=2019, month=1, day=1, hour=0, minute=0, second=0), 'UTC'),
            }
        ])
        assert market_on_new_tick.called


class TestLiveProvider:

    def test_subscribe(self, mocker):
        provider = LiveProviderFactory()
        login_mocker = mocker.patch.object(provider, 'login', return_value=True)
        generate_ticks_mocker = mocker.patch.object(provider, 'generate_ticks', return_value=True)
        market = MarketFactory(provider=provider)
        provider.logged = True
        market.run()
        login_mocker.assert_called_once()
        generate_ticks_mocker.assert_called_once()
