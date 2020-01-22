from datetime import datetime, timedelta

import arrow
import factory

from estrade.candle import Candle
from estrade.candle_set import CandleSet
from estrade.epic import Epic
from estrade.market import Market
from estrade.provider import Provider
from estrade.strategy import Strategy
from estrade.tick import Tick


class MarketFactory(factory.Factory):
    class Meta:
        model = Market


DEFAULT_MARKET = MarketFactory()


class EpicFactory(factory.Factory):
    class Meta:
        model = Epic

    market = DEFAULT_MARKET


DEFAULT_EPIC = EpicFactory()


class CandleSetFactory(factory.Factory):
    class Meta:
        model = CandleSet

    epic = DEFAULT_EPIC
    timeframe = '5minutes'


class StrategyFactory(factory.Factory):
    class Meta:
        model = Strategy

    market = DEFAULT_MARKET
    epics = [DEFAULT_EPIC]


class ProviderFactory(factory.Factory):
    class Meta:
        model = Provider

    market = DEFAULT_MARKET


class TickFactory(factory.Factory):
    class Meta:
        model = Tick

    epic = DEFAULT_EPIC
    datetime = arrow.get(
        datetime(year=2019, month=1, day=1, hour=0, minute=0, second=0), 'UTC'
    )
    bid = 999
    ask = 1001


class CandleFactory(factory.Factory):
    class Meta:
        model = Candle

    timeframe = '5minutes'
    epic_ref = DEFAULT_EPIC.ref
    open_tick = TickFactory()


def CandleFullFactory(timeframe, epic=DEFAULT_EPIC, ticks=[], close=False):

    candle = CandleFactory(
        timeframe=timeframe,
        epic_ref=epic.ref,
        open_tick=ticks[0]
    )
    for tick in ticks[1:]:
        candle.on_new_tick(tick=tick)

    if close:
        candle.close_candle()

    return candle


def CandleGreenFactory(timeframe, epic=DEFAULT_EPIC, close=False, first_tick=None):

    if not first_tick:
        first_tick = TickFactory(epic=epic)

    ticks = [
        first_tick,
        TickFactory(
            epic=epic,
            datetime=first_tick.datetime + timedelta(seconds=20),
            bid=first_tick.bid + 10,
            ask=first_tick.ask + 10,
        ),
        TickFactory(
            epic=epic,
            datetime=first_tick.datetime + timedelta(seconds=60),
            bid=first_tick.bid - 10,
            ask=first_tick.ask - 10,
        ),
        TickFactory(
            epic=epic,
            datetime=first_tick.datetime + timedelta(seconds=120),
            bid=first_tick.bid + 5,
            ask=first_tick.ask + 5,
        ),
    ]
    return CandleFullFactory(timeframe=timeframe, epic=epic, ticks=ticks, close=close)


def CandleRedFactory(timeframe, epic=DEFAULT_EPIC, close=False, first_tick=None):

    if not first_tick:
        first_tick = TickFactory(epic=epic)

    ticks = [
        first_tick,
        TickFactory(
            epic=epic,
            datetime=first_tick.datetime + timedelta(seconds=20),
            bid=first_tick.bid - 10,
            ask=first_tick.ask - 10,
        ),
        TickFactory(
            epic=epic,
            datetime=first_tick.datetime + timedelta(seconds=60),
            bid=first_tick.bid + 10,
            ask=first_tick.ask + 10,
        ),
        TickFactory(
            epic=epic,
            datetime=first_tick.datetime + timedelta(seconds=120),
            bid=first_tick.bid - 5,
            ask=first_tick.ask - 5,
        ),
    ]
    return CandleFullFactory(timeframe=timeframe, epic=epic, ticks=ticks, close=close)
