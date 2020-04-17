from datetime import timedelta
from typing import Callable, TYPE_CHECKING

from estrade.enums import Unit
from estrade.exceptions import TimeFrameException


if TYPE_CHECKING:  # pragma: no cover
    from arrow import Arrow  # type: ignore


class TimeframeMixin:
    def __init__(self, unit: Unit, unit_quantity: int):
        self.unit = unit
        self.unit_quantity = int(unit_quantity)
        self.check_unit_consistency()

        get_frame_start_func_map = {
            Unit.TICK: self._return_input,
            Unit.SECOND: self._get_timeframe_start_seconds,
            Unit.MINUTE: self._get_timeframe_start_minutes,
            Unit.HOUR: self._get_timeframe_start_hours,
            Unit.DAY: self._get_timeframe_start_days,
            Unit.WEEK: self._get_timeframe_start_week,
            Unit.MONTH: self._get_timeframe_start_month,
            Unit.YEAR: self._get_timeframe_start_year,
        }
        self._get_frame_start_func: Callable = get_frame_start_func_map[unit]

        self._timedelta = None
        if self.unit != Unit.TICK:
            self._timedelta = {f"{self.unit.name.lower()}s": self.unit_quantity}

        self._check_unit_consistency()

    def _check_unit_consistency(self) -> None:
        if self.unit in [Unit.TICK, Unit.YEAR]:
            return

        unit_quantity_modulo = {
            Unit.SECOND: 60,
            Unit.MINUTE: 60,
            Unit.HOUR: 12,
            Unit.DAY: 7,
            Unit.WEEK: 1,
            Unit.MONTH: 12,
        }
        if unit_quantity_modulo[self.unit] % self.unit_quantity != 0:
            raise TimeFrameException("Invalid timeframe Unit")
        return

    def get_frame_start(self, dt: "Arrow") -> "Arrow":
        """
        Get the timeframe start from a input datetime.

        Arguments:
            dt: datetime to find the timeframe start from.

        Returns:
            Start of the timeframe.
        """
        timeframe_start = self._get_frame_start_func(dt)
        return timeframe_start

    def get_frame_end(self, frame_start: "Arrow") -> "Arrow":
        """
        Get the timeframe end from a input datetime representing a timeframe start.

        Arguments:
            frame_start: datetime to find the timeframe end from.

        Returns:
            End of the timeframe.
        """
        if not self._timedelta:
            return frame_start
        frame_end = frame_start.shift(**self._timedelta)
        return frame_end

    def check_unit_consistency(self) -> bool:
        # TODO
        return True

    def _return_input(self, dt: "Arrow") -> "Arrow":
        return dt

    def _get_timeframe_start_seconds(self, dt: "Arrow") -> "Arrow":
        seconds_start = dt - timedelta(
            seconds=dt.second % self.unit_quantity,
            microseconds=dt.microsecond,
        )
        return seconds_start

    def _get_timeframe_start_minutes(self, dt: "Arrow") -> "Arrow":
        minutes_start = dt - timedelta(
            minutes=dt.minute % self.unit_quantity,
            seconds=dt.second,
            microseconds=dt.microsecond,
        )
        return minutes_start

    def _get_timeframe_start_hours(self, dt: "Arrow") -> "Arrow":
        hours_start = dt - timedelta(
            hours=dt.hour % self.unit_quantity,
            minutes=dt.minute,
            seconds=dt.second,
            microseconds=dt.microsecond,
        )
        return hours_start

    def _get_timeframe_start_days(self, dt: "Arrow") -> "Arrow":
        days_start = dt - timedelta(
            days=dt.weekday() % self.unit_quantity,
            hours=dt.hour,
            minutes=dt.minute,
            seconds=dt.second,
            microseconds=dt.microsecond,
        )
        return days_start

    def _get_timeframe_start_week(self, dt: "Arrow") -> "Arrow":
        week_start = dt - timedelta(
            days=dt.weekday(),
            hours=dt.hour,
            minutes=dt.minute,
            seconds=dt.second,
            microseconds=dt.microsecond,
        )
        return week_start

    def _get_timeframe_start_month(self, dt: "Arrow") -> "Arrow":
        def get_target_month(current_month, div):
            month_delta = (current_month - 1) % div
            target_month = current_month - month_delta
            return target_month

        month_start = dt.replace(
            month=get_target_month(dt.month, self.unit_quantity),
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return month_start

    def _get_timeframe_start_year(self, dt: "Arrow") -> "Arrow":
        def get_target_year(current_year, div):
            delta = current_year % div
            target_year = current_year - delta
            return target_year

        year_start = dt.replace(
            year=get_target_year(dt.year, self.unit_quantity),
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return year_start
