# import os
#
# import arrow
#
# from estrade import Epic, Tick
# from estrade.enums import TradeDirection
# from estrade.reporting.csv import ReportingCSV
#
#
# def test_reporting_csv():
#
#     epic = Epic(ref="MY_EPIC")
#
#     tick = Tick(datetime=arrow.get("2020-01-01 12:34:56"), bid=99, ask=101)
#     epic.on_new_tick(tick)
#
#     trade = epic.open_trade(direction=TradeDirection.BUY, quantity=2)
#
#     tick = Tick(datetime=arrow.get("2020-01-01 12:50:00"), bid=101, ask=102)
#     epic.on_new_tick(tick)
#
#     epic.close_trade(trade)
#
#     reporting = ReportingCSV()
#     report_file_path = reporting.report(epic)
#
#     expected_report = (
#         f"ref,status,epic,strategy,open_date,direction,open_quantity,open_value,"
#         f"closed_quantities,result,cumul\n"
#         f"{trade.ref},TransactionStatus.CONFIRMED,MY_EPIC,undefined,"
#         f"2020-01-01 12:34:56"
#         f",TradeDirection.BUY,2,101.0,2,0.0,0.0\n"
#     )
#
#     with open(report_file_path, "rU") as f:
#         text = f.read()
#
#         assert text == expected_report
#
#     os.remove(report_file_path)
