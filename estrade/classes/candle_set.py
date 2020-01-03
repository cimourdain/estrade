"""This file define the CandleSet object.
"""
import logging
import re
from datetime import timedelta

from estrade.classes.abstract.Acandle_set_indicator import AbstractCandleSetIndicator
from estrade.classes.candle import Candle
from estrade.classes.exceptions import CandleSetException
from estrade.classes.observer import Observable

logger = logging.getLogger(__name__)

ALLOWED_UT = [
    'ticks',
    'seconds',
    'minutes',
    'hours',
    'days',
]


class CandleSet(Observable):
    """
    A CandleSet create candles, add ticks and close a list of Candles<estrade.classes.candle.Candle>
    based on its timeframe.

    CandleSet receive ticks via its on_new_tick method :
        - if candle timeframe is over : close last candle and open a new one with the new tick
        - else append the tick to the current candle
    """
    def __init__(self, timeframe, indicators=None, max_candles_in_memory=100, log_level=None):
        """
        Init a new CandleSet.
        :param timeframe: <str>
            A timeframe define either a number of time units either a number of ticks.
            It defines how long will last every candle.

            eg. '3ticks', '56ticks', '30seconds', '3minutes', '4hours'
            notes:
                - unit must always be plural ('1hours' and not '1hour')
                - timeframe is splitted between (see timeframe setter)
                    - "ut" (time unit, eg. ticks, minutes, hours etc.)
                    - "nb" (nb of time unit)
        :param indicators: [children of <estrade.classes.Acandleset_indicators.AbstractCandleSetIndicators>]
        :param max_candles_in_memory: <int> defines the number of candles kept in memory by candleSet.
            - note: the bigger the number of candles, the slower your program will be
            - warning: keep this number high enough for your indicators using candle to work properly (eg. if you use
            an indicator for moving average 200, the max number of candles in memory should at least be 200)
            FIXME : control this on CandleSet init
        """
        logger.debug('Create new candle Set with timeframe %s' % timeframe)
        # CandleSet fire events to
        #   - indicators (to update indicator values)
        #   - strategies (on open/close candle)
        Observable.__init__(self)

        # epic is null on init
        # epic is set when CandleSet is set in candlesets of an <estrade.classes.epic.Epic> instance
        self.epic = None

        # ut and nb are set by timeframe setter
        self._ut = None
        self._nb = None
        self.timeframe = timeframe

        # init an empty list of candles
        self.candles = []

        # add candleSet indicators
        self.indicators = indicators

        self.max_candles_in_memory = max_candles_in_memory
        logger.debug('Candle set created with timeframe %s' % self.timeframe)

    ##################################################
    # REF
    ##################################################
    @property
    def ref(self):
        """
        Ref of a candle set cannot be set manually, it is a fixed name with format <epic_ref>-<nb><ut>
        example: NASDAQ-4hours
        :return: <str>
        """
        # TODO: handle ref if epic is not set
        return '{}-{}{}'.format(self.epic.ref, self.nb, self.ut)

    ##################################################
    # EPIC
    ##################################################
    @property
    def epic(self):
        """
        Return candle set epic
        :return: <estrade.classes.epic.Epic> instance
        """
        return self._epic

    @epic.setter
    def epic(self, epic):
        """
        Set candle set Epic
        :param epic: <estrade.classes.epic.Epic> instance or None
        :return:
        """
        # import Epic here to prevent ImportError
        from estrade.classes.epic import Epic
        if getattr(self, '_epic', None) and isinstance(self._epic, Epic) and self._epic != epic:
            raise CandleSetException('Cannot CandleSet %s to epic %s, as it was already assigned to epic %s' % (
                self.timeframe,
                epic.ref, self._epic.ref
            ))

        # allow empty epic
        if not epic:
            self._epic = None
            return

        if not isinstance(epic, Epic):
            raise CandleSetException('Invalid Epic')
        self._epic = epic

    ##################################################
    # TIMEFRAME -> UT + NB
    ##################################################
    @property
    def timeframe(self):
        """
        return tiemeframe value as provided in CandleSet instanciation.
        :return: <str>
        """
        return self._timeframe

    @staticmethod
    def check_timeframe_coherence(ut, nb):
        """
        Check that ut and nb (result of timeframe split) are coherent.
            - if ut is in minutes/seconds, nb must be inferior to 60 and nb/60 must be an integer.
            - if ut is in hours, nb must be inferior to 12 and nb/12 must be an integer.
            - as only one day period is supported: if ut is 'days' nb must be 1.

        note: nb and ut values individual consistencies are checked in ut and nb setters.
        :return: <bool>
        """
        if ut in ['seconds', 'minutes'] and int(60 / nb) != 60 / nb:
            raise CandleSetException(
                'Inconsistent UT: munutes/seconds timeframe must be '
                'inferior to 60 and {}/60 must be an integer.'.format(
                    nb
                )
            )
        elif ut in ['hours'] and int(12 / nb) != 12 / nb:
            raise CandleSetException(
                'Inconsistent UT: hour timeframe must be inferor or equal to 12. And {}/12 must be an int'.format(nb)
            )
        elif ut == 'days' and nb != 1:
            raise CandleSetException('Inconsistent UT, only 1days timeframe is allowed.')

        return True

    @timeframe.setter
    def timeframe(self, timeframe):
        """
        Split timeframe value provided in instance init to define:
            - ut: time unit name, that can be any value of ALLOWED_UT
            - nb: number of time units, that is a int
        :param timeframe: <str>
        :return:
        """
        regex_result = re.search(r'^(\d+)(\w+)$', timeframe)
        if not regex_result:
            raise CandleSetException(
                'Impossible to create candle set {}'.format(timeframe)
            )

        ut = regex_result.group(2)
        self.ut = ut
        nb = int(regex_result.group(1))
        self.nb = nb

        if CandleSet.check_timeframe_coherence(ut=ut, nb=nb):
            self._timeframe = timeframe

    @property
    def ut(self):
        """
        return CandleSet UT (time unit).
        See timeframe setter and ut setter to view allowed value.
        :return: <str>
        """
        return self._ut

    @ut.setter
    def ut(self, ut):
        """
        Check that ut found by the result of splitting timeframe is an authorized value.
        if it is valid, set the value of CandleSet.ut (time unit)
        :param ut: <str>
        :return:
        """
        if ut.lower() not in ALLOWED_UT:
            raise CandleSetException('Invalid CandleSet UT')
        self._ut = ut.lower()

    @property
    def nb(self):
        """
        Return the number of time units (see nb and timeframe setters)
        :return: <int>
        """
        return self._nb

    @nb.setter
    def nb(self, nb):
        """
        Define the number of time units. Set is called by the timeframe setter.
        The nb must be an int > 0
        :param nb: <int>
        :return:
        """
        if not isinstance(nb, int) or nb <= 0:
            raise CandleSetException(
                'Impossible to set a negative number for candleSet timeframe'
            )
        self._nb = nb

    ##################################################
    # INDICATORS
    ##################################################
    @property
    def indicators(self):
        """
        Return list of indicators
        :return: [childen of <estrade.classes.candleset_indicators.Acandle_set_indicator.AbstractCandleSetIndicator>]
        """
        return self._indicators

    @indicators.setter
    def indicators(self, indicators):
        """
        Set candle set indicators.
        :param indicators: [<estrade.classes.candleset_indicators.Acandle_set_indicator.AbstractCandleSetIndicator>]
        :return:
        """
        self._indicators = []

        if indicators:
            if not isinstance(indicators, list):
                raise CandleSetException('Indicators must be a list')

            for indicator in indicators:
                if not isinstance(indicator, AbstractCandleSetIndicator):
                    raise CandleSetException('Indicators must be instances of '
                                             'estrade.classes.Acandle_set_indicator.AbstractCandleSetIndicator')
                logger.debug('add indicator %s' % indicator.name)
                indicator.candle_set = self
                self._indicators.append(indicator)

    def indicator(self, indicator_name):
        """
        find an indicator in this instance indicators by its name.
        :param indicator_name: <str>
        :return: indicator instance or CandleSetException if not found
        """
        for indicator in self.indicators:
            if indicator.name == indicator_name:
                return indicator
        raise CandleSetException('No indicator found with name {}'.format(indicator_name))

    ##################################################
    # CANDLE GETTERS PROPERTIES
    ##################################################
    @property
    def current_candle(self):
        """
        return current candle. The current candle is the last candle in instance candles.
        :return: None if no candles in instance, else instance of <estrade.classes.candle.Candle>
        """
        return self.candles[-1] if self.candles else None

    @property
    def last_closed_candle(self):
        """
        return the last closed candle. The earlier closed candle in instance candles.
        :return: None if no candle closed, else instance of <estrade.classes.candle.Candle>
        """
        for c in reversed(self.candles):
            if c.closed:
                return c
        return None

    @property
    def new_candle_opened(self):
        """
        Check if current candle is newly opened (only one tick is in the last candle)
        :return: <bool>
        """
        return len(self.current_candle.ticks) <= 1 if self.current_candle else False

    @property
    def is_closing_candle(self):
        """
        This method check if the last candle will be closed on next tick.

        Warning: this method can only be used when this instance UT is ticks.
        It cannot be used on time based candlesets.
        :return: <bool>
        """
        if not self.ut == 'ticks':
            raise CandleSetException('Impossible to determine if it is the last tick on timed candles')
        return bool(len(self.candles[-1].ticks) == self.nb)

    @property
    def nb_closed_candles(self):
        """
        Get the number of closed candles
        :return: <int>
        """
        return len(self.candles) - 1 if self.candles else 0

    def closed_candles(self, nb=None):
        """
        Get a list of the last closed candles
        :param nb: <int> nb of closed candle to get
        :return: [<Candle>,] list of closed candles
        """
        if nb and nb > self.nb_closed_candles:
            raise CandleSetException('Impossible to get {} candles from {} bc only contains {}'.format(
                nb,
                self.ref,
                self.nb_closed_candles
            ))
        elif nb is None:
            nb = self.nb_closed_candles

        return self.candles[((nb + 1) * -1):-1]

    ##################################################
    # CANDLE OPEN/CLOSE METHODS
    ##################################################
    def round_candle_open_dt(self, dt):
        """
        For "timed" candle set (candleSet with an UT that is a time unit.). The open time must be rounded down.

        Eg. with a CandleSet having a '5minutes' timeframe. If the first tick received to open the candle is 22 min
        and 03 seconds, it must be rounded to the closest down division of 5minutes. In this case, the candle must
        be opened at 20mn and 00seconds.
        :param dt: <datetime.datetime>
        :return: <datetime.datetime>
        """
        if self.ut == 'seconds':
            return dt - timedelta(
                seconds=dt.second % self.nb, microseconds=dt.microsecond
            )
        elif self.ut == 'minutes':
            return dt - timedelta(
                minutes=dt.minute % self.nb,
                seconds=dt.second,
                microseconds=dt.microsecond,
            )
        elif self.ut == 'hours':
            return dt - timedelta(
                hours=dt.hour % self.nb,
                minutes=dt.minute,
                seconds=dt.second,
                microseconds=dt.microsecond,
            )
        elif self.ut == 'days':
            return dt - timedelta(
                days=dt.day % self.nb,
                hours=dt.hour,
                minutes=dt.minute,
                seconds=dt.second,
                microseconds=dt.microsecond,
            )
        return dt

    def create_new_candle(self, tick):
        """
        This method create a new candle from an tick and add it to the instance list of candles.
        This method fire candle opening events.

        :param tick: instance of <estrade.classes.tick.Tick>
        :return:
        """
        self.candles.append(Candle(
            open_at=self.round_candle_open_dt(tick.datetime),
            open_tick=tick
        ))
        self.candles = self.candles[(self.max_candles_in_memory * -1):]

    def is_current_candle_finished(self, dt):
        """
        Check if the current candle is finished.
        For CandleSet with a time unit in ticks, it means check if the current candle nb of ticks is reached.
        For CandleSet with a "timed" time unit, it means check if the received datetime is out of the current candle
        time range.

        note: the input datetime is the tick received datetime.

        :param dt: <datetime.datetime>
        :return: <bool>
        """
        if self.ut == 'ticks':
            if len(self.current_candle.ticks) >= self.nb:
                logger.debug('%s: current candle is finished' % self.timeframe)
                return True
        else:
            timedelta_params = {self.ut: self.nb}
            if self.current_candle.open_at + timedelta(**timedelta_params) <= dt:
                logger.debug(
                    '%s: current candle is finished: %s + %s <= %s' % (
                        self.timeframe,
                        self.current_candle.open_at,
                        timedelta_params,
                        dt,
                    )
                )
                return True
            else:
                logger.debug('%s: current candle is not finished %s + %s < %s' % (
                    self.timeframe,
                    self.current_candle.open_at,
                    timedelta_params,
                    dt
                ))
        return False

    def close_last_candle(self, tick):
        """
        This method close the current candle.
        :param tick: <estrade.classes.tick.Tick>
        :return:
        """
        if self.candles:
            self.current_candle.close_candle()

    ##################################################
    # EVENTS
    ##################################################
    def on_new_tick(self, tick):
        """
        This method is the entry point called on every new tick.
            - update candles (close and open candles if required or add tick to current candle)
            - send events (to update indicators, call strategies candle events etc.)
        :param tick: <estrade.classes.tick.Tick>
        :return: <bool>
        """
        logger.debug('%s : add tick in candle set: %s' % (self.timeframe, tick))
        if not self.epic:
            raise CandleSetException('Impossible to add tick to a candle set with no epic')

        self.fire('candle_set_before_on_new_tick_{}'.format(tick.epic.ref), tick=tick)
        new_candle_created = False
        current_candle_closed = False
        if not self.candles:
            logger.debug('%s : init list of candles with a new candle' % self.timeframe)
            self.create_new_candle(tick)
            new_candle_created = True
        else:
            logger.debug('%s: check if tick datetime %s require to close candle' % (self.timeframe, tick.datetime))
            if self.is_current_candle_finished(tick.datetime):
                logger.debug('%s: close candle' % self.timeframe)
                self.close_last_candle(tick)
                current_candle_closed = True

                logger.debug('%s: create a new candle' % self.timeframe)
                self.create_new_candle(tick)
                new_candle_created = True

            else:
                logger.debug('%s: add new tick to current candle' % self.timeframe)
                self.current_candle.on_new_tick(tick)

        # update indicators
        for indicator in self.indicators:

            if current_candle_closed:
                indicator.on_candle_close(closed_candle=self.candles[-2])
            if new_candle_created:
                indicator.on_new_candle(new_candle=self.candles[-1])

            indicator.on_new_tick(tick=tick)

        self.fire('candle_set_after_on_new_tick_{}'.format(tick.epic.ref), tick=tick)
        return True

    ##################################################
    # FLUSH
    ##################################################
    def flush(self):
        """
        This method delete all candles in current list of candles.
        Note: it is not used in the nominal workflow, its only purpose is to provide a helper that can be used in
        strategies if required.
        :return:
        """
        self.candles = []
