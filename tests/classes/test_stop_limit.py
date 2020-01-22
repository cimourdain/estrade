import pytest


from tests.factories import (
    StopLimitAbsoluteFactory,
    StopLimitRelativeFactory,
    TickFactory,
    TradeFactory,
)
from estrade.exceptions import StopLimitException


class TestStopLimitEmpty:

    def test_empty_stop_on_init(self):
        trade = TradeFactory(stop_absolute=None, stop_relative=None)
        assert trade.stop is None

        trade = TradeFactory(stop_absolute=900)
        trade.set_stop(stop_value=None)
        assert trade.stop is None

        trade = TradeFactory(stop_relative=10)
        trade.set_stop(stop_value=None, relative=True)
        assert trade.stop is None

    def test_empty_limit_on_init(self):
        trade = TradeFactory(limit_absolute=None, limit_relative=None)
        assert trade.limit is None

        trade = TradeFactory(limit_absolute=1010)
        trade.set_limit(limit_value=None)
        assert trade.limit is None

        trade = TradeFactory(limit_relative=10)
        trade.set_limit(limit_value=None, relative=True)
        assert trade.limit is None


class TestInvalidStopLimitCall:

    def test_invalid_stop_setter(self):
        trade = TradeFactory()
        with pytest.raises(NotImplementedError):
            trade.stop = 10

    def test_invalid_limit_setter(self):
        trade = TradeFactory()
        with pytest.raises(NotImplementedError):
            trade.limit = 10


class TestStopLimitAbsolute:

    def test_trade_absolute_stop(self):
        tick = TickFactory(bid=999, ask=1001)
        trade = TradeFactory(tick=tick, stop_absolute=995)
        assert trade.stop.absolute_value == 995

    def test_trade_absolute_limit(self):
        tick = TickFactory(bid=999, ask=1001)
        trade = TradeFactory(tick=tick, limit_absolute=1005)
        assert trade.limit.absolute_value == 1005

    @pytest.mark.parametrize(
        ['trade_direction', 'type_', 'value', 'expected_relative_value'],
        [
            pytest.param('BUY', 'limit', 1005, 4, id='init absolute limit of 1005 on a BUY opened @1000'),
            pytest.param('BUY', 'stop', 900, 101, id='init absolute stop of 900 on a BUY opened @1000'),
            pytest.param('SELL', 'limit', 900, 99, id='init absolute limit of 900 on a SELL opened @1000'),
            pytest.param('SELL', 'stop', 1005, 6, id='init absolute stop of 1005 on a SELL opened @1000'),
        ],
    )
    def test_base_absolute_stop_limit(self, trade_direction, type_, value, expected_relative_value):
        # GIVEN a trade opened @ 1000
        tick = TickFactory(bid=999, ask=1001)
        trade = TradeFactory(tick=tick, direction=trade_direction)

        # WHEN i create a Stop/Limit for this trade with the input value
        sla = StopLimitAbsoluteFactory(
            trade=trade,
            type_=type_,
            value=value
        )

        # THEN the stop/limit type is the one expected
        assert sla.type_ == type_.upper()
        # THEN the stop/limit trade is the expected trade
        assert sla.trade == trade
        # THEN the direction is None
        assert not sla.direction
        # THEN the absolute value is the input value
        assert sla.absolute_value == value
        assert sla.relative_value == expected_relative_value

    @pytest.mark.parametrize(
        ['trade_direction', 'stop_absolute', 'limit_absolute', 'unclosed_tick', 'tick'],
        [
            pytest.param(
                'BUY',
                950,
                None,
                {'bid': 951, 'ask': 952},
                {'bid': 950, 'ask': 951},
                id='stop reached on BUY'
            ),
            pytest.param(
                'SELL',
                1050,
                None,
                {'bid': 1048, 'ask': 1049},
                {'bid': 1049, 'ask': 1050},
                id='stop reached on SELL'
            ),
            pytest.param(
                'BUY',
                None,
                1050,
                {'bid': 1049, 'ask': 1050},
                {'bid': 1050, 'ask': 1051},
                id='limit reached on BUY'
            ),
            pytest.param(
                'SELL',
                None,
                950,
                {'bid': 950, 'ask': 951},
                {'bid': 949, 'ask': 950},
                id='limit reached on SELL'
            ),
        ]
    )
    def test_close_on_absolute_stop_reached(self, trade_direction, stop_absolute, limit_absolute, unclosed_tick, tick):
        trade = TradeFactory(
            direction=trade_direction,
            tick=TickFactory(bid=999, ask=1001),
            limit_absolute=limit_absolute,
            stop_absolute=stop_absolute,
        )
        trade.on_new_tick(tick=TickFactory(**unclosed_tick))
        assert not trade.closed

        trade.on_new_tick(tick=TickFactory(**tick))
        assert trade.closed


