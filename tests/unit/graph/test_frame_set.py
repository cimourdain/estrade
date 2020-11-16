from unittest.mock import call

import arrow
import pytest

from estrade.enums import Unit
from estrade.graph.base_indicator import BaseIndicator
from estrade.graph.frame_set import Frame
from estrade.mixins import RefMixin, TimeframeMixin
from tests.unit.factories import (
    EpicFactory,
    FrameFactory,
    FrameSetFactory,
    TickFactory,
)
from tests.unit.factories.graph.frame_set import FrameSetRawFactory
from tests.unit.graph.test_frame import (
    CLASS_DEFINITION_PATH as CLASS_FRAME_DEFINITION_PATH,
)


CLASS_DEFINITION_PATH = "estrade.graph.frame_set.FrameSet"


class TestInheritance:
    def test_timeframe_mixin(self):
        fs = FrameSetFactory()

        assert TimeframeMixin in fs.__class__.__bases__

    def test_timeframe_mixin_call(self, mocker):
        mixin_init_mock = mocker.patch.object(
            TimeframeMixin, "__init__", wraps=TimeframeMixin.__init__
        )

        fs = FrameSetFactory(unit=Unit.SECOND, unit_quantity=30)

        assert mixin_init_mock.call_args_list == [call(fs, Unit.SECOND, 30)]

    def test_ref_mixin(self):
        fs = FrameSetFactory()

        assert RefMixin in fs.__class__.__bases__

    def test_ref_mixin_call(self, mocker):
        mixin_init_mock = mocker.patch.object(
            RefMixin, "__init__", wraps=RefMixin.__init__
        )

        fs = FrameSetFactory(ref="test_ref")

        assert call(fs, "test_ref") in mixin_init_mock.call_args_list


class TestInit:
    def test_max_frames_in_memory__default(self):
        fs = FrameSetFactory()

        assert fs.max_frames_in_memory == 100

    def test_max_frames_in_memory__manual(self):
        fs = FrameSetFactory(max_frames_in_memory=23)

        assert fs.max_frames_in_memory == 23

    def test_epic__default(self):
        fs = FrameSetRawFactory()

        assert fs.epic is None

    def test_frames__default(self):
        fs = FrameSetFactory()

        assert fs.frames == []

    def test_indicators__default(self):
        fs = FrameSetFactory()

        assert fs.indicators == {}


class TestCreateNewFrame:
    @pytest.fixture
    def mock_frame_init(self, mocker):
        mock = mocker.patch(f"{CLASS_FRAME_DEFINITION_PATH}")
        return mock

    @pytest.fixture(autouse=True)
    def mock_current(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.current", new_callable=lambda: None)

    @pytest.fixture(autouse=True)
    def mock_clean_old_frames(self, mocker):
        mock = mocker.patch(f"{CLASS_DEFINITION_PATH}.clean_old_frames")
        return mock

    def test_frame_init__minimal(self, mock_frame_init):
        tick = TickFactory()
        period_start = arrow.get("2020-01-01 12:35:00")

        fs = FrameSetFactory()
        fs.create_new_frame(tick=tick, period_start=period_start)

        assert mock_frame_init.call_args_list == [
            call(
                parent_frameset=fs,
                first_tick=tick,
                period_start=period_start,
                period_end=None,
                previous_frame=None,
                empty=False,
            )
        ]

    def test_period_end(self, mock_frame_init):
        tick = TickFactory()
        period_start = arrow.get("2020-01-01 12:35:00")
        period_end = arrow.get("2020-01-01 12:40:00")

        fs = FrameSetFactory()
        fs.create_new_frame(tick=tick, period_start=period_start, period_end=period_end)

        assert mock_frame_init.call_args_list == [
            call(
                parent_frameset=fs,
                first_tick=tick,
                period_start=period_start,
                period_end=period_end,
                previous_frame=None,
                empty=False,
            )
        ]

    def test_previous_frame(self, mocker, mock_frame_init):
        mock_current = mocker.Mock()
        mock_current.next_frame = None
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.current",
            new_callable=lambda: mock_current,
        )

        tick = TickFactory()
        period_start = arrow.get("2020-01-01 12:35:00")

        fs = FrameSetFactory()
        fs.create_new_frame(tick=tick, period_start=period_start)

        assert mock_frame_init.call_args_list == [
            call(
                parent_frameset=fs,
                first_tick=tick,
                period_start=period_start,
                period_end=None,
                previous_frame=mock_current,
                empty=False,
            )
        ]

    def test_set_new_as_current_next(self, mocker):
        mock_current = mocker.Mock()
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.current",
            new_callable=lambda: mock_current,
        )

        mocker.patch(f"{CLASS_FRAME_DEFINITION_PATH}", return_value="my_new_frame")

        tick = TickFactory()
        period_start = arrow.get("2020-01-01 12:35:00")
        fs = FrameSetFactory()
        fs.create_new_frame(tick=tick, period_start=period_start)

        assert mock_current.next_frame == "my_new_frame"

    def test_add_to_frames(self, mocker):
        mocker.patch(f"{CLASS_FRAME_DEFINITION_PATH}", return_value="my_new_frame")

        tick = TickFactory()
        period_start = arrow.get("2020-01-01 12:35:00")
        fs = FrameSetFactory()
        fs.create_new_frame(tick=tick, period_start=period_start)

        assert fs.frames == ["my_new_frame"]

    def test_clean_old_frames(self, mock_clean_old_frames):
        tick = TickFactory()
        period_start = arrow.get("2020-01-01 12:35:00")

        fs = FrameSetFactory()
        fs.create_new_frame(tick=tick, period_start=period_start)

        assert mock_clean_old_frames.call_args_list == [call()]


