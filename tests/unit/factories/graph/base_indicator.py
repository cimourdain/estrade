from estrade.graph.base_indicator import BaseIndicator, BaseIndicatorValue
from tests.unit.factories.factory import Factory
from tests.unit.factories.graph.frame_set import FrameFactory


class BaseIndicatorFactory(Factory):
    class Meta:
        model = BaseIndicator

    def value_class():
        return BaseIndicatorValue


class BaseIndicatorValueFactory(Factory):
    class Meta:
        model = BaseIndicatorValue

    indicator = BaseIndicatorFactory()
    frame = FrameFactory()
