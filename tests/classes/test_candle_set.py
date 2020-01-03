from datetime import datetime
from dateutil import tz

import pytest

from estrade.classes.exceptions import CandleSetException

from tests.factories import (
    CandleSetFactory,
    CandleSetIndicatorFactory,
    EpicFactory,
    TickFactory
)


class TestCandleSet:

    def test_base(self):
        # GIVEN a candle set
        candle_set = CandleSetFactory(timeframe='4hours')

        # THEN the candle set ut and nb are split of tiemeframe
        assert candle_set.ut == 'hours'
        assert candle_set.nb == 4
        assert candle_set.timeframe == '4hours'

        # THEN the candle set has no candles
        assert len(candle_set.candles) == 0
        assert not candle_set.current_candle


class TestCandleSetEpic:

    def test_epic_assign(self):
        # GIVEN a candle set
        candle_set = CandleSetFactory(timeframe='4hours')

        # WHEN i assign this candle set to an epic
        epic = EpicFactory(ref='test_epic_ref', candle_sets=[candle_set])

        # THEN the candle set ref is a concat of epic ref and timeframe
        assert candle_set.ref == 'test_epic_ref-4hours'
        # THEN the candle set epic is the epic it was assigned to
        assert candle_set.epic == epic

        epic2 = EpicFactory()
        with pytest.raises(CandleSetException):
            candle_set.epic = epic2


    @pytest.mark.parametrize(
        'invalid_epic',
        [
            pytest.param('string'),
            pytest.param(3),
            pytest.param(['string', 'string2']),
            pytest.param({'key': 1}),
        ],
    )
    def test_invalid_epic(self, invalid_epic):
        # GIVEN a candle set
        candle_set = CandleSetFactory()

        # WHEN i assign an invalid epic to it
        # THEN an Exception is raised
        with pytest.raises(CandleSetException):
            candle_set.epic = invalid_epic


class TestCandleSetIndicators:

    def test_add_indicators(self):
        # GIVEN 2 indicators
        indicator1 = CandleSetIndicatorFactory(name='i1')
        indicator2 = CandleSetIndicatorFactory(name='i2')
        # WHEN I add these indicators to a candle_set
        candle_set = CandleSetFactory(indicators=[indicator2, indicator1])

        # THEN the candle_set holds the 2 indicators
        assert len(candle_set.indicators) == 2
        assert indicator1 in candle_set.indicators
        assert indicator2 in candle_set.indicators

        # THEN the indicators getter returns the right indicator when used
        assert candle_set.indicator('i1') == indicator1
        assert candle_set.indicator('i2') == indicator2

    def test_get_indicator(self):
        # GIVEN 2 indicators on a candle set
        indicator1 = CandleSetIndicatorFactory(name='i1')
        indicator2 = CandleSetIndicatorFactory(name='i2')
        candle_set = CandleSetFactory(indicators=[indicator2, indicator1])

        # WHEN I call the indicator getter with a non exiting indicator name
        # THEN an exception is raised
        with pytest.raises(CandleSetException):
            candle_set.indicator('undefined')

    @pytest.mark.parametrize('invalid_indicators', (
        pytest.param('string', id='string indicators'),
        pytest.param(2, id='int indicators'),
        pytest.param([CandleSetIndicatorFactory(), 1], id='mixed indicators'),
    ))
    def test_invalid_indicators(self, invalid_indicators):
        with pytest.raises(CandleSetException):
            CandleSetFactory(indicators=invalid_indicators)

    def test_update_indicator_on_new_tick(self, mocker):
        # GIVEN 2 indicators on a candleSet
        indicator1 = CandleSetIndicatorFactory(name='i1')
        indicator2 = CandleSetIndicatorFactory(name='i2')
        # GIVEN mocker of the indicators on_new_tick methods
        i1_on_new_tick = mocker.spy(indicator1, 'on_new_tick')
        i2_on_new_tick = mocker.patch.object(indicator2, 'on_new_tick')

        # GIVEN a candleset holding these 2 indicators
        candle_set = CandleSetFactory(indicators=[indicator2, indicator1])
        # add candleset to epic (because event subscription is done on epic set)
        EpicFactory(candle_sets=[candle_set])

        # WHEN i call the candle set on_new_tick method
        tick = TickFactory()
        candle_set.on_new_tick(tick=tick)

        # THEN the indicators on_new_tick method is called
        assert i1_on_new_tick.called
        assert i2_on_new_tick.called


