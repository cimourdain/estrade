import pytest

from estrade.mixins.candle_set_indicator_mixin import CandleSetIndicatorMixin


class TestAbstractCandleSetIndicator:

    def test_abstract_instanciation(self):
        ainstance = CandleSetIndicatorMixin()

        with pytest.raises(NotImplementedError):
            ainstance.on_new_tick(tick=None)

        with pytest.raises(NotImplementedError):
            ainstance.on_new_candle(new_candle=None)

        with pytest.raises(NotImplementedError):
            ainstance.on_candle_close(closed_candle=None)