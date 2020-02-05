import pytest

from estrade.exceptions import TradeException
from tests.factories import (
    EpicFactory,
    MarketFactory,
    TickFactory,
    TradeFactory,
    TradeManagerFactory,
)


class TestTradeBase:
    @pytest.mark.parametrize(
        ['init_quantity', 'direction', 'trade_quantity', 'trade_direction'],
        [
            pytest.param(1, 'BUY', 1, 1, id='open buy of 1'),
            pytest.param(5, 'BUY', 5, 1, id='open buy of 5'),
            pytest.param(1, 'SELL', 1, -1, id='open sell of 1'),
            pytest.param(4, 'SELL', 4, -1, id='open sell of 4'),
        ],
    )
    def test_base(self, init_quantity, direction, trade_quantity, trade_direction):
        tick = TickFactory(bid=999, ask=1001)
        trade = TradeFactory(tick=tick, quantity=init_quantity, direction=direction)
        assert trade.ref
        assert trade.epic == tick.epic
        assert trade.quantity == trade_quantity
        assert trade.direction == trade_direction
        assert len(trade.ticks) == 1


class TestTradeDirection:

    @pytest.mark.parametrize('direction,expected_direction', [
        pytest.param(1, 1, id='open trade with direction 1'),
        pytest.param(-1, -1, id='open trade with direction -1'),
        pytest.param('BUY', 1, id='open trade with direction BUY'),
        pytest.param('SELL', -1, id='open trade with direction SELL'),
        pytest.param('buy', 1, id='open trade with direction buy'),
        pytest.param('sell', -1, id='open trade with direction sell'),
    ])
    def test_open_direction(self, direction, expected_direction):
        trade = TradeFactory(direction=direction)
        assert trade.direction == expected_direction

    @pytest.mark.parametrize('invalid_direction', [
        pytest.param(None),
        pytest.param('string'),
        pytest.param(['string']),
        pytest.param({'key': 1}),
    ])
    def test_invalid_direction(self, invalid_direction):
        with pytest.raises(TradeException):
            TradeFactory(direction=invalid_direction)


class TestTradeOpenTick:

    @pytest.mark.parametrize('invalid_tick', [
        pytest.param(None),
        pytest.param('string'),
        pytest.param(1),
        pytest.param(['string']),
        pytest.param({'key': 1}),
    ])
    def test_open_with_invalid_tick(self, invalid_tick):
        with pytest.raises(TradeException):
            TradeFactory(tick=invalid_tick, quantity=1)

    def test_open_with_trading_not_allowed(self, mocker):
        epic = EpicFactory()
        tick = TickFactory(epic=epic)
        epic.tradeable = False

        with pytest.raises(TradeException, match='.* is not tradeable.*'):
            TradeFactory(tick=tick, quantity=1)


class TestTradeRef:
    def test_base_ref(self):
        trade = TradeFactory()
        assert trade.ref
        assert trade.ref[:6] == 'trade_'
        assert len(trade.ref) == 10

    def test_manual_ref(self):
        trade = TradeFactory(ref='toto')
        assert trade.ref == 'toto'

    def test_update_ref(self):
        trade = TradeFactory()
        trade.ref = 'toto'
        assert trade.ref == 'toto'


class TestTradeTradeManager:
    def test_trade_manager(self):
        tm = TradeManagerFactory()
        trade = TradeFactory(trade_manager=tm)
        assert trade.trade_manager == tm

    def test_empty_trade_manager(self):
        trade = TradeFactory(trade_manager=None)
        assert trade.trade_manager is None

    @pytest.mark.parametrize('invalid_trade_manager', [
        pytest.param('test', id='string trade manager'),
        pytest.param(123, id='int trade manager'),
        pytest.param(['toto'], id='list trade manager')
    ])
    def test_invalid_trade_manager(self, invalid_trade_manager):
        with pytest.raises(TradeException):
            TradeFactory(trade_manager=invalid_trade_manager)

    def test_update_trade_manager(self):
        trade = TradeFactory()
        tm = TradeManagerFactory()
        trade.trade_manager = tm
        assert trade.trade_manager == tm


