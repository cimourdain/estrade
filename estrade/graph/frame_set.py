import logging
from typing import Dict, List, Optional, TYPE_CHECKING

from estrade.enums import Unit
from estrade.mixins import RefMixin, TimeframeMixin


if TYPE_CHECKING:  # pragma: no cover
    from arrow import Arrow  # type: ignore
    from estrade import Epic, Tick
    from estrade.graph.base_indicator import BaseIndicator, BaseIndicatorValue

logger = logging.getLogger(__name__)


class Frame:
    """
    A [`Frame`][estrade.graph.frame_set.Frame] is a group [`Ticks`][estrade.tick.Tick].

    Attributes:
        parent_frameset (estrade.graph.frame_set.FrameSet): parent FrameSet
        first_tick (estrade.tick.Tick): first tick registered on this instance.
        high_tick (estrade.tick.Tick): highest tick registered on this instance.
        low_tick (estrade.tick.Tick): lowest tick registered on this instance.
        last_tick (estrade.tick.Tick): last tick registered on this instance.
        period_start (arrow.Arrow): open datetime of this instance.
        period_end (arrow.Arrow): scheduled end datetime of this instance.
        previous_frame (Optional[estrade.graph.frame_set.Frame]): previous frame.
        next_frame (Optional[estrade.graph.frame_set.Frame]): next frame.
        nb_ticks (int): Number of ticks received by this instance.
        indicators
            (Dict[str, Optional[estrade.graph.base_indicator.BaseIndicatorValue]]):
            Indicators values indexed by their reference.


    """

    def __init__(
        self,
        parent_frameset: "FrameSet",
        first_tick: "Tick",
        period_start: "Arrow",
        period_end: Optional["Arrow"] = None,
        previous_frame: Optional["Frame"] = None,
    ) -> None:
        """
        Create a new Frame.

        Arguments:
            parent_frameset: parent FrameSet
            first_tick: first tick registered on this instance.
            period_start: open datetime of this instance.
            period_end: scheduled end datetime of this instance.
            previous_frame: previous frame.
        """
        self.parent_frameset = parent_frameset
        self.first_tick = first_tick
        self.period_start = period_start
        self.period_end = period_end
        self.previous_frame = previous_frame
        self.next_frame: Optional["Frame"] = None

        self.nb_ticks = 1
        self.last_tick = first_tick
        self.high_tick = first_tick
        self.low_tick = first_tick
        self.indicators: Dict[str, Optional["BaseIndicatorValue"]] = {}

        self._upsert_indicators(first_tick)

    def __getitem__(self, indicator_ref: str) -> Optional["BaseIndicatorValue"]:
        indicator_value = self.indicators.get(indicator_ref, None)
        return indicator_value

    @property
    def closed(self) -> bool:
        """
        Check if the current instance is closed.

        An instance is considered as closed when its `next_frame` value is set.
        """
        return self.next_frame is not None

    def _create_new_indicator_value(
        self, indicator: "BaseIndicator", market_open: bool
    ) -> None:
        logger.debug("Market Open: %s", market_open)
        new_indicator_value = indicator.build_value_from_frame(self, market_open)
        logger.debug(
            "create new value for indicator %s: %s", indicator.ref, new_indicator_value
        )
        self.indicators[indicator.ref] = new_indicator_value

    def _upsert_indicators(self, tick: "Tick"):
        market_open = self.parent_frameset.epic_market_open
        for indicator_ref, indicator in self.parent_frameset.indicators.items():
            current_indicator_value = self.indicators.get(indicator_ref, None)
            if current_indicator_value:
                current_indicator_value.on_new_tick(tick, market_open)
            else:
                self._create_new_indicator_value(indicator, market_open)

    def on_new_tick(self, tick: "Tick"):
        """
        Update the current instance with a new [`Tick`][estrade.tick.Tick].

         - Update `nb_ticks`
         - Update `last_tick`, `high_tick`, `low_tick`
         - Call each indicator `on_new_tick` method.

        Arguments:
            tick: new received Tick.
        """
        logger.debug("Update frame with new tick")
        self.nb_ticks += 1
        self.last_tick = tick

        if tick.value > self.high_tick.value:
            self.high_tick = tick
        elif tick.value < self.low_tick.value:
            self.low_tick = tick

        self._upsert_indicators(tick)


