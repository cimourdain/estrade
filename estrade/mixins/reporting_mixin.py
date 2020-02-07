import logging

from estrade.market_mixin import MarketOptionalMixin
from estrade.exceptions import ReportingException


logger = logging.getLogger(__name__)


class ReportingMixin(MarketOptionalMixin):
    """
    Define Reporting Abstract class.
    A reporting class is able to generate reporting:
        - on new tick
        - on trade update (open/update/close)
        - on epic update
        - when all ticks are generated
    """
    def __init__(self, log_level=None):
        MarketOptionalMixin.__init__(self, market=None)

    def _post_set_market(self):
        """
        When market is attached to reporting, subscribe reporting to events
        :return:
        """
        self.subscribe()

    def subscribe(self):
        """
        subscribe Reporting class to events depending if methods were implemented.
        :return:
        """
        if not self.market:
            raise ReportingException('cannot subscribe Reporting when no market set')

        if self.on_new_tick != ReportingMixin.on_new_tick:
            logger.info('subscribe Reporting %s to on_new_tick events' % self.__class__.__name__)
            for epic in self.market.epics:
                self.market.subscribe('market_after_on_new_tick_{}'.format(epic.ref), self.on_new_tick)

        if self.on_trade_update != ReportingMixin.on_trade_update:
            # TODO: implement events in trade_manager
            logger.info('subscribe Reporting %s to on_trade_update events' % self.__class__.__name__)
            self.market.trade_manager.subscribe('trade_update', self.on_trade_update)

        if self.on_run_end != ReportingMixin.on_run_end:
            logger.info('subscribe Reporting %s to on_new_tick events' % self.__class__.__name__)
            self.market.trade_manager.subscribe('market_run_end', self.on_run_end)

    def on_new_tick(self, tick):
        """
        Method called when a new tick is received by market
        :param tick: <estrade.tick.Tick>
        :return:
        """
        raise NotImplementedError('To report on every tick, please implement your Reporting ')

    def on_trade_update(self, trade):
        """
        Method called when a trade is created/updated/closed
        # TODO: implement events in trade_manager
        :param trade: <estrade.trade.Trade>
        :return:
        """
        raise NotImplementedError('To report on every epic update, please implement your Reporting ')

    def on_run_end(self):
        """
        Method called when Market run ends.
        :return:
        """
        raise NotImplementedError('To report on every epic update, please implement your Reporting ')
