import arrow
import pytest

from estrade.exceptions import EpicException, StrategyException
from tests.factories import (
    CandleSetFactory,
    EpicFactory,
    MarketFactory,
    StrategyFactory,
    TickFactory
)


class TestStrategy:

    def test_base(self):
        strategy = StrategyFactory()
        assert strategy.ref
        assert strategy.epics


class TestStrategyRef:

    def test_base(self):
        strategy = StrategyFactory()
        assert strategy.ref
        assert strategy.ref[:9] == 'strategy_'

    def test_manual_set(self):
        strategy = StrategyFactory(ref='test_ref')
        assert strategy.ref == 'test_ref'

        strategy = StrategyFactory()
        strategy.ref = 'test_ref2'
        assert strategy.ref == 'test_ref2'

    @pytest.mark.parametrize('invalid_ref', [
        pytest.param(1, id='int ref'),
        pytest.param([], id='list ref'),
        pytest.param({}, id='dict ref'),
    ])
    def test_invalid_ref(self, invalid_ref):
        with pytest.raises(StrategyException):
            StrategyFactory(ref=invalid_ref)

        s = StrategyFactory()
        with pytest.raises(StrategyException):
            s.ref = invalid_ref


class TestStrategyEpics:

    def test_base(self):
        epic1 = EpicFactory()
        epic2 = EpicFactory()

        strategy = StrategyFactory(epics=[epic1])
        assert strategy.epics == [epic1]

        strategy = StrategyFactory(epics=[epic1, epic2])
        assert strategy.epics == [epic1, epic2]

    def test_empty_epics(self):
        strategy = StrategyFactory(epics=None)
        assert not strategy.epics

        strategy = StrategyFactory(epics=[])
        assert not strategy.epics

    @pytest.mark.parametrize('invalid_epics', [
        pytest.param('string', id='string epics'),
        pytest.param(1, id='int epics'),
        pytest.param(['string', 1], id='list epics'),
        pytest.param({}, id='dict epics'),
    ])
    def test_invalid_epics(self, invalid_epics):
        with pytest.raises(StrategyException):
            StrategyFactory(epics=invalid_epics)

        s = StrategyFactory()
        with pytest.raises(StrategyException):
            s.epics = invalid_epics

    def test_get_candle_set(self):
        cs3m1 = CandleSetFactory(timeframe='3minutes')
        cs5m1 = CandleSetFactory(timeframe='5minutes')
        epic1 = EpicFactory(ref='epic1', candle_sets=[cs3m1, cs5m1])

        cs1m2 = CandleSetFactory(timeframe='1minutes')
        cs5m2 = CandleSetFactory(timeframe='5minutes')
        epic2 = EpicFactory(ref='epic2', candle_sets=[cs5m2, cs1m2])

        strategy = StrategyFactory(epics=[epic1, epic2])
        assert strategy.get_candle_set(epic_ref='epic1', timeframe='3minutes') == cs3m1
        assert strategy.get_candle_set(epic_ref='epic1', timeframe='5minutes') == cs5m1
        assert strategy.get_candle_set(epic_ref='epic2', timeframe='5minutes') == cs5m2
        assert strategy.get_candle_set(epic_ref='epic2', timeframe='1minutes') == cs1m2

        # ask for non existant epic_ref
        with pytest.raises(StrategyException):
            strategy.get_candle_set(epic_ref='inexistant', timeframe='1minutes')

        with pytest.raises(EpicException):
            strategy.get_candle_set(epic_ref='epic2', timeframe='inexistant')


class TestStrategyParams:

    def test_base(self):
        params = {
            'key1': 1,
            'key2': 'string'
        }
        strategy = StrategyFactory(params=params)
        assert strategy.params == params

    @pytest.mark.parametrize('invalid_params', [
        pytest.param('string', id='string params'),
        pytest.param(1, id='int params'),
        pytest.param(['string', 1], id='list params'),
    ])
    def test_invalid_params(self, invalid_params):
        with pytest.raises(StrategyException):
            StrategyFactory(params=invalid_params)

        s = StrategyFactory()
        with pytest.raises(StrategyException):
            s.params = invalid_params


