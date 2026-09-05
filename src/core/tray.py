import os
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QStyle, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal
from .i18n import t


class AppTrayIcon(QSystemTrayIcon):
    """现代化应用托盘图标与高质感右键上下文菜单"""

    show_window_signal = Signal()
    navigate_signal = Signal(str)
    toggle_compute_signal = Signal()
    quit_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        # 优先读取应用自定义高质感图标，不存在则使用系统图标兜底
        icon = None
        for candidate in ["icon.ico", "icon.png"]:
            p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", candidate)
            if os.path.exists(p):
                icon = QIcon(p)
                break
        if not icon or icon.isNull():
            icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
        
        self.setIcon(icon)
        self.setToolTip("TheBoringEnglish 桌面算力与发音客户端")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #13161F;
                color: #F1F5F9;
                border: 1px solid #272C3D;
                border-radius: 10px;
                padding: 6px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
                font-size: 12.5px;
            }
            QMenu::item {
                padding: 7px 22px;
                border-radius: 6px;
                margin: 1px 0px;
            }
            QMenu::item:selected {
                background-color: #F97316;
                color: #FFFFFF;
                font-weight: 500;
            }
            QMenu::separator {
                height: 1px;
                background-color: #272C3D;
                margin: 5px 8px;
            }
        """)

        # 1. 窗口显隐
        self.act_show = QAction(t("tray_show"), self)
        self.act_show.triggered.connect(self.show_window_signal.emit)
        menu.addAction(self.act_show)

        menu.addSeparator()

        # 2. 核心功能快捷入口
        self.act_settings = QAction("⚙️  系统设置", self)
        self.act_settings.triggered.connect(lambda: self.navigate_signal.emit("settings"))
        menu.addAction(self.act_settings)

        self.act_fp = QAction("🎬  出片历史", self)
        self.act_fp.triggered.connect(lambda: self.navigate_signal.emit("footprints"))
        menu.addAction(self.act_fp)

        menu.addSeparator()

        # 3. 发音引擎状态与启停
        self.act_compute = QAction("⚡  启动发音引擎", self)
        self.act_compute.triggered.connect(self.toggle_compute_signal.emit)
        menu.addAction(self.act_compute)

        menu.addSeparator()

        # 4. 安全退出
        self.act_quit = QAction("🚪  退出程序", self)
        self.act_quit.triggered.connect(self.quit_signal.emit)
        menu.addAction(self.act_quit)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def retranslate_ui(self):
        """刷新托盘菜单语言"""
        is_zh = t("save") == "保存"
        self.act_show.setText("🖥️  显示主界面" if is_zh else "🖥️  Show Window")
        self.act_settings.setText("⚙️  系统设置" if is_zh else "⚙️  Settings")
        self.act_fp.setText("🎬  出片历史" if is_zh else "🎬  Video History")
        self.act_quit.setText("🚪  退出程序" if is_zh else "🚪  Quit")

    def _on_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_window_signal.emit()

    def update_compute_status(self, is_running: bool):
        if is_running:
            self.act_compute.setText("🟢  " + t("engine_running"))
        else:
            self.act_compute.setText("⚡  " + t("engine_stopped"))
