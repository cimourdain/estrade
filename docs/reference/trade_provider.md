# TradeProvider

## Backtests
For backtests there is no need to define a Trade Provider. On creation the 
[`Epic`][estrade.epic.Epic] object automatically uses a 
[`TradeProviderBacktests`][estrade.trade_provider.TradeProviderBacktests] that set 
every open trade status to confirmed.


## Live trade provider

In order to call your custom trade provider, you have to instanciate a 
[`BaseTradeProvider`][estrade.trade_provider.BaseTradeProvider].

```python
--8<-- "tests/doc/tutorial/test_trade_provider_custom.py"
```

---

## TradeProvider Base Class

::: estrade.trade_provider.BaseTradeProvider

## TradeProviderBacktests Class

::: estrade.trade_provider.TradeProviderBacktests


