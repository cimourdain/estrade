import pytest
from datetime import datetime

from estrade.provider import LiveProvider, Provider
from estrade.trade import Trade
from estrade.exceptions import ProviderException


class TestProvider:

    def test_usage_of_abstract_instance(self):
        # WHEN I instanciate an instance of AProvider
        provider = Provider()

        # THEN market is initated to None
        assert provider.market is None
        # THEN provider is logged
        assert provider.logged

        # THEN no trade is fetched when call of get_open_trades
        assert not provider.get_open_trades()

    def test_call_on_new_tick_with_no_market(self):
        # GIVEN a provider instanciated from mixins method with no market attached
        provider = Provider()

        # WHEN i call the on_new_tick method, then an exception is raised because no market is attached
        with pytest.raises(AttributeError):
            provider.market.on_new_tick(epic_ref='test', bid=1000, ask=1001, datetime=datetime.now())


class TestTradeClass:
    @pytest.mark.parametrize(
        'invalid_trade_class',
        [
            pytest.param(str, id='str trade class'),
            pytest.param('string', id='string trade class'),
            pytest.param({}, id='dict trade class'),
        ]
    )
    def test_invalid_trade_class(self, invalid_trade_class):

        with pytest.raises(ProviderException, match='Trade class .*'):
            Provider(trade_class=invalid_trade_class)

        provider = Provider()
        with pytest.raises(ProviderException, match='Trade class .*'):
            provider.trade_class = invalid_trade_class

    def test_valid_trade_class(self):
        class SubTradeClass(Trade):
            pass

        provider = Provider(trade_class=SubTradeClass)
        assert provider.trade_class == SubTradeClass

        provider = Provider()
        provider.trade_class = SubTradeClass
        assert provider.trade_class == SubTradeClass


class TestLiveProvider:

    def test_abstract_class(self):
        # GIVEN a live provider instanciated from mixins class
        provider = LiveProvider()

        # THEN no market is set on init
        assert provider.market is None
        # THEN the provider is not logged
        assert not provider.logged
        # THEN the list of open trades is empty
        assert not provider.get_open_trades()
