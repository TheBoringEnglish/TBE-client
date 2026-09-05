# -*- coding: utf-8 -*-
"""
系统托盘 (System Tray Icon) 与后台挂机支持
"""

from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QStyle, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal


class AppTrayIcon(QSystemTrayIcon):
    """应用托盘图标与后台菜单"""

    show_window_signal = Signal()
    toggle_compute_signal = Signal()
    quit_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        # 默认使用系统应用图标兜底
        icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
        self.setIcon(icon)
        self.setToolTip("TheBoringEnglish 桌面算力与发音客户端")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1A1D24;
                color: #EAECF0;
                border: 1px solid #2D3139;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #F97316;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #2D3139;
                margin: 4px 8px;
            }
        """)

        act_show = QAction("🖥️ 显示主窗口", self)
        act_show.triggered.connect(self.show_window_signal.emit)
        menu.addAction(act_show)

        self.act_compute = QAction("⚡ 算力挂机: 已停止", self)
        self.act_compute.triggered.connect(self.toggle_compute_signal.emit)
        menu.addAction(self.act_compute)

        menu.addSeparator()

        act_quit = QAction("🚪 退出应用", self)
        act_quit.triggered.connect(self.quit_signal.emit)
        menu.addAction(act_quit)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_window_signal.emit()

    def update_compute_status(self, is_running: bool):
        self.act_compute.setText("⚡ 算力挂机: 运行中 (点击暂停)" if is_running else "⚡ 算力挂机: 已暂停 (点击启动)")
