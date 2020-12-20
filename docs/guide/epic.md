## Epic
An [`Epic`][estrade.epic.Epic] is a financial instrument.


## Handling ticks
The main purpose of an [`Epic`][estrade.epic.Epic] is to handle 
[`Ticks`][estrade.tick.Tick]. 

### Basic

The following example show the minimal usage of handling a [`Tick`][estrade.tick.Tick].

```python
--8<-- "tests/doc/guide/epic/test_handle_tick.py"
```

!!! note
    See  [`TickProvider`][estrade.tick_provider.BaseTickProvider] to wrap the call of
    [`Epic.on_new_tick`][estrade.epic.Epic.on_new_tick] onto your data source. 

### Tick timezone conversion

Upon receiving a new [`Tick`][estrade.tick.Tick], an [`Epic`][estrade.epic.Epic] 
convert the [`Tick`][estrade.tick.Tick] `datetime` to its `timezone`.

```python
--8<-- "tests/doc/guide/epic/test_tick_timezone_conversion.py"
```


## Epic Open periods

Upon initialization, you can set [`Epic`][estrade.epic.Epic] open periods.

### Impacts on `Epic.market_open` attribute

When the last [`Tick`][estrade.tick.Tick] received by an [`Epic`][estrade.epic.Epic] 
(`epic.last_tick`) is :

 - inside one of its open periods, the `epic.market_open is True`
 - out of its open periods, then the `epic.market_open is False`.
 
#### Usage examples

##### Open/close times
```python
--8<-- "tests/doc/guide/epic/test_open_close_time.py"
```

##### Trade days
You can set that only some weekdays are available for trading.

```python
--8<-- "tests/doc/guide/epic/test_trade_days.py"
```
    
### Impacts on strategy method called attribute

When the [`Tick`][estrade.tick.Tick] received by an [`Epic`][estrade.epic.Epic] 
(`epic.last_tick`) is out of its open periods, then the following method are called 
on very strategy attached to the `Epic`: 

 - [`on_every_tick`][estrade.strategy.BaseStrategy.on_every_tick].
    

When the [`Tick`][estrade.tick.Tick] received by an [`Epic`][estrade.epic.Epic] 
(`epic.last_tick`) is inside of its open periods but the previous `epic.last_tick` 
was out of trading period, then the following method are called on very strategy 
attached to the `Epic`: 

 - [`on_every_tick`][estrade.strategy.BaseStrategy.on_every_tick],
 - [`on_market_open`][estrade.strategy.BaseStrategy.on_market_open],
 - [`on_every_tick_market_open`][estrade.strategy.BaseStrategy.on_every_tick_market_open].

When the last [`Tick`][estrade.tick.Tick] received by an [`Epic`][estrade.epic.Epic] 
(`epic.last_tick`) is inside one of its open periods, then the following method 
are called on strategies: 

 - [`on_every_tick`][estrade.strategy.BaseStrategy.on_every_tick],
 - [`on_every_tick_market_open`][estrade.strategy.BaseStrategy.on_every_tick_market_open].

When the [`Tick`][estrade.tick.Tick] received by an [`Epic`][estrade.epic.Epic] 
(`epic.last_tick`) is out of its open periods but the previous `epic.last_tick` 
was inside of trading period, then the following method are called on very strategy 
attached to the `Epic`: 

 - [`on_every_tick`][estrade.strategy.BaseStrategy.on_every_tick],
 - [`on_market_close`][estrade.strategy.BaseStrategy.on_market_close].


