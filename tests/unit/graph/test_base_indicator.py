from unittest.mock import call

from estrade.graph.base_indicator import BaseIndicatorValue
from estrade.mixins import RefMixin
from tests.unit.factories import BaseIndicatorFactory, FrameSetFactory


CLASS_DEFINITION_PATH = "estrade.graph.base_indicator.BaseIndicator"


class TestInheritance:
    def test_ref_mixin(self):
        bi = BaseIndicatorFactory()

        assert RefMixin in bi.__class__.__bases__

    def test_ref_mixin_call(self, mocker):
        mixin_init_mock = mocker.patch.object(
            RefMixin, "__init__", wraps=RefMixin.__init__
        )

        bi = BaseIndicatorFactory(ref="test_ref")

        assert mixin_init_mock.call_args_list == [call(bi, ref="test_ref")]


class TestInit:
    def test_value_class__default(self):
        bi = BaseIndicatorFactory()

        assert bi.value_class == BaseIndicatorValue

    def test_value_class_manual(self):
        class Dummy(BaseIndicatorValue):
            pass

        bi = BaseIndicatorFactory(value_class=Dummy)

        assert bi.value_class == Dummy

    def test_market_open_only__default(self):
        bi = BaseIndicatorFactory()

        assert bi.market_open_only is False

    def test_market_open_only__manual(self):
        bi = BaseIndicatorFactory(market_open_only=True)

        assert bi.market_open_only is True

    def test_frame_set__default(self):
        bi = BaseIndicatorFactory()

        assert bi.frame_set is None


class TestEpic:
    def test_no_frame_set(self):
        bi = BaseIndicatorFactory()

        assert bi.epic is None

    def test_frameset_without_epic(self, mocker):
        frameset_mock = mocker.Mock()
        frameset_mock.epic = None

        bi = BaseIndicatorFactory()
        bi.frame_set = frameset_mock

        assert bi.epic is None

    def test_frameset_with_epic(self, mocker):
        frameset_mock = mocker.Mock()
        frameset_mock.epic = "my_epic"

        bi = BaseIndicatorFactory()
        bi.frame_set = frameset_mock

        assert bi.epic == "my_epic"


class TestBuildValueFromFrame:
    def test_market_open_required_and_open(self, mocker):
        bi = BaseIndicatorFactory(market_open_only=True)
        value_mock = mocker.patch.object(bi, "value_class", return_value="new_frame")

        response = bi.build_value_from_frame("test_frame", True)

        assert value_mock.call_args_list == [call(indicator=bi, frame="test_frame")]
        assert response == "new_frame"

    def test_market_open_required_and_close(self, mocker):
        bi = BaseIndicatorFactory(market_open_only=True)
        frame_mock = mocker.Mock()
        frame_mock.previous_frame = None
        value_mock = mocker.patch.object(bi, "value_class")

        response = bi.build_value_from_frame(frame_mock, False)

        assert value_mock.call_args_list == []
        assert response is None

    def test_market_open_not_required_and_closed(self, mocker):
        bi = BaseIndicatorFactory(market_open_only=False)
        frame_mock = mocker.Mock()
        frame_mock.previous_frame = None
        value_mock = mocker.patch.object(bi, "value_class", return_value="new_frame")

        response = bi.build_value_from_frame(frame_mock, False)

        assert value_mock.call_args_list == [call(indicator=bi, frame=frame_mock)]
        assert response == "new_frame"


class TestSetFrameSet:
    def test_nominal(self):
        indicator = BaseIndicatorFactory()
        frame_set = FrameSetFactory()

        indicator.set_frame_set(frame_set)

        assert indicator.frame_set == frame_set
