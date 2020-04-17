from estrade import Epic
from estrade.trade_provider import TradeProviderBacktests


def test_defaults():
    # WHEN I create a new Epic instance with the default parameters
    epic = Epic()

    # THEN a string reference is automatically generated
    assert epic.ref is not None and isinstance(epic.ref, str)
    # THEN the timezone is set to UTC
    assert epic.timezone == "UTC"
    # THEN the default trade provider is the TradeProviderBacktests
    assert isinstance(epic.trade_provider, TradeProviderBacktests)
