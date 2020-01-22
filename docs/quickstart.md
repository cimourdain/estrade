# Quickstart


## Create a Provider

A Provider is used to generate data.


Example of a provider generating random data:
```python
from random import randint, uniform
from datetime import datetime, timedelta

from estrade import Tick, Provider


class RandomProvider(Provider):

    def generate_ticks(self):
        """
        This method generate estrade.Tick from random data and feed them to the estrade.Market.
        The estrade.Market will later :
            - dispatch them to its candle sets to build candles, indicators etc.
            - dispatch them to strategies to open/close trades
        """
        tick_value = 1000
        current = datetime.now() 
        end = current + timedelta(hours=6)
        while current < end:
            # generate nez tick value and date
            tick_value = tick_value + round(uniform(-10, 10), 2)
            # increment current time of few seconds
            current = current + timedelta(seconds=randint(1, 5))

            # build a new estrade.Tick
            tick = Tick(
                epic=self.market.get_epic('MY_EPIC'),
                datetime=current,
                bid=(tick_value - 1),
                ask=(tick_value + 1)
            )

            # dispatch tick to market
            yield tick

```


## Create a Strategy

Define strategy(ies) to apply on your data.

A strategy defines when to open and close trades. It could be applied :

 - on every tick
 - on candle open

Example of a strategy that randomly open and close trades on every tick.

```python
from random import choice, randint

from estrade import Strategy


class RandomStrategy(Strategy):
    """
    This strategy randomly open/close trades on every tick between 10am and 11am
    """
    random_factor = 1000

    def on_new_tick_opening_strategy(self, tick):
        """
        This method is called for every tick of every Epic attached to Strategy
        when the number of open trades is inferior to the Strategy.max_concurrent_trades  
        
        :param tick: instance of estrade.Tick
        """
        r = randint(0, self.random_factor)
        if r == 0:
            # open a new trade (see estrade.Trade)
            self.open_trade(
                epic=tick.epic, # for the tick epic
                quantity=1,
                direction=choice([-1, 1]),  # direction of -1 = SELL, 1 = BUY
                stop_relative=5,
            )

    def on_new_tick_closing_strategy(self, tick):
        """
        This method is called for every tick received by strategy. Its purpose is to close 
        open trades.
        Note: this method is called BEFORE the `on_new_tick_opening_strategy`

        """
        r = randint(0, self.random_factor)
        if r == 0:
            # close all trades opened for this strategy
            self.close_all_trades()
```

## Wrap up and Run
The following example is a minimal definition to run the above strategy against the above provider.

```python

from estrade import Epic, Market, ReportingCSV


# import your strategy and provider defined above
from samples.providers.random import RandomProvider
from samples.strategies.random_strategy import RandomStrategy

market = Market()
# create your epic
my_epic = Epic(market=market, ref='MY_EPIC1')

# create instance of provider
provider = RandomProvider(market=market)

# build instance of your strategy
strategy = RandomStrategy(
    market=market, 
    epics=[my_epic]
)

# define your reporting
reporting = ReportingCSV(market=market)

# run market
market.run()

```

After execution, the `estrade.ReportingCSV` will create a `report` folder with the detailed results.


## Next steps

- Add candle sets to your epics `estrade.CandleSet` to be able to use candles details in your strategy
- Add indicators

