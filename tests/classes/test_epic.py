import pytest
from datetime import datetime, timezone
from dateutil import tz

from tests.factories import (
    CandleSetFactory,
    EpicFactory,
    MarketFactory,
    TickFactory
)
from estrade.classes.exceptions import EpicException


class TestEpic:

    def test_base(self):
        epic = EpicFactory(ref='epic_ref', timezone='Europe/Berlin')

        assert epic.ref == 'epic_ref'
        assert epic.timezone == 'Europe/Berlin'
        assert epic.tradeable


class TestEpicTimezone:

    def test_invalid_timezone(self):
        with pytest.raises(EpicException, match=r".*Invalid"):
            EpicFactory(ref='epic_ref', timezone='Invalid')


class TestEpicCandleSet:

    def test_empty_candle_set(self):
        epic = EpicFactory(candle_sets=None)
        assert not epic.candle_sets

    @pytest.mark.parametrize(
        'candle_sets',
        [
            pytest.param('string', id='string candle_set'),
            pytest.param(2, id='int candle_set'),
            pytest.param([CandleSetFactory(), 1], id='mixed list elements')
        ],
    )
    def test_invalid_candle_sets(self, candle_sets):
        with pytest.raises(EpicException, match=r'.*Invalid candleSet.*'):
            EpicFactory(candle_sets=candle_sets)


class TestEpicMarket:

    def test_base(self):
        market = MarketFactory()
        epic = EpicFactory()
        epic.market = market
        assert epic.market == market

    @pytest.mark.parametrize('invalid_market', [
        pytest.param('string', id='str market'),
        pytest.param(1, id='int market'),
        pytest.param([], id='list market'),
        pytest.param({}, id='dict market'),
    ])
    def test_invalid_market(self, invalid_market):
        epic = EpicFactory()
        with pytest.raises(EpicException):
            epic.market = invalid_market

