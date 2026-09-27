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

from src.config import get_asset_path
from src.core.single_instance import SingleInstanceManager, activate_window
from src.app import MainWindow


def apply_windows_taskbar_icon(hwnd, ico_path: str):
    """通过 Win32 API 强行将窗口图标注入任务栏与窗口标题栏，确保显示 TBE 图标"""
    if sys.platform != "win32" or not ico_path or not os.path.exists(ico_path):
        return
    try:
        LR_LOADFROMFILE = 0x00000010
        IMAGE_ICON = 1
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1

        # 加载原生大图标与小图标 (32x32 / 16x16)
        h_icon_big = ctypes.windll.user32.LoadImageW(
            None, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE
        )
        h_icon_small = ctypes.windll.user32.LoadImageW(
            None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE
        )
        if h_icon_big:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon_big)
        if h_icon_small:
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon_small)
    except Exception as e:
        print(f"[Icon] Win32 SetIcon fallback failed: {e}")


def main():
    # 1. Windows 任务栏原生图标与分组标识 (AppUserModelID) - 必须在创建 QApplication 前设置
    if sys.platform == "win32":
        try:
            myappid = "theboringenglish.client.desktop.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("TheBoringEnglish Client")
    app.setOrganizationName("TheBoringEnglish")

    # 2. 单例运行检测：如果已有实例正在运行，唤醒已有窗口后当前进程立即退出
    single_instance = SingleInstanceManager()
    if single_instance.is_another_instance_running():
        print("[SingleInstance] 检测到已有客户端正在运行，已唤醒已有窗口，当前实例退出。")
        sys.exit(0)

    # 3. 解析与配置应用全局图标
    icon_path = get_asset_path("icon.ico")
    if not os.path.exists(icon_path):
        icon_path = get_asset_path("icon.png")

    app_icon = None
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    # 4. 创建主窗口
    window = MainWindow()
    if app_icon:
        window.setWindowIcon(app_icon)

    # 5. 绑定单例管理器消息：当后续启动被阻止时，将当前主窗口唤醒并置顶
    single_instance.message_received.connect(lambda msg: activate_window(window))
    app.aboutToQuit.connect(single_instance.cleanup)

    window.show()

    # 6. Windows 原生任务栏图标注入
    if icon_path and icon_path.endswith(".ico") and os.path.exists(icon_path):
        apply_windows_taskbar_icon(int(window.winId()), icon_path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

