"""
model.py — Model 层（图像数据处理）

职责（RDD — 信息专家原则）：
  - 图片文件加载与格式解码
  - 图像旋转/翻转等变换操作
  - 图像元信息（分辨率、格式、大小、EXIF）提取
  - 缩放比例数学计算

不负责：
  - 任何 UI 绘制或 Tkinter 组件操作
  - 用户输入处理
  - 文件对话框或路径选择逻辑
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from PIL import Image
from PIL import ExifTags as ImageExifTags


# ============================================================
# 数据结构定义
# ============================================================

@dataclass
class ImageInfo:
    """图片元信息 — 纯数据结构，不包含任何行为逻辑。

    遵循 RDD 原则：数据结构与行为分离。
    ImageInfo 只负责「持有数据」，操作逻辑全部在 ImageModel 中。
    """
    filename: str = ""           # 文件名（含扩展名），如 "photo.jpg"
    filepath: str = ""           # 完整路径
    format: str = ""             # 图片格式，如 "JPEG" / "PNG" / "BMP"
    width: int = 0               # 像素宽度
    height: int = 0              # 像素高度
    file_size: str = ""          # 人类可读的文件大小，如 "2.3 MB"
    mode: str = ""               # 色彩模式，如 "RGB" / "RGBA" / "L"
    modified_time: str = ""      # 文件最后修改时间
    exif: Dict[str, Any] = field(default_factory=dict)  # EXIF 元数据


# ============================================================
# ImageModel — 图像数据处理核心
# ============================================================

class ImageModel:
    """封装所有图像数据处理逻辑。

    设计要点：
    1. 保留 _original（原始加载的 PIL Image）不动，所有旋转变换
       应用到 _current 上。这样旋转可以无损回退（reload_original），
       避免 JPEG 多次旋转造成的累积压缩失真。
    2. 缩放计算与缩放渲染分离：Model 只提供数学比例值，
       View 层负责实际的图片缩放显示（Tkinter 的 subsample/zoom）。
    """

    # 支持的图片文件扩展名
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'}

    def __init__(self):
        """初始化 Model，所有状态为空。"""
        self._original: Optional[Image.Image] = None  # 原始图片，只读
        self._current: Optional[Image.Image] = None   # 当前变换后的图片
        self._rotation: int = 0       # 累计旋转角度：0 / 90 / 180 / 270
        self._filepath: str = ""      # 当前文件的完整路径
        self._info: Optional[ImageInfo] = None  # 缓存的元信息

    # ---- 文件操作 ----

    def load(self, path: str) -> ImageInfo:
        """加载图片文件并提取元信息。

        Args:
            path: 图片文件的完整路径。

        Returns:
            包含图片元信息的 ImageInfo 对象。

        Raises:
            FileNotFoundError: 文件不存在。
            ValueError: 文件不是支持的图片格式。
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(f"文件不存在: {path}")

        ext = os.path.splitext(path)[1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的图片格式: {ext}。支持的格式: {self.SUPPORTED_EXTENSIONS}")

        # 使用 Pillow 打开图片
        img = Image.open(path)

        # 处理 EXIF 旋转标记（部分相机拍摄的照片需要自动旋转）
        # Pillow 的 ImageOps.exif_transpose 可以自动处理 EXIF Orientation
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)

        # 统一转为 RGB 模式（便于 Tkinter 显示，RGBA 在部分场景有兼容问题）
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGBA')
        elif img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        # 保存状态
        self._original = img.copy()
        self._current = img.copy()
        self._rotation = 0
        self._filepath = path
        self._info = self._extract_info(path, img)

        return self._info

    def reload_original(self) -> None:
        """丢弃所有旋转变换，恢复到最初加载的原始图片。

        用于用户点击「重置」或切换图片时的状态清理。
        """
        if self._original is not None:
            self._current = self._original.copy()
            self._rotation = 0

    # ---- 旋转操作 ----

    def rotate_cw(self) -> None:
        """顺时针旋转 90°。

        使用 PIL 的 rotate 方法，expand=True 确保旋转后画布扩展，
        不会裁剪图片内容。
        """
        if self._current is not None:
            self._current = self._current.rotate(-90, expand=True)
            self._rotation = (self._rotation + 90) % 360

    def rotate_ccw(self) -> None:
        """逆时针旋转 90°（等价于顺时针 270°）。"""
        if self._current is not None:
            self._current = self._current.rotate(90, expand=True)
            self._rotation = (self._rotation + 270) % 360

    def rotate_180(self) -> None:
        """旋转 180°。"""
        if self._current is not None:
            self._current = self._current.rotate(180, expand=True)
            self._rotation = (self._rotation + 180) % 360

    # ---- 缩放计算 ----

    def get_fit_scale(self, view_width: int, view_height: int) -> float:
        """计算「适配窗口」模式下的缩放比例。

        按比例缩放使图片完全容纳在给定视口内（保持宽高比）。

        Args:
            view_width: 视口宽度（像素）。
            view_height: 视口高度（像素）。

        Returns:
            缩放比例浮点数（如 0.5 表示缩小为 50%）。
        """
        if self._current is None:
            return 1.0
        img_w, img_h = self._current.size
        if img_w == 0 or img_h == 0:
            return 1.0
        scale_w = view_width / img_w
        scale_h = view_height / img_h
        return min(scale_w, scale_h)  # 取较小值，确保完整显示

    # ---- 信息查询 ----

    @property
    def current_image(self) -> Optional[Image.Image]:
        """返回当前变换后的 PIL Image 对象（供 View 层渲染使用）。"""
        return self._current

    @property
    def original_image(self) -> Optional[Image.Image]:
        """返回原始 PIL Image 对象（供需要原始数据的场景使用）。"""
        return self._original

    @property
    def rotation(self) -> int:
        """返回当前累计旋转角度（0/90/180/270）。"""
        return self._rotation

    @property
    def filepath(self) -> str:
        """返回当前文件路径。"""
        return self._filepath

    def get_info(self) -> ImageInfo:
        """返回当前图片的元信息。

        Returns:
            ImageInfo 对象。如果未加载图片，返回空 ImageInfo。
        """
        if self._info is None:
            return ImageInfo()
        return self._info

    def is_loaded(self) -> bool:
        """检查是否已加载图片。"""
        return self._current is not None

    # ---- 内部辅助方法 ----

    def _extract_info(self, path: str, img: Image.Image) -> ImageInfo:
        """从文件路径和 PIL Image 对象中提取完整元信息。

        Args:
            path: 图片文件完整路径。
            img: 已打开的 PIL Image 对象。

        Returns:
            填充完整的 ImageInfo 对象。
        """
        stat = os.stat(path)

        # 文件大小格式化
        size_bytes = stat.st_size
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.2f} MB"

        # 修改时间格式化
        mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))

        # EXIF 提取（仅 JPEG/TIFF 通常有 EXIF）
        exif_data: Dict[str, Any] = {}
        try:
            exif_raw = img.getexif()
            if exif_raw:
                for tag_id, value in exif_raw.items():
                    tag_name = ImageExifTags.TAGS.get(tag_id, str(tag_id))
                    # 跳过二进制数据（如缩略图），只保留可读字段
                    if isinstance(value, (str, int, float)):
                        exif_data[tag_name] = value
        except Exception:
            pass  # EXIF 读取失败不影响主流程

        return ImageInfo(
            filename=os.path.basename(path),
            filepath=path,
            format=img.format or os.path.splitext(path)[1].upper().lstrip('.'),
            width=img.width,
            height=img.height,
            file_size=size_str,
            mode=img.mode,
            modified_time=mtime,
            exif=exif_data,
        )

    @staticmethod
    def is_supported(path: str) -> bool:
        """静态方法：检查给定路径是否为支持的图片格式。

        Args:
            path: 文件路径。

        Returns:
            True 表示该文件是支持的图片格式。
        """
        ext = os.path.splitext(path)[1].lower()
        return ext in ImageModel.SUPPORTED_EXTENSIONS
