import pytest
from datetime import datetime

import arrow

from tests.factories import EpicFactory, CandleFactory, TickFactory
from estrade.exceptions import CandleException, CandleSetException


class TestTimeframe:
    @pytest.mark.parametrize(
        ['timeframe'],
        [
            pytest.param('21ticks'),
            pytest.param('1minutes'),
            pytest.param('15minutes'),
            pytest.param('1hours'),
            pytest.param('4hours'),
        ]
    )
    def test_timeframe__ok(self, timeframe):
        candle = CandleFactory(timeframe=timeframe)
        assert candle.timeframe == timeframe

    @pytest.mark.parametrize(
        ['timeframe'],
        [
            pytest.param('minutes', id='missing nb'),
            pytest.param('15', id='missing UT'),
            pytest.param('0hours', id='0 nb'),
            pytest.param('5miliseconds', id='invalid UT'),
            pytest.param('21tick', id='missing UT \'s\''),
            pytest.param('13minutes', id='Incoherent 13minutes'),
            pytest.param('22seconds', id='Incoherent 22seconds'),
            pytest.param('5hours', id='Incoherent 5hours'),
            pytest.param('2days', id='Incoherent 2days'),
        ]
    )
    def test_timeframe__nok(self, timeframe):
        with pytest.raises(CandleSetException):
            CandleFactory(timeframe=timeframe)


class TestEpicRef:
    def test_epic_ref__ok(self):
        candle = CandleFactory(epic_ref='test_epic')
        assert candle.epic_ref == 'test_epic'

    @pytest.mark.parametrize(
        ['invalid_epic_ref'],
        [
            pytest.param(None),
            pytest.param({}),
            pytest.param(EpicFactory()),
        ]
    )
    def test_epic_ref_nok(self, invalid_epic_ref):
        with pytest.raises(CandleException):
            CandleFactory(epic_ref=invalid_epic_ref)


class TestOpenTick:
    def test_open_tick_ok(self):
        open_tick = TickFactory()
        candle = CandleFactory(open_tick=open_tick)
        assert candle.ticks[0] == open_tick

    @pytest.mark.parametrize(
        ['invalid_open_tick'],
        [
            pytest.param(None),
            pytest.param('test'),
            pytest.param({'test': 'test'}),
        ]
    )
    def test_open_tick__nok(self, invalid_open_tick):
        with pytest.raises(CandleException):
            CandleFactory(open_tick=invalid_open_tick)


class TestHighLowTick:
    def test_high_tick_init(self):
        tick = TickFactory()
        candle = CandleFactory(open_tick=tick)
        assert candle.high_tick == tick

    def test_low_tick_init(self):
        tick = TickFactory()
        candle = CandleFactory(open_tick=tick)
        assert candle.low_tick == tick

    def test_high_tick_update(self):
        open_tick = TickFactory(bid=999, ask=1000)
        candle = CandleFactory(open_tick=open_tick)
        new_low_tick = TickFactory(bid=998, ask=999)
        candle.on_new_tick(new_low_tick)
        new_max_tick = TickFactory(bid=1000, ask=1001)
        candle.on_new_tick(new_max_tick)
        other_low_tick = TickFactory(bid=990, ask=991)
        candle.on_new_tick(other_low_tick)

        assert candle.high_tick == new_max_tick

    def test_low_tick_update(self):
        open_tick = TickFactory(bid=999, ask=1000)
        candle = CandleFactory(open_tick=open_tick)

        new_high_tick = TickFactory(bid=1001, ask=1002)
        candle.on_new_tick(new_high_tick)
        new_min_tick = TickFactory(bid=998, ask=999)
        candle.on_new_tick(new_min_tick)
        other_high_tick = TickFactory(bid=1002, ask=1003)
        candle.on_new_tick(other_high_tick)

        assert candle.low_tick == new_min_tick


class TestClose:
    def test_not_closed_on_init(self):
        candle = CandleFactory()
        assert candle.closed is False

    def test_close_candle(self):
        candle = CandleFactory()
        candle.close_candle()
        assert candle.closed is True


class TestOpenAt:
    def test_open_at(self):
        tick = TickFactory(datetime=arrow.get(
            datetime(year=2019, month=1, day=1, hour=0, minute=7, second=0), 'UTC'
        ))
        candle = CandleFactory(timeframe='5minutes', open_tick=tick)

        assert candle.open_at == arrow.get(
            datetime(year=2019, month=1, day=1, hour=0, minute=5, second=0), 'UTC'
        )


