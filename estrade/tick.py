import arrow
from datetime import datetime

from estrade.epic import Epic
from estrade.exceptions import TickException


class Tick:
    """
    Class designed to manage a tick (market point value)

    :param estrade.Epic epic: tick epic
    :param arrow.Arrow datetime: tick datetime
    :param float bid: market bid value for this tick
    :param float ask: market ask value for this tick
    :param dict meta: free dictionary where you can store anything you need
    """
    def __init__(self, epic, datetime, bid, ask, meta=None):
        """
        Create a new tick.
        """
        self.epic = epic
        self.datetime = datetime
        self.ask = ask
        self.bid = bid

        self.meta = meta

    @property
    def epic(self):
        return self._epic

    @epic.setter
    def epic(self, epic):

        if not isinstance(epic, Epic):
            raise TickException('Invalid tick epic')

        self._epic = epic

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
    def datetime(self):
        """
        return tick datetime

        :return: `arrow.Arrow`: tick datetime
        """
        return self._datetime

    @property
    def datetime_utc(self):
        """
        Return datetime as UTC, this method is useful when your tick datetime
        is zoned.

        :return: (`arrow.Arrow`): tick datetime zoned to UTC
        """
        return self._datetime.to('UTC')

    @datetime.setter
    def datetime(self, dt):
        """
        Set tick datetime, apply timezone to received datetime.
        :param dt: <datetime.datetime>
        :return:
        """
        if not isinstance(dt, (datetime, arrow.Arrow)):
            raise TickException('Invalid tick datetime')

        if not dt.tzinfo:
            raise TickException('Tick datetime must be localized')

        dt = arrow.get(dt).to(self.epic.timezone)

        self._datetime = dt

    def __str__(self):
        """
        String representation of tick (mainly used for logging)
        :return:
        """
        return '@{}: {} (bid: {}, ask: {}, spread: {})'.format(
            self.datetime, self.value, self.bid, self.ask, self.spread
        )

    def to_json(self, datetime_to_str=False):
        """
        Convert tick to dictionary (mainly used for reporting)
        :param datetime_to_str: <bool> => does the datetime value in dict must convert datetime to string?
        :return:
        """
        return {
            'datetime': self.datetime.strftime('%Y-%m-%d %H:%M:%S') if datetime_to_str else self.datetime,
            'bid': self.bid,
            'ask': self.ask,
            'spread': self.spread,
            'value': self.value
        }

    @staticmethod
    def validate(tick):
        if not isinstance(tick, Tick):
            raise TickException('Invalid tick instance')
        return True
