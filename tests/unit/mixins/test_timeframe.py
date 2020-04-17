import arrow
import pytest

from estrade.enums import Unit
from estrade.exceptions import TimeFrameException
from estrade.mixins.timeframe import TimeframeMixin


class TestInit:
    @pytest.mark.parametrize(
        ["unit"],
        [
            (Unit.TICK,),
            (Unit.SECOND,),
            (Unit.MINUTE,),
            (Unit.HOUR,),
            (Unit.DAY,),
            (Unit.WEEK,),
            (Unit.MONTH,),
            (Unit.YEAR,),
        ],
    )
    def test_unit(self, unit):
        tf = TimeframeMixin(unit=unit, unit_quantity=1)

        assert tf.unit == unit

    def test_unit_quantity(self):
        tf = TimeframeMixin(unit=Unit.SECOND, unit_quantity=4)

        assert tf.unit_quantity == 4


class TestUnitConsistency:
    @pytest.mark.parametrize(
        ["unit", "unit_quantity"],
        [
            (Unit.SECOND, 7),
            (Unit.MINUTE, 7),
            (Unit.HOUR, 5),
            (Unit.DAY, 2),
            (Unit.MONTH, 5),
        ],
    )
    def test_nominal(self, unit, unit_quantity):
        with pytest.raises(TimeFrameException):
            TimeframeMixin(unit=unit, unit_quantity=unit_quantity)


