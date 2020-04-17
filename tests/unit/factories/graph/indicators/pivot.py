from estrade.enums import PivotType
from estrade.graph.indicators.pivot import (
    Pivot,
    PivotTypeClassic,
    PivotTypeOLHC,
)
from tests.unit.factories.factory import Factory
from tests.unit.factories.graph.frame_set import FrameFactory


class PivotFactory(Factory):
    class Meta:
        model = Pivot

    pivot_type = PivotType.CLASSIC


class PivotTypeClassicFactory(Factory):
    class Meta:
        model = PivotTypeClassic

    frame = FrameFactory()
    indicator = PivotFactory(pivot_type=PivotType.CLASSIC)


class PivotTypeOLHCFactory(Factory):
    class Meta:
        model = PivotTypeOLHC

    frame = FrameFactory()
    indicator = PivotFactory(pivot_type=PivotType.OLHC)
