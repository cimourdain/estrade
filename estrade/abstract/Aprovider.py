import logging

from estrade.exceptions import AProviderException
from estrade.market_mixin import MarketOptionalMixin
from estrade.abstract.Atrade_class import ATradeClassUser
from estrade.candle import Candle
from estrade.tick import Tick

logger = logging.getLogger(__name__)


class AProvider(MarketOptionalMixin, ATradeClassUser):
    """
    A provider defines how to fetch data to run your strategies.

    Use this class as a parent of your provider when your provider only have to fetch ticks.
    This is recommended for backtests.

    If your provider is a 'live provider', ie. must login to a service, call api to open/close trades etc.
    you should use the :class:`estrade.ALiveProvider` as a parent of your provider.
    """
    def __init__(self, trade_class=None):
        """
        Init a new provider
        :param: trade_class: instance of :class:`estrade.abstract.ATrade_class.ATradeClassUser`

        """
        # init a market property to None
        MarketOptionalMixin.__init__(self, None)
        ATradeClassUser.__init__(self, trade_class=trade_class)

        # the default provider is automatically logged
        self.logged = True

    def build_tick(self, epic_ref, datetime, bid, ask, **kwargs):
        if not self.market:
            raise AProviderException('Cannot build tick when provider has no market')

        return Tick(
            epic=self.market.get_epic(epic_ref),
            datetime=datetime,
            bid=bid,
            ask=ask,
            meta=kwargs
        )

    def build_candle(self, timeframe, open_tick, close_tick, high_tick=None, low_tick=None):
        candle = Candle(
            timeframe=timeframe,
            epic_ref=open_tick.epic.ref,
            open_tick=open_tick
        )
        if high_tick:
            candle.on_new_tick(high_tick)
        if low_tick:
            candle.on_new_tick(low_tick)

        candle.on_new_tick(close_tick)

        return candle

    ##################################################
    # EVENTS
    ##################################################
    def generate(self):
        """
        This method must be implemented to fetch ticks or candles from provider.

        If your provider generates ticks: this method must call `self.market.on_new_tick(tick)` method.
        If your provider gererates candles: this method must call `self.market.on_new_candle(candle)` method.

        :return:

        """
        raise NotImplementedError('Implement this method to generate ticks.')

    def get_open_trades(self):
        """
        Implement this method to fetch list of open trades from your provider.
        :return: [<estrade.trade.Trade>,]
        """
        return []


class ALiveProvider(AProvider, MarketOptionalMixin):
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