class FrameSet(TimeframeMixin, RefMixin):
    """
    Group of [`Ticks`][estrade.tick.Tick].

    A [`FrameSet`][estrade.graph.frame_set.FrameSet] group [`Ticks`][estrade.tick.Tick]
        into [`Frames`][estrade.graph.frame_set.Frame].

    Attributes:
        unit (estrade.enums.Unit): unit used to group ticks.
        unit_quantity (int): quantity of unit
        max_frames_in_memory (int): number of frames to keep in memory
        epic (estrade.epic.Epic): epic updating this instance
        frames (List[estrade.graph.frame_set.Frame]): List of
            [`Frame`][estrade.graph.frame_set.Frame]
        indicators (Dict[str, estrade.graph.base_indicator.BaseIndicator]): Dict
            of indicators calculated on every [`Frame`][estrade.graph.frame_set.Frame]
            with their ref as index.

        ref (str): reference of this instance
            (see `estrade.mixins.ref.RefMixin`)
    """

    def __init__(
        self,
        unit: Unit,
        unit_quantity: int,
        ref: Optional[str] = None,
        max_frames_in_memory: int = 100,
    ) -> None:
        """
        Instanciate a new [`FrameSet`][estrade.graph.frame_set.FrameSet].

        Arguments:
            unit: unit used to group ticks.
            unit_quantity: quantity of unit
            max_frames_in_memory: number of frames to keep in memory
            ref: reference of this instance
        """
        TimeframeMixin.__init__(self, unit, unit_quantity)
        RefMixin.__init__(self, ref)

        self._is_timeframe_over_func = self.is_frame_over_timed
        self._create_new_frame_func = self._create_new_frame_timed
        if self.unit == Unit.TICK:
            self._is_timeframe_over_func = self.is_frame_over_tick
            self._create_new_frame_func = self._create_new_frame_tick

        self.epic: Optional["Epic"] = None
        self.frames: List[Frame] = []
        self.indicators: Dict[str, "BaseIndicator"] = {}
        self.max_frames_in_memory = max_frames_in_memory

    @property
    def current(self) -> Optional[Frame]:
        """Return the current [`Frame`][estrade.graph.frame_set.Frame]."""
        if self.frames:
            return self.frames[-1]
        return None

    @property
    def epic_market_open(self) -> bool:
        return bool(self.epic and self.epic.market_open)

    def add_indicator(self, indicator: "BaseIndicator"):
        self.indicators[indicator.ref] = indicator
        indicator.set_frame_set(self)

    def clean_old_frames(self):
        import gc

        while len(self.frames) > self.max_frames_in_memory:
            self.frames[1].previous_frame = None
            self.frames[0].next_frame = None
            self.frames.pop(0)
            gc.collect()  # WHY ?

    def create_new_frame(
        self,
        tick: "Tick",
        period_start: "Arrow",
        period_end: Optional["Arrow"] = None,
    ) -> None:
        new_frame = Frame(
            parent_frameset=self,
            first_tick=tick,
            period_start=period_start,
            period_end=period_end,
            previous_frame=self.current,
        )

        if self.current:
            self.current.next_frame = new_frame
        self.frames.append(new_frame)
        self.clean_old_frames()

    def _create_new_frame_timed(self, tick: "Tick") -> None:
        period_start = self.get_frame_start(tick.datetime)
        period_end = self.get_frame_end(period_start)
        if self.current:
            while period_start > self.current.period_end:
                self.create_new_frame(
                    self.current.last_tick,
                    self.current.period_end,
                    self.get_frame_end(self.current.period_end),
                )

        self.create_new_frame(tick, period_start, period_end)

    def _create_new_frame_tick(self, tick: "Tick"):
        period_start = tick.datetime

        self.create_new_frame(
            tick=tick,
            period_start=period_start,
            period_end=None,
        )

    def is_frame_over_timed(self, tick: "Tick") -> bool:
        if not self.current or tick.datetime >= self.current.period_end:
            return True
        return False

    def is_frame_over_tick(self, tick: "Tick") -> bool:
        if (
            not self.current
            or self.current.nb_ticks >= self.unit_quantity
            or self.epic is None
            or tick.datetime.date() > self.epic.last_tick.datetime.date()
        ):
            return True
        return False

    def add_tick_to_last(self, tick: "Tick") -> None:
        if self.current:
            self.current.on_new_tick(tick)

    def on_new_tick(self, tick: "Tick") -> None:
        """
        Update the current instance with a new [`Tick`][estrade.tick.Tick].

        This method will either:

         - add the received tick to the current instance.
         - create a new [`Frame`][estrade.graph.frame_set.Frame] if the current
                frame is over.

        Arguments:
            tick: new tick to update the current instance with.

        """
        if self._is_timeframe_over_func(tick):
            self._create_new_frame_func(tick)
        else:
            self.add_tick_to_last(tick)

    def __getitem__(self, frame_index: int) -> Optional[Frame]:
        try:
            frame = self.frames[frame_index]
        except IndexError:
            return None
        return frame
