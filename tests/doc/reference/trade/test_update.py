# import arrow
#
# from estrade import Epic, Tick, Trade
# from estrade.enums import TradeDirection


# def test_update_buy():
#     now = arrow.utcnow()
#     epic = Epic()
#     tick = Tick(bid=54.3, ask=68.9, datetime=now)
#     epic.on_new_tick(tick)
#     trade = Trade(
#         epic=epic,
#         direction=TradeDirection.BUY,
#         quantity=4,
#     )
#
#     trade.update(bid=100.6)
#     assert trade.result == round(100.6 - 68.9, 2) * 4
#     assert trade.max_result == round(100.6 - 68.9, 2) * 4
#     assert trade.min_result == round(54.3 - 68.9, 2) * 4
#
#     trade.update(bid=23.7)
#     assert trade.result == round(23.7 - 68.9, 2) * 4
#     assert trade.max_result == round(100.6 - 68.9, 2) * 4
#     assert trade.min_result == round(23.7 - 68.9, 2) * 4
#
#
# def test_update_sell():
#     now = arrow.utcnow()
#     epic = Epic()
#     tick = Tick(bid=76.3, ask=76.4, datetime=now)
#     epic.on_new_tick(tick)
#     trade = Trade(
#         epic=epic,
#         direction=TradeDirection.SELL,
#         quantity=9,
#     )
#
#     trade.update(ask=89.6)
#     assert trade.result == round(76.3 - 89.6, 2) * 9
#     assert trade.max_result == round(76.3 - 76.4, 2) * 9
#     assert trade.min_result == round(76.3 - 89.6, 2) * 9
#
#     trade.update(ask=55.2)
#     assert trade.result == round(76.3 - 55.2, 2) * 9
#     assert trade.max_result == round(76.3 - 55.2, 2) * 9
#     assert trade.min_result == round(76.3 - 89.6, 2) * 9