class TestStrategyMarket:

    def test_base(self):
        strategy = StrategyFactory()
        market = MarketFactory(strategies=[strategy])
        assert strategy.market == market


class TestDatetimeConstraint:
    # TODO
    pass


class TestStrategyOnNewTick:

    def test_call_opening_strategy(self, mocker):
        tick = TickFactory()
        strategy = StrategyFactory()
        mock_opening_strategy = mocker.patch.object(strategy, 'on_new_tick_opening_strategy')
        mock_closing_strategy = mocker.patch.object(strategy, 'on_new_tick_closing_strategy')
        MarketFactory(strategies=[strategy])
        strategy.on_new_tick(tick)

        assert mock_opening_strategy.called_once
        assert not mock_closing_strategy.called

    def test_call_closing_strategy(self, mocker):
        tick = TickFactory()
        strategy = StrategyFactory()
        mock_opening_strategy = mocker.patch.object(strategy, 'on_new_tick_opening_strategy')
        mock_closing_strategy = mocker.patch.object(strategy, 'on_new_tick_closing_strategy')
        MarketFactory(strategies=[strategy])
        strategy.open_trade(
            tick=tick,
            quantity=5,
            direction='BUY'
        )
        strategy.on_new_tick(tick)
        assert not mock_opening_strategy.called
        assert mock_closing_strategy.called_once

    def test_incomplete_strategy(self):
        tick = TickFactory()
        strategy = StrategyFactory()
        with pytest.raises(StrategyException):
            strategy.on_new_tick(tick)

    def test_methods_are_pass(self):
        tick = TickFactory()
        strategy = StrategyFactory()
        assert strategy.on_new_tick_opening_strategy(tick) is None
        assert strategy.on_new_tick_closing_strategy(tick) is None


class TestStrategyOnNewCandle:

    def test_opening_strategy(self, mocker):

        strategy = StrategyFactory(epics=[
            EpicFactory(
                candle_sets=[
                    CandleSetFactory(timeframe='5minutes')
                ]
            )
        ])
        mock_opening_strategy = mocker.patch.object(strategy, 'on_new_tick_opening_strategy')
        MarketFactory(strategies=[strategy])

        tick = TickFactory(
            datetime=arrow.get('2019-01-01 03:00:00', 'YYYY-MM-DD HH:mm:ss').to('UTC')
        )
        strategy.on_new_tick(tick)

        tick = TickFactory(
            datetime=arrow.get('2019-01-01 03:05:01', 'YYYY-MM-DD HH:mm:ss').to('UTC')
        )
        strategy.on_new_tick(tick)
        assert mock_opening_strategy.called_once

    def test_closing_strategy(self, mocker):
        strategy = StrategyFactory(epics=[
            EpicFactory(
                candle_sets=[
                    CandleSetFactory(timeframe='5minutes')
                ]
            )
        ])
        mock_closing_strategy = mocker.patch.object(strategy, 'on_new_tick_closing_strategy')
        MarketFactory(strategies=[strategy])

        tick = TickFactory(
            datetime=arrow.get('2019-01-01 03:00:00', 'YYYY-MM-DD HH:mm:ss').to('UTC')
        )
        strategy.on_new_tick(tick)

        strategy.open_trade(tick=tick, quantity=2, direction='BUY')

        tick = TickFactory(
            datetime=arrow.get('2019-01-01 03:05:01', 'YYYY-MM-DD HH:mm:ss').to('UTC')
        )
        strategy.on_new_tick(tick)
        assert mock_closing_strategy.called_once

    def test_get_candle(self):
        # GIVEN a market with an epic containing 2 candle sets
        candle_set5m = CandleSetFactory(timeframe='5minutes')
        candle_set1m = CandleSetFactory(timeframe='1minutes')
        epic = EpicFactory(candle_sets=[candle_set5m, candle_set1m])
        strategy = StrategyFactory(epics=[epic])
        market = MarketFactory(strategies=[strategy])

        tick = TickFactory(
            epic=epic,
            datetime=arrow.get('2019-01-01 03:00:00', 'YYYY-MM-DD HH:mm:ss').to('UTC')
        )
        market.on_new_tick(tick)

        strategy.open_trade(tick=tick, quantity=2, direction='BUY')

        tick = TickFactory(
            epic=epic,
            datetime=arrow.get('2019-01-01 03:05:01', 'YYYY-MM-DD HH:mm:ss').to('UTC')
        )
        market.on_new_tick(tick)

        assert len(candle_set5m.candles) == 2
        assert strategy.get_candle(epic_ref=epic.ref, timeframe='5minutes') == candle_set5m.candles[-1]
        assert strategy.get_candle(epic_ref=epic.ref, timeframe='5minutes', offset=1) == candle_set5m.candles[-2]
        assert strategy.get_candle(epic_ref=epic.ref, timeframe='5minutes', offset=3) is None

    def test_get_indicators(self):
        # TODO
        pass


