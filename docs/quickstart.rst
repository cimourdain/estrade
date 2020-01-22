.. _quickstart:
.. currentmodule:: estrade

Quickstart
==========


Create a Provider
-----------------

A class: `Provider` is used to generate data. As your data can come from a local source (database etc.) or from an external
source (api, etc.) you have to define it.

The minimal definition of a provider is the following:


.. code-block:: python

    from estrade import AProvider

    class MyProvider(AProvider):

        def generate(self):
            # eg. query ticks in your database
            for tick in my_database:
                # build a tick from your data
                tick = self.build_tick(
                    epic_ref=tick['epic_code'],
                    bid=tick['bid'],
                    ask=tick['ask'],
                    datetime['datetime']
                )
                # dispatch tick to market
                self.market.on_new_tick(tick)





Create a Strategy
-----------------

.. code-block:: python

    from estrade import Strategy

    class MyStrategy:

        def on_new_tick_opening_strategy(self, tick):
            # if tick value == 1000 => open a BUY position
            if tick.value == 1000:
                self.open_trade(
                    epic=tick.epic.code,
                    quantity=1,
                    direction='BUY',
                )
            elif tick.value == 2000:
                self.open_trade(
                    epic=tick.epic.code,
                    quantity=1,
                    direction='SELL'
                )

