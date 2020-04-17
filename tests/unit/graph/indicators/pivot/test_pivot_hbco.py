from estrade.graph.indicators.pivot import PivotTypeClassic
from tests.unit.factories import PivotTypeOLHCFactory


class TestInheritance:
    def test_base_indicator(self):
        ptc = PivotTypeOLHCFactory()

        assert PivotTypeClassic in ptc.__class__.__bases__


class TestPivot:
    def test_no_previous(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeOLHC.previous",
            new_callable=lambda: None,
        )
        ptc = PivotTypeOLHCFactory()

        assert ptc.pivot is None

    def test_nominal(self, mocker):
        previous_mock = mocker.Mock()

        previous_mock.high_tick.value = 987.654
        previous_mock.low_tick.value = 876.543
        previous_mock.last_tick.value = 912.345
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeOLHC.previous",
            new_callable=lambda: previous_mock,
        )
        ptc = PivotTypeOLHCFactory()
        current_first_mock = mocker.Mock()
        current_first_mock.value = 1003.678
        ptc.first_tick = current_first_mock

        assert ptc.pivot == round((987.654 + 876.543 + 912.345 + 1003.678) / 4, 2)
