import pytest

from estrade.classes.exceptions import TradeManagerException
from estrade.classes.trade import Trade
from tests.factories import (
    MarketFactory,
    StrategyFactory,
    TickFactory,
    TradeManagerFactory
)


class TestTradeManager:
    def test_base(self):
        market = MarketFactory()
        trade_manager = TradeManagerFactory(market=market)
        assert trade_manager.market == market
        assert not trade_manager.trades


class TestTradeManagerMarket:
    @pytest.mark.parametrize('invalid_market', [
        pytest.param(None),
        pytest.param('string'),
        pytest.param(1),
        pytest.param(['string']),
        pytest.param({'key': 1}),
    ])
    def test_invalid_market(self, invalid_market):
        with pytest.raises(TradeManagerException):
            TradeManagerFactory(market=invalid_market)


class TestTradeClass:
    @pytest.mark.parametrize(
        'invalid_trade_class',
        [
            pytest.param(str, id='str trade class'),
            pytest.param('string', id='string trade class'),
            pytest.param({}, id='dict trade class'),
        ]
    )
    def test_invalid_trade_class(self, invalid_trade_class):
        tm = TradeManagerFactory()
        with pytest.raises(TradeManagerException, match='Trade class .*'):
            tm.trade_class = invalid_trade_class

    def test_valid_trade_class(self):
        class SubTradeClass(Trade):
            pass

        tm = TradeManagerFactory()
        tm.trade_class = SubTradeClass
        assert tm.trade_class == SubTradeClass


class TestTradeManagerOpenTrade:

    def test_open_trade(self):
        trade_manager = TradeManagerFactory()

        for trade_params in [
            {'quantity': 5, 'direction': -1},
            {'quantity': 2, 'direction': -1},
            {'quantity': 1, 'direction': -1},
            {'quantity': 1, 'direction': 1},
            {'quantity': 2, 'direction': 1},
            {'quantity': 5, 'direction': 1}
        ]:
            tick = TickFactory()
            trade_manager.open_trade(tick=tick, **trade_params)
            assert len(trade_manager.trades)
            assert trade_manager.trades[-1].quantity == trade_params['quantity']
            assert trade_manager.trades[-1].direction == trade_params['direction']
            assert trade_manager.trades[-1].trade_manager == trade_manager
            assert trade_manager.trades[-1].epic == tick.epic

        assert len(trade_manager.open_buys) == 3
        assert len(trade_manager.open_sells) == 3
        assert len(trade_manager.open_trades) == 6
        assert len(trade_manager.get_trades(strategy=trade_manager.market.strategies[0])) == 6

    def test_trade_strategies_affectation(self):
        strategy1 = StrategyFactory()
        strategy2 = StrategyFactory()
        market = MarketFactory(strategies=[strategy1, strategy2])
        trade_manager = TradeManagerFactory(market=market)

        tick = TickFactory()
        trade_manager.open_trade(tick=tick, strategy=strategy1, quantity=2, direction='BUY')
        trade_manager.open_trade(tick=tick, strategy=strategy1, quantity=2, direction='BUY')
        trade_manager.open_trade(tick=tick, strategy=strategy2, quantity=2, direction='BUY')

        assert len(trade_manager.get_trades(strategy=strategy1)) == 2
        assert len(trade_manager.get_trades(strategy=strategy2)) == 1


class TestOnNewTick:

    def test_on_new_tick(self):
        trade_manager = TradeManagerFactory()

        tick = TickFactory()
        for trade_params in [
            {'quantity': 5, 'direction': -1},
            {'quantity': 2, 'direction': -1},
            {'quantity': 1, 'direction': -1},
            {'quantity': 1, 'direction': 1},
            {'quantity': 2, 'direction': 1},
            {'quantity': 5, 'direction': 1}
        ]:
            trade_manager.open_trade(tick=tick, **trade_params)
            assert len(trade_manager.trades)

        # close 2 trades
        trade_manager.close_trade_by_ref(ref=trade_manager.trades[1].ref)
        trade_manager.close_trade_by_ref(ref=trade_manager.trades[4].ref)

        new_tick = TickFactory()
        trade_manager.on_new_tick(new_tick)
        for trade in trade_manager.trades:
            if trade.closed:
                assert trade.ticks[-1] == tick
            else:
                assert trade.ticks[-1] == new_tick


class TestClose:

    def test_close_trade_by_ref(self):
        tm = TradeManagerFactory()
        tick = TickFactory()
        tm.open_trade(tick=tick, quantity=2, direction='BUY')
        tm.open_trade(tick=tick, quantity=5, direction='SELL')

        assert len(tm.trades) == 2
        tm.close_trade_by_ref(ref=tm.trades[0].ref)
        assert len(tm.closed_trades) == 1
        assert len(tm.open_trades) == 1
        assert tm.trades[0].closed

    def test_close_invalid_trade_by_red(self):
        tm = TradeManagerFactory()
        tick = TickFactory()
        tm.open_trade(tick=tick, quantity=2, direction='BUY')
        tm.open_trade(tick=tick, quantity=5, direction='SELL')

        assert len(tm.trades) == 2
        with pytest.raises(TradeManagerException):
            tm.close_trade_by_ref(ref='test')

    @pytest.mark.parametrize(['method', 'nb_closed', 'nb_open'], [
        pytest.param('close_all_trades', 5, 0),
        pytest.param('close_all_buys', 3, 2),
        pytest.param('close_all_sells', 2, 3),
    ])
    def test_close_all_trades(self, method, nb_closed, nb_open):
        tm = TradeManagerFactory()
        tick = TickFactory()
        tm.open_trade(tick=tick, quantity=2, direction='BUY')
        tm.open_trade(tick=tick, quantity=5, direction='SELL')
        tm.open_trade(tick=tick, quantity=3, direction='BUY')
        tm.open_trade(tick=tick, quantity=8, direction='SELL')
        tm.open_trade(tick=tick, quantity=7, direction='BUY')

        assert len(tm.trades) == 5
        getattr(tm, method)()
        assert len(tm.closed_trades) == nb_closed
        assert len(tm.open_trades) == nb_open


