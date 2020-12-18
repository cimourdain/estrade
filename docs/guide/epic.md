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

### Tick timezone conversion

Upon receiving a new [`Tick`][estrade.tick.Tick], an [`Epic`][estrade.epic.Epic] 
convert the [`Tick`][estrade.tick.Tick] `datetime` to its `timezone`.

```python
--8<-- "tests/doc/guide/epic/test_tick_timezone_conversion.py"
```


## Epic Open periods

Upon initialization, you can set [`Epic`][estrade.epic.Epic] open periods.

