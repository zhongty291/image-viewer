"""
test_controller.py — Controller 层单元测试（TDD 实践）

测试策略：
  测试 Controller 的核心业务逻辑：缩放范围校验、旋转命令转发、
  导航索引计算、平移偏移更新。View 层被 mock 掉，不依赖 Tkinter。
"""

import os
import tempfile

import pytest
from PIL import Image as PILImage

from src.controller import ImageController
from src.model import ImageModel


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def controller():
    """提供一个全新的 Controller 实例。"""
    return ImageController()


@pytest.fixture
def controller_with_image():
    """创建一个已加载测试图片的 Controller。"""
    ctrl = ImageController()
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建多张测试图片模拟目录浏览
        for name in ["img_01.png", "img_02.jpg", "img_03.png", "img_04.jpg"]:
            img = PILImage.new("RGB", (100, 80), color="blue")
            img.save(os.path.join(tmpdir, name))
        # 加载第一张
        ctrl.open_file(os.path.join(tmpdir, "img_01.png"))
        yield ctrl
    # 自动清理


# ============================================================
# 测试用例 1: 缩放控制
# ============================================================

class TestZoomControl:
    """测试缩放业务逻辑。"""

    def test_zoom_in_increases_scale(self, controller):
        """测试: 放大后比例增大。"""
        initial = controller.scale  # 1.0
        new_scale = controller.zoom_in()
        assert new_scale > initial
        assert new_scale == pytest.approx(1.10)

    def test_zoom_out_decreases_scale(self, controller):
        """测试: 缩小后比例减小。"""
        controller.zoom_to(2.0)
        new_scale = controller.zoom_out()
        assert new_scale < 2.0
        assert new_scale == pytest.approx(1.90)

    def test_zoom_in_respects_max(self, controller):
        """测试: 不能放大超过 500%（MAX_SCALE）。"""
        controller.zoom_to(5.0)
        new_scale = controller.zoom_in()
        assert new_scale <= ImageController.MAX_SCALE
        assert new_scale == 5.0

    def test_zoom_out_respects_min(self, controller):
        """测试: 不能缩小低于 10%（MIN_SCALE）。"""
        controller.zoom_to(0.10)
        new_scale = controller.zoom_out()
        assert new_scale >= ImageController.MIN_SCALE
        assert new_scale == 0.10

    def test_zoom_to_clamps_value(self, controller):
        """测试: zoom_to 将非法值钳制到有效范围。"""
        result_too_high = controller.zoom_to(10.0)
        assert result_too_high == ImageController.MAX_SCALE

        result_too_low = controller.zoom_to(0.01)
        assert result_too_low == ImageController.MIN_SCALE

        result_valid = controller.zoom_to(2.5)
        assert result_valid == 2.5

    def test_zoom_100_sets_scale_to_one(self, controller):
        """测试: 100% 缩放恢复到 1.0。"""
        controller.zoom_to(3.0)
        scale = controller.zoom_100()
        assert scale == 1.0

    def test_zoom_fit_calculates_fit_scale(self, controller_with_image):
        """测试: 适配窗口缩放调用 Model 的 get_fit_scale。"""
        ctrl = controller_with_image
        ctrl.zoom_fit(200, 400)
        # 图片 100x80, 视口 200x400, 适配比 = min(200/100, 400/80) = min(2, 5) = 2
        assert ctrl.scale == pytest.approx(2.0)


# ============================================================
# 测试用例 2: 旋转控制
# ============================================================

class TestRotationControl:
    """测试旋转命令转发。"""

    def test_rotate_cw_updates_model(self, controller_with_image):
        """测试: Controller.rotate_cw() 正确委托给 Model。"""
        ctrl = controller_with_image
        assert ctrl.model.rotation == 0
        ctrl.rotate_cw()
        assert ctrl.model.rotation == 90

    def test_rotate_ccw_updates_model(self, controller_with_image):
        """测试: 逆时针旋转。"""
        ctrl = controller_with_image
        ctrl.rotate_ccw()
        assert ctrl.model.rotation == 270

    def test_rotate_180_updates_model(self, controller_with_image):
        """测试: 180° 旋转。"""
        ctrl = controller_with_image
        ctrl.rotate_180()
        assert ctrl.model.rotation == 180

    def test_reset_rotation(self, controller_with_image):
        """测试: 重置旋转归零。"""
        ctrl = controller_with_image
        ctrl.rotate_cw()
        ctrl.rotate_cw()
        ctrl.reset_rotation()
        assert ctrl.model.rotation == 0


# ============================================================
# 测试用例 3: 图片导航
# ============================================================

class TestNavigation:
    """测试图片导航逻辑。"""

    def test_build_file_list(self, controller_with_image):
        """测试: 打开图片后自动建立同目录文件列表。"""
        ctrl = controller_with_image
        current, total = ctrl.get_navigation_info()
        assert total == 4  # 创建了 4 张图片
        assert current >= 1

    def test_navigate_next(self, controller_with_image):
        """测试: 切换到下一张图片。"""
        ctrl = controller_with_image
        _, total = ctrl.get_navigation_info()
        assert total == 4

        # 切换到下一张
        info = ctrl.open_next()
        assert info is not None
        # 验证当前图片变了
        assert "img_02" in ctrl.model.filepath

    def test_navigate_prev(self, controller_with_image):
        """测试: 切换到上一张图片。"""
        ctrl = controller_with_image
        info = ctrl.open_prev()
        assert info is not None
        # 第一张的上一条应该是最后一张（循环）
        assert "img_04" in ctrl.model.filepath


# ============================================================
# 测试用例 4: 平移偏移
# ============================================================

class TestPanOffset:
    """测试拖拽平移状态。"""

    def test_update_pan_accumulates(self, controller):
        """测试: 多次平移偏移量累加。"""
        controller.update_pan(10, 5)
        controller.update_pan(-3, 2)
        x, y = controller.pan_offset
        assert x == 7.0
        assert y == 7.0

    def test_reset_pan_zeros_offset(self, controller):
        """测试: reset_pan 将偏移归零。"""
        controller.update_pan(50, 50)
        controller.reset_pan()
        x, y = controller.pan_offset
        assert x == 0.0
        assert y == 0.0
