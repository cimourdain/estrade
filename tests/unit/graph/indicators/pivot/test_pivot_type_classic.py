from estrade.graph.indicators.pivot import BasePivotType
from tests.unit.factories import PivotTypeClassicFactory


class TestInheritance:
    def test_base_indicator(self):
        ptc = PivotTypeClassicFactory()

        assert BasePivotType in ptc.__class__.__bases__


class TestPivot:
    def test_no_previous(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.previous",
            new_callable=lambda: None,
        )
        ptc = PivotTypeClassicFactory()

        assert ptc.pivot is None

    def test_nominal(self, mocker):
        previous_mock = mocker.Mock()

        previous_mock.high_tick.value = 3.6
        previous_mock.low_tick.value = 4.22
        previous_mock.last_tick.value = 5.77
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.previous",
            new_callable=lambda: previous_mock,
        )
        ptc = PivotTypeClassicFactory()

        assert ptc.pivot == round((3.6 + 4.22 + 5.77) / 3, 2)


class TestSupport1:
    def test_no_pivot(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: None,
        )
        ptc = PivotTypeClassicFactory()

        assert ptc.support1 is None

    def test_nominal(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: 116.68,
        )
        previous_mock = mocker.Mock()
        previous_mock.high_tick.value = 118.34
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.previous",
            new_callable=lambda: previous_mock,
        )

        ptc = PivotTypeClassicFactory()

        assert ptc.support1 == round((116.68 * 2) - 118.34, 2)


class TestSupport2:
    def test_no_pivot(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: None,
        )
        ptc = PivotTypeClassicFactory()

        assert ptc.support2 is None

    def test_nominal(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: 34.56,
        )
        previous_mock = mocker.Mock()
        previous_mock.high_tick.value = 45.67
        previous_mock.low_tick.value = 31.81
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.previous",
            new_callable=lambda: previous_mock,
        )

        ptc = PivotTypeClassicFactory()

        assert ptc.support2 == round(34.56 - (45.67 - 31.81), 2)


class TestSupport3:
    def test_no_pivot(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: None,
        )
        ptc = PivotTypeClassicFactory()

        assert ptc.support3 is None

    def test_nominal(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: 234.723,
        )
        previous_mock = mocker.Mock()
        previous_mock.high_tick.value = 255.38
        previous_mock.low_tick.value = 188.92
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.previous",
            new_callable=lambda: previous_mock,
        )

        ptc = PivotTypeClassicFactory()

        assert ptc.support3 == round(188.92 - ((255.38 - 234.723) * 2), 2)


class TestResistance1:
    def test_no_pivot(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: None,
        )
        ptc = PivotTypeClassicFactory()

        assert ptc.resistance1 is None

    def test_nominal(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: 645.32,
        )
        previous_mock = mocker.Mock()
        previous_mock.low_tick.value = 622.56
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.previous",
            new_callable=lambda: previous_mock,
        )

        ptc = PivotTypeClassicFactory()

        assert ptc.resistance1 == round((645.32 * 2) - 622.56, 2)


class TestResistance2:
    def test_no_pivot(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: None,
        )
        ptc = PivotTypeClassicFactory()

        assert ptc.resistance2 is None

    def test_nominal(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: 5.484,
        )
        previous_mock = mocker.Mock()
        previous_mock.high_tick.value = 9.417
        previous_mock.low_tick.value = 2.712
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.previous",
            new_callable=lambda: previous_mock,
        )

        ptc = PivotTypeClassicFactory()

        assert ptc.resistance2 == round(5.484 + (9.417 - 2.712), 2)


class TestResistance3:
    def test_no_pivot(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: None,
        )
        ptc = PivotTypeClassicFactory()

        assert ptc.resistance3 is None

    def test_nominal(self, mocker):
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.pivot",
            new_callable=lambda: 345.285,
        )
        previous_mock = mocker.Mock()
        previous_mock.high_tick.value = 436.619
        previous_mock.low_tick.value = 326.472
        mocker.patch(
            "estrade.graph.indicators.pivot.PivotTypeClassic.previous",
            new_callable=lambda: previous_mock,
        )

        ptc = PivotTypeClassicFactory()

        assert ptc.resistance3 == round(436.619 + (345.285 - 326.472) * 2, 2)
