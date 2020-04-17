import pytest

from tests.unit.factories import (
    BaseIndicatorFactory,
    BaseIndicatorValueFactory,
    FrameFactory,
    TickFactory,
)


CLASS_DEFINITION_PATH = "estrade.graph.base_indicator.BaseIndicatorValue"


class TestInit:
    def test_indicator(self):
        bi = BaseIndicatorFactory()
        biv = BaseIndicatorValueFactory(indicator=bi)

        assert biv.indicator == bi

    def test_frame(self):
        fr = FrameFactory()
        biv = BaseIndicatorValueFactory(frame=fr)

        assert biv.frame == fr

    def test_first_tick(self, mocker):
        frame_mock = mocker.Mock()
        frame_mock.last_tick = "last_tick"
        biv = BaseIndicatorValueFactory(frame=frame_mock)

        assert biv.first_tick == "last_tick"

    def test_high_tick(self, mocker):
        frame_mock = mocker.Mock()
        frame_mock.last_tick = "last_tick"
        biv = BaseIndicatorValueFactory(frame=frame_mock)

        assert biv.high_tick == "last_tick"

    def test_low_tick(self, mocker):
        frame_mock = mocker.Mock()
        frame_mock.last_tick = "last_tick"
        biv = BaseIndicatorValueFactory(frame=frame_mock)

        assert biv.low_tick == "last_tick"

    def test_last_tick(self, mocker):
        frame_mock = mocker.Mock()
        frame_mock.last_tick = "last_tick"
        biv = BaseIndicatorValueFactory(frame=frame_mock)

        assert biv.last_tick == "last_tick"


class TestPrevious:
    def test_no_previous(self, mocker):
        biv = BaseIndicatorValueFactory()

        frame_mock = mocker.Mock()
        frame_mock.previous_frame = None
        biv.frame = frame_mock

        assert biv.previous is None

    def test_missing_on_previous(self, mocker):
        biv = BaseIndicatorValueFactory(indicator=BaseIndicatorFactory(ref="my_ref"))

        frame_mock = mocker.Mock()
        previous_frame_mock = mocker.Mock()
        previous_frame_mock.indicators = {}
        previous_frame_mock.previous_frame = None
        frame_mock.previous_frame = previous_frame_mock

        biv.frame = frame_mock

        assert biv.previous is None

    def test_nominal(self, mocker):
        biv = BaseIndicatorValueFactory(indicator=BaseIndicatorFactory(ref="my_ref"))

        frame_mock = mocker.Mock()
        previous_frame_mock = mocker.Mock()
        previous_frame_mock.indicators = {"my_ref": "my_indicator"}
        frame_mock.previous_frame = previous_frame_mock
        biv.frame = frame_mock

        assert biv.previous == "my_indicator"


class TestNext:
    def test_no_next(self, mocker):
        biv = BaseIndicatorValueFactory()

        frame_mock = mocker.Mock()
        frame_mock.next_frame = None
        biv.frame = frame_mock

        assert biv.next is None

    def test_missing_on_next(self, mocker):
        biv = BaseIndicatorValueFactory(indicator=BaseIndicatorFactory(ref="my_ref"))

        frame_mock = mocker.Mock()
        next_frame_mock = mocker.Mock()
        next_frame_mock.indicators = {}
        frame_mock.next_frame = next_frame_mock
        biv.frame = frame_mock

        assert biv.next is None

    def test_nominal(self, mocker):
        biv = BaseIndicatorValueFactory(indicator=BaseIndicatorFactory(ref="my_ref"))

        frame_mock = mocker.Mock()
        next_frame_mock = mocker.Mock()
        next_frame_mock.indicators = {"my_ref": "my_indicator"}
        frame_mock.next_frame = next_frame_mock
        biv.frame = frame_mock

        assert biv.next == "my_indicator"


class TestNbTicks:
    def test_nominal(self, mocker):
        biv = BaseIndicatorValueFactory()

        frame_mock = mocker.Mock()
        frame_mock.nb_ticks = 66
        biv.frame = frame_mock

        assert biv.nb_ticks == 66


class TestClosed:
    @pytest.mark.parametrize(["frame_closed"], [(True,), (False,)])
    def test_nominal(self, mocker, frame_closed):
        biv = BaseIndicatorValueFactory()

        frame_mock = mocker.Mock()
        frame_mock.closed = frame_closed
        biv.frame = frame_mock

        assert biv.closed == frame_closed


class TestOnNewTick:
    @pytest.mark.parametrize(
        ["market_open_only", "market_open", "expected_last_tick_update"],
        [
            (True, True, True),
            (True, False, False),
            (False, True, True),
            (False, False, True),
        ],
    )
    def test_update_last_tick(
        self, mocker, market_open_only, market_open, expected_last_tick_update
    ):
        biv = BaseIndicatorValueFactory()
        parent_indicator_mock = mocker.Mock()
        parent_indicator_mock.market_open_only = market_open_only
        biv.indicator = parent_indicator_mock

        current_last_tick = TickFactory()
        biv.last_tick = current_last_tick

        tick = TickFactory()
        biv.on_new_tick(tick, market_open)

        if expected_last_tick_update:
            assert biv.last_tick == tick
        else:
            assert biv.last_tick == current_last_tick

    def test_update_high_tick(self, mocker):
        biv = BaseIndicatorValueFactory()
        parent_indicator_mock = mocker.Mock()
        parent_indicator_mock.market_open_only = False
        biv.indicator = parent_indicator_mock

        current_high_tick = TickFactory(bid=99, ask=101)
        biv.high_tick = current_high_tick

        tick = TickFactory(bid=100, ask=101)
        biv.on_new_tick(tick, True)

        assert biv.high_tick == tick

    def test_update_low_tick(self, mocker):
        biv = BaseIndicatorValueFactory()
        parent_indicator_mock = mocker.Mock()
        parent_indicator_mock.market_open_only = False
        biv.indicator = parent_indicator_mock

        current_low_tick = TickFactory(bid=99, ask=101)
        biv.low_tick = current_low_tick

        tick = TickFactory(bid=98, ask=101)
        biv.on_new_tick(tick, True)

        assert biv.low_tick == tick
