.. _quickstart:
.. currentmodule:: estrade

Quickstart
==========


Create a Provider
-----------------

A Provider is used to generate data.

As your data can come from a local source or from an external source you have to define it manually.
 - If your provider render static data (database, files etc.), define it by inherinting from a :class:`estrade.Provider` instance.
 - If your provider fetch data from a remote source (apis, stream etc.), define it by inherinting from a :class:`estrade.LiveProvider` instance.


Example of a provider generating random data:

.. include:: ../samples/providers/random.py
   :literal:

.. seealso::
    see :class:`estrade.Provider` and :class:`estrade.LiveProvider`

Create a Strategy
-----------------

Define strategy(ies) to apply on your data.

A strategy defines when to open and close trades. It could be applied :
 - on every tick
 - on candle open

Example of a strategy that randomly open and close trades on every tick.

.. include:: ../samples/strategies/random.py
   :literal:

.. seealso::
    see :class:`estrade.Strategy`


Wrap up and Run
---------------
The following example is a minimal definition to run the above strategy against the above provider.

After execution, the reporting will create a `report` folder with the detailed results.

.. include:: ../samples/run.py
   :literal:


Next steps
----------

- Add candle sets to your epics :class:`estrade.CandleSet` to be able to use candles details in your strategy
- Add indicators

