# Tutorial
## Tick

A [`Tick`][estrade.tick.Tick] represent the value of an Epic at a given point in time.

```python
--8<-- "tests/doc/tutorial/test_tick.py"
```

## Epic
An [`Epic`][estrade.epic.Epic] is a financial instrument.

```python
--8<-- "tests/doc/tutorial/test_epic.py"
```

## Tick Provider

A [`BaseTickProvider`][estrade.tick_provider.BaseTickProvider] is used to dispatch 
[`Tick`][estrade.tick.Tick] to [`Epic`][estrade.epic.Epic] instances.

```python
--8<-- "tests/doc/tutorial/test_tick_provider.py"
```

## Trade Provider

A [`BaseTradeProvider`][estrade.trade_provider.BaseTradeProvider] create, update and close 
[`Trades`][estrade.trade.Trade].

### Backtests
For backtests you do not have to worry about the Trade Provider. A 
[`TradeProviderBacktests`][estrade.trade_provider.TradeProviderBacktests] is automatically
added on [`Epic`][estrade.epic.Epic] upon creation when no `trade_provider` param is 
provided.

The [`TradeProviderBacktests`][estrade.trade_provider.TradeProviderBacktests] automatically
set each [`Trade`][estrade.trade.Trade] and [`TradeClose`][estrade.trade.TradeClose] status
to `CONFIRMED`.

```python
--8<-- "tests/doc/tutorial/test_trade_provider_backtest.py"
```

### Live

When going live you want to specify how to open/update and close trades in a custom 
[BaseTradeProvider][estrade.trade_provider.BaseTradeProvider].

```python
--8<-- "tests/doc/tutorial/test_trade_provider_custom.py"
```


## Strategy

A [`Strategy`][estrade.strategy.BaseStrategy] is the object where you connect
everything to open/close your trades based on the epic, its indicators etc.

On your [`Strategy`][estrade.strategy.BaseStrategy] define a method that will be triggered
on every new [`Tick`][estrade.tick.Tick] received by one of its [`Epics`][estrade.epic.Epic].
 
```python
--8<-- "tests/doc/tutorial/test_strategy.py"
```

!!!note

    here we used the `on_every_tick_method` refer to 
    [`Strategy`][estrade.strategy.BaseStrategy] to view other methods available.

## Graphical

### Frame Set & Frames

A [`FrameSet`][estrade.graph.frame_set.FrameSet] is registered on [`Epic`][estrade.epic.Epic]
and generate (or update) [`Frames`][estrade.graph.frame_set.Frame] on every 
[`Tick`][estrade.tick.Tick] received.

```python
--8<-- "tests/doc/tutorial/test_frame_set.py"
```

### Indicators

[`Indicators`][estrade.graph.base_indicator.BaseIndicator] are generators of [`Indicator Values`][estrade.graph.base_indicator.BaseIndicatorValue].

On every [`Frame`][estrade.graph.frame_set.Frame] created by a [`FrameSet`][estrade.graph.frame_set.FrameSet]
[`indicators values`][estrade.graph.base_indicator.BaseIndicatorValue] values are created on the new created [`Frame`][estrade.graph.frame_set.Frame].

#### Candle Sets

```python
--8<-- "tests/doc/tutorial/test_candle_set.py"
```

#### Simple Moving Average

```python
--8<-- "tests/doc/tutorial/test_simple_moving_average.py"
```


#### Other Indicators

- [`RSI`][estrade.graph.indicators.rsi.RSI]


## Reporting

### Csv reporting

Estrade includes a very basic CSV reporting functionality that build a 
CSV file from an [`Epic`][estrade.epic.Epic] instance.

see: [`ReportingCSV`][estrade.reporting.csv.ReportingCSV]



