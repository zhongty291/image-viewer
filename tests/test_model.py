"""
test_model.py — Model 层单元测试（TDD 实践）

测试策略：
  遵循 TDD 的红-绿-重构循环。每个测试方法验证一个具体行为。
  使用 pytest fixture 创建测试用的临时图片文件，避免依赖外部资源。
  测试覆盖：图片加载、旋转操作、缩放计算、信息提取、边界情况。
"""

import os
import tempfile

import pytest
from PIL import Image as PILImage

from src.model import ImageModel, ImageInfo


# ============================================================
# Fixtures — 测试数据准备
# ============================================================

@pytest.fixture
def test_image_path():
    """创建一个临时测试图片文件（100x80 的纯蓝色 PNG）。

    使用 tempfile 确保测试不污染项目目录，测试结束后自动清理。
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_image.png")
        img = PILImage.new("RGB", (100, 80), color="blue")
        img.save(filepath, "PNG")
        yield filepath
    # with 块结束后自动清理临时目录


@pytest.fixture
def test_jpg_path():
    """创建一个临时 JPEG 测试图片。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_photo.jpg")
        img = PILImage.new("RGB", (200, 150), color="red")
        img.save(filepath, "JPEG")
        yield filepath


@pytest.fixture
def model():
    """提供一个全新的 ImageModel 实例。"""
    return ImageModel()


# ============================================================
# 测试用例 1: 图片加载
# ============================================================

