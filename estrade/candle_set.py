"""This file define the CandleSet object.
"""
import logging
import re
from datetime import timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING

from arrow import Arrow

from estrade.epic import Epic
from estrade.mixins.candle_set_indicator_mixin import CandleSetIndicatorMixin
from estrade.candle import Candle
from estrade.exceptions import CandleSetException
from estrade.observer import Observable

if TYPE_CHECKING:
    from estrade.tick import Tick

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
    A CandleSet create candles, add ticks and close a list of `estrade.Candles`
    based on its timeframe.

    Arguments:
        epic: Epic instance to attach to CandleSet
        timeframe: Define either a number of time units either a number of ticks.
        indicators: List of indicators attached to CandleSet
        max_candles_in_memory: Number of candles kept in memory

    !!! info "timeframe"
        - unit must always be plural ('1hours' and not '1hour')
        - inside a CandleSet timeframe is splitted between:
            - `ut` (time unit, eg. ticks, minutes, hours etc.)
            - `nb` (nb of time unit)
        - eg: '3ticks', '56ticks', '30seconds', '3minutes', '4hours'.

    !!! info "max_candles_in_memory"
        - note: the bigger the number of candles, the slower your program will be
        - warning: keep this number high enough for your indicators using candle
        to work properly
        (eg. if you use an indicator for moving average 200, the max number of candles
        in memory should at least be 200)

    !!! example
        Example of usage of candle set

        ```python
        from estrade import Epic, CandleSet, Market

        market = Market()
        # create candle sets with your timeframes and assign them to your epics
        epic1 = Epic(market=market, ref='EPIC1')
        cs_21ticks = CandleSet(epic=epic1, timeframe='21ticks')
        cs_1mn1 = CandleSet(epic=epic1, timeframe='1minutes')

        epic2 = EPIC(market=market, ref='EPIC2')
        cs_1mn2 = CandleSet(epic=epic2, timeframe='1minutes')
        cs_4hours = CandleSet(epic=epic2, timeframe='4hours')

        ```

    """

    def __init__(
        self,
        epic: Epic,
        timeframe: str,
        indicators: Optional[List[CandleSetIndicatorMixin]] = None,
        max_candles_in_memory: int = 100,
    ) -> None:
        logger.debug('Create new candle Set with timeframe %s' % timeframe)
        # CandleSet fire events to
        #   - indicators (to update indicator values)
        #   - strategies (on open/close candle)
        Observable.__init__(self)

        # epic is null on init
        # epic is set when CandleSet is set in candlesets of an
        # `estrade.epic.Epic` instance
        if not isinstance(epic, Epic):
            raise CandleSetException('Invalid epic')
        self.epic: Epic = epic
        self.epic.candle_sets.append(self)

        # ut and nb are set by timeframe setter
        self.ut: Optional[str] = None
        self.nb: Optional[int] = None
        self.timeframe = timeframe

        # init an empty list of candles
        self.candles: List[Candle] = []

        # add candleSet indicators
        self.indicators = indicators

        self.max_candles_in_memory = max_candles_in_memory
        logger.debug('Candle set created with timeframe %s' % self.timeframe)

    ##################################################
    # REF
    ##################################################
    @property
    def ref(self) -> str:
        """
        Returns:
            the reference (~name) of a Candle Set.

        !!! info
            Ref of a candle set cannot be set manually, it is a fixed name with
            format `<epic_ref>-<nb><ut>`

            example: NASDAQ-4hours

        !!! note
            CandleSet has a ref `undefined` while no epic is set.

        """
        return f'{self.epic.ref}-{self.nb}{self.ut}'

    ##################################################
    # TIMEFRAME -> UT + NB
    ##################################################
    @property
    def timeframe(self) -> str:
        """
        Returns:
            the timeframe value as provided in CandleSet instanciation.

        """
        return self._timeframe

    @timeframe.setter
    def timeframe(self, timeframe: str) -> None:
        """
        Split timeframe value provided in instance init to define:
            - ut: time unit name, that can be any value of ALLOWED_UT
            - nb: number of time units, that is a int
        :param timeframe: <str>
        :return:
        """
        nb, ut = self.split_timeframe(timeframe)

        if self.check_timeframe_coherence(ut=ut, nb=nb):
            self.ut = ut
            self.nb = nb
            self._timeframe: str = timeframe

    @staticmethod
    def validate_timeframe(timeframe: str) -> bool:
        nb, ut = CandleSet.split_timeframe(timeframe)
        if CandleSet.check_timeframe_coherence(ut, nb):
            return True
        return False

    @staticmethod
    def split_timeframe(timeframe: str) -> Tuple[int, str]:
        regex_result = re.search(r'^(\d+)(\w+)$', timeframe)
        if not regex_result:
            raise CandleSetException(f'Impossible to create candle set {timeframe}')
        ut = regex_result.group(2).lower()
        nb = int(regex_result.group(1))

        if ut.lower() not in ALLOWED_UT:
            raise CandleSetException('Invalid timeframe UT')
        try:
            nb = int(nb)
        except ValueError:
            raise CandleSetException('Invalid timeframe nb')

        if nb <= 0:
            raise CandleSetException('Invalid timeframe NB value')

        return nb, ut

    @staticmethod
    def check_timeframe_coherence(ut: str, nb: int) -> bool:
        """
        Check that ut and nb (result of timeframe split) are coherent.

         - if ut is in minutes/seconds, nb must be inferior to 60 and nb/60 must be
         an integer.
         - if ut is in hours, nb must be inferior to 12 and nb/12 must be an integer.
         - as only one day period is supported: if ut is 'days' nb must be 1.

        !!! note
            nb and ut values individual consistencies are checked in ut and nb setters.

        """
        if ut in ['seconds', 'minutes'] and int(60 / nb) != 60 / nb:
            raise CandleSetException(
                f'Inconsistent UT: munutes/seconds timeframe must be '
                f'inferior to 60 and {nb}/60 must be an integer.'
            )
        elif ut in ['hours'] and int(12 / nb) != 12 / nb:
            raise CandleSetException(
                f'Inconsistent UT: hour timeframe must be inferor or equal to 12. '
                f'And {nb}/12 must be an int'
            )
        elif ut == 'days' and nb != 1:
            raise CandleSetException(
                'Inconsistent UT, only 1days timeframe is allowed.'
            )

        return True

    ##################################################
    # INDICATORS
    ##################################################
    @property
    def indicators(self) -> Optional[List[CandleSetIndicatorMixin]]:
        """
        Returns:
            Return list of indicators attached to candle set
        """
        return self._indicators

    @indicators.setter
    def indicators(self, indicators: Optional[List[CandleSetIndicatorMixin]]) -> None:
        """
        Set candle set indicators.
        """
        self._indicators = []

        if indicators:
            if not isinstance(indicators, list):
                raise CandleSetException('Indicators must be a list')

            for indicator in indicators:
                if not isinstance(indicator, CandleSetIndicatorMixin):
                    raise CandleSetException(
                        'Indicators must be instances of '
                        'estrade.Acandle_set_indicator.AbstractCandleSetIndicator'
                    )
                logger.debug('add indicator %s' % indicator.name)
                indicator.candle_set = self
                self._indicators.append(indicator)

    def indicator(self, indicator_name: str) -> Optional[CandleSetIndicatorMixin]:
        """
        Arguments:
            indicator_name: name of the indicator to fetch

        Raises:
            CandleSetException: if no indicator is found with this name

        Returns:
            the an indicator in this instance indicators by its name.
        """
        if self.indicators:
            for indicator in self.indicators:
                if indicator.name == indicator_name:
                    return indicator
        raise CandleSetException(f'No indicator found with name {indicator_name}')

    ##################################################
    # CANDLE GETTERS PROPERTIES
    ##################################################
    @property
    def current_candle(self) -> Optional[Candle]:
        """
        Returns:
            return the candle that is currently fed by ticks received.

        """
        return self.candles[-1] if self.candles else None

    @property
    def last_closed_candle(self) -> Optional[Candle]:
        """
        Returns:
            return the last candle that was closed.

        !!! info
            At beginning of Market run, the ticks feed a the first candle,
            while this first candle is not closed (=its timeframe over) the
            `last_closed_candle` is empty.
            As a consequence, in your strategies, it is strongly advised
            that your check that the `last_closed_candle` is not None before using it.
        """
        for c in reversed(self.candles):
            if c.closed:
                return c
        return None

    @property
    def new_candle_opened(self) -> bool:
        """
        Check if current candle is newly opened (only one tick is in the last candle)

        Returns:
            True if the current candle has only one tick.
        """
        return len(self.current_candle.ticks) <= 1 if self.current_candle else False

    @property
    def is_closing_candle(self) -> bool:
        """
        This method check if the last candle will be closed on next tick.

        Returns:
            True if the current candle will be closed on next tick, else False

        Raises:
            CandleSetException: if attempt to use this method on a timed CandleSet.

        !!! warning
            This method can only be used when this instance UT is ticks.
            It cannot be used on time based candlesets.

        """
        if not self.ut == 'ticks':
            raise CandleSetException(
                'Impossible to determine if it is the last tick on timed candles'
            )
        return bool(len(self.candles[-1].ticks) == self.nb)

    @property
    def nb_closed_candles(self) -> int:
        """
        Returns:
            The number of closed candles

        !!! warning
            when the number of closed candle reach the `max_candles_in_memory` value
            set on init, then this value will always returns the `max_candles_in_memory`

        """
        return len(self.candles) - 1 if self.candles else 0

    def closed_candles(self, nb: int = None) -> List[Candle]:
        """
        Get a list of the last closed candles

        Arguments:
            nb: nb of closed candles to retrieve

        """
        if nb and nb > self.nb_closed_candles:
            raise CandleSetException(
                f'Impossible to get {nb} candles from {self.ref} '
                f'bc only contains {self.nb_closed_candles}'
            )
        elif nb is None:
            nb = self.nb_closed_candles

        return self.candles[((nb + 1) * -1) : -1]

    ##################################################
    # CANDLE OPEN/CLOSE METHODS
    ##################################################
    @staticmethod
    def round_candle_open_datetime(tick_datetime: Arrow, nb: int, ut: str) -> Arrow:
        """
        For "timed" candle set (candleSet with an UT that is a time unit.).
        The open time must be rounded down.

        Eg. with a CandleSet having a '5minutes' timeframe. If the first tick received
        to open the candle is 22 min and 03 seconds, it must be rounded to the closest
        down division of 5minutes. In this case, the candle must be opened
        at 20mn and 00seconds.

        Arguments:
            tick_datetime: the tick datetime to round to the timeframe open
            nb: the timeframe number of UT
            ut: the time unit

        Returns:
            Datetime rounded to the timeframe open
        """
        if ut == 'seconds':
            return tick_datetime - timedelta(
                seconds=tick_datetime.second % nb,
                microseconds=tick_datetime.microsecond,
            )
        elif ut == 'minutes':
            return tick_datetime - timedelta(
                minutes=tick_datetime.minute % nb,
                seconds=tick_datetime.second,
                microseconds=tick_datetime.microsecond,
            )
        elif ut == 'hours':
            return tick_datetime - timedelta(
                hours=tick_datetime.hour % nb,
                minutes=tick_datetime.minute,
                seconds=tick_datetime.second,
                microseconds=tick_datetime.microsecond,
            )
        elif ut == 'days':
            return tick_datetime - timedelta(
                days=tick_datetime.day % nb,
                hours=tick_datetime.hour,
                minutes=tick_datetime.minute,
                seconds=tick_datetime.second,
                microseconds=tick_datetime.microsecond,
            )
        return tick_datetime

    def _create_new_candle(self, tick: 'Tick') -> None:
        """
        This method create a new candle from an tick and add it to
        the instance list of candles.
        This method fire candle opening events.

        :param tick: instance of <estrade.tick.Tick>
        :return:
        """
        if self.epic is None:
            raise CandleSetException('Cannot create candle when epic is not set.')

        self.candles.append(
            Candle(timeframe=self.timeframe, epic_ref=self.epic.ref, open_tick=tick)
        )
        self.candles = self.candles[(self.max_candles_in_memory * -1) :]

    def _is_current_candle_finished(self, dt: Arrow) -> bool:
        """
        Check if the current candle is finished.
        For CandleSet with a time unit in ticks, it means check if
        the current candle nb of ticks is reached.
        For CandleSet with a "timed" time unit, it means check if
        the received datetime is out of the current candle
        time range.

        note: the input datetime is the tick received datetime.

        :param dt: <datetime.datetime>
        :return: <bool>
        """
        if self.ut is None or self.nb is None:
            raise CandleSetException(
                'Cannot define if candle is finished when' 'ut or nb is not defined.'
            )
        if not self.current_candle:
            raise CandleSetException(
                'Cannot define if candle is finished when no '
                'tick were added to candleSet.'
            )
        if self.ut == 'ticks':
            if len(self.current_candle.ticks) >= self.nb:
                logger.debug('%s: current candle is finished' % self.timeframe)
                return True
        else:
            timedelta_params = {self.ut: self.nb}
            if self.current_candle.open_at + timedelta(**timedelta_params) <= dt:
                logger.debug(
                    '%s: current candle is finished: %s + %s <= %s'
                    % (
                        self.timeframe,
                        self.current_candle.open_at,
                        timedelta_params,
                        dt,
                    )
                )
                return True
            else:
                logger.debug(
                    '%s: current candle is not finished %s + %s < %s'
                    % (
                        self.timeframe,
                        self.current_candle.open_at,
                        timedelta_params,
                        dt,
                    )
                )
        return False

    def _close_last_candle(self) -> None:
        """
        This method close the current candle.
        """
        if self.current_candle:
            self.current_candle.close_candle()

    ##################################################
    # EVENTS
    ##################################################
    def on_new_tick(self, tick: 'Tick') -> None:
        """
        This method is the entry point called on every new tick.

         - update candles (close and open candles if required or add tick
         to current candle)
         - send events (to update indicators, call strategies candle events etc.)

        Arguments:
            tick: new tick received to be dispatched to candles and indicators

        """
        logger.debug('%s : add tick in candle set: %s' % (self.timeframe, tick))
        if not self.epic:
            raise CandleSetException(
                'Impossible to add tick to a candle set with no epic'
            )

        self.fire(f'candle_set_before_on_new_tick_{tick.epic.ref}', tick=tick)
        new_candle_created = False
        current_candle_closed = False
        if not self.current_candle:
            logger.debug('%s : init list of candles with a new candle' % self.timeframe)
            self._create_new_candle(tick)
            new_candle_created = True
        else:
            logger.debug(
                '%s: check if tick datetime %s require to close candle'
                % (self.timeframe, tick.datetime)
            )
            if self._is_current_candle_finished(tick.datetime):
                logger.debug('%s: close candle' % self.timeframe)
                self._close_last_candle()
                current_candle_closed = True

                logger.debug('%s: create a new candle' % self.timeframe)
                self._create_new_candle(tick)
                new_candle_created = True

            else:
                logger.debug('%s: add new tick to current candle' % self.timeframe)
                self.current_candle.on_new_tick(tick)

        # update indicators
        if self.indicators:
            for indicator in self.indicators:

                if current_candle_closed:
                    indicator.on_candle_close(closed_candle=self.candles[-2])
                if new_candle_created:
                    indicator.on_new_candle(new_candle=self.candles[-1])

                indicator.on_new_tick(tick=tick)
                self.current_candle.indicators[indicator.name] = indicator.value

        self.fire(f'candle_set_after_on_new_tick_{tick.epic.ref}', tick=tick)
