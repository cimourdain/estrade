from estrade.graph.indicators.candle_set import (
    BaseCandle,
    CandleSet,
    HeikinAshiCandle,
    JapaneseCandle,
)
from tests.unit.factories.factory import Factory
from tests.unit.factories.graph.frame_set import FrameFactory


class CandleSetFactory(Factory):
    class Meta:
        model = CandleSet


class BaseCandleFactory(Factory):
    class Meta:
        model = BaseCandle

    frame = FrameFactory()
    indicator = CandleSetFactory()


class HeikinAshiCandleFactory(BaseCandleFactory):
    class Meta:
        model = HeikinAshiCandle


class JapaneseCandleFactory(BaseCandleFactory):
    class Meta:
        model = JapaneseCandle
