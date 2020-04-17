from estrade.graph.indicators.rsi import RSI, RSIValue
from tests.unit.factories.factory import Factory, post_build
from tests.unit.factories.graph.frame_set import FrameFactory, FrameSetFactory


class RSIFactory(Factory):
    class Meta:
        model = RSI

    periods = 7


class RSIWithFrameSetFactory(RSIFactory):
    @post_build
    def add_frame_set(rsi):
        rsi.set_frame_set(FrameSetFactory())


class RSIValueFactory(Factory):
    class Meta:
        model = RSIValue

    frame = FrameFactory()
    indicator = RSIWithFrameSetFactory()
