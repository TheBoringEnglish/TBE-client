# -*- coding: utf-8 -*-
"""
TheBoringEnglish 桌面算力与发音客户端 - 主启动入口
"""

import os
import sys

# 确保项目根目录和 src 在 sys.path 中
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CURRENT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.app import MainWindow


def main():
    # Windows 任务栏原生图标与分组标识 (AppUserModelID)
    if sys.platform == "win32":
        try:
            myappid = "theboringenglish.client.desktop.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("TheBoringEnglish Client")
    app.setOrganizationName("TheBoringEnglish")

    # 全局设置应用图标（确保任务栏和右键图标均正常展示）
    icon_path = os.path.join(_PROJECT_ROOT, "assets", "icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(_PROJECT_ROOT, "assets", "icon.png")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
