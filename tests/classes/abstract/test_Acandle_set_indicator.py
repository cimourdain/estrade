import pytest

from estrade.abstract.Acandle_set_indicator import AbstractCandleSetIndicator


class TestAbstractCandleSetIndicator:

    def test_abstract_instanciation(self):
        ainstance = AbstractCandleSetIndicator()

        with pytest.raises(NotImplementedError):
            ainstance.on_new_tick(tick=None)

        with pytest.raises(NotImplementedError):
            ainstance.on_new_candle(new_candle=None)

        with pytest.raises(NotImplementedError):
            ainstance.on_candle_close(closed_candle=None)