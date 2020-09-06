# Estrade

# Estrade: Trading bot manager

Estrade is a python library that allows you to easily backtest and run stock trading strategies.

Estrade focus on providing tools so you mainly focus on your strategy definition.


## Features

- Estrade provides a **market environnement**, so you do not have to worry about
   - Trades result calculation
   - Candle Graph building
   - Indicators calculation
- Estrade allows you to define your strategies based on market events (new tick received, new candle created)
- Estrade allows you to create your own data providers to generate ticks data and manage trades (open/close)
- Estrade allows you to create your own indicators
- Estrade allows you to create your own reporting


## What Estrade does NOT provides

- **Data**: You have to define your own data provider (live or static)
- **Strategies**: Although some very basic (and useless) strategies are provided as examples in samples, Estrate does not provide any financially relevant strategy.