class TestStrategy:
    def test_valid_strategy(self):
        trade = TradeFactory()
        assert trade.strategy

    def test_empty_strategy_uses_market_default(self):
        market = MarketFactory()

        trade = TradeFactory(strategy=None, trade_manager=market.trade_manager)
        assert trade.strategy == trade.trade_manager.market.strategies[0]

    def test_empty_stratregy(self):
        trade = TradeFactory(trade_manager=None, strategy=None)
        assert trade.trade_manager is None
        assert trade.strategy is None

    @pytest.mark.parametrize(
        'invalid_strategy',
        [
            pytest.param('string'),
            pytest.param(3),
            pytest.param(['string1', 2]),
            pytest.param({'key': 1}),
        ],
    )
    def test_invalid_strategy(self, invalid_strategy):
        trade = TradeFactory(strategy=None)
        with pytest.raises(TradeException):
            trade.strategy = invalid_strategy

        with pytest.raises(TradeException):
            TradeFactory(strategy=invalid_strategy)


class TestTradeMinMax:
    def test_min_max(self):
        tick1 = TickFactory(bid=999, ask=1001)
        trade = TradeFactory(tick=tick1, quantity=2, direction=-1)
        assert trade.min == 1000
        assert trade.max == 1000

        tick2 = TickFactory(bid=4999, ask=5001)
        trade.on_new_tick(tick2)
        assert trade.min == 1000
        assert trade.max == 5000

        tick3 = TickFactory(bid=99, ask=101)
        trade.on_new_tick(tick3)
        assert trade.min == 100
        assert trade.max == 5000

        tick3 = TickFactory(bid=1199, ask=1201)
        trade.on_new_tick(tick3)
        assert trade.min == 100
        assert trade.max == 5000


class TestTradeResult:
    @pytest.mark.parametrize(
        ['quantity', 'direction', 'r1', 'r2', 'r3'],
        [
            pytest.param(1, 1, -1, 4, -6, id='buy 1'),
            pytest.param(5, 1, -5, 20, -30, id='buy 5'),
            pytest.param(1, -1, -1, -6, 4, id='sell 1'),
            pytest.param(2, -1, -2, -12, 8, id='sell 2'),
        ],
    )
    def test_trade_update(self, quantity, direction, r1, r2, r3):
        tick = TickFactory(bid=999.5, ask=1000.5)
        trade = TradeFactory(tick=tick, quantity=quantity, direction=direction)
        assert trade.result == r1

        tick = TickFactory(bid=1004.5, ask=1005.5)
        trade.on_new_tick(tick)
        assert trade.result == r2

        tick = TickFactory(bid=994.5, ask=995.5)
        trade.on_new_tick(tick)
        assert trade.result == r3


class TestOnNewTick:

    @pytest.mark.parametrize('invalid_tick', [
        pytest.param('string', id='string tick'),
        pytest.param([], id='empty array tick'),
        pytest.param(['string', 1], id='array tick'),
        pytest.param({}, id='empty dict tick'),
        pytest.param({'toto': 1}, id='dict tick'),
    ])
    def test_invalid_tick(self, invalid_tick):
        epic = EpicFactory()
        tick = TickFactory(epic=epic)
        trade = TradeFactory(tick=tick)

        with pytest.raises(TradeException, match='Invalid tick .*'):
            trade.on_new_tick(invalid_tick)


