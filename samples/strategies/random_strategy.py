import logging
from datetime import timedelta
from random import choice, randint

from estrade import Strategy

logger = logging.getLogger(__name__)


class RandomStrategy(Strategy):
    """
    This strategy randomly open/close trades on every tick
    """
    random_factor = 1000

    def set_stop(self, tick_datetime):
        """
        Stop strategy after 3 trades.
        """
        if len(self.get_trades()) >= 3:
            logger.warning('Stop strategy after 3 trades')
            self.stopped = True

    def set_pause(self, tick_datetime):
        """
        Pause strategy for 30 mn if last trade was lost.
        """
        trades = self.get_trades(only_closed=True)
        if trades and self.meta.get('last_trade_causing_pause') != trades[-1] and trades[-1].result < 0:
            # pause for 30 mn after the last trade close datetime
            self.paused_until = trades[-1].last_tick.datetime + timedelta(minutes=30)
            self.meta['last_trade_causing_pause'] = trades[-1]
            logger.debug('Pause until %s' % self.paused_until)

    def on_new_tick_opening_strategy(self, tick):
        """
        Opening strategy: executed when number of opened trades < self.max_concurrent_trades

        this strategy randomly open a trade.
        """
        r = randint(0, self.random_factor)
        if r == 0:
            logger.info('open trade from random strategy')
            self.open_trade(
                epic=tick.epic,
                quantity=1,
                direction=choice([-1, 1]),
                stop_relative=5,
            )

    def on_new_tick_closing_strategy(self, tick):
        """
        Closing strategy: executed when a trade is open

        this strategy randomly close opened trades.
        """
        r = randint(0, self.random_factor)
        if r == 0:
            logger.info('close all trades from random strategy')
            self.close_all_trades()