class TestStats:

    def test_won_trades(self):
        tm = TradeManagerFactory()
        tick = TickFactory(
            bid=998,
            ask=1000
        )
        tm.open_trade(tick=tick, quantity=2, direction='BUY')
        tm.open_trade(tick=tick, quantity=5, direction='SELL')
        tm.open_trade(tick=tick, quantity=3, direction='BUY')
        tm.open_trade(tick=tick, quantity=8, direction='SELL')
        tm.open_trade(tick=tick, quantity=7, direction='BUY')

        assert tm.nb_trades() == 5

        tick2 = TickFactory(
            bid=1004,
            ask=1006
        )
        tm.on_new_tick(tick=tick2)

        tm.close_all_trades()
        assert len(tm.won_trades()) == 3
        assert tm.nb_win() == 3
        assert len(tm.lost_trades()) == 2
        assert tm.nb_losses() == 2
        assert tm.nb_trades() == 5

        expected_buy_rst = 4
        expected_sell_rst = -8

        tm.open_trade(tick=tick, quantity=3, direction='SELL')
        tm.open_trade(tick=tick, quantity=4, direction='BUY')
        tm.on_new_tick(tick=tick2)

        assert len(tm.get_trades()) == 7
        assert len(tm.get_trades(only_opened=True)) == 2
        assert len(tm.get_trades(only_closed=True)) == 5

        assert tm.total_win(only_closed=True) == expected_buy_rst * (2 + 3 + 7)
        assert tm.total_win(only_opened=True) == expected_buy_rst * 4
        assert tm.total_win() == expected_buy_rst * (2 + 3 + 7 + 4)

        assert tm.total_losses(only_closed=True) == expected_sell_rst * (5 + 8)
        assert tm.total_losses(only_opened=True) == expected_sell_rst * 3
        assert tm.total_losses() == expected_sell_rst * (5 + 8 + 3)

        assert tm.result(only_closed=True) == expected_buy_rst * (2 + 3 + 7) + expected_sell_rst * (5 + 8)
        assert tm.result(only_opened=True) == expected_buy_rst * 4 + expected_sell_rst * 3
        assert tm.result() == expected_buy_rst * (2 + 3 + 7 + 4) + expected_sell_rst * (5 + 8 + 3)

        assert tm.profit_factor(only_closed=True) == (expected_buy_rst * (2 + 3 + 7)) / abs(expected_sell_rst * (5 + 8))
        assert tm.profit_factor(only_opened=True) == (expected_buy_rst * 4) / abs(expected_sell_rst * 3)
        assert tm.profit_factor() == (expected_buy_rst * (2 + 3 + 7 + 4)) / abs(expected_sell_rst * (5 + 8 + 3))

    def test_profit_factor_0_win(self):
        tm = TradeManagerFactory()
        tick = TickFactory(
            bid=998,
            ask=1000
        )
        tm.open_trade(tick=tick, quantity=2, direction='BUY')
        tick2 = TickFactory(
            bid=1004,
            ask=1006
        )
        tm.on_new_tick(tick=tick2)
        assert tm.profit_factor() == 4 * 2


class TestMaxDD:

    def test_base(self):
        tm = TradeManagerFactory()
        tick = TickFactory(bid=999, ask=1001)
        trade1 = tm.open_trade(tick=tick, quantity=1, direction='BUY')
        tick = TickFactory(bid=1021, ask=1023)
        tm.close_trade_by_ref(ref=trade1.ref, tick=tick)
        assert trade1.result == 20
        assert tm.max_drowdown() == 0

        tick = TickFactory(bid=999, ask=1001)
        trade2 = tm.open_trade(tick=tick, quantity=1, direction='BUY')
        tick = TickFactory(bid=991, ask=993)
        tm.close_trade_by_ref(ref=trade2.ref, tick=tick)
        assert trade2.result == -10
        assert tm.max_drowdown() == 10

        tick = TickFactory(bid=999, ask=1001)
        trade3 = tm.open_trade(tick=tick, quantity=1, direction='BUY')
        tick = TickFactory(bid=1051, ask=1053)
        tm.close_trade_by_ref(ref=trade3.ref, tick=tick)
        assert trade3.result == 50
        assert tm.max_drowdown() == 10

        tick = TickFactory(bid=999, ask=1001)
        trade4 = tm.open_trade(tick=tick, quantity=1, direction='BUY')
        tick = TickFactory(bid=996, ask=998)
        tm.close_trade_by_ref(ref=trade4.ref, tick=tick)
        assert trade4.result == -5
        assert tm.max_drowdown() == 10

        tick = TickFactory(bid=999, ask=1001)
        trade5 = tm.open_trade(tick=tick, quantity=1, direction='BUY')
        tick = TickFactory(bid=941, ask=943)
        tm.close_trade_by_ref(ref=trade5.ref, tick=tick)
        assert trade5.result == -60
        assert tm.max_drowdown() == 65

        tick = TickFactory(bid=999, ask=1001)
        trade6 = tm.open_trade(tick=tick, quantity=1, direction='BUY')
        tick = TickFactory(bid=1021, ask=1023)
        tm.close_trade_by_ref(ref=trade6.ref, tick=tick)
        assert trade6.result == 20
        assert tm.max_drowdown() == 65