class TestCandleSetTimeFrame:

    @pytest.mark.parametrize(
        ['timeframe', 'expected_error_msg'],
        [
            pytest.param(
                '0seconds',
                'Impossible to set a negative number for candleSet timeframe',
                id='0seconds',
            ),
            pytest.param('7seconds', 'Inconsistent UT', id='7 seconds'),
            pytest.param('21seconds', 'Inconsistent UT', id='21 seconds'),
            pytest.param('62seconds', 'Inconsistent UT', id='62 seconds'),
            pytest.param(
                '0minutes',
                'Impossible to set a negative number for candleSet timeframe',
                id='0minutes',
            ),
            pytest.param('7minutes', 'Inconsistent UT', id='7 minutes'),
            pytest.param('21minutes', 'Inconsistent UT', id='21 minutes'),
            pytest.param('62minutes', 'Inconsistent UT', id='62 minutes'),
            pytest.param(
                '0hours',
                'Impossible to set a negative number for candleSet timeframe',
                id='0hours',
            ),
            pytest.param('5hours', 'Inconsistent UT', id='5 hours'),
            pytest.param('9hours', 'Inconsistent UT', id='9 hours'),
            pytest.param('21hours', 'Inconsistent UT', id='21 hours'),
            pytest.param(
                '0days',
                'Impossible to set a negative number for candleSet timeframe',
                id='0 days',
            ),
            pytest.param('2days', 'Inconsistent UT', id='2 days'),
            pytest.param('2test', 'Invalid CandleSet UT', id='Invalid UT string'),
            pytest.param(
                'lololo',
                'Impossible to create candle set',
                id='Invalid timeframe string',
            ),
        ],
    )
    def test_invalid_timeframe(self, timeframe, expected_error_msg):
        # WHEN i instanciate a candleset with an invalid timeframe value
        # THEN an exception is raised
        with pytest.raises(CandleSetException, match=r'.*{}.*'.format(expected_error_msg)):
            CandleSetFactory(timeframe=timeframe)