class TestGetTimeFrameStart:
    def test_tick(self):
        tf = TimeframeMixin(unit=Unit.TICK, unit_quantity=3)

        now = arrow.utcnow()
        assert tf.get_frame_start(now) == now

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_start"],
        [
            ("2020-01-01 12:34:56", 1, "2020-01-01 12:34:56"),
            ("2020-01-01 12:34:56", 2, "2020-01-01 12:34:56"),
            ("2020-01-01 12:34:55", 2, "2020-01-01 12:34:54"),
            ("2020-01-01 12:34:59", 3, "2020-01-01 12:34:57"),
            ("2020-01-01 12:34:58", 3, "2020-01-01 12:34:57"),
            ("2020-01-01 12:34:57", 3, "2020-01-01 12:34:57"),
            ("2020-01-01 12:34:54", 5, "2020-01-01 12:34:50"),
            ("2020-01-01 12:34:52", 5, "2020-01-01 12:34:50"),
            ("2020-01-01 12:34:50", 5, "2020-01-01 12:34:50"),
            ("2020-01-01 12:34:59", 10, "2020-01-01 12:34:50"),
            ("2020-01-01 12:34:56", 10, "2020-01-01 12:34:50"),
            ("2020-01-01 12:34:55", 10, "2020-01-01 12:34:50"),
            ("2020-01-01 12:34:51", 10, "2020-01-01 12:34:50"),
            ("2020-01-01 12:34:50", 10, "2020-01-01 12:34:50"),
            ("2020-01-01 12:34:10", 15, "2020-01-01 12:34:00"),
            ("2020-01-01 12:34:16", 15, "2020-01-01 12:34:15"),
            ("2020-01-01 12:34:19", 15, "2020-01-01 12:34:15"),
            ("2020-01-01 12:34:19", 15, "2020-01-01 12:34:15"),
            ("2020-01-01 12:34:57", 15, "2020-01-01 12:34:45"),
        ],
    )
    def test_seconds(self, input_datetime, unit_quantity, expected_start):
        tf = TimeframeMixin(unit=Unit.SECOND, unit_quantity=unit_quantity)

        assert tf.get_frame_start(arrow.get(input_datetime)) == arrow.get(
            expected_start
        )

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_start"],
        [
            ("2020-01-01 12:33:59", 1, "2020-01-01 12:33:00"),
            ("2020-01-01 12:34:00", 1, "2020-01-01 12:34:00"),
            ("2020-01-01 12:34:41", 1, "2020-01-01 12:34:00"),
            ("2020-01-01 12:34:59", 1, "2020-01-01 12:34:00"),
            ("2020-01-01 12:35:00", 1, "2020-01-01 12:35:00"),
            ("2020-01-01 12:33:59", 2, "2020-01-01 12:32:00"),
            ("2020-01-01 12:34:00", 2, "2020-01-01 12:34:00"),
            ("2020-01-01 12:34:41", 2, "2020-01-01 12:34:00"),
            ("2020-01-01 12:35:26", 2, "2020-01-01 12:34:00"),
            ("2020-01-01 12:35:59", 2, "2020-01-01 12:34:00"),
            ("2020-01-01 12:36:00", 2, "2020-01-01 12:36:00"),
            ("2020-01-01 12:29:59", 5, "2020-01-01 12:25:00"),
            ("2020-01-01 12:30:00", 5, "2020-01-01 12:30:00"),
            ("2020-01-01 12:32:11", 5, "2020-01-01 12:30:00"),
            ("2020-01-01 12:34:44", 5, "2020-01-01 12:30:00"),
            ("2020-01-01 12:34:59", 5, "2020-01-01 12:30:00"),
            ("2020-01-01 12:35:00", 5, "2020-01-01 12:35:00"),
            ("2020-01-01 12:29:59", 10, "2020-01-01 12:20:00"),
            ("2020-01-01 12:30:00", 10, "2020-01-01 12:30:00"),
            ("2020-01-01 12:32:11", 10, "2020-01-01 12:30:00"),
            ("2020-01-01 12:38:57", 10, "2020-01-01 12:30:00"),
            ("2020-01-01 12:39:59", 10, "2020-01-01 12:30:00"),
            ("2020-01-01 12:40:00", 10, "2020-01-01 12:40:00"),
            ("2020-01-01 12:29:59", 15, "2020-01-01 12:15:00"),
            ("2020-01-01 12:30:00", 15, "2020-01-01 12:30:00"),
            ("2020-01-01 12:32:11", 15, "2020-01-01 12:30:00"),
            ("2020-01-01 12:43:34", 15, "2020-01-01 12:30:00"),
            ("2020-01-01 12:44:59", 15, "2020-01-01 12:30:00"),
            ("2020-01-01 12:45:00", 15, "2020-01-01 12:45:00"),
        ],
    )
    def test_minutes(self, input_datetime, unit_quantity, expected_start):
        tf = TimeframeMixin(unit=Unit.MINUTE, unit_quantity=unit_quantity)

        assert tf.get_frame_start(arrow.get(input_datetime)) == arrow.get(
            expected_start
        )

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_start"],
        [
            ("2020-01-01 11:59:59", 1, "2020-01-01 11:00:00"),
            ("2020-01-01 12:00:00", 1, "2020-01-01 12:00:00"),
            ("2020-01-01 12:34:56", 1, "2020-01-01 12:00:00"),
            ("2020-01-01 12:59:59", 1, "2020-01-01 12:00:00"),
            ("2020-01-01 13:00:00", 1, "2020-01-01 13:00:00"),
            ("2020-01-01 11:59:59", 2, "2020-01-01 10:00:00"),
            ("2020-01-01 12:00:00", 2, "2020-01-01 12:00:00"),
            ("2020-01-01 13:12:21", 2, "2020-01-01 12:00:00"),
            ("2020-01-01 13:59:59", 2, "2020-01-01 12:00:00"),
            ("2020-01-01 14:00:00", 2, "2020-01-01 14:00:00"),
            ("2020-01-01 11:59:59", 4, "2020-01-01 08:00:00"),
            ("2020-01-01 12:00:00", 4, "2020-01-01 12:00:00"),
            ("2020-01-01 14:26:03", 4, "2020-01-01 12:00:00"),
            ("2020-01-01 15:48:22", 4, "2020-01-01 12:00:00"),
            ("2020-01-01 15:59:59", 4, "2020-01-01 12:00:00"),
            ("2020-01-01 16:00:00", 4, "2020-01-01 16:00:00"),
        ],
    )
    def test_hours(self, input_datetime, unit_quantity, expected_start):
        tf = TimeframeMixin(unit=Unit.HOUR, unit_quantity=unit_quantity)

        assert tf.get_frame_start(arrow.get(input_datetime)) == arrow.get(
            expected_start
        )

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_start"],
        [
            ("2020-10-02 11:59:59", 1, "2020-10-02 00:00:00"),
            ("2020-09-27 23:59:59", 7, "2020-09-21 00:00:00"),
            ("2020-09-28 00:00:00", 7, "2020-09-28 00:00:00"),
            ("2020-10-02 11:59:59", 7, "2020-09-28 00:00:00"),
            ("2020-10-04 23:59:59", 7, "2020-09-28 00:00:00"),
            ("2020-10-05 00:00:00", 7, "2020-10-05 00:00:00"),
        ],
    )
    def test_days(self, input_datetime, unit_quantity, expected_start):
        tf = TimeframeMixin(unit=Unit.DAY, unit_quantity=unit_quantity)

        assert tf.get_frame_start(arrow.get(input_datetime)) == arrow.get(
            expected_start
        )

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_start"],
        [
            ("2020-01-05 23:59:59", 1, "2019-12-30 00:00:00"),
            ("2020-01-06 00:00:00", 1, "2020-01-06 00:00:00"),
            ("2020-01-08 14:34:51", 1, "2020-01-06 00:00:00"),
            ("2020-01-12 23:59:59", 1, "2020-01-06 00:00:00"),
            ("2020-01-13 00:00:00", 1, "2020-01-13 00:00:00"),
            # TODO 2 weeks
        ],
    )
    def test_week(self, input_datetime, unit_quantity, expected_start):
        tf = TimeframeMixin(unit=Unit.WEEK, unit_quantity=unit_quantity)

        assert tf.get_frame_start(arrow.get(input_datetime)) == arrow.get(
            expected_start
        )

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_start"],
        [
            ("2019-12-31 23:59:59", 1, "2019-12-01 00:00:00"),
            ("2020-01-01 00:00:00", 1, "2020-01-01 00:00:00"),
            ("2020-01-15 14:34:51", 1, "2020-01-01 00:00:00"),
            ("2020-01-31 23:59:59", 1, "2020-01-01 00:00:00"),
            ("2020-02-01 00:00:00", 1, "2020-02-01 00:00:00"),
            ("2019-12-31 23:59:59", 3, "2019-10-01 00:00:00"),
            ("2020-01-01 00:00:00", 3, "2020-01-01 00:00:00"),
            ("2020-02-15 00:00:00", 3, "2020-01-01 00:00:00"),
            ("2020-03-31 23:59:59", 3, "2020-01-01 00:00:00"),
            ("2020-04-01 00:00:00", 3, "2020-04-01 00:00:00"),
            ("2019-12-31 23:59:59", 4, "2019-09-01 00:00:00"),
            ("2020-01-01 00:00:00", 4, "2020-01-01 00:00:00"),
            ("2020-02-15 00:00:00", 4, "2020-01-01 00:00:00"),
            ("2020-04-30 23:59:59", 4, "2020-01-01 00:00:00"),
            ("2020-05-01 00:00:00", 4, "2020-05-01 00:00:00"),
            ("2019-12-31 23:59:59", 6, "2019-07-01 00:00:00"),
            ("2020-01-01 00:00:00", 6, "2020-01-01 00:00:00"),
            ("2020-05-15 00:00:00", 6, "2020-01-01 00:00:00"),
            ("2020-06-30 23:59:59", 6, "2020-01-01 00:00:00"),
            ("2020-07-01 00:00:00", 6, "2020-07-01 00:00:00"),
        ],
    )
    def test_month(self, input_datetime, unit_quantity, expected_start):
        tf = TimeframeMixin(unit=Unit.MONTH, unit_quantity=unit_quantity)

        assert tf.get_frame_start(arrow.get(input_datetime)) == arrow.get(
            expected_start
        )

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_start"],
        [
            ("2019-12-31 23:59:59", 1, "2019-01-01 00:00:00"),
            ("2020-01-01 00:00:00", 1, "2020-01-01 00:00:00"),
            ("2020-06-30 12:34:56", 1, "2020-01-01 00:00:00"),
            ("2020-12-31 23:59:59", 1, "2020-01-01 00:00:00"),
            ("2021-01-01 00:00:00", 1, "2021-01-01 00:00:00"),
            ("2019-12-31 23:59:59", 2, "2018-01-01 00:00:00"),
            ("2020-01-01 00:00:00", 2, "2020-01-01 00:00:00"),
            ("2020-12-31 23:59:59", 2, "2020-01-01 00:00:00"),
            ("2021-12-31 23:59:59", 2, "2020-01-01 00:00:00"),
            ("2022-01-01 00:00:00", 2, "2022-01-01 00:00:00"),
        ],
    )
    def test_year(self, input_datetime, unit_quantity, expected_start):
        tf = TimeframeMixin(unit=Unit.YEAR, unit_quantity=unit_quantity)

        assert tf.get_frame_start(arrow.get(input_datetime)) == arrow.get(
            expected_start
        )


