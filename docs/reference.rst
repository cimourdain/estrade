.. _reference:


*************
API Reference
*************
.. module:: estrade

Provider
========
.. autoclass:: estrade.AProvider

    :members:

    .. automethod:: generate
    .. automethod:: build_tick
    .. automethod:: build_candle


Strategy
========
.. autoclass:: estrade.Strategy

    :members:

    .. automethod:: check_tick_time
    .. automethod:: on_new_tick_opening_strategy
    .. automethod:: on_new_candle_opening_strategy
    .. automethod:: on_new_tick_closing_strategy
    .. automethod:: on_new_candle_closing_strategy

Tick
======
.. autoclass:: estrade.Tick
