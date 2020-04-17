import arrow

from estrade.enums import Unit
from estrade.graph.frame_set import Frame, FrameSet
from tests.unit.factories import EpicFactory
from tests.unit.factories.factory import Factory, post_build
from tests.unit.factories.tick import TickFactory


class FrameSetRawFactory(Factory):
    class Meta:
        model = FrameSet

    unit = Unit.MINUTE
    unit_quantity = 5


class FrameSetFactory(FrameSetRawFactory):
    @post_build
    def set_epic(fs):
        fs.epic = EpicFactory()


class FrameFactory(Factory):
    class Meta:
        model = Frame

    parent_frameset = FrameSetFactory()
    first_tick = TickFactory(datetime=arrow.get("2020-01-01 12:36:12"))

    def period_start():
        return arrow.get("2020-01-01 12:35:00")
