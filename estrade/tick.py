import arrow
from datetime import datetime
from typing import Any, Dict, Optional, Union

from estrade.exceptions import TickException
from estrade.epic import Epic


class Tick:
    """
    Class designed to manage a tick (market point value)

    Arguments:
        epic: epic instance
        datetime: tick datetime
        bid: tick bid value
        ask: tick ask value
        meta: free dictionary where you can store anything you need

    """

    def __init__(
        self,
        epic: 'Epic',
        datetime: Union[datetime, arrow.Arrow],
        bid: Union[float, int],
        ask: Union[float, int],
        meta: Optional[Dict[str, Any]] = None,
    ):

        # check epic
        if not isinstance(epic, Epic):
            raise TickException('Invalid tick epic')
        self.epic = epic

        # check datetime
        if not hasattr(datetime, 'tzinfo') or datetime.tzinfo is None:
            raise TickException('Invalid tick datetime')
        self._datetime = arrow.get(datetime).to(self.epic.timezone)

        # check bid/ask
        if not isinstance(ask, (int, float)):
            raise TickException('Invalid ask value')
        if not isinstance(bid, (int, float)):
            raise TickException('Invalid bid value')
        if bid > ask:
            raise TickException('Inconsistent bid/ask values.')
        self.ask = float(ask)
        self.bid = float(bid)

        self.meta = meta

    @property
    def spread(self):
        """
        The spread is the difference between bid and ask

        :return: (float) spread value
        """
        return round(self.ask - self.bid, 2)

    @property
    def value(self):
        """
        The tick value is the value exactly in the middle between bid and ask

        :return: (float) spread value
        """
        return round(self.bid + (self.spread / 2), 2)

    @property
    def datetime(self) -> arrow.Arrow:
        """
        Returns:
            Tick datetime
        """
        return self._datetime

    @property
    def datetime_utc(self) -> arrow.Arrow:
        """
        Return datetime as UTC, this method is useful when your tick datetime
        is zoned.

        :return: (`arrow.Arrow`): tick datetime zoned to UTC
        """
        return self._datetime.to('UTC')

    def __str__(self) -> str:
        """
        String representation of tick (mainly used for logging)
        :return:
        """
        return (
            f'@{self._datetime}: {self.value} '
            f'(bid: {self.bid}, ask: {self.ask}, spread: {self.spread})'
        )

    def to_json(self, datetime_to_str: bool = False) -> Dict[str, Any]:
        """
        Convert tick to dictionary (mainly used for reporting)
        :param datetime_to_str: <bool> => does the datetime value in dict must convert
        datetime to string?
        :return:
        """
        return {
            'datetime': self._datetime.strftime('%Y-%m-%d %H:%M:%S')
            if datetime_to_str
            else self._datetime,
            'bid': self.bid,
            'ask': self.ask,
            'spread': self.spread,
            'value': self.value,
        }

    @staticmethod
    def validate(tick: 'Tick') -> bool:
        if not isinstance(tick, Tick):
            raise TickException('Invalid tick instance')
        return True
