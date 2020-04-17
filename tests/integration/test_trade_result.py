from datetime import timedelta

import arrow

from estrade import BaseStrategy, BaseTickProvider, Epic, Tick
from estrade.enums import TradeDirection


class MyTickProvider(BaseTickProvider):
    def run(self):
        current_datetime = arrow.utcnow()

        i = 0
        while i < 10:
            tick = Tick(
                bid=i - 0.2,
                ask=i + 0.2,
                datetime=current_datetime,
            )
            self.get_epic_by_ref("MY_EPIC").on_new_tick(tick)

            current_datetime = current_datetime + timedelta(minutes=1)
            i += 0.01


def test_base():
    class MyBuyStrategy(BaseStrategy):
        def on_every_tick(self, epic: "Epic") -> None:
            if epic.last_tick.value == 3.36:
                self.open_trade(epic=epic, quantity=3, direction=TradeDirection.BUY)

            elif epic.last_tick.value == 6.44:
                for trade in epic.trade_provider.opened_trades:
                    self.close_trade(trade, quantity=5)

            elif epic.last_tick.value == 8.24:
                self.open_trade(epic=epic, quantity=2, direction=TradeDirection.SELL)

            elif epic.last_tick.value == 9.56:
                for trade in epic.trade_provider.opened_trades:
                    epic.close_trade(trade, quantity=1)

    epic = Epic(ref="MY_EPIC")
    tick_provider = MyTickProvider(epics=[epic])
    strategy = MyBuyStrategy()
    epic.add_strategy(strategy)
    tick_provider.run()

    assert len(epic.trade_provider.trades) == 2
    assert len(epic.trade_provider.opened_trades) == 1
    assert strategy.result() == 4.16
