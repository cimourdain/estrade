from estrade.trade_provider import BaseTradeProvider, TradeProviderBacktests
from tests.unit.factories.factory import Factory, post_build


class TradeProviderFactory(Factory):
    class Meta:
        model = BaseTradeProvider


class TradeProviderBacktestsFactory(Factory):
    class Meta:
        model = TradeProviderBacktests


class TradeProviderImplementedFactory(TradeProviderFactory):
    @post_build
    def implement_required(trade_provider):
        def open_trade_request(self, trade):
            return trade

        def close_trade_request(self, trade_close):
            return trade_close

        trade_provider.open_trade_request = open_trade_request
        trade_provider.close_trade_request = close_trade_request
