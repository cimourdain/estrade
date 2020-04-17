from typing import Dict, Optional, Type

from estrade.enums import PivotType as PivotTypeEnum
from estrade.graph.base_indicator import BaseIndicator, BaseIndicatorValue


class BasePivotType(BaseIndicatorValue):
    """Abstract Pivot Type."""

    @property
    def pivot(self) -> Optional[float]:
        """
        Pivot value.

        Returns:
            pivot value.
        """
        raise NotImplementedError

    @property
    def support1(self) -> Optional[float]:
        """
        Support 1 value.

        Returns:
            Support 1 value.
        """
        raise NotImplementedError

    @property
    def support2(self) -> Optional[float]:
        """
        Support 2 value.

        Returns:
            Support 2 value.
        """
        raise NotImplementedError

    @property
    def support3(self) -> Optional[float]:
        """
        Support 3 value.

        Returns:
            Support 3 value.
        """
        raise NotImplementedError

    @property
    def resistance1(self) -> Optional[float]:
        """
        Resistance 1 value.

        Returns:
            Resistance 1 value.
        """
        raise NotImplementedError

    @property
    def resistance2(self) -> Optional[float]:
        """
        Resistance 2 value.

        Returns:
            Resistance 2 value.
        """
        raise NotImplementedError

    @property
    def resistance3(self) -> Optional[float]:
        """
        Resistance 3 value.

        Returns:
            Resistance 3 value.
        """
        raise NotImplementedError


class PivotTypeClassic(BasePivotType):
    """
    Representation of a classic pivot value.

    Attributes:
        indicator (estrade.graph.base_indicator.BaseIndicator): Parent indicator.
        frame (estrade.graph.frame_set.Frame): Parent frame.
    """

    @property
    def pivot(self) -> Optional[float]:
        """
        Pivot value.

        Returns:
            pivot value (high + low + close) / 3.
        """
        if self.previous:
            pivot = round(
                (
                    self.previous.high_tick.value
                    + self.previous.low_tick.value
                    + self.previous.last_tick.value
                )
                / 3,
                2,
            )
            return pivot
        return None

    @property
    def support1(self) -> Optional[float]:
        """
        Support 1 value.

        Returns:
            Support 1 value (pivot * 2 - high).
        """
        pivot = self.pivot
        if pivot:
            return round((pivot * 2) - self.previous.high_tick.value, 2)  # type: ignore
        return None

    @property
    def support2(self) -> Optional[float]:
        """
        Support 2 value.

        Returns:
            Support 2 value (pivot - (high - low)).
        """
        pivot = self.pivot
        if pivot:
            return round(
                pivot
                - (
                    self.previous.high_tick.value  # type: ignore
                    - self.previous.low_tick.value  # type: ignore
                ),
                2,
            )
        return None

    @property
    def support3(self) -> Optional[float]:
        """
        Support 3 value.

        Returns:
            Support 3 value (low - (high - pivot) * 2).
        """
        pivot = self.pivot
        if pivot:
            return round(
                self.previous.low_tick.value  # type: ignore
                - ((self.previous.high_tick.value - pivot) * 2),  # type: ignore
                2,
            )
        return None

    @property
    def resistance1(self) -> Optional[float]:
        """
        Resistance 1 value.

        Returns:
            Resistance 1 value (pivot * 2 - low).
        """
        pivot = self.pivot
        if pivot:
            return round((pivot * 2) - self.previous.low_tick.value, 2)  # type: ignore
        return None

    @property
    def resistance2(self) -> Optional[float]:
        """
        Resistance 2 value.

        Returns:
            Resistance 2 value (pivot - (high - low)).
        """
        pivot = self.pivot
        if pivot:
            return round(
                pivot
                + (
                    self.previous.high_tick.value  # type: ignore
                    - self.previous.low_tick.value  # type: ignore
                ),
                2,
            )
        return None

    @property
    def resistance3(self) -> Optional[float]:
        """
        Resistance 3 value.

        Returns:
            Resistance 3 value (high + (pivot - low) * 2).
        """
        pivot = self.pivot
        if pivot:
            return round(
                self.previous.high_tick.value  # type: ignore
                + ((pivot - self.previous.low_tick.value) * 2),  # type: ignore
                2,
            )
        return None


class PivotTypeOLHC(PivotTypeClassic):
    """
    Representation of a HBCO pivot value.

    Attributes:
        indicator (estrade.graph.base_indicator.BaseIndicator): Parent indicator.
        frame (estrade.graph.frame_set.Frame): Parent frame.
    """

    @property
    def pivot(self) -> Optional[float]:
        """
        Pivot value.

        Returns:
            pivot value (high + low + close + current open) / 4.
        """
        if self.previous:
            pivot = round(
                (
                    self.previous.high_tick.value
                    + self.previous.low_tick.value
                    + self.previous.last_tick.value
                    + self.first_tick.value
                )
                / 4,
                2,
            )
            return pivot
        return None


PIVOT_TYPE_CLASS_MAPPING: Dict[PivotTypeEnum, Type[BasePivotType]] = {
    PivotTypeEnum.CLASSIC: PivotTypeClassic,
    PivotTypeEnum.OLHC: PivotTypeOLHC,
}


class Pivot(BaseIndicator):
    """
    Pivot Point representation.

    Attributes:
        value_class: Class to use to generate pivot values
        ref (str): reference of this instance
            (see `estrade.mixins.ref.RefMixin`)
        epic (estrade.epic.Epic): Epic Instance
            (see `estrade.graph.indicator.base_indicator.BaseIndicator`)
    """

    def __init__(
        self, pivot_type: PivotTypeEnum = PivotTypeEnum.CLASSIC, **kwargs
    ) -> None:
        """
        Create a new Daily Pivot.

        Arguments:
            pivot_type: Type of pivot (see PivotType enum)
            kwargs: see [`BaseIndicator`][estrade.graph.base_indicator.BaseIndicator]
        """
        value_class = PIVOT_TYPE_CLASS_MAPPING[pivot_type]
        BaseIndicator.__init__(
            self,
            value_class=value_class,
            **kwargs,
        )