class TestImageLoading:
    """测试图片加载相关功能。"""

    def test_load_png_success(self, model, test_image_path):
        """测试: 成功加载 PNG 图片并返回正确的元信息。"""
        info = model.load(test_image_path)

        # 验证返回类型
        assert isinstance(info, ImageInfo)

        # 验证基本信息
        assert info.filename == "test_image.png"
        assert info.width == 100
        assert info.height == 80
        assert info.format == "PNG"
        assert info.mode == "RGB"

        # 验证文件大小字段非空
        assert len(info.file_size) > 0

        # 验证 Model 内部状态
        assert model.is_loaded() is True
        assert model.current_image is not None
        assert model.rotation == 0

    def test_load_jpg_success(self, model, test_jpg_path):
        """测试: 成功加载 JPG 图片。"""
        info = model.load(test_jpg_path)

        assert info.width == 200
        assert info.height == 150
        assert info.format in ("JPEG", "JPG")  # Pillow 可能返回 JPEG 或 JPG

    def test_load_nonexistent_file(self, model):
        """测试: 加载不存在的文件应抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            model.load("C:/nonexistent/path/image.png")

    def test_load_unsupported_format(self, model):
        """测试: 加载不支持的文件格式应抛出 ValueError。"""
        # 创建一个 .txt 文件尝试加载
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = os.path.join(tmpdir, "not_image.txt")
            with open(txt_path, "w") as f:
                f.write("Hello")
            with pytest.raises(ValueError, match="不支持的图片格式"):
                model.load(txt_path)

    def test_is_supported_static_method(self):
        """测试: 静态方法 is_supported 正确判断文件格式。"""
        assert ImageModel.is_supported("photo.jpg") is True
        assert ImageModel.is_supported("photo.PNG") is True
        assert ImageModel.is_supported("photo.bmp") is True
        assert ImageModel.is_supported("document.pdf") is False
        assert ImageModel.is_supported("script.py") is False


# ============================================================
# 测试用例 2: 旋转操作
# ============================================================

class TestRotation:
    """测试图片旋转功能。"""

    def test_rotate_cw_changes_rotation_angle(self, model, test_image_path):
        """测试: 顺时针旋转后旋转角度更新为 90。"""
        model.load(test_image_path)
        model.rotate_cw()
        assert model.rotation == 90

    def test_rotate_ccw_changes_rotation_angle(self, model, test_image_path):
        """测试: 逆时针旋转后旋转角度更新为 270（即 -90 mod 360）。"""
        model.load(test_image_path)
        model.rotate_ccw()
        assert model.rotation == 270

    def test_rotate_180_changes_rotation_angle(self, model, test_image_path):
        """测试: 180° 旋转。"""
        model.load(test_image_path)
        model.rotate_180()
        assert model.rotation == 180

    def test_four_rotations_return_to_zero(self, model, test_image_path):
        """测试: 连续 4 次顺时针旋转 90° 后角度回到 0。"""
        model.load(test_image_path)
        for _ in range(4):
            model.rotate_cw()
        assert model.rotation == 0

    def test_rotation_swaps_dimensions(self, model, test_image_path):
        """测试: 旋转 90° 后图片宽高互换。"""
        model.load(test_image_path)
        original_w, original_h = model.current_image.size  # 100, 80

        model.rotate_cw()
        new_w, new_h = model.current_image.size

        assert new_w == original_h
        assert new_h == original_w

    def test_reload_original_resets_rotation(self, model, test_image_path):
        """测试: reload_original 后旋转角度归零。"""
        model.load(test_image_path)
        model.rotate_cw()
        model.rotate_cw()  # 180°

        model.reload_original()
        assert model.rotation == 0

    def test_rotate_without_loaded_image(self, model):
        """测试: 未加载图片时调用旋转不应抛出异常。"""
        # 应该安全地什么都不做
        model.rotate_cw()
        model.rotate_ccw()
        model.rotate_180()
        assert model.rotation == 0


# ============================================================
# 测试用例 3: 缩放计算
# ============================================================

class TestZoomCalculation:
    """测试缩放比例计算。"""

    def test_fit_scale_wider_image(self, model, test_image_path):
        """测试: 宽图片适配视口时，按宽度限制计算缩放比。"""
        model.load(test_image_path)  # 100x80
        # 视口 50x100 — 宽度方向更受限
        scale = model.get_fit_scale(50, 100)
        # 按宽度: 50/100 = 0.5, 按高度: 100/80 = 1.25, 取 min = 0.5
        assert scale == pytest.approx(0.5)

    def test_fit_scale_taller_viewport(self, model, test_image_path):
        """测试: 视口高度方向更受限时的缩放计算。"""
        model.load(test_image_path)  # 100x80
        # 视口 200x40 — 高度方向更受限
        scale = model.get_fit_scale(200, 40)
        # 按宽度: 200/100 = 2.0, 按高度: 40/80 = 0.5, 取 min = 0.5
        assert scale == pytest.approx(0.5)

    def test_fit_scale_no_image(self, model):
        """测试: 未加载图片时返回默认缩放比 1.0。"""
        scale = model.get_fit_scale(800, 600)
        assert scale == 1.0

    def test_fit_scale_exact_fit(self, model, test_image_path):
        """测试: 视口与图片尺寸完全一致时缩放比为 1.0。"""
        model.load(test_image_path)  # 100x80
        scale = model.get_fit_scale(100, 80)
        assert scale == pytest.approx(1.0)


# ============================================================
# 测试用例 4: 信息提取
# ============================================================

class TestImageInfo:
    """测试图片元信息提取。"""

    def test_get_info_returns_imageinfo(self, model, test_image_path):
        """测试: get_info 返回 ImageInfo 对象且字段正确。"""
        model.load(test_image_path)
        info = model.get_info()

        assert isinstance(info, ImageInfo)
        assert info.width == 100
        assert info.height == 80
        assert info.format == "PNG"
        assert len(info.modified_time) > 0  # 修改时间非空

    def test_get_info_before_load(self, model):
        """测试: 未加载图片时 get_info 返回空 ImageInfo。"""
        info = model.get_info()
        assert info.filename == ""
        assert info.width == 0

    def test_info_file_size_format(self, model, test_image_path):
        """测试: 文件大小格式合理（包含单位）。"""
        model.load(test_image_path)
        info = model.get_info()
        # 文件大小应该包含单位标识
        assert "B" in info.file_size or "KB" in info.file_size or "MB" in info.file_size

    def test_filepath_property(self, model, test_image_path):
        """测试: filepath 属性返回正确的路径。"""
        model.load(test_image_path)
        assert model.filepath == test_image_path
