from estrade.tick_provider import BaseTickProvider
from tests.unit.factories import EpicFactory
from tests.unit.factories.factory import Factory


class TickProviderFactory(Factory):
    class Meta:
        model = BaseTickProvider

    epics = [EpicFactory()]
