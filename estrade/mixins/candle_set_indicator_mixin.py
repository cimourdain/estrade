import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CandleSetIndicatorMixin:
    def __init__(self, name: str) -> None:
        self.candle_set: Optional['CandleSet'] = None
        self.name = name

    def on_new_tick(self, tick):
        raise NotImplementedError()

    def on_new_candle(self, new_candle):
        raise NotImplementedError()

    def on_candle_close(self, closed_candle):
        raise NotImplementedError()
