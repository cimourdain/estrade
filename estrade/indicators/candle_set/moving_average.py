from estrade.mixins.candle_set_indicator_mixin import CandleSetIndicatorMixin
import logging

logger = logging.getLogger(__name__)


class MovingAverageMixin(CandleSetIndicatorMixin):
    def __init__(self, periods: int, name: str) -> None:
        self.periods = periods
        self.sum_finished = 0
        self._sma = None
        CandleSetIndicatorMixin.__init__(self, name=name)

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
            self.sum_finished = sum(
                [c.close for c in self.candle_set.closed_candles(nb=(self.periods - 1))]
            )

            logger.debug('Update sum of finished candles to %d' % (self.sum_finished,))
        self._post_candle_close(closed_candle)


class SimpleMovingAverage(MovingAverageMixin):
    """
    Simple moving average indicator to add on a `estrade.CandleSet` object.

    Arguments:
        periods: nb of periods
        name: name of indicator

    !!! warning
        It is **strongly** advised to give a name to your indicator so you can fetch
        their values in your strategy (see `estrade.Strategy.get_indicator`)

    !!! example
        ```python
        from estrade import Epic, CandleSet, Market, SimpleMovingAverage, Strategy

        class MyStrategy(Strategy):
            def on_new_candle_opening_strategy(candle_set):
                # fetch indicator value
                sma200 = self.get_indicator(
                    epic_ref=candle_set.epic.ref,
                    timeframe=candle_set.timeframe,
                    indicator_name='sma200',
                )

                # check if indicator value is defined (for the first 199 ticks,
                # the Moving Average 200 will not be set)
                if sma200.value:
                    # do something....

                # fetch indicator value on a previous candle
                old_candle_sma200 = self.get_indicator(
                    epic_ref=candle_set.epic.ref,
                    timeframe=candle_set.timeframe,
                    indicator_name='sma200',
                    offset=4,
                )

                if old_candle_sma200:
                    # do something

            def on_new_tick_opening_strategy(tick):
                # to fetch indicator, the from a `on_new_tick...` method in strategy,
                # the easiest way is to use the `Strategy.get_indicator()` helper
                sma200 = self.get_indicator(timeframe='5minutes', name='sma200')

                # check if indicator value is defined (for the first 199 ticks,
                # the Moving Average 200 will not be set)
                if sma200.value:
                    # do something....


        if __name__ == '__main__':
            market = Market()
            epic = Epic(ref='MY_EPIC', market=market)
            sma200 = SimpleMovingAverage(periods=200, name='sma200')
            CandleSet(epic=epic, timeframe='5minutes', indicators=[sma200])
            # ...
            market.run()
        ```
    """

    @property
    def value(self):
        return round(self._sma, 2) if self._sma else None


class ExponentialMovingAverage(MovingAverageMixin):
    """
    Exponential moving average indicator to add on a `estrade.CandleSet` object.

    As all Candle Set Indicators, indicator value is stored :

     - On candle set : access it from your strategy with
     `CandleSet.indicator('<indicator_name>').value`
     - On every candle: access it from your strategy with
     `CandleSet.candles[<candle_idx>].indicators.get('<indicator_name>').value`


    Arguments:
        periods: nb of periods
        name: name of indicator

    !!! warning
        It is **strongly** advised to give a name to your indicator so you can fetch
        their values in your strategy (see `estrade.Strategy.get_indicator`)

    !!! example
        ```python
        from estrade import Epic, CandleSet, ExponentialMovingAverage, Strategy

        class MyStrategy(Strategy):
            def on_new_candle_opening_strategy(candle_set):
                # fetch indicator value
                ema200 = self.get_indicator(
                    epic_ref=candle_set.epic.ref,
                    timeframe=candle_set.timeframe,
                    indicator_name='ema200',
                )

                # check if indicator value is defined (for the first 199 ticks,
                # the Moving Average 200 will not be set)
                if ema200.value:
                    # do something....

                # fetch indicator value on a previous candle
                old_candle_ema200 = self.get_indicator(
                    epic_ref=candle_set.epic.ref,
                    timeframe=candle_set.timeframe,
                    indicator_name='ema200',
                    offset=4,
                )

                if old_candle_ema200:
                    # do something

            def on_new_tick_opening_strategy(tick):
                # to fetch indicator, the from a `on_new_tick...` method in strategy,
                # the easiest way is to use the `Strategy.get_indicator()` helper
                ema200 = self.get_indicator(timeframe='5minutes', name='ema200')

                # check if indicator value is defined (for the first 199 ticks,
                # the Moving Average 200 will not be set)
                if ema200.value:
                    # do something....


        if __name__ == '__main__':
            market = Market()
            epic = Epic(ref='MY_EPIC', market=market)
            ema200 = ExponentialMovingAverage(periods=200, name='ema200')
            CandleSet(epic=epic, timeframe='5minutes', indicators=[ema200])
            # ...
            market.run()
        ```

    """

    def __init__(self, periods: int, name: str) -> None:
        self._ema = None
        self.shooting_constant = 2 / (periods + 1)
        self.last_candle_sma = None
        MovingAverageMixin.__init__(self, periods=periods, name=name)

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
            logger.debug(
                f'Calulate EMA: {self.shooting_constant} * '
                f'({tick.value} - {self.last_candle_sma}) + {self.last_candle_sma}'
            )
            self._ema = (
                self.shooting_constant * (tick.value - self.last_candle_sma)
                + self.last_candle_sma
            )
