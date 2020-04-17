import arrow

from estrade import BaseStrategy, Epic, Tick
from estrade.enums import TradeDirection


class MyStrategy(BaseStrategy):
    """
    Define a basic Strategy.

    Open a trade when the tick value is 100 and close all opened trades otherwise.
    """

    def on_every_tick(self, epic: "Epic") -> None:
        # on every new tick received this method is triggered.
        if epic.last_tick.value == 100:
            # create a new trade
            self.open_trade(epic=epic, quantity=5, direction=TradeDirection.BUY)
        else:
            # close all opened trades
            self.close_opened_trades()


def test_basic_strategy():
    epic = Epic(ref="MY_EPIC_CODE")

    # GIVEN a instance of MyStrategy on an Epic
    strategy = MyStrategy()
    epic.add_strategy(strategy)

    # WHEN a tick of value 100 is received
    tick = Tick(arrow.utcnow(), 99, 101)
    epic.on_new_tick(tick)
    # THEN a trade is created
    assert len(epic.trade_provider.opened_trades) == 1

    # WHEN a tick of value != 100 is received
    tick = Tick(arrow.utcnow(), 101, 103)
    epic.on_new_tick(tick)
    # THEN the previously opened trade is closed
    assert len(epic.trade_provider.opened_trades) == 0
