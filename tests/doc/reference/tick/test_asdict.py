import arrow
from freezegun import freeze_time

from estrade import Tick


@freeze_time("2020-01-02 15:30:12")
def test_asdict():
    now = arrow.utcnow()
    tick = Tick(
        now,
        bid=49,
        ask=50,
    )

    assert tick.asdict() == {
        "ask": 50.0,
        "bid": 49.0,
        "datetime": now,
        "spread": 1.0,
        "value": 49.5,
    }

    assert tick.asdict(datetime_to_str=True) == {
        "ask": 50.0,
        "bid": 49.0,
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "spread": 1.0,
        "value": 49.5,
    }
