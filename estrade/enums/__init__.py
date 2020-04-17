from enum import Enum


class TradeDirection(Enum):
    """
    Direction (buy or sell) of a Trade.

    Allowed valued are:

     - `BUY`
     - `SELL`
    """

    BUY = 1
    SELL = -1


class TransactionStatus(Enum):
    """
    Status of a transaction.

    Allowed valued are:

     - `CREATED`: trade was created
     - `REQUIRED`: trade was required to provider
     - `PENDING`: trade was required to provider and waiting for answer
     - `CONFIRMED`: trade was confirmed by provider
     - `CLOSED`: trade was closed by provider
     - `REFUSED`: trade was refused by provider
    """

    CREATED = 0
    REQUIRED = 1
    PENDING = 2
    CONFIRMED = 3
    CLOSED = 4
    REFUSED = 5


class Unit(Enum):
    """
    Available units for a CandleSet.

    Possible values are:

     - `TICK`
     - `SECOND`
     - `MINUTE`
     - `HOUR`
     - `DAY`
     - `WEEK`
     - `MONTH`
     - `YEAR`

    """

    TICK = 0
    SECOND = 1
    MINUTE = 2
    HOUR = 3
    DAY = 4
    WEEK = 5
    MONTH = 6
    YEAR = 7


class CandleType(Enum):
    """
    Available type of Candles for a Candle Set.

    Possible values are:

     - `CLASSIC`
     - `HEIKIN_ASHI`
    """

    CLASSIC = 0
    HEIKIN_ASHI = 1


class CandleColor(Enum):
    """
    Available colors of a Candle.

    Possible values are:

     - `GREEN` last is superior to open
     - `RED` last is inferior to open
     - `BLACK` last is equal to open
    """

    GREEN = 1
    BLACK = 0
    RED = -1


class PivotType(Enum):
    """
    Available pivot types.

    Possible values are:

     - `CLASSIC`: P = (H + L + C) / 3.
     - `OLHC` : P = (O + H + L + C) / 4.

    P: Pivot
    H: high
    L: low
    C: close
    O: current period open.
    """

    CLASSIC = 0
    OLHC = 1