class TestGetTimeFrameEnd:
    def test_tick(self):
        tf = TimeframeMixin(unit=Unit.TICK, unit_quantity=1)
        input_dt = arrow.utcnow()
        timeframe_end = tf.get_frame_end(input_dt)

        assert timeframe_end == input_dt

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_end"],
        [
            ("2020-01-01 12:34:56", 1, "2020-01-01 12:34:57"),
            ("2020-01-01 12:35:00", 5, "2020-01-01 12:35:05"),
            ("2020-01-01 12:35:25", 5, "2020-01-01 12:35:30"),
        ],
    )
    def test_seconds(self, input_datetime, unit_quantity, expected_end):
        tf = TimeframeMixin(unit=Unit.SECOND, unit_quantity=unit_quantity)

        timeframe_end = tf.get_frame_end(arrow.get(input_datetime))

        assert timeframe_end == arrow.get(expected_end)

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_end"],
        [
            ("2020-01-01 12:34:00", 1, "2020-01-01 12:35:00"),
            ("2020-01-01 12:35:00", 5, "2020-01-01 12:40:00"),
            ("2020-01-01 12:15:00", 15, "2020-01-01 12:30:00"),
        ],
    )
    def test_minutes(self, input_datetime, unit_quantity, expected_end):
        tf = TimeframeMixin(unit=Unit.MINUTE, unit_quantity=unit_quantity)

        timeframe_end = tf.get_frame_end(arrow.get(input_datetime))

        assert timeframe_end == arrow.get(expected_end)

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_end"],
        [
            ("2020-01-01 12:00:00", 1, "2020-01-01 13:00:00"),
            ("2020-01-01 00:00:00", 4, "2020-01-01 04:00:00"),
            ("2020-01-01 10:00:00", 4, "2020-01-01 14:00:00"),
            ("2020-01-01 20:00:00", 4, "2020-01-02 00:00:00"),
        ],
    )
    def test_hours(self, input_datetime, unit_quantity, expected_end):
        tf = TimeframeMixin(unit=Unit.HOUR, unit_quantity=unit_quantity)

        timeframe_end = tf.get_frame_end(arrow.get(input_datetime))

        assert timeframe_end == arrow.get(expected_end)

    @pytest.mark.parametrize(
        ["input_datetime", "unit_quantity", "expected_end"],
        [
            ("2020-01-01 00:00:00", 1, "2020-01-02 00:00:00"),
            ("2020-01-06 00:00:00", 7, "2020-01-13 00:00:00"),
        ],
    )
    def test_days(self, input_datetime, unit_quantity, expected_end):
        tf = TimeframeMixin(unit=Unit.DAY, unit_quantity=unit_quantity)

        timeframe_end = tf.get_frame_end(arrow.get(input_datetime))

        assert timeframe_end == arrow.get(expected_end)
