import pytest

from tests.unit.factories import EpicFactory, TickProviderFactory


CLASS_DEFINITION_PATH = "estrade.tick_provider.BaseTickProvider"


class TestInit:
    def test_epic(self):
        epic = EpicFactory()
        tick_provider = TickProviderFactory(epics=[epic])

        assert tick_provider.epics == {epic.ref: epic}


class TestGetEpicByRef:
    def test_nominal(self):
        epic1 = EpicFactory()
        epic2 = EpicFactory()
        tick_provider = TickProviderFactory(epics=[epic1, epic2])

        assert tick_provider.get_epic_by_ref(epic2.ref) == epic2


class TestRun:
    def test_run_unimplemented(self):
        tick_provider = TickProviderFactory()
        with pytest.raises(NotImplementedError):
            tick_provider.run()
