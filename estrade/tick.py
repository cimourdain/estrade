import logging
from datetime import datetime as pydatetime
from typing import Any, Dict, Optional, Union

import arrow  # type: ignore

from estrade.exceptions import TickException
from estrade.mixins import MetaMixin, TimedMixin


logger = logging.getLogger(__name__)


class Tick(MetaMixin, TimedMixin):
    """Market value at a given time representation.

    A [`Tick`][estrade.tick.Tick] represents the market value of a financial instrument
    at a given time.

    Attributes:
        bid (float): bid value
        ask (float): ask value

        datetime (arrow.Arrow): datetime of open
            (see `estrade.mixins.timed.TimedMixin`)
        meta (Dict[str, Any]): Dictionary free of use
            (see `estrade.mixins.meta.MetaMixin`)
    """

    def __init__(
        self,
        datetime: Union[pydatetime, arrow.Arrow],
        bid: Union[float, int],
        ask: Union[float, int],
        meta: Optional[Dict[Any, Any]] = None,
    ) -> None:
        """
        Instantiate a new tick object.

        Arguments:
            datetime: timezoned datetime
            bid: tick bid value
            ask: tick ask value
            meta: free dictionary where you can store anything you need

        !!! note
            The Tick instance can be created with either a python datetime or an
            [`Arrow`](https://arrow.readthedocs.io/) datetime.
            ```python
            --8<-- "tests/doc/reference/tick/test_datetime.py"
            ```
        """
        TimedMixin.__init__(self, datetime)
        self.ask = ask
        self.bid = bid
        if self.bid > self.ask:
            raise TickException(f"Tick bid {bid} cannot be superior to ask {ask}")
        MetaMixin.__init__(self, meta)

        # add tick to epic
        logger.debug(f"New tick : {self}")

    @staticmethod
    def check_value(v: Any) -> bool:
        """
        Check if bid/ask values are in either float or int.

        Returns:
            Is the bid/ask value of the correct type.
        """
        if not isinstance(v, (int, float)):
            return False
        return True

    @property
    def ask(self) -> float:
        """
        Return the current instance ask.

        Returns:
            tick ask value.
        """
        return self._ask

    @ask.setter
    def ask(self, ask: Union[int, float]) -> None:
        if not Tick.check_value(ask):
            raise TickException(f"invalid ask value: {ask}")
        self._ask = float(ask)

    @property
    def bid(self) -> float:
        """
        Return the current instance bid.

        Returns:
            tick bid value.
        """
        return self._bid

    @bid.setter
    def bid(self, bid: Union[int, float]) -> None:
        if not Tick.check_value(bid):
            raise TickException(f"invalid bid value: {bid}")
        self._bid = float(bid)

    @property
    def spread(self) -> float:
        """
        Return the difference between bid and ask.

        !!! example
            ```python
            --8<-- "tests/doc/reference/tick/test_spread.py"
            ```

        Returns:
            spread value
        """
        return round(self.ask - self.bid, 2)

    @property
    def value(self) -> float:
        """
        Return value in the middle between bid and ask.

        !!! example
            ```python
            --8<-- "tests/doc/reference/tick/test_value.py"
            ```

        Returns:
            median value between bid and ask
        """
        return round(self.bid + (self.spread / 2), 2)

    def __str__(self) -> str:
        """
        Return current instance as string.

        !!! example
            ```python
            --8<-- "tests/doc/reference/tick/test_str.py"
            ```

        Returns:
            String representation of tick (mainly used for logging)
        """
        return (
            f"{self.datetime.strftime('%Y-%m-%d %H:%M:%S')} : {self.value} "
            f"(bid: {self.bid}, ask: {self.ask}, spread: {self.spread})"
        )

    def asdict(self, datetime_to_str: bool = False) -> Dict[str, Any]:
        """
        Convert Tick to dictionary (mainly used for reporting).

        Arguments:
            datetime_to_str: convert the tick datetime to string?

        Returns:
            tick as dictionary containing

        !!! example
            ```python
            --8<-- "tests/doc/reference/tick/test_asdict.py"
            ```

        """
        return {
            "datetime": self.datetime.strftime("%Y-%m-%d %H:%M:%S")
            if datetime_to_str
            else self.datetime,
            "bid": self.bid,
            "ask": self.ask,
            "spread": self.spread,
            "value": self.value,
        }
