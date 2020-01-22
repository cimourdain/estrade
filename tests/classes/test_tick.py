import pytz
import pytest
from datetime import datetime
from dateutil import tz

from estrade.exceptions import TickException
from tests.factories import EpicFactory, TickFactory


class TestTick:
    def test_base(self):
        tick = TickFactory(bid=999, ask=1001)

        assert tick.value == 1000
        assert tick.spread == 2


class TestTickDatetime:

    def test_invalid_datetime(self):
        # A tick with an empty timezone raises an error
        with pytest.raises(TickException, match='Invalid tick datetime'):
            TickFactory(datetime=None)

    def test_utc(self):
        epic = EpicFactory()
        tick = TickFactory(epic=epic)
        assert tick.datetime.tzinfo == tz.tzutc()

    def test_unzoned_tick_datetime(self):
        # a tick with a non timezoned datetime uses the epic timezone as fallback
        epic = EpicFactory(timezone='Asia/Tokyo')
        naive_dt = datetime(year=2019, month=1, day=1, hour=0, minute=0, second=0)
        with pytest.raises(TickException, match='Tick datetime .*'):
            TickFactory(
                epic=epic,
                datetime=naive_dt,
            )

    def test_zoned_datetime(self):
        epic = EpicFactory(timezone='Asia/Tokyo')
        tz_NY = pytz.timezone('America/New_York')
        datetime_NY = datetime.now(tz_NY)
        tick = TickFactory(
            epic=epic,
            datetime=datetime_NY
        )
        assert tick.datetime.tzinfo == tz.gettz(epic.timezone)
        assert tick.datetime_utc.tzinfo == tz.tzutc()



class TestEpic:

    @pytest.mark.parametrize('invalid_epic', [
        pytest.param([], id='Empty array Epic'),
        pytest.param({}, id='Empty dict Epic'),
        pytest.param([1, 'string'], id='Array Epic'),
        pytest.param({'toto': 1}, id='Dict Epic'),
    ])
    def test_invalid_epic(self, invalid_epic):
        with pytest.raises(TickException, match='Invalid tick epic'):
            TickFactory(epic=invalid_epic)