class TestAddIndicators:
    @pytest.fixture
    def indicator_mock(self, mocker):
        indicator_mock = mocker.Mock(spec=BaseIndicator)
        indicator_mock.set_frame_set.return_value = None
        return indicator_mock

    def test_set_as_indicator(self, indicator_mock):
        indicator_mock.ref = "test_indicator_ref"

        fs = FrameSetFactory()
        fs.add_indicator(indicator_mock)

        assert fs.indicators == {"test_indicator_ref": indicator_mock}

    def test_indicator_frame_set(self, indicator_mock):
        indicator_mock.ref = "test_indicator_ref"

        fs = FrameSetFactory()
        fs.add_indicator(indicator_mock)

        assert indicator_mock.set_frame_set.call_args_list == [call(fs)]


class TestEpicMarketOpen:
    def test_no_epic(self):
        fs = FrameSetFactory()
        fs.epic = None

        assert fs.epic_market_open is False

    @pytest.mark.parametrize(["market_open"], [(True,), (False,)])
    def test_epic_market_open(self, market_open):
        fs = FrameSetFactory()
        epic = EpicFactory()
        epic.market_open = market_open
        fs.epic = epic

        assert fs.epic_market_open == market_open


class TestCurrent:
    def test_no_current(self):
        fs = FrameSetFactory()

        assert fs.current is None

    def test_exists(self):
        fs = FrameSetFactory()
        last_frame = FrameFactory()
        fs.frames = ["first", last_frame]

        assert fs.current == last_frame


class TestIsFrameOverTimed:
    def test_no_current(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.current", new_callable=lambda: None)
        fs = FrameSetFactory()
        tick = TickFactory()

        assert fs.is_frame_over_timed(tick) is True

    @pytest.mark.parametrize(
        ["frame_end", "tick_datetime", "expected_response"],
        [
            ("2020-01-01 12:34:56", "2020-01-01 12:35:00", True),
            ("2020-01-01 12:34:56", "2020-01-01 12:34:56", True),
            ("2020-01-01 12:34:56", "2020-01-01 12:34:55", False),
        ],
    )
    def test_nominal(self, mocker, frame_end, tick_datetime, expected_response):
        frame_mock = mocker.Mock(spec=Frame)
        frame_mock.period_end = arrow.get(frame_end)
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.current",
            new_callable=lambda: frame_mock,
        )
        fs = FrameSetFactory()
        tick = TickFactory(datetime=arrow.get(tick_datetime))

        assert fs.is_frame_over_timed(tick) == expected_response


