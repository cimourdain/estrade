import logging

from estrade.classes.abstract.Amarket_class import AMarketOptionalClass
from estrade.classes.abstract.Atrade_class import ATradeClassUser
from estrade.classes.exceptions import AProviderException
from estrade.classes.tick import Tick

logger = logging.getLogger(__name__)


class AProvider(AMarketOptionalClass, ATradeClassUser):
    """
    A provider define :
        - (optionnaly) login to an external provider
        - tick generation
        - (optionally) open/close trades management

    Use this Class as parent when you define a 'local' provider (ticks from a database)
    """
    def __init__(self, trade_class=None):
        """
        Init a new Provider
        """
        # init a market property to None
        AMarketOptionalClass.__init__(self, None)
        ATradeClassUser.__init__(self, trade_class=trade_class)

        # the default provider is automatically logged
        self.logged = True

    ##################################################
    # EVENTS
    ##################################################
    def on_new_tick(self, epic_ref, bid, ask, datetime):
        """
        Function called by `generate_tick` method for every new tick received. This method:
            - convert parameters to <estrade.classes.tick.Tick>
            - send tick to market
        :param epic_ref: <str>
        :param bid: <float>
        :param ask: <float>
        :param datetime: <datetime.datetime>
        :return:
        """
        if not self.market:
            raise AProviderException('Cannot handle new tick if provider has no market')

        # convert tick data to estrade.classes.tick.Tick object
        tick = Tick(
            epic=self.market.get_epic(epic_ref),
            bid=bid,
            ask=ask,
            datetime=datetime
        )

        self.market.on_new_tick(tick)

    def generate_ticks(self):
        """
        This method must be implemented to fetch ticks from provider and call self.on_new_tick for every tick.
        :return
        """
        raise NotImplementedError('Implement this method to generate ticks.')

    def get_open_trades(self):
        """
        Implement this method to fetch list of open trades from your provider.
        :return: [<estrade.classes.trade.Trade>,]
        """
        return []


class ALiveProvider(AProvider, AMarketOptionalClass):
    """
    A LiveProvider is a Provider with a template for :
        - login
        - fetch/open/close trade methods

    Use this class as a parent for API providers.
    """
    def __init__(self, *args, **kwargs):
        AProvider.__init__(self, *args, **kwargs)
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
        raise NotImplementedError('Login method must be implemented in a LiveProvider')

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