class TestCandleSetAddTick:

    def test_add_candles_ticks(self):
        for nb_ticks in [1, 3, 21, 50]:
            candle_set = CandleSetFactory(timeframe='{}ticks'.format(nb_ticks))
            EpicFactory(candle_sets=[candle_set])
            assert not len(candle_set.candles)

            for _ in range(nb_ticks):
                tick = TickFactory()
                candle_set.on_new_tick(tick)
                assert len(candle_set.candles) == 1
                assert not candle_set.current_candle.closed
                assert not candle_set.last_closed_candle

            for _ in range(nb_ticks):
                tick = TickFactory()
                candle_set.on_new_tick(tick)
                assert len(candle_set.candles) == 2
                assert not candle_set.current_candle.closed
                assert candle_set.candles[0].closed
                assert candle_set.last_closed_candle == candle_set.candles[0]

            for _ in range(nb_ticks):
                tick = TickFactory()
                candle_set.on_new_tick(tick)
                assert len(candle_set.candles) == 3
                assert not candle_set.current_candle.closed
                assert candle_set.candles[0].closed
                assert candle_set.candles[1].closed
                assert candle_set.last_closed_candle == candle_set.candles[1]

    def test_prevent_add_tick_if_no_epic_set(self):
        candle_set = CandleSetFactory()
        tick = TickFactory()
        with pytest.raises(CandleSetException):
            candle_set.on_new_tick(tick)

    @pytest.mark.parametrize(
        ['timeframe', 'tick_second', 'candle_open_second'],
        [
            pytest.param('1seconds', 0, 0),
            pytest.param('1seconds', 1, 1),
            pytest.param('1seconds', 2, 2),
            pytest.param('1seconds', 3, 3),
            pytest.param('1seconds', 4, 4),
            pytest.param('1seconds', 59, 59),
            pytest.param('2seconds', 0, 0),
            pytest.param('2seconds', 1, 0),
            pytest.param('2seconds', 2, 2),
            pytest.param('2seconds', 3, 2),
            pytest.param('2seconds', 4, 4),
            pytest.param('2seconds', 59, 58),
            pytest.param('3seconds', 0, 0),
            pytest.param('3seconds', 1, 0),
            pytest.param('3seconds', 2, 0),
            pytest.param('3seconds', 3, 3),
            pytest.param('3seconds', 4, 3),
            pytest.param('3seconds', 59, 57),
        ],
    )
    def test_candles_second_change(self, timeframe, tick_second, candle_open_second):
        candle_set = CandleSetFactory(timeframe=timeframe)
        EpicFactory(candle_sets=[candle_set])

        tick = TickFactory(
            datetime=datetime(
                year=2019, month=1, day=1, hour=0, minute=0, second=tick_second, tzinfo=tz.gettz('UTC')
            )
        )
        candle_set.on_new_tick(tick)
        assert candle_set.candles[0].open_at.second == candle_open_second

    @pytest.mark.parametrize(
        'nb_seconds',
        [
            pytest.param(2, id='2 seconds'),
            pytest.param(3, id='3 seconds'),
            pytest.param(12, id='12 seconds'),
            pytest.param(20, id='20 seconds'),
        ],
    )
    def test_add_candles_seconds(self, nb_seconds):
        candle_set = CandleSetFactory(timeframe='{}seconds'.format(nb_seconds))
        epic = EpicFactory(candle_sets=[candle_set])

        tick = TickFactory(epic=epic)
        candle_set.on_new_tick(tick)
        for i in range(nb_seconds - 1):
            tick = TickFactory(
                epic=epic,
                datetime=datetime(year=2019, month=1, day=1, hour=0, minute=0, second=i, tzinfo=tz.gettz('UTC'))
            )
            candle_set.on_new_tick(tick)
            assert len(candle_set.candles) == 1, 'iteration: {}'.format(i)
            assert not candle_set.candles[0].closed

        for _ in range(nb_seconds):
            tick = TickFactory(
                epic=epic,
                datetime=datetime(
                    year=2019, month=1, day=1, hour=0, minute=0, second=i + nb_seconds, tzinfo=tz.gettz('UTC')
                )
            )
            candle_set.on_new_tick(tick)
            assert len(candle_set.candles) == 2
            assert candle_set.candles[0].closed
            assert not candle_set.candles[1].closed

    @pytest.mark.parametrize(
        ['timeframe', 'tick_minute', 'candle_open_minute'],
        [
            pytest.param('1minutes', 0, 0),
            pytest.param('1minutes', 1, 1),
            pytest.param('1minutes', 2, 2),
            pytest.param('1minutes', 3, 3),
            pytest.param('1minutes', 4, 4),
            pytest.param('1minutes', 59, 59),
            pytest.param('2minutes', 0, 0),
            pytest.param('2minutes', 1, 0),
            pytest.param('2minutes', 2, 2),
            pytest.param('2minutes', 3, 2),
            pytest.param('2minutes', 4, 4),
            pytest.param('2minutes', 59, 58),
            pytest.param('5minutes', 0, 0),
            pytest.param('5minutes', 1, 0),
            pytest.param('5minutes', 2, 0),
            pytest.param('5minutes', 3, 0),
            pytest.param('5minutes', 4, 0),
            pytest.param('5minutes', 5, 5),
            pytest.param('5minutes', 59, 55),
        ],
    )
    def test_candles_minute_change(self, timeframe, tick_minute, candle_open_minute):
        candle_set = CandleSetFactory(timeframe=timeframe)
        epic = EpicFactory(candle_sets=[candle_set])

        tick = TickFactory(
            datetime=datetime(
                year=2019, month=1, day=1, hour=0, minute=tick_minute, second=0, tzinfo=tz.gettz('UTC')
            )
        )
        candle_set.on_new_tick(tick)
        assert candle_set.candles[0].open_at.minute == candle_open_minute
        assert candle_set.candles[0].open_at.second == 0

    @pytest.mark.parametrize(
        'nb_minutes',
        [
            pytest.param(2, id='2 minutes'),
            pytest.param(3, id='3 minutes'),
            pytest.param(12, id='12 minutes'),
            pytest.param(20, id='20 minutes'),
        ],
    )
    def test_add_candles_minutes(self, nb_minutes):
        candle_set = CandleSetFactory(timeframe='{}minutes'.format(nb_minutes))
        epic = EpicFactory(candle_sets=[candle_set])

        tick = TickFactory()
        candle_set.on_new_tick(tick)
        for i in range(nb_minutes - 1):
            tick = TickFactory(
                datetime=datetime(year=2019, month=1, day=1, hour=0, minute=i, second=0, tzinfo=tz.gettz('UTC'))
            )
            candle_set.on_new_tick(tick)
            assert len(candle_set.candles) == 1, 'iteration: {}'.format(i)
            assert not candle_set.candles[0].closed

        for _ in range(nb_minutes):
            tick = TickFactory(
                datetime=datetime(
                    year=2019, month=1, day=1, hour=0, minute=i + nb_minutes, second=0, tzinfo=tz.gettz('UTC')
                )
            )
            candle_set.on_new_tick(tick)
            assert len(candle_set.candles) == 2
            assert candle_set.candles[0].closed
            assert not candle_set.candles[1].closed

    @pytest.mark.parametrize(
        ['timeframe', 'tick_hour', 'candle_open_hour'],
        [
            pytest.param('1hours', 0, 0),
            pytest.param('1hours', 1, 1),
            pytest.param('1hours', 2, 2),
            pytest.param('1hours', 3, 3),
            pytest.param('1hours', 4, 4),
            pytest.param('1hours', 11, 11),
            pytest.param('1hours', 23, 23),
            pytest.param('2hours', 0, 0),
            pytest.param('2hours', 1, 0),
            pytest.param('2hours', 2, 2),
            pytest.param('2hours', 3, 2),
            pytest.param('2hours', 4, 4),
            pytest.param('2hours', 23, 22),
            pytest.param('4hours', 0, 0),
            pytest.param('4hours', 2, 0),
            pytest.param('4hours', 3, 0),
            pytest.param('4hours', 4, 4),
            pytest.param('4hours', 5, 4),
            pytest.param('4hours', 23, 20),
        ],
    )
    def test_candles_hour_change(self, timeframe, tick_hour, candle_open_hour):
        candle_set = CandleSetFactory(timeframe=timeframe)
        epic = EpicFactory(candle_sets=[candle_set])

        tick = TickFactory(
            datetime=datetime(
                year=2019, month=1, day=1, hour=tick_hour, minute=0, second=0, tzinfo=tz.gettz('UTC')
            )
        )
        candle_set.on_new_tick(tick)
        assert candle_set.candles[0].open_at.hour == candle_open_hour
        assert candle_set.candles[0].open_at.minute == 0
        assert candle_set.candles[0].open_at.second == 0

    @pytest.mark.parametrize(
        'nb_hours',
        [
            pytest.param(2, id='2 hours'),
            pytest.param(3, id='3 hours'),
            pytest.param(4, id='4 hours'),
            pytest.param(6, id='6 hours'),
        ],
    )
    def test_add_candles_hours(self, nb_hours):
        candle_set = CandleSetFactory(timeframe='{}hours'.format(nb_hours))
        epic = EpicFactory(candle_sets=[candle_set])

        tick = TickFactory()
        candle_set.on_new_tick(tick)
        for i in range(nb_hours - 1):
            tick = TickFactory(
                datetime=datetime(year=2019, month=1, day=1, hour=i, minute=0, second=0, tzinfo=tz.gettz('UTC'))
            )
            candle_set.on_new_tick(tick)
            assert len(candle_set.candles) == 1, 'iteration: {}'.format(i)
            assert not candle_set.candles[0].closed

        for _ in range(nb_hours):
            tick = TickFactory(
                datetime=datetime(
                    year=2019, month=1, day=1, hour=i + nb_hours, minute=0, second=0, tzinfo=tz.gettz('UTC')
                )
            )
            candle_set.on_new_tick(tick)
            assert len(candle_set.candles) == 2
            assert candle_set.candles[0].closed
            assert not candle_set.candles[1].closed

    @pytest.mark.parametrize('nb_days', [pytest.param(1, id='1 days')])
    def test_add_candles_days(self, nb_days):
        candle_set = CandleSetFactory(timeframe='{}days'.format(nb_days))
        epic = EpicFactory(candle_sets=[candle_set])

        tick = TickFactory(
            datetime=datetime(year=2019, month=1, day=2, hour=0, minute=0, second=0, tzinfo=tz.gettz('UTC'))
        )
        candle_set.on_new_tick(tick)
        for i in range(nb_days - 1):
            tick = TickFactory(
                datetime=datetime(
                    year=2019, month=1, day=i + 2, hour=0, minute=0, second=0
                )
            )
            candle_set.on_new_tick(tick)
            assert len(candle_set.candles) == 1, 'iteration: {}'.format(i)
            assert not candle_set.candles[0].closed

        for i in range(nb_days):
            tick = TickFactory(
                datetime=datetime(
                    year=2019, month=1, day=nb_days + i + 2, hour=0, minute=0, second=0, tzinfo=tz.gettz('UTC')
                )
            )
            candle_set.on_new_tick(tick)
            assert len(candle_set.candles) == 2
            assert candle_set.candles[0].closed
            assert not candle_set.candles[1].closed


