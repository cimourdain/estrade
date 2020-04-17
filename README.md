<h1 align="center">
  <a href="https://github.com/cimourdain/estrade"><img src="https://github.com/cimourdain/estrade/raw/master/assets/logo.png" alt="Estrade" width="399"/></a><br>
  <a href="https://github.com/cimourdain/estrade">Estrade</a>
</h1>


<div align="center">
<a href="https://travis-ci.com/cimourdain/estrade">
    <img src="https://travis-ci.com/cimourdain/estrade.svg?branch=master" alt="Build Status" />
</a>
<a href='https://estrade.readthedocs.io/en/latest'>
    <img src='https://readthedocs.org/projects/estrade/badge/?version=latest' alt='Documentation Status' />
</a>
<img src="https://badgen.net/badge/python/3.6,3.7,3.8?list=|" alt="python version" />
<img src="https://badgen.net/badge/version/0.2.0" alt="current app version" />
<a href="https://pypi.org/project/estrade/">
    <img src="https://badgen.net/pypi/v/estrade" alt="PyPi version" />
</a>
<img src="https://badgen.net/badge/coverage/96%25" alt="Coverage" />
<img src="https://badgen.net/badge/complexity/A%20%281.9210526315789473%29" alt="Complexity" />
<a href="https://gitlab.com/pycqa/flake8">
    <img src="https://badgen.net/badge/lint/flake8/purple" alt="Lint" />
</a>
<a href="https://github.com/ambv/black">
    <img src="https://badgen.net/badge/code%20style/black/000" alt="Code format" />
</a>
<a href="https://github.com/python/mypy">
    <img src="https://badgen.net/badge/static%20typing/mypy/pink" alt="Typing" />
</a>
<img src="https://badgen.net/badge/licence/GNU-GPL3" alt="Licence" />
</div>


# Backtest and run your trading strategies

Estrade is a python library that allows you to easily backtest and run stock trading strategies at tick level.

Estrade focus on providing tools so you mainly focus on your strategy definition.

>  **WARNING**: Estrade is still in an alpha state of developpement and very unmature. Do not use it for other purposes than testing.

## Features

Estrade provides a **market environnement**, so you do not have to worry about
 - Trades result calculation
 - Indicators building & calculation (candle sets, graph indicators etc.)

Estrade is build to be extended so you can define your own:
- Strategies
- Tick provider (to feed your backtests and/or live trading)
- Indicators
- Reporting


## What Estrade does NOT provides

- **Data**: You have to define your own data provider (live or static)
- **Strategies**: Although some very basic (and useless) strategies are provided as examples in samples, Estrade does not provide any financially relevant strategy.


## Documentation

[Documentation](https://estrade.readthedocs.io/en/latest)