class TestStopLimitRelative:

    def test_trade_stop(self):
        tick = TickFactory()
        trade = TradeFactory(tick=tick, stop_relative=10)
        assert trade.stop.relative_value == 10, trade.stop

    def test_trade_limit(self):
        tick = TickFactory()
        trade = TradeFactory(tick=tick, limit_relative=15)
        assert trade.limit.relative_value == 15, trade.limit

    @pytest.mark.parametrize(
        ['trade_direction', 'type_', 'value', 'stop_limit_direction', 'expected_abs_value'],
        [
            pytest.param('BUY', 'limit', 5, 1, 1006, id='init relative limit of 5 on a BUY opened @1000'),
            pytest.param('BUY', 'stop', 10, -1, 991, id='init relative stop of 10 on a BUY opened @1000'),
            pytest.param('SELL', 'limit', 12, -1, 987, id='init relative limit of 12 on a SELL opened @1000'),
            pytest.param('SELL', 'stop', 8, 1, 1007, id='init relative stop of 8 on a SELL opened @1000'),
        ],
    )
    def test_base_relative_stop_limit(self, trade_direction, type_, value, stop_limit_direction, expected_abs_value):
        # GIVEN a trade opened @ 1000
        tick = TickFactory(bid=999, ask=1001)
        trade = TradeFactory(tick=tick, direction=trade_direction)

        # WHEN i create a Stop/Limit for this trade with the input value
        sla = StopLimitRelativeFactory(
            trade=trade,
            type_=type_,
            value=value,
        )

        # THEN the stop/limit type is the one expected
        assert sla.type_ == type_.upper()
        # THEN the stop/limit trade is the expected trade
        assert sla.trade == trade
        # THEN the direction is as expected
        assert sla.direction == stop_limit_direction
        # THEN the absolute value is the input value
        assert sla.absolute_value == expected_abs_value
        # THEN the relative value is the one expected
        assert sla.relative_value == value

    @pytest.mark.parametrize(
        ['trade_direction', 'stop_relative', 'limit_relative', 'unclosed_tick', 'tick'],
        [
            pytest.param(
                'BUY',
                10,
                None,
                {'bid': 992, 'ask': 993},
                {'bid': 991, 'ask': 992},
                id='stop reached on BUY'
            ),
            pytest.param(
                'SELL',
                10,
                None,
                {'bid': 1007, 'ask': 1008},
                {'bid': 1008, 'ask': 1009},
                id='stop reached on SELL'
            ),
            pytest.param(
                'BUY',
                None,
                10,
                {'bid': 1010, 'ask': 1011},
                {'bid': 1011, 'ask': 1012},
                id='limit reached on BUY'
            ),
            pytest.param(
                'SELL',
                None,
                10,
                {'bid': 989, 'ask': 990},
                {'bid': 988, 'ask': 989},
                id='limit reached on SELL'
            ),
        ]
    )
    def test_close_on_relative_stop_reached(self, trade_direction, stop_relative, limit_relative, unclosed_tick, tick):
        trade = TradeFactory(
            direction=trade_direction,
            tick=TickFactory(bid=999, ask=1001),
            limit_relative=limit_relative,
            stop_relative=stop_relative,
        )
        trade.on_new_tick(tick=TickFactory(**unclosed_tick))
        assert not trade.closed

        trade.on_new_tick(tick=TickFactory(**tick))
        assert trade.closed


class TestStopLimitInvalidParams:

    @pytest.mark.parametrize(['invalid_stop_limit_type'], [
        pytest.param(None, id='None type'),
        pytest.param('str', id='string type'),
    ])
    def test_invalid_type(self, invalid_stop_limit_type):
        # WHEN I instanciate a StopLimitAbsolute instance with an invalid stop_limit_type
        # THEN a StopLimitException is raised
        with pytest.raises(StopLimitException):
            StopLimitAbsoluteFactory(type_=invalid_stop_limit_type)

        # WHEN I instanciate a StopLimitRelative instance with an invalid stop_limit_type
        # THEN a StopLimitException is raised
        with pytest.raises(StopLimitException):
            StopLimitRelativeFactory(type_=invalid_stop_limit_type)

    @pytest.mark.parametrize(['invalid_trade'], [
        pytest.param(None, id='None trade'),
        pytest.param('str', id='string trade'),
        pytest.param([], id='empty list trade'),
        pytest.param({}, id='empty dict trade'),
    ])
    def test_invalid_trade(self, invalid_trade):
        # WHEN I instanciate a StopLimitAbsolute instance with an invalid trade
        # THEN a StopLimitException is raised
        with pytest.raises(StopLimitException):
            StopLimitAbsoluteFactory(trade=invalid_trade)

        # WHEN I instanciate a StopLimitRelative instance with an invalid trade
        # THEN a StopLimitException is raised
        with pytest.raises(StopLimitException):
            StopLimitRelativeFactory(trade=invalid_trade)

    @pytest.mark.parametrize('invalid_value', [
        pytest.param(True, id='bool stop/limit value')
    ])
    def test_invalid_value(self, invalid_value):

        with pytest.raises(StopLimitException):
            TradeFactory(stop_absolute=invalid_value)
