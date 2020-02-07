.. _strategy:
.. currentmodule:: estrade

********
Strategy
********

Strategy Instance
=================
.. autoclass:: estrade.Strategy


Events
========

A strategy is triggered by market (when a new tick is received, a new candle is created).
Your strategy can define actions to perform (opening and closing trades) on theses triggers.

Opening methods
----------------
Use the following methods to open your trades.

.. autofunction:: estrade.Strategy.on_new_tick_opening_strategy
.. autofunction:: estrade.Strategy.on_new_candle_opening_strategy


Closing methods
----------------
Use the following methods to define your closing strategies (closing opened trades).

.. autofunction:: estrade.Strategy.on_new_tick_closing_strategy
.. autofunction:: estrade.Strategy.on_new_candle_closing_strategy




Opening and closing trades
==========================

Opening trades
--------------
.. autofunction:: estrade.Strategy.open_trade

Closing trades
--------------
The following methods are available to close strategy trades

.. autofunction:: estrade.Strategy.close_trade_by_ref
.. autofunction:: estrade.Strategy.close_all_trades
.. autofunction:: estrade.Strategy.close_all_buys
.. autofunction:: estrade.Strategy.close_all_sells



Getters
=======
.. autofunction:: estrade.Strategy.get_epic
.. autofunction:: estrade.Strategy.get_candle_set
.. autofunction:: estrade.Strategy.get_candle
.. autofunction:: estrade.Strategy.get_indicator
.. autofunction:: estrade.Strategy.get_trades


Other
=====
.. autofunction:: estrade.Strategy.check_tick_time
