from estrade import Epic, Market, ReportingCSV


# import your strategy and provider
from samples.providers.random import RandomProvider
from samples.strategies.random import RandomStrategy


# create your epic
my_epic = Epic(ref='MY_EPIC1')

# build instance of your strategy
strategy = RandomStrategy(epics=[my_epic])

# build instance of your provider
provider = RandomProvider()

# define your reporting
reporting = ReportingCSV()

# build and run a market instance
market = Market(
    strategies=[strategy],
    provider=provider,
    reporting=reporting
)
market.run()



