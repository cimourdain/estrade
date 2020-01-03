from estrade.classes.abstract.Acandle_set_indicator import AbstractCandleSetIndicator
import logging

logger = logging.getLogger(__name__)


class AbstractMovingAverage(AbstractCandleSetIndicator):
    def __init__(self, periods, *args, **kwargs):
        self.periods = periods
        self.sum_finished = 0
        self._sma = None
        AbstractCandleSetIndicator.__init__(self, *args, **kwargs)

    def _post_on_new_tick(self, tick):
        pass

    def on_new_tick(self, tick):
        logger.debug('Update Moving average %s with %d' % (self.name, tick.value))
        if len(self.candle_set.candles) >= self.periods:
            self._sma = (tick.value + self.sum_finished) / self.periods
            logger.debug('indicator %s: set mm value to %d' % (self.name, self._sma))
            self.candle_set.candles[-1].indicators[self.name] = self._sma

        self._post_on_new_tick(tick)

    def on_new_candle(self, new_candle):
        pass

    def _post_candle_close(self, closed_candle):
        pass

    def on_candle_close(self, closed_candle):
        if self.candle_set.nb_closed_candles >= (self.periods - 1):
            self.sum_finished = sum([c.close for c in self.candle_set.closed_candles(nb=(self.periods - 1))])

            logger.debug('Update sum of finished candles to %d' % (
                self.sum_finished,
            ))
        self._post_candle_close(closed_candle)


class SimpleMovingAverage(AbstractMovingAverage):

    @property
    def value(self):
        return round(self._sma, 2) if self._sma else None


class ExponentialMovingAverage(AbstractMovingAverage):

    def __init__(self, periods, *args, **kwargs):
        self._ema = None
        self.shooting_constant = 2 / (periods + 1)
        self.last_candle_sma = None
        AbstractMovingAverage.__init__(self, *args, periods=periods, **kwargs)

    @property
    def value(self):
        return round(self._ema, 2) if self._ema else None

    @property
    def sma(self):
        return round(self._sma, 2) if self._sma else None

    def _post_candle_close(self, _):
        if self._sma:
            self.last_candle_sma = self._sma

    def _post_on_new_tick(self, tick):
        if self.last_candle_sma:
            logger.debug('Calulate EMA: {} * ({} - {}) + {}'.format(
                self.shooting_constant,
                tick.value,
                self.last_candle_sma,
                self.last_candle_sma
            ))
            self._ema = self.shooting_constant * (tick.value - self.last_candle_sma) + self.last_candle_sma
