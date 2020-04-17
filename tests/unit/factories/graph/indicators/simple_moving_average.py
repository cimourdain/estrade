from estrade.graph.indicators.simple_moving_average import (
    SimpleMovingAverage,
    SimpleMovingAverageValue,
)
from tests.unit.factories.factory import Factory
from tests.unit.factories.graph.frame_set import FrameFactory


class SimpleMovingAverageFactory(Factory):
    class Meta:
        model = SimpleMovingAverage

    max_periods = 10


class SimpleMovingAverageValueFactory(Factory):
    class Meta:
        model = SimpleMovingAverageValue

    frame = FrameFactory()
    indicator = SimpleMovingAverageFactory()
