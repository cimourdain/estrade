import arrow

from estrade.tick import Tick
from tests.unit.factories.factory import Factory


class TickFactory(Factory):
    class Meta:
        model = Tick

    datetime = lambda: arrow.utcnow()  # NOQA
    bid = 999
    ask = 1001
