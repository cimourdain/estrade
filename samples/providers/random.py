from random import randint, uniform
from datetime import timedelta

from estrade import Tick, Provider


class RandomProvider(Provider):

    def __init__(self, start_date, end_date, **kwargs):
        self.start_date = start_date
        self.end_date = end_date
        Provider.__init__(self, **kwargs)

    def generate_ticks(self):
        tick_value = 1000
        dt = self.start_date
        while dt < self.end_date:
            # generate nez tick value and date
            tick_value = tick_value + round(uniform(-10, 10), 2)
            dt = dt + timedelta(seconds=randint(1, 5))

            # build a new tick
            tick = Tick(
                epic=self.market.get_epic('MY_EPIC'),
                datetime=dt,
                bid=(tick_value - 1),
                ask=(tick_value + 1)
            )

            # dispatch tick to market (update candle set, update opened trades,
            # dispatch to strategies etc.)
            yield tick