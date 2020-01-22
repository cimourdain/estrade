import pytest

from tests.factories import CandleFactory, TickFactory
from estrade.exceptions import CandleException


class TestCandle:

    def test_open(self):
        # GIVEN a tick @1000
        tick = TickFactory(bid=999.5, ask=1000.5)

        # WHEN i use it as open tick of a candle
        candle = CandleFactory(open_tick=tick)

        # THEN the candle open matches the tick value
        assert candle.open == tick.value
        # THEN the candle is not closed
        assert not candle.close
        # THEN the last value of candle is the open tick value
        assert candle.last == tick.value
        # THEN the candle open_at is the open tick datetime
        assert candle.open_at == tick.datetime

        # THEN only one tick is contained in candle
        assert len(candle.ticks) == 1
        # THEN the only tick in candle is the open tick
        assert candle.ticks[0] == tick

        # THEN the candle color is black (open=close as only one tick is in candle)
        assert candle.color == 'black'
        # THEN the candle high and low are the open tick value
        assert candle.low == tick.value
        assert candle.high == tick.value
        # THEN the height/body/head and tail are 0
        assert candle.height == 0
        assert candle.body == 0
        assert candle.head == 0
        assert candle.tail == 0

    def test_on_new_tick_valid(self):
        # GIVEN a candle with an open tick @1000
        tick1 = TickFactory(bid=999.5, ask=1000.5)
        candle = CandleFactory(open_tick=tick1)

        # WHEN i add a second tick @1005 on candle
        tick2 = TickFactory(bid=1004.5, ask=1005.5)
        candle.on_new_tick(tick2)
        # THEN the candle contains 2 ticks
        assert len(candle.ticks) == 2
        assert candle.ticks[1] == tick2

        # THEN the candle color is green (ticks are 1000 and 1005=> open < close)
        assert candle.color == 'green'
        # THEN the candle low is the open tick
        assert candle.low == tick1.value
        # THEN the candle high is the last tick
        assert candle.high == tick2.value
        # THEN the candle height and body is the difference between open and last tick
        assert candle.height == 5
        assert candle.body == 5
        # THEN the candle has no head and tails
        assert candle.head == 0
        assert candle.tail == 0
        # THEN the candle is not closed
        assert not candle.closed
        assert not candle.close

        tick3 = TickFactory(bid=1002.5, ask=1003.5)
        candle.on_new_tick(tick3)
        assert len(candle.ticks) == 3
        assert candle.ticks[2] == tick3
        assert candle.color == 'green'

        assert candle.low == tick1.value
        assert candle.high == tick2.value
        assert candle.height == 5
        assert candle.body == 3
        assert candle.head == 2
        assert candle.tail == 0
        assert not candle.closed
        assert not candle.close

        tick4 = TickFactory(bid=994.5, ask=995.5)
        candle.on_new_tick(tick4)
        assert len(candle.ticks) == 4
        assert candle.ticks[3] == tick4
        assert candle.color == 'red'

        assert candle.low == tick4.value
        assert candle.high == tick2.value
        assert candle.height == 10
        assert candle.body == 5
        assert candle.head == 5
        assert candle.tail == 0
        assert not candle.closed
        assert not candle.close

        tick5 = TickFactory(bid=997.5, ask=998.5)
        candle.on_new_tick(tick5)
        assert len(candle.ticks) == 5
        assert candle.ticks[4] == tick5
        assert candle.color == 'red'

        assert candle.low == tick4.value
        assert candle.high == tick2.value
        assert candle.height == 10
        assert candle.body == 2
        assert candle.head == 5
        assert candle.tail == 3
        assert not candle.closed
        assert not candle.close

    @pytest.mark.parametrize(
        'invalid_tick',
        [
            pytest.param('string', id='tick as string'),
            pytest.param(1, id='int tick'),
            pytest.param([], id='empty array tick'),
            pytest.param({}, id='empty dict tick')
        ],
    )
    def test_on_new_tick_invalid(self, invalid_tick):
        # GIVEN a tick @1000
        tick1 = TickFactory(bid=999.5, ask=1000.5)
        # WHEN I use this tick as open tick for a candle
        candle = CandleFactory(open_tick=tick1)

        # THEN if i add an invalid type tick on candle, a CandleException is raised
        with pytest.raises(CandleException):
            candle.on_new_tick(invalid_tick)

    def test_close_candle(self):
        # GIVEN a tick @1000
        tick1 = TickFactory(bid=999.5, ask=1000.5)
        # WHEN I use this tick as open tick for a candle
        candle = CandleFactory(open_tick=tick1)
        # THEN the candle is not closed
        assert not candle.closed
        assert not candle.close

        # GIVEN a second tick @ 1001
        tick2 = TickFactory(bid=1000.5, ask=1001.5)
        # WHEN I use this tick as open tick for a candle
        candle.on_new_tick(tick2)
        # THEN the candle is not closed
        assert not candle.closed
        assert not candle.close

        # WHEN I close the candle
        candle.close_candle()

        # THEN the candle is closed
        assert candle.closed
        # THEN the close property returns the last tick value
        assert candle.close == tick2.value