class TestOpenTrades:

    def test_open_trade(self, mocker):
        open_trade_mocker = mocker.patch('estrade.trade_manager.TradeManager.open_trade')

        strategy = StrategyFactory(epics=None)
        market = MarketFactory()
        strategy.market = market

        tick = TickFactory()
        open_params = {
            'tick': tick,
            'quantity': -5,
        }
        strategy.open_trade(**open_params)
        open_params['strategy'] = strategy
        open_trade_mocker.assert_called_with(**open_params)


class TestCloseTrades:

    def test_close_trade(self, mocker):
        close_trade_mocker = mocker.patch('estrade.trade_manager.TradeManager.close_trade_by_ref')

        strategy = StrategyFactory(epics=None)
        MarketFactory(strategies=[strategy])

        tick = TickFactory()
        open_params = {
            'tick': tick,
            'quantity': -5,
            'direction': 'BUY'
        }
        strategy.open_trade(**open_params)
        assert strategy.market.trade_manager.nb_trades() == 1

        close_params = {
            'ref': strategy.market.trade_manager.trades[0].ref,
            'close_reason': 'reason',
            'quantity': 2,
        }
        strategy.close_trade_by_ref(**close_params)
        close_params['strategy'] = strategy
        close_trade_mocker.assert_called_with(**close_params)

    def test_close_all_trades(self, mocker):
        close_trade_mocker = mocker.patch('estrade.trade_manager.TradeManager.close_all_trades')

        strategy = StrategyFactory(epics=None)
        MarketFactory(strategies=[strategy])

        tick = TickFactory()
        strategy.open_trade(quantity=-5, direction='BUY', tick=tick)
        strategy.open_trade(quantity=-8, direction='BUY', tick=tick)
        strategy.open_trade(quantity=1, direction='BUY', tick=tick)
        strategy.open_trade(quantity=12, direction='BUY', tick=tick)
        assert strategy.market.trade_manager.nb_trades() == 4

        close_params = {
            'close_reason': 'reason',
        }
        strategy.close_all_trades(**close_params)
        close_params['strategy'] = strategy
        close_trade_mocker.assert_called_with(**close_params)

    def test_close_all_buys(self, mocker):
        close_trade_mocker = mocker.patch('estrade.trade_manager.TradeManager.close_all_buys')

        strategy = StrategyFactory(epics=None)
        MarketFactory(strategies=[strategy])

        tick = TickFactory()
        strategy.open_trade(quantity=-5, tick=tick, direction='BUY')
        strategy.open_trade(quantity=-8, tick=tick, direction='BUY')
        strategy.open_trade(quantity=1, tick=tick, direction='BUY')
        strategy.open_trade(quantity=12, tick=tick, direction='BUY')
        assert strategy.market.trade_manager.nb_trades() == 4

        close_params = {
            'close_reason': 'reason',
        }
        strategy.close_all_buys(**close_params)
        close_params['strategy'] = strategy
        close_trade_mocker.assert_called_with(**close_params)

    def test_close_all_sells(self, mocker):
        close_trade_mocker = mocker.patch('estrade.trade_manager.TradeManager.close_all_sells')

        strategy = StrategyFactory(epics=None)
        MarketFactory(strategies=[strategy])

        tick = TickFactory()
        strategy.open_trade(quantity=-5, tick=tick, direction='BUY')
        strategy.open_trade(quantity=-8, tick=tick, direction='BUY')
        strategy.open_trade(quantity=1, tick=tick, direction='BUY')
        strategy.open_trade(quantity=12, tick=tick, direction='BUY')
        assert strategy.market.trade_manager.nb_trades() == 4

        close_params = {
            'close_reason': 'reason',
        }
        strategy.close_all_sells(**close_params)
        close_params['strategy'] = strategy
        close_trade_mocker.assert_called_with(**close_params)