class TestTradeClose:
    @pytest.mark.parametrize(
        ['quantity', 'direction', 'result'],
        [
            pytest.param(1, 1, 4, id='close buy of 1'),
            pytest.param(3, 1, 12, id='close buy of 3'),
            pytest.param(1, -1, -6, id='close sell of 1'),
            pytest.param(5, -1, -30, id='close sell of 5'),
        ],
    )
    def test_trade_total_close(self, quantity, direction, result):
        tick = TickFactory(bid=999.5, ask=1000.5)
        trade = TradeFactory(tick=tick, quantity=quantity, direction=direction)
        assert not trade.closed

        tick1 = TickFactory(bid=1004.5, ask=1005.5)
        trade.on_new_tick(tick1)
        assert trade.result == result
        assert not trade.closed
        assert trade.closed_quantity == 0
        assert trade.opened_quantity == abs(quantity)

        trade.close()
        assert trade.result == result
        assert trade.closed_quantity == abs(quantity)
        assert trade.opened_quantity == 0
        assert trade.closed

    @pytest.mark.parametrize(
        [
            'quantity',
            'direction',
            'partial_close_quantity',
            'closed_result',
            'partial_result',
            'final_result',
        ],
        [
            pytest.param(3, 1, 2, -12, -18, -2, id='buy of 3, partial close 2'),
            pytest.param(3, 1, 1, -6, -18, 14, id='buy of 3, partial close 1'),
            pytest.param(5, -1, 2, 8, 20, -28, id='sell of 5, partial close of 2'),
            pytest.param(5, -1, 3, 12, 20, -12, id='sell of 5, partial close of 3'),
        ],
    )
    def test_trade_partial_close(
        self,
        quantity,
        direction,
        partial_close_quantity,
        closed_result,
        partial_result,
        final_result,
    ):
        tick = TickFactory(bid=999.5, ask=1000.5)
        trade = TradeFactory(tick=tick, quantity=quantity, direction=direction)
        assert not trade.closed

        tick1 = TickFactory(bid=994.5, ask=995.5)
        trade.on_new_tick(tick1)
        assert trade.result == partial_result
        assert not trade.closed

        # partial close
        trade.close(quantity=partial_close_quantity)
        assert trade.closed_result == closed_result, trade.closes
        assert trade.result == partial_result
        assert trade.closed_quantity == partial_close_quantity
        assert trade.opened_quantity == abs(quantity) - partial_close_quantity
        assert not trade.closed

        # final close
        tick2 = TickFactory(bid=1010.5, ask=1011.5)
        trade.close(tick=tick2)
        assert trade.result == final_result, trade.closes
        assert trade.closed
        assert trade.opened_quantity == 0
        assert trade.closed_quantity == abs(quantity)

    @pytest.mark.parametrize(['open_quantity', 'open_direction', 'close_quantity'], [
        pytest.param(2, 1, 3),
        pytest.param(3, -1, 4)
    ])
    def test_invalid_close(self, open_quantity, open_direction, close_quantity):
        trade = TradeFactory(quantity=open_quantity, direction=open_direction)

        with pytest.raises(TradeException):
            trade.close(quantity=close_quantity)

    @pytest.mark.parametrize('invalid_tick', [
        pytest.param('string', id='close with string'),
        pytest.param(['string', 1], id='close with array'),
        pytest.param({'string': 1}, id='close with dict'),
    ])
    def test_close_invalid_tick(self, invalid_tick):
        trade = TradeFactory()

        with pytest.raises(TradeException, match='Invalid tick .*'):
            trade.close(tick=invalid_tick)

    def test_close_tick_not_tradeable(self):
        trade = TradeFactory()
        epic = EpicFactory()
        epic.tradeable = False
        tick = TickFactory(epic=epic)

        trade.close(tick=tick)
        assert trade.closed_quantity == 0

    def test_close_to_dict(self):
        trade = TradeFactory(quantity=3, direction=-1)
        trade.close(quantity=2)
        assert trade.closed_quantity == 2
        close_dict = trade.closes[0].to_json()
        assert isinstance(close_dict['tick'], dict)
        assert isinstance(close_dict['tick']['datetime'], str)


class TestReporting:
    def test_base(self):
        trade = TradeFactory()
        assert trade.to_json
        assert trade.json_headers
