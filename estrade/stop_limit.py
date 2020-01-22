from estrade.mixins.stop_limit_mixin import StopLimitMixin
from estrade.exceptions import StopLimitException


class StopLimitMixinAbsolute(StopLimitMixin):
    """
    Class used to manage absolute stop and limits for <estrade.trade.Trade> classes
    """

    ##################################################
    # DIRECTION
    ##################################################
    @property
    def direction(self):
        """
        Not used for absolute stop/limit
        :return: None
        """
        return None

    @property
    def is_absolute(self):
        """
        Check if stop/limit is absolute
        :return: <bool>
        """
        return True

    ##################################################
    # VALUES
    ##################################################
    @property
    def absolute_value(self):
        """
        In an absolute stop/limit the absolute value is the value provided on init
        :return: <int>
        """
        return self._value

    @property
    def relative_value(self):
        """
        calculate relative stop/limit value from trade open and value
        :return:
        """
        if self._value:
            return abs(self.trade.open - self._value)
        return None

    def _check_value_consistency(self, value):
        """
        Check that the value provided is coherent with the trade open and direction
        :param value: <int/float>
        :return:
        """
        if self.trade.direction > 0 and (
            (self.type_ == 'STOP' and value >= self.trade.open)
            or (self.type_ == 'LIMIT' and value <= self.trade.open)
        ):
            raise StopLimitException(
                f'Impossible to set a {self.type_.upper()} ({value}) '
                f'{"higher" if self.type_ == "STOP" else "lower"} than open tick on a '
                f'{"BUY" if self.trade.direction > 0 else "SELL"} opened '
                f'@ {self.trade.open}'
            )
        elif self.trade.direction < 0 and (
            (self.type_ == 'STOP' and value <= self.trade.open)
            or (self.type_ == 'LIMIT' and value >= self.trade.open)
        ):
            raise StopLimitException(
                f'Impossible to set a {self.type_.upper()} ({value}) '
                f'{"higher" if self.type_ == "LIMIT" else "lower"} than open tick on a '
                f'{"BUY" if self.trade.direction > 0 else "SELL"} opened '
                f'@{self.trade.open}'
            )
        return True


class StopLimitMixinRelative(StopLimitMixin):
    """
    This class handles relative stop/limit for trades.
    """

    ##################################################
    # DIRECTION
    ##################################################
    @property
    def direction(self):
        """
        return stop/limit direction
        direction define if stop/limit is above (direction=1) or under (direction=-1)
        the trade open.
        :return: <int> in [-1, 1] or None
        """
        if (self.type_ == 'STOP' and self.trade.direction >= 1) or (
            self.type_ == 'LIMIT' and self.trade.direction <= -1
        ):
            return -1
        elif (self.type_ == 'LIMIT' and self.trade.direction >= 1) or (
            self.type_ == 'STOP' and self.trade.direction <= -1
        ):
            return 1
        return None

    @property
    def is_relative(self):
        """
        Check if stop/limit is relative
        :return: <bool>
        """
        return True

    ##################################################
    # VALUES
    ##################################################
    @property
    def relative_value(self):
        """
        In a relative stop/limit, the relative value is the value provided on init.
        :return: <int> or <float>
        """
        return self._value

    @property
    def absolute_value(self):
        """
        In a relative stop/limit, calculate the absolute value with trade open
        and direction
        :return: <int> or <float>
        """
        if self._value:
            return self.trade.open + (self.direction * self._value)

        return None

    def _check_value_consistency(self, value):
        """
        Override this method that is not applicable for relative.
        :param value: <int> or <float>
        :return:
        """
        pass
