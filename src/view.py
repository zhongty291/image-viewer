"""
view.py — View 层（Tkinter 图形用户界面）

职责（RDD — 视图模式）：
  - 创建和管理所有 Tkinter 窗口组件
  - 捕获用户输入事件（鼠标、键盘、菜单点击）
  - 将事件转发给 Controller 处理
  - 根据 Controller 的状态更新显示（图片渲染、信息面板、状态栏）

不负责：
  - 图片数据处理逻辑（委托给 Model）
  - 缩放/旋转/导航的业务规则（委托给 Controller）
  - 文件 I/O（委托给 Model）
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
from PIL import Image, ImageTk

from src.controller import ImageController


class ImageViewerApp:
    """图片查看器主窗口 — View 层。

    设计要点：
    1. View 持有 Controller 的引用，所有用户操作通过 Controller 方法调用。
    2. View 不直接操作 Model，不直接修改 Controller 的内部状态。
    3. UI 布局使用 ttk 组件以获得 Windows 原生外观。
    """

    # 窗口默认尺寸
    DEFAULT_WIDTH = 1100
    DEFAULT_HEIGHT = 700
    # 信息面板宽度
    INFO_PANEL_WIDTH = 240
    # Canvas 背景色
    CANVAS_BG = "#2d2d2d"

    def __init__(self):
        """初始化 View 层：创建窗口和所有 UI 组件。"""
        # ---- 创建 Controller ----
        self._controller = ImageController()
        self._controller.set_view(self)

        # ---- 创建主窗口 ----
        self._root = tk.Tk()
        self._root.title("Image Viewer — 图片查看器")
        self._root.geometry(f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}")
        self._root.minsize(600, 400)

        # ---- 变量绑定 ----
        self._photo_ref = None  # 持有 PhotoImage 引用（防止 Python GC 回收导致图片不显示）

        # 拖拽状态
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False

        # ---- 构建 UI ----
        self._create_menu_bar()
        self._create_main_layout()
        self._create_status_bar()

        # ---- 绑定快捷键 ----
        self._bind_shortcuts()

    # ============================================================
    # 菜单栏
    # ============================================================

    def _create_menu_bar(self):
        """创建菜单栏。"""
        menubar = tk.Menu(self._root)
        self._root.config(menu=menubar)

        # ---- 文件菜单 ----
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="打开图片...\tCtrl+O", command=self._on_open_file)
        file_menu.add_command(label="打开文件夹...\tCtrl+D", command=self._on_open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="上一张\t←", command=self._on_prev_image)
        file_menu.add_command(label="下一张\t→", command=self._on_next_image)
        file_menu.add_separator()
        file_menu.add_command(label="退出\tAlt+F4", command=self._root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        # ---- 视图菜单 ----
        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="放大\tCtrl++", command=self._on_zoom_in)
        view_menu.add_command(label="缩小\tCtrl+-", command=self._on_zoom_out)
        view_menu.add_command(label="原始大小\tCtrl+0", command=self._on_zoom_100)
        view_menu.add_command(label="适配窗口\tCtrl+9", command=self._on_zoom_fit)
        menubar.add_cascade(label="视图", menu=view_menu)

        # ---- 旋转菜单 ----
        rotate_menu = tk.Menu(menubar, tearoff=False)
        rotate_menu.add_command(label="顺时针旋转 90°\tCtrl+R", command=self._on_rotate_cw)
        rotate_menu.add_command(label="逆时针旋转 90°\tCtrl+L", command=self._on_rotate_ccw)
        rotate_menu.add_command(label="旋转 180°", command=self._on_rotate_180)
        rotate_menu.add_separator()
        rotate_menu.add_command(label="重置旋转", command=self._on_reset_rotation)
        menubar.add_cascade(label="旋转", menu=rotate_menu)

        # ---- 帮助菜单 ----
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="关于", command=self._on_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

    # ============================================================
    # 主布局
    # ============================================================

    def _create_main_layout(self):
        """创建主布局：工具栏 + 画布 + 信息面板。"""
        # 顶部工具栏
        self._create_toolbar()

        # 主内容区（水平分割：Canvas 左侧 + 信息面板右侧）
        main_frame = ttk.Frame(self._root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：图片显示 Canvas
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(
            canvas_frame,
            bg=self.CANVAS_BG,
            cursor="crosshair",
            highlightthickness=0,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # 绑定 Canvas 事件
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)       # Windows 滚轮
        self._canvas.bind("<Button-4>", self._on_mousewheel_up)      # Linux 滚轮上
        self._canvas.bind("<Button-5>", self._on_mousewheel_down)    # Linux 滚轮下
        self._canvas.bind("<ButtonPress-1>", self._on_mouse_press)   # 鼠标按下
        self._canvas.bind("<B1-Motion>", self._on_mouse_drag)        # 鼠标拖拽
        self._canvas.bind("<ButtonRelease-1>", self._on_mouse_release)  # 鼠标释放
        self._canvas.bind("<Configure>", self._on_canvas_resize)     # Canvas 大小变化

        # 右侧：信息面板
        self._create_info_panel(main_frame)

    def _create_toolbar(self):
        """创建顶部工具栏。"""
        toolbar = ttk.Frame(self._root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # 文件操作
        ttk.Button(toolbar, text="📂 打开", command=self._on_open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="◀ 上一张", command=self._on_prev_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="▶ 下一张", command=self._on_next_image).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=2)

        # 缩放
        ttk.Button(toolbar, text="🔍- 缩小", command=self._on_zoom_out).pack(side=tk.LEFT, padx=2)
        self._scale_label = ttk.Label(toolbar, text="100%", width=6, anchor=tk.CENTER)
        self._scale_label.pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍+ 放大", command=self._on_zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="适应", command=self._on_zoom_fit).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="1:1", command=self._on_zoom_100).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=2)

        # 旋转
        ttk.Button(toolbar, text="↻ 左转90°", command=self._on_rotate_ccw).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="↺ 右转90°", command=self._on_rotate_cw).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="↔ 180°", command=self._on_rotate_180).pack(side=tk.LEFT, padx=2)

    def _create_info_panel(self, parent):
        """创建右侧信息面板。"""
        panel = ttk.LabelFrame(parent, text="图片信息", width=self.INFO_PANEL_WIDTH)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=4, pady=4)
        panel.pack_propagate(False)  # 固定宽度

        # 使用 Text 组件展示信息（只读模式，模拟信息面板）
        self._info_text = tk.Text(
            panel,
            width=28,
            height=24,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#f5f5f5",
            relief=tk.FLAT,
            font=("Microsoft YaHei UI", 9),
        )
        self._info_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 配置文本标签样式
        self._info_text.tag_configure("label", foreground="#666666", font=("Microsoft YaHei UI", 9))
        self._info_text.tag_configure("value", foreground="#1a1a1a", font=("Microsoft YaHei UI", 9, "bold"))
        self._info_text.tag_configure("heading", foreground="#333333", font=("Microsoft YaHei UI", 10, "bold"))

    # ============================================================
    # 状态栏
    # ============================================================

    def _create_status_bar(self):
        """创建底部状态栏。"""
        status_frame = ttk.Frame(self._root, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self._status_label = ttk.Label(status_frame, text="就绪 — 请打开一张图片")
        self._status_label.pack(side=tk.LEFT, padx=8, pady=2)

        self._nav_label = ttk.Label(status_frame, text="")
        self._nav_label.pack(side=tk.RIGHT, padx=8, pady=2)

    # ============================================================
    # 事件处理 — 文件操作
    # ============================================================

    def _on_open_file(self):
        """处理「打开图片」事件。"""
        filetypes = [
            ("所有支持的图片", "*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.webp"),
            ("JPEG 图片", "*.jpg;*.jpeg"),
            ("PNG 图片", "*.png"),
            ("BMP 图片", "*.bmp"),
            ("GIF 图片", "*.gif"),
            ("所有文件", "*.*"),
        ]
        path = filedialog.askopenfilename(title="选择图片", filetypes=filetypes)
        if not path:
            return  # 用户取消

        info = self._controller.open_file(path)
        if info is not None:
            self._update_display()

    def _on_open_folder(self):
        """处理「打开文件夹」事件。"""
        directory = filedialog.askdirectory(title="选择图片目录")
        if not directory:
            return

        # 在目录中查找第一张支持的图片
        import os
        from src.model import ImageModel
        for entry in sorted(os.listdir(directory)):
            full_path = os.path.join(directory, entry)
            if os.path.isfile(full_path) and ImageModel.is_supported(full_path):
                info = self._controller.open_file(full_path)
                if info is not None:
                    self._update_display()
                    return

        messagebox.showinfo("提示", "该目录中没有找到支持的图片文件。")

    def _on_next_image(self):
        """切换到下一张图片。"""
        info = self._controller.open_next()
        if info is not None:
            self._update_display()

    def _on_prev_image(self):
        """切换到上一张图片。"""
        info = self._controller.open_prev()
        if info is not None:
            self._update_display()

    # ============================================================
    # 事件处理 — 缩放
    # ============================================================

    def _on_zoom_in(self):
        self._controller.zoom_in()
        self._update_display()

    def _on_zoom_out(self):
        self._controller.zoom_out()
        self._update_display()

    def _on_zoom_fit(self):
        self._controller.zoom_fit(self._canvas.winfo_width(), self._canvas.winfo_height())
        self._update_display()

    def _on_zoom_100(self):
        self._controller.zoom_100()
        self._update_display()

    def _on_mousewheel(self, event):
        """Windows 鼠标滚轮事件。"""
        if event.delta > 0:
            self._controller.zoom_in()
        else:
            self._controller.zoom_out()
        self._update_display()

    def _on_mousewheel_up(self, event):
        """Linux 滚轮上事件。"""
        self._controller.zoom_in()
        self._update_display()

    def _on_mousewheel_down(self, event):
        """Linux 滚轮下事件。"""
        self._controller.zoom_out()
        self._update_display()

    # ============================================================
    # 事件处理 — 旋转
    # ============================================================

    def _on_rotate_cw(self):
        self._controller.rotate_cw()
        self._update_display()

    def _on_rotate_ccw(self):
        self._controller.rotate_ccw()
        self._update_display()

    def _on_rotate_180(self):
        self._controller.rotate_180()
        self._update_display()

    def _on_reset_rotation(self):
        self._controller.reset_rotation()
        self._update_display()

    # ============================================================
    # 事件处理 — 拖拽平移
    # ============================================================

    def _on_mouse_press(self, event):
        """鼠标按下：记录拖拽起始点。"""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._is_dragging = True
        self._canvas.config(cursor="fleur")  # 移动光标

    def _on_mouse_drag(self, event):
        """鼠标拖拽：计算偏移量并更新画布。"""
        if not self._is_dragging:
            return
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        self._controller.update_pan(dx, dy)
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._render_image()

    def _on_mouse_release(self, event):
        """鼠标释放：结束拖拽。"""
        self._is_dragging = False
        self._canvas.config(cursor="crosshair")

    # ============================================================
    # 事件处理 — Canvas 大小变化
    # ============================================================

    def _on_canvas_resize(self, event):
        """Canvas 尺寸变化时重新适配（如果当前是刚加载的状态）。"""
        # 仅在首次加载或用户触发时适配，避免过于频繁
        pass

    # ============================================================
    # 事件处理 — 其他
    # ============================================================

    def _on_about(self):
        """显示关于对话框。"""
        messagebox.showinfo(
            "关于 Image Viewer",
            "图片查看器 v1.0\n\n"
            "功能：图片浏览、缩放（10%-500%）、旋转、信息查看\n"
            "技术栈：Python + Tkinter + Pillow\n"
            "架构：MVC（Model-View-Controller）\n"
            "开发模式：RDD + TDD"
        )

    # ============================================================
    # 显示更新
    # ============================================================

    def _update_display(self):
        """统一更新显示：图片渲染 + 信息面板 + 状态栏。"""
        self._render_image()
        self._update_info_panel()
        self._update_status_bar()

    def _render_image(self):
        """将当前图片渲染到 Canvas 上。

        核心渲染逻辑：
        1. 从 Model 获取当前 PIL Image
        2. 按 Controller 中的缩放比例计算目标尺寸
        3. 使用 PIL 的 resize 生成缩略图
        4. 转换为 Tkinter PhotoImage 并绘制到 Canvas
        5. 应用拖拽平移偏移
        """
        img = self._controller.model.current_image
        if img is None:
            self._canvas.delete("all")
            self._canvas.create_text(
                self._canvas.winfo_width() // 2,
                self._canvas.winfo_height() // 2,
                text="拖拽图片到此处\n或使用 文件 → 打开图片",
                fill="#888888",
                font=("Microsoft YaHei UI", 14),
                anchor=tk.CENTER,
            )
            return

        canvas_w = self._canvas.winfo_width()
        canvas_h = self._canvas.winfo_height()

        if canvas_w < 2 or canvas_h < 2:
            return  # Canvas 尚未完成布局

        # 计算缩放后的尺寸
        scale = self._controller.scale
        orig_w, orig_h = img.size
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))

        # PIL 缩放图片
        try:
            resized = img.resize((new_w, new_h), Image.LANCZOS)
        except Exception:
            return

        # 转换为 Tkinter PhotoImage
        self._photo_ref = ImageTk.PhotoImage(resized)

        # 计算绘制位置（居中 + 平移偏移）
        pan_x, pan_y = self._controller.pan_offset
        draw_x = (canvas_w - new_w) // 2 + pan_x
        draw_y = (canvas_h - new_h) // 2 + pan_y

        # 绘制到 Canvas
        self._canvas.delete("all")
        self._canvas.create_image(draw_x, draw_y, anchor=tk.NW, image=self._photo_ref)

    def _update_info_panel(self):
        """更新右侧信息面板。"""
        info = self._controller.model.get_info()

        # 启用编辑状态
        self._info_text.config(state=tk.NORMAL)
        self._info_text.delete("1.0", tk.END)

        if not info.filename:
            self._info_text.insert(tk.END, "未加载图片", "heading")
            self._info_text.config(state=tk.DISABLED)
            return

        # 构建信息内容
        lines = [
            ("heading", "📷 基本属性\n"),
            ("label", "文件名："), ("value", f"{info.filename}\n"),
            ("label", "格式：  "), ("value", f"{info.format}\n"),
            ("label", "色彩模式："), ("value", f"{info.mode}\n"),
            ("label", "分辨率："), ("value", f"{info.width} × {info.height} px\n"),
            ("label", "文件大小："), ("value", f"{info.file_size}\n"),
            ("separator", "\n"),
            ("heading", "📁 文件信息\n"),
            ("label", "修改时间："), ("value", f"{info.modified_time}\n"),
            ("label", "路径："), ("value", f"{info.filepath}\n"),
        ]

        # 如果有 EXIF 数据，追加显示
        if info.exif:
            lines.append(("separator", "\n"))
            lines.append(("heading", "📸 EXIF 信息\n"))
            for key, val in info.exif.items():
                # 只显示简短的 EXIF 值
                val_str = str(val)
                if len(val_str) > 40:
                    val_str = val_str[:37] + "..."
                lines.append(("label", f"{key}："))
                lines.append(("value", f"{val_str}\n"))

        for tag, text in lines:
            if tag == "separator":
                self._info_text.insert(tk.END, text)
            else:
                self._info_text.insert(tk.END, text, tag)

        self._info_text.config(state=tk.DISABLED)

    def _update_status_bar(self):
        """更新底部状态栏。"""
        model = self._controller.model
        if not model.is_loaded():
            self._status_label.config(text="就绪 — 请打开一张图片")
            self._nav_label.config(text="")
            return

        # 缩放比例
        scale_pct = int(self._controller.scale * 100)
        self._scale_label.config(text=f"{scale_pct}%")

        # 导航信息
        current, total = self._controller.get_navigation_info()
        if total > 0:
            self._nav_label.config(text=f"图片 {current} / {total}")

        # 状态信息
        info = model.get_info()
        rotation = model.rotation
        rot_text = f" | 旋转: {rotation}°" if rotation != 0 else ""
        self._status_label.config(
            text=f"{info.filename} | {info.width}×{info.height} | {scale_pct}%{rot_text}"
        )

    # ============================================================
    # 快捷键绑定
    # ============================================================

    def _bind_shortcuts(self):
        """绑定键盘快捷键。"""
        self._root.bind("<Control-o>", lambda e: self._on_open_file())
        self._root.bind("<Control-O>", lambda e: self._on_open_file())
        self._root.bind("<Control-d>", lambda e: self._on_open_folder())
        self._root.bind("<Control-D>", lambda e: self._on_open_folder())
        self._root.bind("<Control-plus>", lambda e: self._on_zoom_in())
        self._root.bind("<Control-equal>", lambda e: self._on_zoom_in())  # Ctrl+= 等价 Ctrl++
        self._root.bind("<Control-minus>", lambda e: self._on_zoom_out())
        self._root.bind("<Control-0>", lambda e: self._on_zoom_100())
        self._root.bind("<Control-9>", lambda e: self._on_zoom_fit())
        self._root.bind("<Control-r>", lambda e: self._on_rotate_cw())
        self._root.bind("<Control-R>", lambda e: self._on_rotate_cw())
        self._root.bind("<Control-l>", lambda e: self._on_rotate_ccw())
        self._root.bind("<Control-L>", lambda e: self._on_rotate_ccw())
        self._root.bind("<Left>", lambda e: self._on_prev_image())
        self._root.bind("<Right>", lambda e: self._on_next_image())

    # ============================================================
    # 公共接口
    # ============================================================

    def show_error(self, message: str):
        """显示错误对话框（供 Controller 调用）。"""
        messagebox.showerror("错误", message)

    def run(self):
        """启动主事件循环。"""
        self._root.mainloop()