class TestCandleSetStatus:

    def test_is_new_candle(self):
        for nb_ticks in [1, 3, 21, 50]:
            candle_set = CandleSetFactory(timeframe='{}ticks'.format(nb_ticks))
            EpicFactory(candle_sets=[candle_set])

            for i in range(nb_ticks):
                tick = TickFactory()
                candle_set.on_new_tick(tick)
                if i == 0:
                    assert candle_set.new_candle_opened

            for i in range(nb_ticks):
                tick = TickFactory()
                candle_set.on_new_tick(tick)
                if i == 0:
                    assert candle_set.new_candle_opened

            for i in range(nb_ticks):
                tick = TickFactory()
                candle_set.on_new_tick(tick)
                if i == 0:
                    assert candle_set.new_candle_opened

    def test_is_closing_candle(self):
        for nb_ticks in [1, 3, 21, 50]:
            candle_set = CandleSetFactory(timeframe='{}ticks'.format(nb_ticks))
            EpicFactory(candle_sets=[candle_set])

            for i in range(nb_ticks):
                tick = TickFactory()
                candle_set.on_new_tick(tick)
                if i == (nb_ticks - 1):
                    assert candle_set.is_closing_candle

            for i in range(nb_ticks):
                tick = TickFactory()
                candle_set.on_new_tick(tick)
                if i == (nb_ticks - 1):
                    assert candle_set.is_closing_candle

            for i in range(nb_ticks):
                tick = TickFactory()
                candle_set.on_new_tick(tick)
                if i == (nb_ticks - 1):
                    assert candle_set.is_closing_candle

    @pytest.mark.parametrize('ut', [
        pytest.param('seconds', id='seconds'),
        pytest.param('minutes', id='minutes'),
        pytest.param('hours', id='hours'),
    ])
    def test_is_closing_candle_invalid_ut(self, ut):
        nb_ticks = 1
        candle_set = CandleSetFactory(timeframe='{}{}'.format(nb_ticks, ut))
        EpicFactory(candle_sets=[candle_set])

        for i in range(nb_ticks):
            tick = TickFactory()
            candle_set.on_new_tick(tick)
            if i == (nb_ticks - 1):
                with pytest.raises(CandleSetException):
                    assert candle_set.is_closing_candle

    @pytest.mark.parametrize(
        ['nb', 'ut', 'sub_ut', 'nb_periods'],
        [
            pytest.param(3, 'minutes', 'seconds', 13, id='3 minutes'),
            pytest.param(2, 'hours', 'minutes', 9, id='2 hours'),
        ],
    )
    def test_get_closed_candles(self, nb, ut, sub_ut, nb_periods):
        candle_set = CandleSetFactory(timeframe='{}{}'.format(nb, ut))
        EpicFactory(candle_sets=[candle_set])
        tick_dt_params = {
            'year': 2019,
            'month': 1,
            'day': 1,
            'hour': 1,
            'minute': 1,
            'second': 1,
            'tzinfo': tz.gettz('UTC')
        }

        for period in range(nb_periods):
            for i in range(59):
                tick_datetime = tick_dt_params.copy()
                tick_datetime[ut[:-1]] = period + 1
                tick_datetime[sub_ut[:-1]] = i
                tick = TickFactory(datetime=datetime(**tick_datetime))
                candle_set.on_new_tick(tick)

        assert len(candle_set.closed_candles()) == 4
        assert candle_set.closed_candles() == candle_set.candles[:-1]
        assert candle_set.closed_candles(nb=3) == candle_set.candles[-4:-1]
        with pytest.raises(CandleSetException):
            candle_set.closed_candles(nb=99)


class TestCandleSetMaxCandleInMemory:

    def test_max_candles_in_memory(self):
        candle_set = CandleSetFactory(timeframe='3ticks', max_candles_in_memory=5)
        EpicFactory(candle_sets=[candle_set])

        for _ in range(20):
            tick = TickFactory()
            candle_set.on_new_tick(tick)
            assert len(candle_set.candles) <= 5


class TestCandleSetFlush:

    def test_flush(self):
        candle_set = CandleSetFactory(timeframe='5ticks')
        EpicFactory(candle_sets=[candle_set])

        for _ in range(20):
            tick = TickFactory()
            candle_set.on_new_tick(tick)

        assert len(candle_set.candles) == 4

        # test flush
        candle_set.flush()
        assert not candle_set.candles
