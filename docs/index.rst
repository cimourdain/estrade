Estrade: Trading bot manager
=============================

Estrade is a python library that allows you to easily backtest and run stock trading strategies.

Estrade focus on providing tools so you mainly focus on your strategy definition.


Features
========

- Estrade provides a **market environnement**, so you do not have to worry about
   - Trades result calculation
   - Candle Graph building
   - Indicators calculation
- Estrade allows you to define your strategies based on market events (new tick received, new candle created)
- Estrade allows you to create your own data providers to generate ticks data and manage trades (open/close)
- Estrade allows you to create your own indicators
- Estrade allows you to create your own reporting


What Estrade does NOT provides
==============================

- **Data**: You have to define your own data provider (live or static)
- **Strategies**: Although some very basic (and useless) strategies are provided as examples in samples, Estrate does not provide any financially relevant strategy.


Guide
=====

.. toctree::
    :maxdepth: 1

    install
    quickstart

API Reference
=============

.. toctree::
    :maxdepth: 3

    provider
    strategy
    tick
    candle_set
    candle
    indicators
    trade
    trade_manager


Contribute
==========

- Issue Tracker: github.com/$project/$project/issues
- Source Code: github.com/$project/$project

Support
=======

If you are having issues, please let us know.

License
=======

The project is licensed under the GPL 3.0 license.