class TestIsFrameOverTick:
    def test_no_current(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.current", new_callable=lambda: None)
        fs = FrameSetFactory()
        tick = TickFactory()

        assert fs.is_frame_over_tick(tick) is True

    @pytest.mark.parametrize(
        ["current_nb_ticks", "tick_datetime", "expected_response"],
        [
            (0, "2020-01-01 14:00:00", False),
            (0, "2020-01-02 14:00:00", True),
            (1, "2020-01-01 14:00:00", False),
            (1, "2020-01-02 14:00:00", True),
            (2, "2020-01-01 14:00:00", False),
            (2, "2020-01-02 14:00:00", True),
            (3, "2020-01-01 14:00:00", True),
            (4, "2020-01-01 14:00:00", True),
        ],
    )
    def test_nominal(self, mocker, current_nb_ticks, tick_datetime, expected_response):
        frame_mock = mocker.Mock(spec=Frame)
        frame_mock.nb_ticks = current_nb_ticks
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.current",
            new_callable=lambda: frame_mock,
        )

        fs = FrameSetFactory(unit_quantity=3)
        fs.epic.last_tick = TickFactory(datetime=arrow.get("2020-01-01 12:34:56"))

        new_tick = TickFactory(datetime=arrow.get(tick_datetime))
        assert fs.is_frame_over_tick(new_tick) == expected_response

    def test_on_day_change(self, mocker):
        frame_mock = mocker.Mock(spec=Frame)
        frame_mock.nb_ticks = 1
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.current",
            new_callable=lambda: frame_mock,
        )

        fs = FrameSetFactory(unit_quantity=3)
        fs.epic.last_tick = TickFactory(datetime=arrow.get("2020-01-01 23:59:59"))

        new_tick = TickFactory(datetime=arrow.get("2020-01-02 00:00:00"))
        assert fs.is_frame_over_tick(new_tick) is True


class TestAddTickToLast:
    def test_no_current(self, mocker):
        mocker.patch(f"{CLASS_DEFINITION_PATH}.current", new_callable=lambda: None)
        fs = FrameSetFactory()

        assert fs.add_tick_to_last(TickFactory()) is None

    def test_nominal(self, mocker):
        frame_mock = mocker.Mock(spec=Frame)
        mocker.patch(
            f"{CLASS_DEFINITION_PATH}.current",
            new_callable=lambda: frame_mock,
        )
        fs = FrameSetFactory()
        tick = TickFactory()

        fs.add_tick_to_last(tick)

        assert frame_mock.on_new_tick.call_args_list == [call(tick)]


class TestOnNewTickTimed:
    @pytest.fixture(autouse=True)
    def mock_is_frame_over_timed(self, mocker):
        mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.is_frame_over_timed", return_value=True
        )
        return mock

    def test_is_frame_over_timed_call(self, mock_is_frame_over_timed):
        fs = FrameSetFactory(unit=Unit.SECOND)
        tick = TickFactory()

        fs.on_new_tick(tick)

        assert mock_is_frame_over_timed.call_args_list == [call(tick)]

    def test_create_new_frame_call__no_gap(self, mocker):
        create_new_frame_mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.create_new_frame",
        )
        fs = FrameSetFactory(unit=Unit.SECOND, unit_quantity=10)
        tick = TickFactory(datetime=arrow.get("2020-01-01 12:34:56"))

        fs.on_new_tick(tick)

        assert create_new_frame_mock.call_args_list == [
            call(
                tick, arrow.get("2020-01-01 12:34:50"), arrow.get("2020-01-01 12:35:00")
            )
        ]

    def test_create_new_frame_call__gap(self, mocker):
        fs = FrameSetFactory(unit=Unit.SECOND, unit_quantity=10)
        create_new_frame_mock = mocker.patch.object(
            fs, "create_new_frame", wraps=fs.create_new_frame
        )
        current_last_tick = TickFactory()
        current_frame = FrameFactory(
            first_tick=current_last_tick,
            period_start=arrow.get("2020-01-01 12:34:10"),
            period_end=arrow.get("2020-01-01 12:34:20"),
        )
        fs.frames = [current_frame]

        new_tick = TickFactory(datetime=arrow.get("2020-01-01 12:34:56"))
        fs.on_new_tick(new_tick)

        assert create_new_frame_mock.call_args_list == [
            call(
                current_last_tick,
                arrow.get("2020-01-01 12:34:20"),
                arrow.get("2020-01-01 12:34:30"),
                empty=True,
            ),
            call(
                current_last_tick,
                arrow.get("2020-01-01 12:34:30"),
                arrow.get("2020-01-01 12:34:40"),
                empty=True,
            ),
            call(
                current_last_tick,
                arrow.get("2020-01-01 12:34:40"),
                arrow.get("2020-01-01 12:34:50"),
                empty=True,
            ),
            call(
                new_tick,
                arrow.get("2020-01-01 12:34:50"),
                arrow.get("2020-01-01 12:35:00"),
            ),
        ]

    def test_add_to_last_tick(self, mocker, mock_is_frame_over_timed):
        mock_is_frame_over_timed.return_value = False
        add_tick_to_last_mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.add_tick_to_last",
        )
        fs = FrameSetFactory(unit=Unit.SECOND)
        tick = TickFactory()

        fs.on_new_tick(tick)

        assert add_tick_to_last_mock.call_args_list == [call(tick)]


