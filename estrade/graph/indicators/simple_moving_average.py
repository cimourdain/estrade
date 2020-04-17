from typing import List, Optional, TYPE_CHECKING

from estrade.graph.base_indicator import BaseIndicator, BaseIndicatorValue


if TYPE_CHECKING:  # pragma: no cover
    from estrade.graph.frame_set import Frame


class SimpleMovingAverageValue(BaseIndicatorValue):
    """
    Simple Moving Average Value representation.

    Attributes:
        indicator (estrade.graph.base_indicator.BaseIndicator): Parent indicator.
        frame (estrade.graph.frame_set.Frame): Parent frame.
        last_closes (List[float]): List of closes values of previous frames
        extended_closes (List[float]): List of closes values of previous frames + last
            value of the current frame.
    """

    def __init__(
        self,
        indicator: "SimpleMovingAverage",
        frame: "Frame",
    ) -> None:
        """
        Create a new Moving Average Value for the input Frame.

        Arguments:
            indicator: parent indicator
            frame: parent frame
        """
        BaseIndicatorValue.__init__(self, indicator=indicator, frame=frame)

        self.last_closes: List[float] = []
        if self.previous:
            self.last_closes = self.previous.extended_closes[:]  # type: ignore

        max_last_closes_size = self.indicator.max_periods - 1  # type: ignore
        self.last_closes = self.last_closes[(max_last_closes_size * -1) :]

    @property
    def extended_closes(self) -> List[float]:
        extended_closes = self.last_closes + [self.frame.last_tick.value]
        return extended_closes

    def get_value(self, periods: int) -> Optional[float]:
        """
        Get a SMA value.

        Arguments:
            periods: Number of periods to calculate the SMA on.

        Returns:
            Simple Moving Average Value
        """
        if len(self.extended_closes) < periods:
            return None
        raw_value = sum(self.extended_closes[(periods * -1) :]) / periods
        return round(raw_value, 2)


class SimpleMovingAverage(BaseIndicator):
    """
    Simple Moving Average representation.

    Attributes:
        max_periods: max closes kept in memory (max periods to calculate SMA)
        value_class (Type[estrade.graph.base_indicator.BaseIndicatorValue]): Class
            of value to generate on new frame.
        frame_set (Optional[estrade.graph.frame_set.FrameSet]): The FrameSet instance
            that send ticks to this instance.
        market_open_only (bool): apply this indicator only when market is open.
        ref (str): reference of this instance
    """

    def __init__(self, max_periods: int, **kwargs):
        """
        Create a new instance of a Simple Moving Average.

        Arguments:
            max_periods: max periods
            kwargs: see [`BaseIndicator`][estrade.graph.base_indicator.BaseIndicator]
        """
        BaseIndicator.__init__(
            self,
            value_class=SimpleMovingAverageValue,
            **kwargs,
        )

        self.max_periods = max_periods
