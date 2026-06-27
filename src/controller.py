"""
controller.py — Controller 层（事件协调与业务逻辑）

职责（RDD — 控制器模式）：
  - 接收 View 层的用户事件，翻译为对 Model 的操作调用
  - 管理缩放状态（当前比例、范围校验）
  - 管理图片导航（同目录文件列表、索引切换）
  - 管理拖拽平移状态

不负责：
  - 直接操作 PIL Image 对象（委托给 Model）
  - 直接创建或修改 Tkinter 组件（委托给 View）
  - 文件 I/O 操作（委托给 Model）
"""

import os
import glob
from typing import List, Optional, Tuple
from src.model import ImageModel, ImageInfo


class ImageController:
    """Controller 层：协调 Model 和 View 的交互。

    设计要点：
    1. Controller 持有 Model 引用和对 View 的弱引用（避免循环依赖）。
    2. 所有从 View 进来的事件都通过 Controller 方法处理，
       然后 Controller 决定调用 Model 的哪个方法、更新 View 的哪个部分。
    3. 缩放范围硬编码在此层（MIN_SCALE / MAX_SCALE），
       这属于业务规则而非 UI 逻辑。
    """

    # 缩放范围常量
    MIN_SCALE = 0.10   # 最小 10%
    MAX_SCALE = 5.00   # 最大 500%
    ZOOM_STEP = 0.10   # 每次缩放步长 10个百分点
    ZOOM_LEVELS = [0.10, 0.25, 0.33, 0.50, 0.67, 0.75,
                   1.00, 1.25, 1.50, 2.00, 3.00, 4.00, 5.00]  # 预设缩放档位

    def __init__(self):
        """初始化 Controller。"""
        self._model = ImageModel()
        self._view = None  # 延迟绑定，由 View 在创建后注入

        # 缩放状态
        self._scale: float = 1.0

        # 图片导航状态
        self._file_list: List[str] = []    # 同目录下所有支持的图片路径
        self._current_index: int = -1      # 当前在 _file_list 中的索引

        # 拖拽平移状态
        self._pan_offset_x: float = 0.0
        self._pan_offset_y: float = 0.0

    def set_view(self, view) -> None:
        """注入 View 引用（避免构造函数中的循环依赖）。"""
        self._view = view

    @property
    def model(self) -> ImageModel:
        """暴露 Model 引用供 View 读取数据。"""
        return self._model

    # ---- 文件操作 ----

    def open_file(self, path: str) -> Optional[ImageInfo]:
        """打开指定图片文件。

        流程：
        1. 调用 Model.load() 加载图片
        2. 重置缩放为「适配窗口」
        3. 扫描同目录下的其他图片，建立导航列表
        4. 返回 ImageInfo 供 View 更新信息面板

        Args:
            path: 图片文件的完整路径。

        Returns:
            ImageInfo 元信息，加载失败返回 None。
        """
        try:
            info = self._model.load(path)
        except (FileNotFoundError, ValueError) as e:
            if self._view:
                self._view.show_error(str(e))
            return None

        # 重置缩放和偏移
        self._scale = 1.0
        self._pan_offset_x = 0.0
        self._pan_offset_y = 0.0

        # 建立同目录图片列表
        self._build_file_list(path)

        return info

    def open_next(self) -> Optional[ImageInfo]:
        """打开目录中的下一张图片。"""
        if not self._file_list:
            return None
        self._current_index = (self._current_index + 1) % len(self._file_list)
        return self.open_file(self._file_list[self._current_index])

    def open_prev(self) -> Optional[ImageInfo]:
        """打开目录中的上一张图片。"""
        if not self._file_list:
            return None
        self._current_index = (self._current_index - 1) % len(self._file_list)
        return self.open_file(self._file_list[self._current_index])

    def get_navigation_info(self) -> Tuple[int, int]:
        """返回 (当前序号, 总数)，例如 (3, 10) 表示第 3 张/共 10 张。"""
        total = len(self._file_list)
        current = self._current_index + 1 if total > 0 else 0
        return current, total

    # ---- 缩放操作 ----

    def zoom_in(self) -> float:
        """放大一档。返回新的缩放比例。"""
        new_scale = self._scale + self.ZOOM_STEP
        if new_scale > self.MAX_SCALE:
            new_scale = self.MAX_SCALE
        self._scale = new_scale
        return self._scale

    def zoom_out(self) -> float:
        """缩小一档。返回新的缩放比例。"""
        new_scale = self._scale - self.ZOOM_STEP
        if new_scale < self.MIN_SCALE:
            new_scale = self.MIN_SCALE
        self._scale = new_scale
        return self._scale

    def zoom_to(self, scale: float) -> float:
        """设置缩放比例为指定值（自动钳制到有效范围）。

        Args:
            scale: 目标缩放比例。

        Returns:
            钳制后的实际缩放比例。
        """
        self._scale = max(self.MIN_SCALE, min(self.MAX_SCALE, scale))
        return self._scale

    def zoom_fit(self, view_width: int, view_height: int) -> float:
        """适配窗口缩放 — 使图片完整显示在视口内。"""
        fit_scale = self._model.get_fit_scale(view_width, view_height)
        self._scale = fit_scale
        self._pan_offset_x = 0.0
        self._pan_offset_y = 0.0
        return self._scale

    def zoom_100(self) -> float:
        """恢复 100%（原始大小）。"""
        self._scale = 1.0
        self._pan_offset_x = 0.0
        self._pan_offset_y = 0.0
        return self._scale

    @property
    def scale(self) -> float:
        return self._scale

    # ---- 旋转操作 ----

    def rotate_cw(self) -> None:
        """顺时针旋转 90°。"""
        self._model.rotate_cw()

    def rotate_ccw(self) -> None:
        """逆时针旋转 90°。"""
        self._model.rotate_ccw()

    def rotate_180(self) -> None:
        """旋转 180°。"""
        self._model.rotate_180()

    def reset_rotation(self) -> None:
        """恢复原始方向。"""
        self._model.reload_original()

    # ---- 拖拽平移 ----

    def begin_pan(self) -> None:
        """开始拖拽（记录起始偏移量）。"""
        # 当前偏移量保持不变，View 层负责记录鼠标起始位置
        pass

    def update_pan(self, dx: float, dy: float) -> Tuple[float, float]:
        """更新拖拽偏移。

        Args:
            dx: 鼠标水平移动量（像素）。
            dy: 鼠标垂直移动量（像素）。

        Returns:
            更新后的 (offset_x, offset_y)。
        """
        self._pan_offset_x += dx
        self._pan_offset_y += dy
        return self._pan_offset_x, self._pan_offset_y

    def reset_pan(self) -> None:
        """重置平移偏移。"""
        self._pan_offset_x = 0.0
        self._pan_offset_y = 0.0

    @property
    def pan_offset(self) -> Tuple[float, float]:
        return self._pan_offset_x, self._pan_offset_y

    # ---- 内部辅助 ----

    def _build_file_list(self, path: str) -> None:
        """扫描指定文件所在目录，建立支持格式的图片列表。

        Args:
            path: 当前打开的文件路径。
        """
        directory = os.path.dirname(path)
        if not directory:
            return

        # 收集目录中所有支持的图片文件
        supported = []
        for ext in ImageModel.SUPPORTED_EXTENSIONS:
            pattern = os.path.join(directory, f"*{ext}")
            supported.extend(glob.glob(pattern, recursive=False))
            # 也匹配大写扩展名
            pattern_upper = os.path.join(directory, f"*{ext.upper()}")
            supported.extend(glob.glob(pattern_upper, recursive=False))

        # 去重并排序
        self._file_list = sorted(set(supported))

        # 找到当前文件在列表中的索引
        try:
            self._current_index = self._file_list.index(path)
        except ValueError:
            self._current_index = 0 if self._file_list else -1
