class EstradeException(Exception):
    message_prefix = ""

    def __init__(self, message, *args, **kwargs):
        message = f"Estrade::{self.message_prefix}::{message}"
        Exception.__init__(self, message, *args, **kwargs)


class BaseIndicatorException(EstradeException):
    message_prefix = "BaseIndicator"


class EpicException(EstradeException):
    message_prefix = "Epic"


class TickException(EstradeException):
    message_prefix = "Tick"


class TradeManagerException(EstradeException):
    message_prefix = "TradeManager"


class TradeException(EstradeException):
    message_prefix = "Trade"


class TimeException(EstradeException):
    message_prefix = "TimedObject"


class TradeProviderException(EstradeException):
    message_prefix = "TradeProvider"


class FrameSetException(EstradeException):
    message_prefix = "FrameSet"


class TimeFrameException(EstradeException):
    message_prefix = "TimeFrame"
