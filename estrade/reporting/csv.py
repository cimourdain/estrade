import csv
import logging
import os
from typing import List, TYPE_CHECKING

import arrow  # type: ignore


if TYPE_CHECKING:  # pragma: no cover
    from estrade import BaseStrategy

logger = logging.getLogger(__name__)


class CSVWriter:
    @staticmethod
    def open_file(path, filename):
        open_mode = "a"
        if not os.path.exists(path):
            os.makedirs(path)

        file_path = f"{path}/{filename}"
        file_exists = True
        if not os.path.isfile(file_path):
            open_mode = "w+"
            file_exists = False

        return file_exists, open(file_path, open_mode, newline="")

    @staticmethod
    def dict_to_csv(path, filename, dict_list, headers):
        file_exists, f = CSVWriter.open_file(path, filename)
        with f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
                for d in dict_list:
                    writer.writerow(d)


class ReportingCSV:
    def __init__(self, target_folder: str = "reports") -> None:
        """
        Create a reporting instance.

        Arguments:
            target_folder: relative target folder.

        """
        self.target_folder = target_folder

    def report(
        self, strategies: List["BaseStrategy"], trade_details: bool = True
    ) -> None:
        """
        Create a CSV reporting all trades of an Epic instance.

        This method creates:

            - A CSV file with input strategy result
            - (Optionally) A CSV file per strategy with the detailed list of trades.

        Arguments:
            strategies: List of strategies to report.
            trade_details: create files with the detailed list of trades of each
                strategy.

        """
        logger.info("Report as CSV")
        dt = arrow.utcnow().format("YYYY-MM-DD_HH:mm:ss")

        strategies_report = []
        for strategy in strategies:
            strategy_trades = list(strategy.get_trades())
            strategies_report.append(
                {
                    "ref": strategy.ref,
                    "nb_trades": len(strategy_trades),
                    "result": strategy.result(),
                    "profit_factor": strategy.profit_factor(),
                }
            )
            if trade_details:
                target_filename = f"{dt}_{strategy.ref}_trades.csv"
                trades = []
                headers: List[str] = []
                for trade in strategy_trades:
                    trade_dict = trade.asdict()
                    if not headers:
                        headers = list(trade_dict.keys())
                    trades.append(trade_dict)

                CSVWriter.dict_to_csv(
                    path=self.target_folder,
                    filename=target_filename,
                    dict_list=trades,
                    headers=headers,
                )

        CSVWriter.dict_to_csv(
            path=self.target_folder,
            filename=f"{dt}_strategies.csv",
            dict_list=strategies_report,
            headers=["ref", "nb_trades", "result", "profit_factor"],
        )
