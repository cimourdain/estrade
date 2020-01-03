import logging
from datetime import datetime, timedelta

import arrow
from sqlalchemy import func

from estrade.classes.exceptions import AProviderException
from estrade.classes.abstract.Aprovider import AProvider
from samples.providers.database.models import Tick


logger = logging.getLogger(__name__)


class DBProvider(AProvider):

    def __init__(self, start_date, end_date, *args, **kwargs):
        self.start_date = start_date
        self.end_date = end_date
        AProvider.__init__(self, *args, **kwargs)

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
                raise AProviderException('Invalid start date format')

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
                raise AProviderException('Invalid start date format')

        if isinstance(end_date, datetime):
            self._end_date = end_date

    @property
    def backtest_dates_generator(self):
        for n in range(int((self.end_date - self.start_date).days + 1)):
            trading_date = self.start_date + timedelta(n)
            yield trading_date.date()

    def generate_ticks(self):
        """
        This function generate ticks from your DB
        :return:
        """
        logger.info('Run backtest for epics %s' % [e.code for e in self.market.epics])

        for trading_date in self.backtest_dates_generator:
            logger.info('Run backtest for %s' % trading_date.strftime('%Y-%m-%d'))
            logger.info('find ticks for date %s and epics %s' % (trading_date.strftime('%Y-%m-%d'), [e.code for e in self.market.epics]))
            ticks = Tick.query.filter(
                func.date(Tick.datetime) == trading_date,
                Tick.epic.in_([e.code for e in self.market.epics]),
                ).order_by(Tick.datetime)

            logger.info('Nb ticks found for this date %d' % ticks.count())

            for tick in ticks:
                self.on_new_tick(
                    epic_code=tick.epic,
                    bid=tick.bid,
                    ask=tick.ask,
                    datetime=arrow.get(tick.datetime).replace(tzinfo='UTC')
                )

        logger.info('All ticks generated')
