import logging

from estrade.exceptions import StopLimitException

logger = logging.getLogger(__name__)


class StopLimitMixin:
    def __init__(self, type_, trade, value):
        """
        Init new stop/limit
        :param type_: <str> in ['STOP', 'LIMIT']
        :param trade: <estrade.trade.Trade> instance
        :param value: <int>
        """
        self.type_ = type_
        self.trade = trade
        self.value = value
        logger.debug('Init new stop/limit: %s' % self.__repr__())

    ##################################################
    # TRADE
    ##################################################
    @property
    def trade(self):
        """
        return trade
        :return: <estrade.trade.Trade> instance
        """
        return self._trade

    @trade.setter
    def trade(self, trade):
        """
        Set trade
        :param trade: <estrade.trade.Trade> instance
        :return:
        """
        from estrade.trade import Trade

        if not isinstance(trade, Trade):
            raise StopLimitException('Invalid Trade on Stop/Limit')
        self._trade = trade

    ##################################################
    # TYPE
    ##################################################
    @property
    def type_(self):
        """
        return stop/limit type
        :return:<str>
        """
        return self._type_

    @type_.setter
    def type_(self, type_):
        """
        Set stop/limit type
        :param type_: <str> in ['STOP', 'LIMIT']
        :return:
        """
        if not isinstance(type_, str) or type_.upper() not in ['STOP', 'LIMIT']:
            raise StopLimitException(f'Invalid type {type_}')
        self._type_ = type_.upper()

    ##################################################
    # VALUES
    ##################################################
    @property
    def value(self):
        """
        return absolute value of stop/limit (value provided on init)
        :return: <int>
        """
        raise StopLimitException(
            'Cannot call value for stop/limit, call absolute_value '
            'or relative_value explicitly.'
        )

    @value.setter
    def value(self, value):
        """
        Check value type is int/float and check consistency
        :param value: <int> or <float>
        :return:
        """

        if type(value) not in [int, float]:
            raise StopLimitException('Stop/limit cannot be a non-numeric value')

        if value <= 0:
            raise StopLimitException('Stop/limit cannot be negative')

        self._check_value_consistency(value)
        self._value = value

        logger.debug(repr(self))
        # TODO: update relative value on trade open update

    @property
    def absolute_value(self):
        """
        This method returns absolute value of stop/limit.
        :return: <int> or <float>
        """
        raise NotImplementedError()

    @property
    def relative_value(self):
        """
        This method returns absolute value of stop/limit.
        :return: <int> or <float>
        """
        raise NotImplementedError()

    def _check_value_consistency(self, value):
        """
        This method must be implemented to check that the provided stop/limit value is
        consistent with trade open.
        :param value: <int> or <float>
        :return:
        """
        raise NotImplementedError()

    ##################################################
    # DIRECTION
    ##################################################
    @property
    def direction(self):
        """
        Depending of stop/limit type, the direction usage must be implemented
        :return:
        """
        raise NotImplementedError()

    @property
    def is_relative(self):
        """
        Check if stop/limit is relative
        :return: <bool>
        """
        return False

    @property
    def is_absolute(self):
        """
        Check if stop/limit is absolute
        :return: <bool>
        """
        return False

    ##################################################
    # CHECK
    ##################################################
    def check(self, tick):
        """
        Check stop/limit value against a tick:
            - returns True if stop/limit reached
            - returns False if stop/limit not reached
        :param tick: <estrade.tick.Tick> instance
        :return: <bool>
        """
        if self.type_ == 'STOP':
            if self.trade.direction > 0 and tick.bid <= self.absolute_value:
                logger.debug(
                    'close BUY because tick %f  <= Stop absolute value %f'
                    % (tick.bid, self.absolute_value)
                )
                return True
            elif self.trade.direction < 0 and tick.ask >= self.absolute_value:
                logger.debug(
                    'close SELL because tick %f >= Stop absolute value %f'
                    % (tick.ask, self.absolute_value)
                )
                return True
        elif self.type_ == 'LIMIT':
            if self.trade.direction > 0 and tick.bid >= self.absolute_value:
                logger.debug(
                    'close BUY because tick %f >= limit absolute value %f'
                    % (tick.bid, self.absolute_value)
                )
                return True
            elif self.trade.direction < 0 and tick.ask <= self.absolute_value:
                logger.debug(
                    'close SELL because tick %f <= limit absolute value %f'
                    % (tick.ask, self.absolute_value)
                )
                return True
        else:
            logger.debug('Stop/Limit not reached.')

        return False

    def __repr__(self):
        """
        Representation of a stop/limit
        :return: <dict>
        """
        repr = f'{self.type_} : direction: {self.direction} of'
        if self.is_absolute:
            return f'absolute {repr} {self.absolute_value}'
        elif self.is_relative:
            return f'relative {repr} {self.relative_value}'
        else:
            return 'undefined stop/limit'
