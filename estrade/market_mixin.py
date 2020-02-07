"""This file define mixins classes used as parent of other classes to define recurrent attributes get/set.
Eg. market, ref
"""

import logging

from estrade.mixins import get_exception

logger = logging.getLogger(__name__)


class MarketMixin:
    """
    Abstract class to use as parent of classes having a market attribute
    """
    def __init__(self, market):
        self.market = market

    def _pre_set_market(self, market):
        """
        Method called before setting market as attribute
        :param market: <estrade.market.Market>
        :return: <bool>
        """
        return True

    def _post_set_market(self):
        """
        Method called after setting market as attribute
        :return: <bool>
        """
        return True

    @property
    def market(self):
        return self._market

    @market.setter
    def market(self, market):
        """
        Method to set market on class
        :param market: <estrade.market.Market>
        :return:
        """

        # do not set market if result of _pre_set_market is False
        if not self._pre_set_market(market):
            return

        logger.debug('Set market on %s instance' % self.__class__.__name__)

        # check that market is instance of estrade.market.Market
        # import Market here to prevent import loop
        from estrade.market import Market
        if not market or not isinstance(market, Market):
            raise get_exception(self)('impossible to add market to {}'.format(self.__class__.__name__))

        # set market
        self._market = market

        self._post_set_market()


class MarketOptionalMixin(MarketMixin):
    """
    Abstract class to set as parent of classes where market is optional
    """
    def _pre_set_market(self, market):
        """
        Allow to set market as None
        :param market: None or <estrade.market.Market>
        :return: <bool>
        """
        if market is None:
            self._market = market
            return False
        return True


class MarketMandatoryMixin(MarketMixin):
    """
    Abstract class to use as parent of classes where market is mandatory
    """
    pass
