import logging
import pytz
from dateutil import tz

from estrade.market_mixin import MarketOptionalMixin
from estrade.ref_mixin import RefMixin
from estrade.exceptions import EpicException

logger = logging.getLogger(__name__)


class Epic(MarketOptionalMixin, RefMixin):
    """
    Class used to define an Epic
    """
    def __init__(self, ref, candle_sets, timezone='UTC', currency_ref='EUR', ticks_in_memory=1):
        """
        Init an new instance of Epic
        :param ref: <str>
        :param candle_sets: [<estrade.candle_set.CandleSet>]
        :param timezone: pytz timezone
        """
        RefMixin.__init__(self, ref)
        logger.info('Init new Epic %s' % self.ref)

        self.timezone = timezone
        self.currency_ref = currency_ref
        self.strategies = []

        # init a market to None
        MarketOptionalMixin.__init__(self, None)
        self.candle_sets = candle_sets
        self.tradeable = True
        self.meta = {}
        self.ticks_in_memory = ticks_in_memory
        self.ticks = []
        logger.info('New epic created with ref %s and %d strategies' % (self.ref, len(self.strategies)))

    ##################################################
    # MARKET
    # note: market property is managed by parent AMarketOptionalClass
    ##################################################
    def _post_set_market(self):
        pass

    ##################################################
    # STRATEGIES
    ##################################################
    @property
    def strategies(self):
        return self._strategies

    @strategies.setter
    def strategies(self, strategies):
        self._strategies = strategies

    def add_strategy(self, strategy):
        logger.debug('add strategy %s to epic %s' % (strategy.ref, self.ref))
        self._strategies.append(strategy)
        logger.debug('epic %s (%s) now has %d strategies' % (self.ref, id(self), len(self._strategies)))

    ##################################################
    # CANDLE SETS
    ##################################################
    @property
    def candle_sets(self):
        """
        :return: [<estrade.candle_set.CandleSet>]
        """
        return self._candle_sets

    @candle_sets.setter
    def candle_sets(self, candle_sets):
        """
        Set list of CandleSet attached to instance
        :param candle_sets: [<estrade.candle_set.CandleSet>]
        :return:
        """
        self._candle_sets = []
        if candle_sets:
            if not isinstance(candle_sets, list):
                raise EpicException('Invalid candleSet {} : epic candle_sets params must be a list'.format(candle_sets))

            # import here to prevent import loop
            from estrade.candle_set import CandleSet

            for cs in candle_sets:
                if not isinstance(cs, CandleSet):
                    raise EpicException('Invalid candleSet: {}'.format(cs))
                logger.debug('Assign candleSet %s on epic %s' % (cs.timeframe, self.ref))
                cs.epic = self
                self._candle_sets.append(cs)

    def get_candle_set(self, timeframe):
        """
        Get candle_set by timeframe in this instance candle_set
        :param timeframe: <str>
        :return: <estrade.candle_set.CandleSet> or EpicException if not found
        """
        for cs in self.candle_sets:
            if cs.timeframe == timeframe:
                return cs
        raise EpicException('No candleSet found with timeframe %s in epic %s' % (timeframe, self.ref))

    ##################################################
    # TICKS
    ##################################################
    @property
    def current_tick(self):
        return self.ticks[-1] if self.ticks else None

    def _add_tick(self, tick):
        """
        Add a new tick to list of epic ticks
        :param tick: <estrade.tick.Tick> instance
        :return:
        """
        self.ticks.append(tick)
        self.ticks = self.ticks[(self.ticks_in_memory * -1):]

    ##################################################
    # TIMEZONE
    ##################################################
    @property
    def timezone(self):
        """
        Return TimeZone
        :return:
        """
        return self._timezone

    @timezone.setter
    def timezone(self, timezone):
        """
        Set Epic timezone

        Timezone is used to update tick date when a new <estrade.tick.Tick> instance is created.

        :param timezone: <str> that should be a valid pytz timezone.
        :return: EpicException if timezone is invalid
        """
        if timezone in pytz.all_timezones:
            self._timezone = timezone
        else:
            raise EpicException('Invalid timezone : {}'.format(timezone))

    ##################################################
    # EVENTS
    ##################################################
    def _check_timezone(self, tick):
        if (self.timezone != 'UTC' and tick.datetime.tzinfo != tz.gettz(self.timezone)) \
                or (self.timezone == 'UTC' and tick.datetime.tzinfo != tz.tzutc()):
            raise EpicException('Invalid tick timezone, found {} when expected {}'.format(
                tick.datetime.tzinfo,
                tz.gettz(self.timezone)
            ))
        return True

    def on_new_tick(self, tick):
        """
        Method used to handle every new tick received by market.
        note: This method is trigered by event 'market_before_new_tick'

        The main purpose is to update Epic high/low in meta.

        :param tick: <estrade.tick.Tick>
        :return:
        """
        if tick.epic != self:
            raise EpicException('Invalid tick epic: cannot update epic {}({}) with tick attached to epic {}({})'.format(
                self.ref,
                id(self),
                tick.epic.ref,
                id(tick.epic)
            ))

        logger.debug('Add new tick to epic %s (%s): %f' % (self.ref, id(self), tick.value))
        self._check_timezone(tick)

        # set tick as the current tick
        self._add_tick(tick)

        # dispatch tick to all candle sets
        for candle_set in self.candle_sets:
            logger.debug('dispatch tick to candle set %s' % candle_set.timeframe)
            candle_set.on_new_tick(tick)

        logger.debug('dispatch tick to %d strategies' % (len(self.strategies)))
        for strategy in self.strategies:
            logger.debug('dispatch tick to strategy %s' % strategy.ref)
            strategy.on_new_tick(tick)
