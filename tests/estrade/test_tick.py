import pytz
import pytest
from datetime import datetime
from dateutil import tz

from estrade.exceptions import TickException
from tests.factories import EpicFactory, TickFactory


class TestBidAsk:
    def test_base(self):
        tick = TickFactory(bid=999, ask=1001)

        assert tick.value == 1000
        assert tick.spread == 2

    @pytest.mark.parametrize(
        ['invalid_bid'],
        [
            pytest.param(None, id='None bid'),
            pytest.param('200', id='string bid'),
        ]
    )
    def test_invalid_bid(self, invalid_bid):
        with pytest.raises(TickException):
            TickFactory(bid=invalid_bid)

    @pytest.mark.parametrize(
        ['invalid_ask'],
        [
            pytest.param(None, id='None ask'),
            pytest.param('200', id='string ask'),
        ]
    )
    def test_invalid_ask(self, invalid_ask):
        with pytest.raises(TickException):
            TickFactory(ask=invalid_ask)

    def test_inconsistent_bid_ask(self):
        with pytest.raises(TickException):
            TickFactory(bid=1000, ask=999)


class TestTickDatetime:
    @pytest.mark.parametrize(
        ['invalid_datetime'],
        [
            pytest.param(None, id='None datetime'),
            pytest.param('2020-01-01 12:00:00', id='String datetime'),
            pytest.param(
                datetime(year=2019, month=1, day=1, hour=0, minute=0, second=0),
                id='Un-timezoned datetime'
            )
        ]
    )
    def test_invalid_datetime(self, invalid_datetime):
        # A tick with an empty timezone raises an error
        with pytest.raises(TickException, match='Invalid tick datetime'):
            TickFactory(datetime=invalid_datetime)

    def test_zoned_datetime(self):
        epic = EpicFactory(timezone='Asia/Tokyo')
        tz_NY = pytz.timezone('America/New_York')
        datetime_NY = datetime.now(tz_NY)
        tick = TickFactory(
            epic=epic,
            datetime=datetime_NY
        )
        # datetime is converted to epic timezone
        assert tick.datetime.tzinfo == tz.gettz(epic.timezone)
        # datetime utc is correctly set
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


class TestToJson:
    def test_base(self):
        tick = TickFactory()
        tick_dict = tick.to_json()
        assert tick_dict == {
            'datetime': tick.datetime,
            'bid': tick.bid,
            'ask': tick.ask,
            'spread': tick.spread,
            'value': tick.value,
        }


