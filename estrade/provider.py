import logging
from datetime import datetime, timedelta

from estrade.exceptions import ProviderException
from estrade.market_mixin import MarketOptionalMixin
from estrade.mixins.trade_class_mixin import TradeClassMixin

logger = logging.getLogger(__name__)


class Provider(MarketOptionalMixin, TradeClassMixin):
    """
    A provider defines how to fetch data to run your strategies.

    This class is recommended for your backtests.

    Inherit from this class to fill your ticks to the :class:`estrade.Market`

    .. note::
        If your provider is a 'live provider' (ie. must login to a service, call api to open/close trades etc.)
        you should use the :class:`estrade.LiveProvider` as a parent of your provider.

    :param Estrade.trade.Trade trade_class: trade class used to open/close trades
    :param datetime.datetime start_date: optional start date
    :param datetime.datetime end_date: optional end date
    """

    def __init__(self, trade_class=None, start_date=None, end_date=None):
        # init a market property to None
        MarketOptionalMixin.__init__(self, None)
        TradeClassMixin.__init__(self, trade_class=trade_class)

        self.start_date = start_date
        self.end_date = end_date

        # the default provider is automatically logged
        self.logged = True

    @property
    def start_date(self):
        return self._start_date

    @start_date.setter
    def start_date(self, start_date):
        self._start_date = None
        if isinstance(start_date, str):
            try:
                self._start_date = datetime.strptime(start_date, '%Y-%m-%d')
            except:
                raise ProviderException('Invalid start date format')

        if isinstance(start_date, datetime):
            self._start_date = start_date

    @property
    def end_date(self):
        return self._end_date

    @end_date.setter
    def end_date(self, end_date):
        self._end_date = None
        if isinstance(end_date, str):
            try:
                self._end_date = datetime.strptime(end_date, '%Y-%m-%d')
            except:
                raise ProviderException('Invalid start date format')

        if isinstance(end_date, datetime):
            self._end_date = end_date

    @property
    def backtest_dates_generator(self):
        if not self.start_date or not self.end_date:
            raise ProviderException('Cannot use backtest_dates_generator when either start_date or end_date is not defined')
        for n in range(int((self.end_date - self.start_date).days + 1)):
            trading_date = self.start_date + timedelta(n)
            yield trading_date.date()

    ##################################################
    # EVENTS
    ##################################################
    def generate(self):
        """
        This method must be implemented to fetch ticks or candles from provider.

        If your provider generates ticks, this method must send the tick
        to market calling :func:`estrade.market.Market.on_new_tick` method.

        eg::

            from estrade import Provider
            from estrade import Tick

            class MyProvider(Provider):

                def generate(self):
                    '''
                        This method parse all ticks from your database.
                        It assumes that your ticks holds the following attributes:
                        - epic code
                        - bid
                        - ask
                        - datetime
                    '''
                    # eg. query ticks in your database (ordered by datetime)
                    for tick in my_database:
                        # build a tick from your data
                        tick = Tick(
                            epic=self.market.get_epic(tick['epic_code']),
                            bid=tick['bid'],
                            ask=tick['ask'],
                            datetime['datetime'],
                        )
                    # dispatch tick to market
                    self.market.on_new_tick(tick)

        """
        pass

    def get_open_trades(self):
        """
        Implement this method to fetch list of open trades from your provider.
        :return: [<estrade.trade.Trade>,]
        """
        return []


class LiveProvider(Provider, MarketOptionalMixin):
    """
    A LiveProvider is a Provider with a template for :
        - login
        - fetch/open/close trade methods

    Use this class as a parent for API providers.
    """
    def __init__(self, *args, **kwargs):
        Provider.__init__(self, *args, **kwargs)
        self.logged = False

    def subscribe(self):
        if self.market:
            self.market.subscribe('market_before_run', self.login)

    ##################################################
    # MARKET
    ##################################################
    def _post_set_market(self):
        """
        After set of market, subscribe provider to market and trade manager events
        :return:
        """
        self.subscribe()

    ##################################################
    # LOGIN/LOGOUT
    ##################################################
    def login(self):
        """
        This method must perform login process with your provider.

        This method is called by `market_before_run` event.

        If login is successful, the instance `logged` attribute must be set to True.
        :return:
        """
        pass

    ##################################################
    # EPIC
    ##################################################
    def update_epic_status(self, epic, tradeable_status):
        """
        TODO: call this method from
        :param epic_ref: <str>
        :param tradeable_status: <bool>
        :return:
        """
        epic.tradeable = tradeable_status
