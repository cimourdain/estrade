import logging
from typing import Optional, TYPE_CHECKING, Type

from estrade.mixins import RefMixin


if TYPE_CHECKING:  # pragma: no cover
    from estrade.graph.frame_set import Frame, FrameSet
    from estrade import Epic, Tick


logger = logging.getLogger(__name__)


class BaseIndicatorValue:
    """
    Base class of an Indicator value.

    Attributes:
        indicator (estrade.graph.base_indicator.BaseIndicator): Parent indicator.
        frame (estrade.graph.frame_set.Frame): Parent frame.
        self.first_tick (estrade.tick.Tick): first tick registered by indicator value
        self.high_tick (estrade.tick.Tick): highest tick registered by indicator value
        self.low_tick (estrade.tick.Tick): lowest tick registered by indicator value
        self.last_tick (estrade.tick.Tick): last tick registered by indicator value
    """

    def __init__(
        self,
        indicator: "BaseIndicator",
        frame: "Frame",
    ) -> None:
        """
        Create a new indicator value.

        Arguments:
            indicator: Parent indicator.
            frame: Parent frame.

        """
        self.indicator = indicator
        self.frame = frame
        self.first_tick = self.frame.last_tick
        self.high_tick = self.frame.last_tick
        self.low_tick = self.frame.last_tick
        self.last_tick = self.frame.last_tick

    @property
    def previous(self) -> Optional["BaseIndicatorValue"]:
        """
        Return the value of this indicator on the previous frame.

        Returns:
            This indicator value on the previous frame (`None` if the parent have no
                previous frame)
        """
        frame = self.frame.previous_frame
        while frame is not None:
            indicator = frame.indicators.get(self.indicator.ref)
            if indicator is not None:
                return indicator
            frame = frame.previous_frame
        return None

    @property
    def next(self) -> Optional["BaseIndicatorValue"]:
        """
        Return the value of this indicator on the next frame.

        Returns:
            This indicator value on the next frame (`None` if the parent have no
                next frame)
        """
        if not self.frame.next_frame:
            return None
        return self.frame.next_frame.indicators.get(self.indicator.ref)

    @property
    def nb_ticks(self) -> int:
        """
        Count of [`Ticks`][estrade.tick.Tick] received by the parent frame.

        Returns:
            Number of [`Ticks`][estrade.tick.Tick] received by the parent frame.
        """
        return self.frame.nb_ticks

    @property
    def closed(self) -> bool:
        """
        Check if the parent frame is closed.

        Returns:
            Is the parent frame closed?
        """
        return self.frame.closed

    def on_new_tick(self, tick: "Tick", market_open: bool) -> None:
        if not self.indicator.market_open_only or market_open:
            self.last_tick = tick

            if tick.value > self.high_tick.value:
                self.high_tick = tick
            elif tick.value < self.low_tick.value:
                self.low_tick = tick


class BaseIndicator(RefMixin):
    """
    Base class of an Indicator.

    Attributes:
        value_class (Type[estrade.graph.base_indicator.BaseIndicatorValue]): Class
            of value to generate on new frame.
        frame_set (Optional[estrade.graph.frame_set.FrameSet]): The FrameSet instance
            that send ticks to this instance.
        market_open_only (bool): apply this indicator only when market is open.
        ref (str): reference of this instance
    """

    def __init__(
        self,
        value_class: Type["BaseIndicatorValue"],
        ref: Optional[str] = None,
        market_open_only: bool = False,
    ) -> None:
        """
        Create a new indicator.

        Arguments:
            value_class: Class of value to generate on new frame.
            market_open_only: apply this indicator only when market is open.
            ref: reference of this instance
        """
        RefMixin.__init__(self, ref=ref)

        self.value_class = value_class
        self.market_open_only = market_open_only
        self.frame_set: Optional["FrameSet"] = None

    @property
    def epic(self) -> Optional["Epic"]:
        """
        Return the [`Epic`][estrade.epic.Epic] associated to this instance.

        Returns:
            Epic associated to this instance.
        """
        if not self.frame_set:
            return None
        return self.frame_set.epic

    def set_frame_set(self, frame_set: "FrameSet"):
        self.frame_set = frame_set

    def build_value_from_frame(
        self, frame: "Frame", epic_market_open: bool
    ) -> Optional["BaseIndicatorValue"]:
        """
        Create a new value for this indicator.

        This method is triggered when its `frame_set` create a new
            [`Frame`][estrade.graph.frame_set.Frame].

        Arguments:
            frame: The newly created frame.
            epic_market_open: is the epic open?

        Returns:
            An instance of this instance `value_class` (`None` Market is not open).
        """
        if not self.market_open_only or epic_market_open:
            new_value = self.value_class(
                indicator=self,
                frame=frame,
            )
            return new_value
        return None
