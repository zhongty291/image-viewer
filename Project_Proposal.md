# 项目方案文档（Project Proposal）

## 项目名称
**Image Viewer — 图片查看器**（Windows 桌面应用）

## 项目背景
在日常学习与工作中，用户经常需要浏览和查看图片文件。Windows 自带图片查看器功能较基础，不支持灵活的缩放操作，也没有直接的内置旋转功能和详细元信息查看。本项目的目标是开发一款轻量级的桌面图片查看器，提供比系统自带工具更便捷的浏览体验。

另一方面，随着 AI 辅助编程工具（Claude Code）的广泛应用，开发者需要适应新的开发范式。本项目在实现图片查看器的过程中，系统性地应用 **RDD（职责驱动设计）** 和 **TDD（测试驱动开发）** 方法，并使用 Claude Code 辅助完成代码编写、测试设计和文档撰写，以此来探索 AI 辅助编程在实际项目中的最佳实践方式。

## 功能需求分析

### 核心功能
| 功能模块 | 详细描述 |
|---------|---------|
| 图片浏览 | 支持 JPG、JPEG、PNG、BMP、GIF、WebP 等常见格式 |
| 缩放功能 | 鼠标滚轮缩放，范围 10% ~ 500%，支持适配窗口和 100% 原始大小 |
| 旋转功能 | 顺时针 90°、逆时针 90°、180° 翻转，支持重置旋转 |
| 图片导航 | 同目录下切换上一张/下一张图片，循环浏览 |
| 信息面板 | 显示文件名、分辨率、格式、色彩模式、文件大小、修改时间、EXIF 元数据 |
| 拖拽平移 | 图片放大后支持鼠标拖拽移动可视区域 |

### 非功能需求
- 启动速度快（图片加载 < 1 秒）
- 界面响应流畅，缩放/旋转操作实时反馈
- 采用 MVC 架构成，模块间低耦合高内聚
- 代码通过完整的单元测试

## 技术选型理由

| 技术 | 选型理由 |
|------|---------|
| **Python 3.12** | 跨平台、语法简洁、开发效率高；主流 Windows 设备均可运行 |
| **Tkinter (ttk)** | Python 标准库内置 GUI 框架，无需额外安装，生成原生 Windows 界面 |
| **Pillow (PIL)** | Python 最成熟的图像处理库，支持 30+ 图片格式、EXIF 读写、旋转/缩放操作 |
| **pytest** | 简洁强大的 Python 测试框架，fixture 机制方便管理测试资源 |
| **Claude Code** | AI 辅助编程工具，用于代码生成、测试设计、文档撰写和代码审查 |

## 系统架构设计

### 架构概览
本项目采用 **MVC（Model-View-Controller）** 分层架构：

```
┌──────────────┐       ┌───────────────┐       ┌──────────────┐
│   View 层    │──事件→│  Controller   │──调用→│   Model 层   │
│  (Tkinter)   │◄─更新─│   (协调器)     │◄─数据─│  (Pillow)    │
│              │       │               │       │              │
│ 负责：       │       │ 负责：         │       │ 负责：       │
│ · 窗口管理   │       │ · 事件路由     │       │ · 图片加载   │
│ · 图片渲染   │       │ · 缩放逻辑     │       │ · 旋转操作   │
│ · 事件捕获   │       │ · 导航管理     │       │ · 元信息提取 │
│ · 信息展示   │       │ · 状态协调     │       │ · 缩放计算   │
└──────────────┘       └───────────────┘       └──────────────┘
```

### RDD 职责划分

| 类 | 所属层 | 单一职责 | 协作对象 |
|----|-------|---------|---------|
| `ImageInfo` | Model | 图片元信息数据结构（纯数据，无行为） | 无 |
| `ImageModel` | Model | 图片加载、变换操作、元信息提取 | PIL.Image |
| `ImageController` | Controller | 业务逻辑协调：缩放、旋转、导航、平移 | ImageModel, ImageViewerApp |
| `ImageViewerApp` | View | Tkinter GUI 创建与事件响应 | ImageController |

### 文件结构
```
image-viewer/
├── src/
│   ├── __init__.py
│   ├── model.py            # Model 层：图像数据处理
│   ├── view.py             # View 层：Tkinter UI 界面
│   └── controller.py       # Controller 层：事件协调
├── tests/
│   ├── __init__.py
│   ├── test_model.py       # Model 单元测试（20 个用例）
│   └── test_controller.py  # Controller 单元测试（16 个用例）
├── main.py                 # 程序入口
├── requirements.txt        # 依赖清单
├── Project_Proposal.md     # 本文件
└── Testing_Report.md       # 测试报告
```

## 开发环境说明

| 项目 | 说明 |
|------|------|
| 操作系统 | Windows 11 x64 |
| Python 版本 | Python 3.12.6 |
| IDE | VS Code / PyCharm |
| AI 辅助工具 | Claude Code（Anthropic） |
| 版本控制 | Git + GitHub |
| 依赖库 | Pillow ≥ 9.0.0, pytest ≥ 7.0.0 |

## 开发流程（TDD + AI 辅助）

开发过程遵循 **Red-Green-Refactor** 循环：

```
Step 1: 编写 test_model.py   → 红灯（测试失败，功能未实现）
Step 2: 实现 model.py        → 绿灯（测试全部通过）
Step 3: 编写 test_controller.py → 红灯
Step 4: 实现 controller.py   → 绿灯
Step 5: 实现 view.py         → 手动集成测试
Step 6: 端到端验证 + 截图     → 完整功能确认
```

在每个步骤中，使用 Claude Code 辅助：
- 生成测试框架代码
- 补充边界情况的测试用例
- 审查代码逻辑和安全隐患
- 优化代码结构和注释

## 项目仓库地址
（待创建）

```
https://github.com/zhongty291/image-viewer
```
