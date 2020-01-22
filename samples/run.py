from datetime import datetime, timedelta

import arrow
from estrade import CandleSet, Epic, Market, ReportingCSV

# import your strategy and provider
from samples.providers.random import RandomProvider
from samples.strategies.random_strategy import RandomStrategy

market = Market()

# create your epic
epic = Epic(ref='MY_EPIC', market=market)
CandleSet(epic=epic, timeframe='21ticks')
CandleSet(epic=epic, timeframe='5minutes')

# build instance of your strategy
strategy = RandomStrategy(market=market, epics=[epic])

# build instance of your provider
provider = RandomProvider(
    market=market,
    start_date=arrow.get(
        datetime(year=2020, month=1, day=1, hour=0, minute=0, second=0), 'UTC'
    ),
    end_date=arrow.get(
        datetime(year=2020, month=1, day=3, hour=0, minute=0, second=0), 'UTC'
    ),
)

# define your reporting
reporting = ReportingCSV(market=market)

# build and run a market instance
market.run()



