import logging

from estrade.classes.abstract.Areporting import AReporting
from estrade.utils.csv import CSVWriter

logger = logging.getLogger(__name__)


class ReportingCSV(AReporting):

    @property
    def base_path(self):
        return self._market.ref

    def strategy_path(self, strategy):
        return '{}/{}/'.format(self.market.ref, strategy.ref)

    def on_new_tick(self, tick):
        pass

    def on_trade_update(self, trade):
        pass

    def on_run_end(self):
        logger.info('Report as CSV')
        strategies_dicts = []
        for strategy in self.market.strategies:
            strategies_dicts.append(strategy.to_json)

            strategy_trades_dict = []
            headers = []
            for trade in self.market.trade_manager.get_trades(strategy=strategy):
                strategy_trades_dict.append(trade.to_json)
                if not headers:
                    headers = trade.json_headers

            consolidated_report_file = 'consolidated_trades.csv'
            CSVWriter.dict_to_csv(
                path=self.strategy_path(strategy),
                filename=consolidated_report_file,
                dict_list=strategy_trades_dict,
                headers=headers,
            )

        CSVWriter.dict_to_csv(
            path=self.base_path,
            filename='strategies_report.csv',
            dict_list=strategies_dicts,
            headers=self._market.strategies[0].json_headers,
        )
        print(strategies_dicts)
