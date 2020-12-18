# Tick

A [`Tick`][estrade.tick.Tick] represent the value of an Epic at a given point in time.

## Minimal usage
The following example show the minimal usage of a [`Tick`][estrade.tick.Tick].

```python
--8<-- "tests/doc/guide/tick/test_nominal.py"
```

## Timezone Management

A [`Tick`][estrade.tick.Tick] instance takes a time-zoned datetime as input.

!!! note
    
    Internaly, Estrade uses the [Arrow module](https://github.com/arrow-py/arrow)
    to handle datetime conversions.

```python
--8<-- "tests/doc/guide/tick/test_timezone.py"
```

## Meta data
A [`Tick`][estrade.tick.Tick] can optionnaly hold meta information.

```python
--8<-- "tests/doc/guide/tick/test_meta.py"
```

## Value
A [`Tick`][estrade.tick.Tick] value represents the value between bid and ask.

```python
--8<-- "tests/doc/guide/tick/test_value.py"
```


## Spread
A [`Tick`][estrade.tick.Tick] spread represents the difference between its bid and ask 
value.

```python
--8<-- "tests/doc/guide/tick/test_spread.py"
```

 