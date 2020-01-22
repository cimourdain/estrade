import logging
from typing import List, Generator, TYPE_CHECKING

from estrade.candle import Candle
from estrade.tick import Tick
from estrade.trade import Trade

if TYPE_CHECKING:
    from estrade.market import Market

logger = logging.getLogger(__name__)


class Provider:
    """
    A provider defines how to fetch your source data (ticks or candles).

    The provider `generate` method feed data to the `estrade.Market` object
    (that will dispatch it to candle sets, indicators, strategies etc.)

    Arguments:
        market: market instance
        requires_login: set to True if your provider requires login before market run.

    !!! note
        if you use the `requires_login`, you have to implement a login method.

    !!! example
        ```python
        from estrade import Epic, Market, Provider, Tick

        MyProvider:
            def generate_ticks():
                from tick in my_source:
                    tick = Tick(
                        epic=self.market.get_epic(tick['epic_code']),
                        datetime=tick.datetime,  # must be timezoned
                        bid=tick['bid']
                        ask=tick['ask']
                    )

                    # dispatch tick to market
                    yield tick

        if __name__ == '__main__':
            market = Market()

            epic = Epic(ref='MY_EPIC', market=market)
            # add candlsets if necessary
            # add strategies
            provider = MyProvider(market=market)

            market.run()
        ```
    """

    def __init__(
        self, market: 'Market', requires_login: bool = False,
    ):
        # init a market property to None
        self.market = market
        self.market.provider = self
        self.market.subscribe('market_before_run', self.login)

        self.requires_login = requires_login

    ##################################################
    # EVENTS
    ##################################################
    def generate_ticks(self) -> Generator[Tick, None, None]:
        """
        This method must be implemented to fetch ticks or candles from provider.

        !!! example "Example of a provider generating ticks"

            ```python
            from estrade import Provider
            from estrade import Tick

            class MyProvider(Provider):

                def generate_ticks(self):
                    '''
                        This method parse all ticks from your database.
                        It assumes that your ticks holds the following attributes:
                        - epic code
                        - bid
                        - ask
                        - datetime
                    '''
                    # eg. query ticks in your database (ordered by datetime)
                    for tick in my_database:
                        # build a tick from your data
                        tick = Tick(
                            epic=self.market.get_epic(tick['epic_code']),
                            bid=tick['bid'],
                            ask=tick['ask'],
                            datetime['datetime'],
                        )
                    # dispatch tick to market
                    yield tick
            ```
        """
        pass

    def generate_candles(self) -> Generator[Candle, None, None]:
        """
        Implement this method to run in "Candle mode" meaning that the generate method
        feed `estrade.Candle` objects to the market.

        !!! warning
            Using candle mode is not recommended, it should be reserved to exceptional
            cases where you only have candle data.

            In addition, your your candle data must be timed (open, close, high and
                                                              low must be timed).

        !!! example "example of a provider in candle mode"
            ```python
            from estrade import Provider
            from estrade import Candle, Tick

            class MyProvider(Provider):

                def generate_candles(self):
                    # eg. query candle in your database (ordered by datetime)
                    for candle in my_database:
                        epic = self.market.get_epic(candle['epic_code'])
                        # build an open tick from your data
                        open = Tick(
                            epic=epic,
                            bid=candle['open_bid'],
                            ask=candle['open_ask'],
                            datetime=candle['open_datetime'],
                        )
                        high = Tick(
                            epic=epic,
                            bid=candle['high_bid'],
                            ask=candle['high_ask'],
                            datetime=candle['high_datetime'],
                        )
                        low = Tick(
                            epic=epic,
                            bid=candle['low_bid'],
                            ask=candle['low_ask'],
                            datetime=candle['low_datetime'],
                        )
                        close = Tick(
                            epic=epic,
                            bid=candle['close_bid'],
                            ask=candle['close_ask'],
                            datetime=candle['close_datetime'],
                        )
                        # build a candle with your ticks
                        candle = Candle(
                            timeframe=candle['timeframe'],
                            epic_ref=candle['epic_code'],
                            open_tick=open
                        )
                        # add high, low tick to candle
                        candle.on_new_tick(high)
                        candle.on_new_tick(low)
                        # finally add the close tick to candle
                        candle.on_new_tick(close)

                    # dispatch candle to market
                    yield(candle)
            ```
        """
        pass

    def get_open_trades(self) -> List[Trade]:
        """
        Implement this method to fetch list of open trades from your provider.

        This method is called before market run to load existing opened trades.

        Returns:
            List of existing trades to load before Market run
        """
        return []

    def login(self) -> bool:
        """
        This method must perform login process with your provider.

        Returns:
            - True if login to provider was successful successfully
            - False if login to provider failed

        """
        return True

    def update_epic_status(self, epic_ref: str, tradeable_status: bool) -> None:
        """
        This method allow to set epic as (not) tradeable.
        When an epic is not tradeable, no open/close trade will be attempted.

        Arguments:
            epic_ref: epic code
            tradeable_status: Is trading allowed on this epic
        """
        epic = self.market.get_epic(epic_ref)
        epic.tradeable = tradeable_status

    def open_trade(self, trade: Trade) -> Trade:
        """
        For a remote provider, use this method to ask your provider to create
        a new trade.

        Arguments:
            trade: trade to be opened

        !!! tip

            - You can use the `trade.meta` property to store any necessary data for
            your provider.
            - In case of error it is recommended to raise a
            `estrade.exception.ProviderException`

        """
        return trade

    def close_trade(self, trade: Trade, quantity: int) -> Trade:
        """
        For a remote provider, use this method to ask your provider to close a trade.

        Arguments:
            trade: trade to be closed
            quantity: quantity to close

        !!! tip

             - You can use the `trade.meta` property to store any necessary data
             for your provider.
             - In case of error it is recommended to raise a
             `estrade.exception.ProviderException`
        """
        return trade

    def update_trade(self, *args, **kwargs) -> None:
        """
        For a remote provider, use this method to update a trade in case your provider
        notifies an update.

        !!! example

            ```python
            from estrade import Provider


            class MyProvider(Provider):
                # ...
                def update_trade(self, remote_update):
                    # search for existing trade by its ref if your provider
                    # update contains it.
                    trade = self.market.trade_manager.get_trade_by_ref(
                        ref=remote_update['ref']
                    )
                    trade.set_stop(value=remote_update['stop'], relative=False)

                    # search in all existing trades if you stored reconciliation data
                    # in trades meta
                    for trade in self.market.trade_manager.trades:
                        if trade.meta['remote_id'] == remote_update['id']:
                            # update your trade
                            trade.set_stop(value=remote_update['stop'], relative=False)
            ```
        """
        pass
