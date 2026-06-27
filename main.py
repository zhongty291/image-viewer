"""
main.py — 图片查看器程序入口

启动方式：
    python main.py
"""

import sys
import os

# 确保项目根目录在 Python 搜索路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.view import ImageViewerApp


def main():
    """启动图片查看器应用程序。"""
    app = ImageViewerApp()
    app.run()


if __name__ == "__main__":
    main()
