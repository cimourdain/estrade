from datetime import datetime, timezone

import arrow
import pytest
from freezegun import freeze_time

from estrade.exceptions import TickException, TimeException
from tests.unit.factories import TickFactory


CLASS_DEFINITION_PATH = "estrade.tick.Tick"


class TestBidAsk:
    def test_base(self):
        tick = TickFactory(bid=999, ask=1001)

        assert tick.value == 1000
        assert tick.spread == 2

    @pytest.mark.parametrize(
        ["invalid_bid"],
        [pytest.param(None, id="None bid"), pytest.param("200", id="string bid")],
    )
    def test_invalid_bid(self, invalid_bid):
        with pytest.raises(TickException):
            TickFactory(bid=invalid_bid)

    @pytest.mark.parametrize(
        ["invalid_ask"],
        [pytest.param(None, id="None ask"), pytest.param("200", id="string ask")],
    )
    def test_invalid_ask(self, invalid_ask):
        with pytest.raises(TickException):
            TickFactory(ask=invalid_ask)

    def test_inconsistent_bid_ask(self):
        with pytest.raises(TickException):
            TickFactory(bid=1000, ask=999)


class TestTickDatetime:
    def test_datetime_as_datetime(self):
        utcnow = datetime.utcnow().replace(tzinfo=timezone.utc)
        tick = TickFactory(datetime=utcnow)
        assert tick.datetime == utcnow

    def test_datetime_as_arrow(self):
        utcnow = arrow.utcnow()
        tick = TickFactory(datetime=utcnow)
        assert tick.datetime == utcnow

    @pytest.mark.parametrize(
        ["invalid_datetime"],
        [
            pytest.param(None, id="None datetime"),
            pytest.param("2020-01-01 12:00:00", id="String datetime"),
            pytest.param(
                datetime(year=2019, month=1, day=1, hour=0, minute=0, second=0),
                id="Un-timezoned datetime",
            ),
        ],
    )
    def test_invalid_datetime(self, invalid_datetime):
        # A tick with an empty timezone raises an error
        with pytest.raises(TimeException, match="timezoned datetime is required."):
            TickFactory(datetime=invalid_datetime)

    def test_get_datetime_utc(self):
        utcnow = arrow.utcnow()
        tick = TickFactory(datetime=utcnow.to("US/Pacific"))

        assert tick.datetime_utc == utcnow


class TestMeta:
    def test_set_meta(self):
        tick = TickFactory(meta={"test": "test"})
        assert tick.meta == {"test": "test"}

    def test_default(self):
        tick = TickFactory()
        assert tick.meta == {}


def test_convert_to_dict():
    tick = TickFactory()
    tick_dict = tick.asdict()
    assert tick_dict == {
        "datetime": tick.datetime,
        "bid": tick.bid,
        "ask": tick.ask,
        "spread": tick.spread,
        "value": tick.value,
    }


@freeze_time("2019-01-01 00:00:00")
def test_convert_to_string():
    tick = TickFactory()
    assert (
        str(tick) == "2019-01-01 00:00:00 : 1000.0 "
        "(bid: 999.0, ask: 1001.0, spread: 2.0)"
    )
