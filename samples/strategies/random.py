import logging
from random import choice, randint

from estrade import Strategy

logger = logging.getLogger(__name__)


class RandomStrategy(Strategy):
    """
    This strategy randomly open/close trades on every tick
    """
    random_factor = 1000

    def check_tick_time(self, tick):
        """
        Only run strategy between 10h and 11H
        """
        if 10 <= tick.datetime.hour < 11:
            return True
        return False

    def on_new_tick_opening_strategy(self, tick):
        """
        Opening strategy: executed when number of opened trades < self.max_concurrent_trades

        this strategy randomly open a trade.
        """
        r = randint(0, self.random_factor)
        if r == 0:
            logger.info('open trade from random strategy')
            self.open_trade(
                epic=tick.epic.ref,
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

