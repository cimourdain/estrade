import logging
from typing import Optional

from estrade.enums import CandleColor, CandleType
from estrade.graph.base_indicator import BaseIndicator, BaseIndicatorValue


logger = logging.getLogger(__name__)


class BaseCandle(BaseIndicatorValue):
    """
    Abstract representation of a Candle.

    Attributes:
        indicator (estrade.graph.base_indicator.BaseIndicator): Parent indicator.
        frame (estrade.graph.frame_set.Frame): Parent frame.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Create a new Candle for the input Frame.

        Arguments:
            indicator: parent indicator
            frame: parent frame
        """
        BaseIndicatorValue.__init__(self, *args, **kwargs)

    @property
    def open(self) -> float:
        raise NotImplementedError

    @property
    def high(self) -> float:
        raise NotImplementedError

    @property
    def low(self) -> float:
        raise NotImplementedError

    @property
    def last(self) -> float:
        raise NotImplementedError

    @property
    def close(self) -> Optional[float]:
        raise NotImplementedError

    @property
    def color(self) -> Optional[CandleColor]:
        """
        Color of the current instance.

        Returns:
            Color as [`CandleColor`][estrade.enums.CandleColor] enum.
        """
        if not self.open or not self.last:
            return None

        if self.last > self.open:
            return CandleColor.GREEN
        elif self.last < self.open:
            return CandleColor.RED
        return CandleColor.BLACK

    @property
    def height(self) -> float:
        """
        Height of candle (high - low).

        ```
                |  ┐
                |  |
                ┴  |
               | | |
               | | |<-- height
               | | |
                ┬  |
                |  |
                |  ┘
        ```
        """
        return self.high - self.low

    @property
    def body(self) -> Optional[float]:
        """
        Absolute difference between open and close of the candle.

        ```
                |
                |
                ┴  ┐
               | | |
               | | |<-- body
               | | |
                ┬  ┘
                |
                |
        ```
        """
        if not self.open or not self.last:
            return None

        return round(abs(self.open - self.last), 2)

    @property
    def head(self) -> Optional[float]:
        """
        Distance between the highest value and the highest from (open/last).

        ```
                |  ┐
                |  | <-- head
                ┴  ┘
               | |
               | |
               | |
                ┬
                |
                |
        ```
        """
        if not self.open or not self.last:
            return None
        return round(self.high - (max(self.open, self.last)), 2)

    @property
    def tail(self) -> Optional[float]:
        """
        Distance between the lowest value and the lowest from (open/last).

        ```
                |
                |
                ┴
               | |
               | |
               | |
                ┬  ┐
                |  | <-- tail
                |  ┘
        ```
        """
        if not self.open or not self.last:
            return None

        return round(min(self.open, self.last) - self.low, 2)


class JapaneseCandle(BaseCandle):
    """
    Representation of a Classic candle in a Candle sticks chart.

    Attributes:
        indicator (estrade.graph.base_indicator.BaseIndicator): Parent indicator.
        frame (estrade.graph.frame_set.Frame): Parent frame.
    """

    @property
    def open(self) -> float:
        """
        Return candle open value.

        Returns:
            Candle first received tick value.
        """
        return round(self.first_tick.value, 2)

    @property
    def high(self) -> float:
        """
        Return candle low value.

        Returns:
            Candle highest received tick value.
        """
        return round(self.high_tick.value, 2)

    @property
    def low(self) -> float:
        """
        Return candle low value.

        Returns:
            Candle lowest received tick value.
        """
        return round(self.low_tick.value, 2)

    @property
    def last(self) -> float:
        """
        Return candle last value.

        Returns:
            Candle last received tick value.
        """
        return round(self.last_tick.value, 2)

    @property
    def close(self) -> Optional[float]:
        """
        Return candle close value.

        !!! note
            The return value is `None` when the candle is not closed.

        Returns:
            Candle close value
        """
        if self.closed:
            return round(self.last_tick.value, 2)
        return None


class HeikinAshiCandle(BaseCandle):
    """
    Representation of a Heikin Ashi candle in a Candle sticks chart.

    Attributes:
        indicator (estrade.graph.base_indicator.BaseIndicator): Parent indicator.
        frame (estrade.graph.frame_set.Frame): Parent frame.
    """

    @property
    def open(self) -> float:
        """
        Return candle open value.

        Returns:
            Open tick value when the candle is the first of its CandleSet, otherwise
            this function returns the mean between the previous candle open and
            last value.
        """
        if not self.previous:
            return round(self.first_tick.value, 2)
        return round((self.previous.open + self.previous.last) / 2, 2)  # type: ignore

    @property
    def high(self) -> float:
        """
        Return candle high value.

        Returns:
            Maximum from open, last and low tick value.
        """
        return round(max(self.open, self.high_tick.value, self.last), 2)

    @property
    def low(self) -> float:
        """
        Return candle low value.

        Returns:
            Minimum from open, last and low tick value.
        """
        return round(min(self.open, self.low_tick.value, self.last), 2)

    @property
    def last(self) -> float:
        """
        Return candle last value.

        Returns:
            Mean of open tick, high tick, low tick and last tick values.
        """
        return round(
            (
                self.first_tick.value
                + self.high_tick.value
                + self.low_tick.value
                + self.last_tick.value
            )
            / 4,
            2,
        )

    @property
    def close(self) -> Optional[float]:
        """
        Return candle close value.

        !!! note
            The return value is `None` when the candle is not closed.

        Returns:
            Candle close value
        """
        if self.closed:
            return self.last
        return None


class CandleSet(BaseIndicator):
    """
    Instance of a CandleSet.

    Attributes:
        value_class (Optional[estrade.graph.candle_set.CandleType]): Type of Candle
        frame_set (Optional[estrade.graph.frame_set.FrameSet]): The FrameSet instance
            that send ticks to this instance.
        market_open_only (bool): apply this indicator only when market is open.
        ref (str): reference of this instance
    """

    def __init__(
        self,
        candle_type: CandleType = CandleType.CLASSIC,
        **kwargs,
    ) -> None:
        """
        Create a new instance of a CandleSet.

        Arguments:
            candle_type: Type of candles to generate.
            kwargs: see [`BaseIndicator`][estrade.graph.base_indicator.BaseIndicator]
        """
        value_class = (
            JapaneseCandle if candle_type == CandleType.CLASSIC else HeikinAshiCandle
        )
        BaseIndicator.__init__(self, value_class=value_class, **kwargs)
