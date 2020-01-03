import logging

from estrade import Strategy

logger = logging.getLogger(__name__)


class MovingAverageStrategy(Strategy):
    """
    This strategy open :
        - a BUY position when candle crosses the mm50 upward
        - a SELL position when candle crosses the mm50 downward
    """
    mm_name = 'mm50'

    def check_tick_time(self, tick):
        """
        Only run strategy bewteen 9AM and 1PM
        :param tick: <Tick instance>
        :return:
        """
        if 9 <= tick.datetime.hour <= 13:
            return True
        return False

    def on_new_candle_opening_strategy(self, candle_set):
        # fetch last closed candle
        last_closed_candle = candle_set.last_closed_candle

        # if last closed candle exists and indicator is calculated
        if last_closed_candle and last_closed_candle.indicators.get(self.mm_name):
            # fetch moving average value
            mm = last_closed_candle.indicators[self.mm_name]

            # if new candle is not the first candle in candle set
            logger.debug('compare mm(%d) to open(%d) and close(%d) of previous candle.' % (
                mm,
                last_closed_candle.open,
                last_closed_candle.close
            ))
            # open buy if mm was crossed upward by last candle
            if last_closed_candle.open < mm < last_closed_candle.close:
                logger.info('open buy from mm strategy')
                self.open_trade(
                    epic=candle_set.epic.code,
                    quantity=1,
                    direction='BUY'
                )
                return
            # open sell if mm was crossed downward by last candle
            elif last_closed_candle.open > mm > last_closed_candle.close:
                logger.info('open sell from mm strategy')
                self.open_trade(
                    epic=candle_set.epic.code,
                    quantity=1,
                    direction='SELL'
                )
                return

    def on_new_candle_closing_strategy(self, candle_set):
        # fetch last closed candle
        last_closed_candle = candle_set.last_closed_candle

        # fetch mm value
        mm = last_closed_candle.indicators[self.mm_name]

        if last_closed_candle and mm:
            # if last candle high is below mm: close all open buys
            if last_closed_candle.open > mm > last_closed_candle.close:
                self.close_all_buys()
            # if last candle low is above mm: close all open sells
            elif last_closed_candle.open < mm < last_closed_candle.close:
                self.close_all_sells()
