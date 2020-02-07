.. _provider:
.. currentmodule:: estrade

********
Provider
********

Provider
========
.. autoclass:: estrade.Provider

    :members:

    .. automethod:: generate

LiveProvider
============
.. autoclass:: estrade.LiveProvider


Provider in Candle Mode
=======================
.. warning::
    Using candle mode is not recommended, it should be reserved to exceptional cases where you only have candle data.

    In addition, your your candle data must be timed (open, close, high and low must be timed).

This mode main difference with tick mode is that when a candle is received, it apply:
    - low before high to open BUY trades
    - high before low to open SELL trades

If your provider generates candles, this method must call :func:`estrade.Market.on_new_candle` method.

.. code-block:: python

    from estrade import Provider
    from estrade import Candle, Tick

    class MyProvider(Provider):

        def generate(self):
            """
                This method parse all candles from your local source. It assumes that your candles holds the following attributes:
                - epic code
                - timeframe (see :class:`estrade.CandleSet` timeframe attribute)
                - open datetime, bid and ask
                - high datetime, bid and ask
                - low datetime, bid and ask
                - close datetime, bid and ask
            """
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
            self.market.on_new_candle(candle)

