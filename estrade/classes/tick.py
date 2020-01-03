import arrow
from datetime import datetime

from estrade.classes.epic import Epic
from estrade.classes.exceptions import TickException


class Tick:
    """
    Class designed to manage a tick (market point value)
    """
    def __init__(self, epic, datetime, bid, ask):
        """
        Create a new tick.
        :param epic: <estrade.classes.epic.Epic> instance => tick epic
        :param datetime: <datetime.datetime> tick datetime
        :param bid: <float> market bid value for this tick
        :param ask: <float> market ask value for this tick
        :param timezone: <str> pytz timezone
        """
        self.epic = epic
        self.datetime = datetime
        self.ask = ask
        self.bid = bid

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
        :return: <float>
        """
        return round(self.ask - self.bid, 2)

    @property
    def value(self):
        """
        The tick value is the value exacly in the middle between bid and ask
        :return: <float>
        """
        return round(self.bid + (self.spread / 2), 2)

    @property
    def datetime(self):
        """
        return tick datetime
        :return: <arrow.Arrow>
        """
        return self._datetime

    @property
    def datetime_utc(self):
        """
        Return datetime as UTC
        :return:<arrow.Arrow>
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

    def to_dict(self, datetime_to_str=False):
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
