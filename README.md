<h1 align="center">
  <a href="https://github.com/cimourdain/estrade"><img src="https://github.com/cimourdain/estrade/raw/master/assets/logo.png" alt="Estrade" width="399"/></a><br>
  <a href="https://github.com/cimourdain/estrade">Estrade</a>
</h1>


<div align="center">
<a href="https://travis-ci.com/cimourdain/estrade">
    <img src="https://travis-ci.com/cimourdain/estrade.svg?branch=v0.2.1" alt="Build Status" />
</a>
<a href='https://estrade.readthedocs.io/en/v0.2.1'>
    <img src='https://readthedocs.org/projects/estrade/badge/?version=v0.2.1' alt='Documentation Status' />
</a>
<img src="https://badgen.net/badge/python/3.6,3.7,3.8?list=|" alt="python version" />
<img src="https://badgen.net/badge/version/0.2.1" alt="current app version" />
<a href="https://pypi.org/project/estrade/">
    <img src="https://badgen.net/pypi/v/estrade" alt="PyPi version" />
</a>
<img src="https://badgen.net/badge/coverage/95%25" alt="Coverage" />
<img src="https://badgen.net/badge/complexity/A%20%281.963855421686747%29" alt="Complexity" />
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

Estrade provides a environnement, so you do not have to worry about:

 - Trades result calculation
 - Indicators building & calculation (candle sets, graph indicators etc.)

Estrade is build to be extended so you can define your own:

 - Strategies
 - Tick provider (to feed your backtests and/or live trading)
 - Indicators
 - Reporting
 - Trade provider


## What Estrade does NOT provides

- **Data**: You have to define your own data provider (live or static)
- **Strategies**: Although some very basic (and useless) strategies are provided as examples in samples, Estrade does not provide any financially relevant strategy.
- **Brokers connexion**: For legal reasons Estrade will never include any broker connection. Anyway Estrade provides the required tools
to define it yourself easily.


## Basic usage example

```python
import arrow

from estrade import BaseStrategy, Epic, Tick, BaseTickProvider
from estrade.enums import Unit, TradeDirection
from estrade.graph import CandleSet, FrameSet, SimpleMovingAverage
from estrade.reporting import ReportingCSV

if __name__ == "__main__":
    # create an epic called "MY_EPIC"
    epic = Epic(ref="MY_EPIC")

    # create a FrameSet
    frameset_5mn = FrameSet(ref="FS5MN", unit=Unit.MINUTE, unit_quantity=5)
    epic.add_frame_set(frameset_5mn)

    # add a CandleSet on FrameSet
    candle_set5mn = CandleSet(ref="CS5MN")
    frameset_5mn.add_indicator(candle_set5mn)

    # add a SimpleMoving Average on FrameSet
    sma5mn = SimpleMovingAverage(ref="SMA5MN", max_periods=20)
    frameset_5mn.add_indicator(sma5mn)

    # define a strategy that will use your indicator to open/close trades
    class MyStrategy(BaseStrategy):
        def on_every_tick(self, epic):
            # get sma20 and the last candle
            sma20 = epic.get_indicator_value(
                frame_set_ref="FS5MN",
                indicator_ref="SMA5MN",
            ).get_value(periods=20)
            current_candle = epic.get_indicator_value(
                frame_set_ref="FS5MN",
                indicator_ref="CS5MN",
            )

            # check that SMA is not None
            # before having 20 candles in memory, the SMA is None
            if not sma20 or not current_candle:
                return

            # if candle crosses the sma20, then open a new trade
            # else if sma20 > current candle high, then close all opened trades
            if current_candle.open < sma20 < current_candle.last:
                self.open_trade(
                    epic=epic,
                    quantity=1,
                    direction=TradeDirection.BUY,
                )
            elif sma20 > current_candle.high:
                self.close_opened_trades()


    # register strategy on epic
    strategy = MyStrategy()
    epic.add_strategy(strategy)

    # define a tick Provider that will dispatch ticks to your epic
    class MyTickProvider(BaseTickProvider):
        def run(self):
            # dispatch all ticks to epic
            epic = self.epics.get("MY_EPIC")
            for tick in [
                Tick(bid=99, ask=101, datetime=arrow.get("2020-01-01 12:34:56.456")),
                Tick(bid=100, ask=102, datetime=arrow.get("2020-01-01 12:34:57.319")),
                # ...
            ]:
                epic.on_new_tick(tick)

    tick_provider = MyTickProvider(epics=[epic])

    # run your tick provider
    tick_provider.run()

    # report results
    reporting = ReportingCSV()
    reporting.report(strategies=[strategy], trade_details=True)
    # In ./reports/ folder, two files will be created
    #   - A file listing strategies result, trades count, profit factor
    #   - A file per strategy detailing trades


```



## Documentation

[Documentation](https://estrade.readthedocs.io/en/v0.2.1)
