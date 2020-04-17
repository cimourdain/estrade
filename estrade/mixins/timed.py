from datetime import datetime as pydatetime
from typing import Union

import arrow  # type: ignore

from estrade.exceptions import TimeException


class TimedMixin:
    def __init__(self, datetime: Union[pydatetime, arrow.Arrow]) -> None:
        self.datetime = datetime

    @property
    def datetime(self) -> arrow.Arrow:
        """
        Object datetime.

        Returns:
            object datetime
        """
        return self._datetime

    @datetime.setter
    def datetime(self, dt: Union[pydatetime, arrow.Arrow]) -> None:
        """
        Set datetime.

        Raises:
            estrade.exceptions.TimeException: if datetime has no timezone defined.

        """
        if not hasattr(dt, "tzinfo") or dt.tzinfo is None:
            raise TimeException(
                f"Invalid {self.__class__.__name__} datetime, "
                f"a timezoned datetime is required."
            )
        # convert to arrow.Arrow
        if isinstance(dt, pydatetime):
            dt = arrow.get(dt)

        self._datetime = dt

    @property
    def datetime_utc(self) -> arrow.Arrow:
        """
        Object datetime as UTC.

        Returns:
            datetime as UTC, this method is useful when datetime is zoned.
        """
        return self.datetime.to("UTC")
