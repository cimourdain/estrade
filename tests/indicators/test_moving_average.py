from datetime import datetime

import arrow

from tests.factories import (
    CandleSetFactory,
    EpicFactory,
    ExponentialMovingAverageFactory,
    MarketFactory,
    SimpleMovingAverageFactory,
    StrategyFactory,
)


class TestSimpleMovingAverage:

    def test_base(self):
        # GIVEN a market with a simple moving average
        sma3 = SimpleMovingAverageFactory(name='sma3', periods=3)
        candle_set = CandleSetFactory(indicators=[sma3])
        epic = EpicFactory(candle_sets=[candle_set])
        strategy = StrategyFactory(epics=[epic])
        market = MarketFactory(strategies=[strategy])

        loops = [
            {'price': 1000, 'minute': '00', 'expected_sma': None},
            {'price': 1010, 'minute': '01', 'expected_sma': None},
            {'price': 1020, 'minute': '02', 'expected_sma': round((1000 + 1010 + 1020) / 3, 2)},
            {'price': 1030, 'minute': '03', 'expected_sma': round((1010 + 1020 + 1030) / 3, 2)},
            {'price': 950, 'minute': '03', 'expected_sma': round((1010 + 1020 + 950) / 3, 2)},
        ]
        for l in loops:
            # WHEN i add a tick @1000, then no sma is calculated (not enough periods)
            market.provider.generate_ticks(ticks_dicts=[{
                'epic_ref': epic.ref,
                'bid': l['price'] - 1,
                'ask': l['price'] + 1,
                'datetime': arrow.get('2019-01-01 00:{}:00'.format(l['minute']), 'YYYY-MM-DD HH:mm:ss').to('UTC')
            }])
            assert market.epics[0].candle_sets[0].indicator('sma3').value == l['expected_sma'], l


class TestExponentialMovingAverage:

    def test_base(self):
        # GIVEN a market with a simple moving average
        sma3 = ExponentialMovingAverageFactory(name='ema3', periods=3)
        candle_set = CandleSetFactory(indicators=[sma3])
        epic = EpicFactory(candle_sets=[candle_set])
        strategy = StrategyFactory(epics=[epic])
        market = MarketFactory(strategies=[strategy])

        shooting_constant = 2 / (3 + 1)
        loops = [
            {'price': 1000, 'expected_sma': None, 'expected_ema': None},
            {'price': 1005, 'expected_sma': None, 'expected_ema': None},
            {
                'price': 1010,
                'expected_sma': round((1000 + 1005 + 1010) / 3, 2),
                'expected_ema': None
            },
            {
                'price': 1020,
                'expected_sma': round((1005 + 1010 + 1020) / 3, 2),
                'expected_ema': round(
                    shooting_constant * (1020 - ((1000 + 1005 + 1010) / 3))
                    + ((1000 + 1005 + 1010) / 3)
                    , 2
                )
            },
            {
                'price': 995,
                'expected_sma': round((1010 + 1020 + 995) / 3, 2),
                'expected_ema': round(
                    shooting_constant * (995 - ((1005 + 1010 + 1020) / 3))
                    + ((1005 + 1010 + 1020) / 3)
                    , 2
                )
            },
        ]

        loop_nb = 0
        for l in loops:
            market.provider.generate_ticks(ticks_dicts=[
                {
                    'epic_ref': epic.ref,
                    'bid': l['price'] - 1,
                    'ask': l['price'] + 1,
                    'datetime': arrow.get('2019-01-01 00:{0:0=2d}:00'.format(loop_nb), 'YYYY-MM-DD HH:mm:ss').to('UTC')
                }
            ])
            assert len(market.epics[0].candle_sets[0].candles) == loop_nb + 1, l
            assert market.epics[0].candle_sets[0].indicator('ema3').sma == l['expected_sma'], l
            assert market.epics[0].candle_sets[0].indicator('ema3').value == l['expected_ema'], l
            loop_nb += 1