class TestOnNewTickTick:
    @pytest.fixture
    def mock_is_frame_over_tick(self, mocker):
        mock = mocker.patch(
            f"{CLASS_DEFINITION_PATH}.is_frame_over_tick", return_value=True
        )
        return mock

    def test_is_frame_over_tick_call(self, mock_is_frame_over_tick):
        fs = FrameSetFactory(unit=Unit.TICK)
        tick = TickFactory()

        fs.on_new_tick(tick)

        assert mock_is_frame_over_tick.call_args_list == [call(tick)]

    def test_create_new_frame_call(self, mocker, mock_is_frame_over_tick):
        mock_is_frame_over_tick.return_value = True

        fs = FrameSetFactory(unit=Unit.TICK)
        create_new_frame_mock = mocker.patch.object(
            fs, "create_new_frame", wraps=fs.create_new_frame
        )

        tick = TickFactory()
        fs.on_new_tick(tick)

        assert create_new_frame_mock.call_args_list == [
            call(tick=tick, period_start=tick.datetime, period_end=None)
        ]

    def test_add_tick_to_last_call(self, mocker, mock_is_frame_over_tick):
        mock_is_frame_over_tick.return_value = False

        fs = FrameSetFactory(unit=Unit.TICK)
        add_tick_to_last_mock = mocker.patch.object(
            fs, "add_tick_to_last", wraps=fs.add_tick_to_last
        )

        tick = TickFactory()
        fs.on_new_tick(tick)

        assert add_tick_to_last_mock.call_args_list == [call(tick)]


class TestCleanOldFrames:
    def test_apply_frames_limit(self, mocker):
        fs = FrameSetFactory(max_frames_in_memory=3)

        frame_mock = mocker.Mock()
        frame_mock.previous_frame = "test"
        for frame_idx in range(10):
            fs.frames.append(frame_mock)

        fs.clean_old_frames()
        assert len(fs.frames) == 3

    def test_keep_only_last_frames(self, mocker):
        fs = FrameSetFactory(max_frames_in_memory=3)

        for frame_idx in range(10):
            frame_mock = mocker.Mock()
            frame_mock.previous_frame = "test"
            frame_mock.idx = frame_idx
            fs.frames.append(frame_mock)

        fs.clean_old_frames()
        assert [frame.idx for frame in fs.frames] == [7, 8, 9]

    def test_reset_last_frame_previous(self, mocker):
        fs = FrameSetFactory(max_frames_in_memory=3)

        for frame_idx in range(10):
            frame_mock = mocker.Mock()
            frame_mock.previous_frame = "test"
            frame_mock.idx = frame_idx
            fs.frames.append(frame_mock)

        fs.clean_old_frames()
        assert [frame.previous_frame for frame in fs.frames] == [None, "test", "test"]


class TestGetItem:
    def test_not_existing_frame(self):
        fs = FrameSetFactory()

        assert fs[-1] is None

    def test_existing_frame(self):
        fs = FrameSetFactory()
        fs.frames.append("test1")
        fs.frames.append("test2")

        assert fs[-1] == "test2"
