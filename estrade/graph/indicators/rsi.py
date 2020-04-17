from typing import List, Optional, TYPE_CHECKING, Tuple

from estrade.exceptions import BaseIndicatorException
from estrade.graph.base_indicator import BaseIndicator, BaseIndicatorValue


if TYPE_CHECKING:  # pragma: no cover
    from estrade import Tick
    from estrade.graph.frame_set import FrameSet, Frame


class RSIValue(BaseIndicatorValue):
    """
    Relative Strength Index (RSI) Value representation.

    Attributes:
        indicator (estrade.graph.base_indicator.BaseIndicator): Parent indicator.
        frame (estrade.graph.frame_set.Frame): Parent frame.
        last_changes (List[float]): List of last frames changes
        value (Optional[float]): value of the RSI
    """

    def __init__(
        self,
        indicator: "RSI",
        frame: "Frame",
    ) -> None:
        """
        Create a new RSI Value for the input Frame.

        Arguments:
            indicator: parent indicator
            frame: parent frame
        """
        BaseIndicatorValue.__init__(self, indicator=indicator, frame=frame)
        if (
            not hasattr(self.indicator, "rsi_periods")
            or not self.indicator.rsi_periods  # type: ignore
        ):
            raise BaseIndicatorException("Invalid RSI Value parent")
        self.rsi_periods = self.indicator.rsi_periods  # type: ignore

        self.last_changes: List[float] = []
        if self.previous:
            self.last_changes = self.previous.extended_changes[:]  # type: ignore

        self.value: Optional[float] = None

        if self.rsi_periods:
            max_last_changes_size = self.rsi_periods - 1
            self.last_changes = self.last_changes[(max_last_changes_size * -1) :]

            self._update_rsi()

    @property
    def extended_changes(self) -> List[float]:
        if not self.frame.previous_frame:
            return []

        current_change = (
            self.frame.last_tick.value - self.frame.previous_frame.last_tick.value
        )
        extended_changes = self.last_changes + [current_change]
        return extended_changes

    def _build_rsi(self) -> float:
        pos_sum, neg_sum = self._build_sums()
        if neg_sum == 0:
            return 100
        elif pos_sum == 0:
            return 0
        else:
            pos_sum_avg = pos_sum / self.rsi_periods
            neg_sum_avg = neg_sum / self.rsi_periods
            rs = pos_sum_avg / abs(neg_sum_avg)
            return round(100 - (100 / (1 + rs)), 2)

    def _build_sums(self) -> Tuple[float, float]:
        pos_sum = 0.0
        neg_sum = 0.0
        for value in self.extended_changes:
            if value >= 0:
                pos_sum += value
            else:
                neg_sum += value

        return pos_sum, neg_sum

    def _update_rsi(self) -> None:
        if self.rsi_periods and len(self.extended_changes) == self.rsi_periods:
            self.value = self._build_rsi()

    def on_new_tick(self, tick: "Tick", market_open: bool) -> None:
        super().on_new_tick(tick, market_open)
        self._update_rsi()


class RSI(BaseIndicator):
    """
    Relative Strength Index (RSI) representation.

    Attributes:
        periods: Number of periods to calculate RSI
        value_class (Type[estrade.graph.base_indicator.BaseIndicatorValue]): Class
            of value to generate on new frame.
        frame_set (Optional[estrade.graph.frame_set.FrameSet]): The FrameSet instance
            that send ticks to this instance.
        market_open_only (bool): apply this indicator only when market is open.
        ref (str): reference of this instance
    """

    def __init__(self, periods: int, **kwargs):
        """
        Create a new instance of a RSI Generator.

        Arguments:
            periods: periods
            kwargs: see [`BaseIndicator`][estrade.graph.base_indicator.BaseIndicator]
        """
        BaseIndicator.__init__(
            self,
            value_class=RSIValue,
            **kwargs,
        )

        self.periods = periods
        self.rsi_periods: Optional[int] = None

    def set_frame_set(self, frame_set: "FrameSet") -> None:
        super(RSI, self).set_frame_set(frame_set)
        self.rsi_periods = self.periods * frame_set.unit_quantity
        if self.rsi_periods > frame_set.max_frames_in_memory:
            raise BaseIndicatorException(
                "Not enough frames kept in memory to calculate RSI"
            )
