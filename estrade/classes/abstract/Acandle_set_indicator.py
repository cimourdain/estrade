import logging

logger = logging.getLogger(__name__)


class AbstractCandleSetIndicator:

    def __init__(self, name=None):
        self.candle_set = None
        self.name = name

    def on_new_tick(self, tick):
        raise NotImplementedError()

    def on_new_candle(self, new_candle):
        raise NotImplementedError()

    def on_candle_close(self, closed_candle):
        raise NotImplementedError()
