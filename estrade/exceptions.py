class EstradeException(Exception):
    message_prefix = ''

    def __init__(self, message, *args, **kwargs):
        message = f'Estrade::{self.message_prefix}::{message}'
        super().__init__(message, *args, **kwargs)


class MarketException(EstradeException):
    message_prefix = 'Market'


class EpicException(EstradeException):
    message_prefix = 'Epic'


class CandleSetException(EstradeException):
    message_prefix = 'CandleSet'


class CandleException(EstradeException):
    message_prefix = 'Candle'


class ProviderException(EstradeException):
    message_prefix = 'Provider'


class ReportingException(EstradeException):
    message_prefix = 'Reporting'


class StopLimitException(EstradeException):
    message_prefix = 'StopLimit'


class StrategyException(EstradeException):
    message_prefix = 'Strategy'


class TickException(EstradeException):
    message_prefix = 'Tick'


class TradeManagerException(EstradeException):
    message_prefix = 'TradeManager'


class TradeException(EstradeException):
    message_prefix = 'Trade'
