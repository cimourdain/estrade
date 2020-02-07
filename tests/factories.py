from datetime import datetime

import arrow
import factory
from faker import Faker

from estrade.mixins.candle_set_indicator_mixin import CandleSetIndicatorMixin
from estrade.candle import Candle
from estrade.stop_limit import StopLimitMixinAbsolute, StopLimitMixinRelative
from estrade.trade import Trade
from estrade.trade_manager import TradeManager
from estrade import CandleSet
from estrade.epic import Epic
from estrade import Market
from estrade.provider import LiveProvider, Provider
from estrade import ReportingMixin
from estrade import Strategy
from estrade import Tick
from estrade import ExponentialMovingAverage, SimpleMovingAverage

fake = Faker()


class ProviderFactory(Provider):

    def generate(self, ticks_dicts):
        for tick in ticks_dicts:
            self.market.on_new_tick(
                Tick(
                    epic=self.market.get_epic(tick['epic_ref']),
                    bid=tick['bid'],
                    ask=tick['ask'],
                    datetime=tick['datetime']
                )
            )


class LiveProviderFactory(LiveProvider):

    def login(self):
        self.logged = True

    def open_trade(self, trade):
        pass

    def close_trade(self, trade):
        pass


class CandleSetFactory(factory.Factory):
    class Meta:
        model = CandleSet

    timeframe = '1minutes'


class CandleSetIndicatorMixin(CandleSetIndicatorMixin):

    def on_new_tick(self, tick):
        pass

    def on_new_candle(self, new_candle):
        pass

    def on_candle_close(self, closed_candle):
        pass


class CandleSetIndicatorFactory(factory.Factory):
    class Meta:
        model = CandleSetIndicatorMixin

    name = 'test indicator'


class SimpleMovingAverageFactory(factory.Factory):
    class Meta:
        model = SimpleMovingAverage

    name = 'mm3'
    periods = 3


class ExponentialMovingAverageFactory(factory.Factory):
    class Meta:
        model = ExponentialMovingAverage

    name = 'ema3'
    periods = 3


class EpicFactory(factory.Factory):
    class Meta:
        model = Epic

    ref = None
    timezone = 'UTC'
    candle_sets = []


class StrategyFactory(factory.Factory):
    class Meta:
        model = Strategy

    epics = [EpicFactory()]


class MarketFactory(factory.Factory):
    class Meta:
        model = Market

    strategies = [StrategyFactory(epics=[EpicFactory()])]
    provider = ProviderFactory()


class TickFactory(factory.Factory):
    class Meta:
        model = Tick

    epic = EpicFactory()
    datetime = arrow.get(datetime(year=2019, month=1, day=1, hour=0, minute=0, second=0), 'UTC')
    bid = 999
    ask = 1001


class CandleFactory(factory.Factory):
    class Meta:
        model = Candle

    timeframe = '5minutes'
    epic_ref = EpicFactory().ref
    open_tick = TickFactory()


class TradeManagerFactory(factory.Factory):
    class Meta:
        model = TradeManager

    market = MarketFactory()


class TradeFactory(factory.Factory):
    class Meta:
        model = Trade

    trade_manager = None
    strategy = StrategyFactory()
    tick = TickFactory()
    quantity = 1
    direction = 1


class StopLimitAbsoluteFactory(factory.Factory):
    class Meta:
        model = StopLimitMixinAbsolute

    type_ = 'STOP'
    trade = TradeFactory()
    value = 990


class StopLimitRelativeFactory(factory.Factory):
    class Meta:
        model = StopLimitMixinRelative

    type_ = 'STOP'
    trade = TradeFactory()
    value = 10


class ReportingMixinFactory(ReportingMixin):

    def on_new_tick(self, tick):
        pass

    def on_trade_update(self, trade):
        pass

    def on_run_end(self):
        pass