class TestMaxConcurrentTrades:

    def test_base(self, mocker):
        market = MarketFactory()
        strategy = market.strategies[0]
        strategy.max_concurrent_trades = 2
        opening_strategy_mocker = mocker.spy(strategy, 'on_new_tick_opening_strategy')
        closing_strategy_mocker = mocker.spy(strategy, 'on_new_tick_closing_strategy')

        tick = TickFactory(epic=market.epics[0])
        market.on_new_tick(tick)
        assert opening_strategy_mocker.call_count == 1
        # closing strategy not called because no trade is open
        assert not closing_strategy_mocker.called

        strategy.open_trade(quantity=5, epic=strategy.epics[0].ref, direction='BUY')
        assert strategy.market.trade_manager.nb_trades(strategy=strategy) == 1

        tick = TickFactory(epic=market.epics[0])
        market.on_new_tick(tick)
        assert closing_strategy_mocker.call_count == 1
        assert opening_strategy_mocker.call_count == 2

        strategy.open_trade(quantity=8, epic=strategy.epics[0].ref, direction='SELL')
        assert strategy.market.trade_manager.nb_trades(strategy=strategy) == 2

        tick = TickFactory(epic=market.epics[0])
        market.on_new_tick(tick)
        assert closing_strategy_mocker.call_count == 2
        # opening strategy is not called
        assert opening_strategy_mocker.call_count == 2

        # close one trade
        strategy.close_trade_by_ref(ref=strategy.market.trade_manager.trades[0].ref)
        assert strategy.market.trade_manager.nb_trades(strategy=strategy, only_opened=True) == 1
        assert strategy.market.trade_manager.nb_trades(strategy=strategy, only_closed=True) == 1

        tick = TickFactory(epic=market.epics[0])
        market.on_new_tick(tick)
        assert closing_strategy_mocker.call_count == 3
        assert opening_strategy_mocker.call_count == 3

        strategy.open_trade(quantity=12, epic=strategy.epics[0].ref, direction='BUY')
        assert strategy.market.trade_manager.nb_trades(strategy=strategy, only_opened=True) == 2
        assert strategy.market.trade_manager.nb_trades(strategy=strategy, only_closed=True) == 1

        tick = TickFactory(epic=market.epics[0])
        market.on_new_tick(tick)
        assert closing_strategy_mocker.call_count == 4
        assert opening_strategy_mocker.call_count == 3

        strategy.close_all_trades()
        assert strategy.market.trade_manager.nb_trades(strategy=strategy, only_opened=True) == 0, strategy.market.trade_manager.strategy_trades[strategy.ref]['opened']
        assert strategy.market.trade_manager.nb_trades(strategy=strategy, only_closed=True) == 3

        tick = TickFactory(epic=market.epics[0])
        market.on_new_tick(tick)
        assert closing_strategy_mocker.call_count == 4
        assert opening_strategy_mocker.call_count == 4


class TestStrategyReporting:

    def test_base(self):
        strategy = StrategyFactory()
        MarketFactory(strategies=[strategy])

        assert strategy.to_json
        assert strategy.json_headers

    def test_no_market(self):
        strategy = StrategyFactory()

        assert strategy.to_json
        assert strategy.json_headers
