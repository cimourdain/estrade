import logging

from estrade.exceptions import ProviderException
from estrade.market_mixin import MarketOptionalMixin
from estrade.mixins.trade_class_mixin import TradeClassMixin
from estrade.candle import Candle
from estrade.tick import Tick

logger = logging.getLogger(__name__)


class Provider(MarketOptionalMixin, TradeClassMixin):
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
        :param: trade_class: instance of :class:`estrade.mixins.ATrade_class.ATradeClassUser`

        """
        # init a market property to None
        MarketOptionalMixin.__init__(self, None)
        TradeClassMixin.__init__(self, trade_class=trade_class)

        # the default provider is automatically logged
        self.logged = True

    def build_tick(self, epic_ref, datetime, bid, ask, **kwargs):
        if not self.market:
            raise ProviderException('Cannot build tick when provider has no market')

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

        Tick mode:
            If your provider generates ticks: this method must :
                1. Build a :class:`estrade.Tick` calling :func:`~estrade.mixins.Aprovider.AProvider.build_tick` method.
                2. Send the tick to market calling :func:`estrade.market.Market.on_new_tick` method

            eg::

                from estrade import AProvider
                from random import randint

                class MyProvider(AProvider):
                    SPREAD = 1

                    def generate():
                        for _ in range(100):
                            # generate a random value
                            random_value = randint(1000, 2000)

                            # build a Tick instance
                            tick = self.build_tick(
                                epic_ref='MY_EPIC_CODE',
                                datetime=datetime.now(),
                                bid=random_value + (SPREAD / 2),
                                ask=random_value - (SPREAD / 2),
                                my_param='test', # extra values are stored in tick meta
                            )

                            # send tick to market
                            self.market.on_new_tick(tick)

        Candle mode:
            If your provider generates candles: this method must call `self.market.on_new_candle(candle)` method.

        :return:

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