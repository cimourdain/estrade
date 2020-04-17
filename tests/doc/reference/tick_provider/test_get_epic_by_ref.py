from estrade import BaseTickProvider, Epic


class MyTickProvider(BaseTickProvider):
    def run(self):
        pass


def test_get_epic_by_ref():
    epic = Epic(ref="MY_EPIC_CODE")

    tick_provider = MyTickProvider(epics=[epic])

    assert tick_provider.get_epic_by_ref("MY_EPIC_CODE") == epic
    assert tick_provider.get_epic_by_ref("undefined") is None
