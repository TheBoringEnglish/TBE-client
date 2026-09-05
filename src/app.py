# -*- coding: utf-8 -*-
"""
TBE Client 主窗口框架 (MainWindow)
大厂级流线型设计：左侧现代侧边栏导航 + 右侧多功能工作区堆叠切换 + 系统托盘后台挂机。
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QCloseEvent

from .config import config
from .ui.theme import generate_qss
from .ui.view_dashboard import DashboardView
from .ui.view_tts import TTSView
from .ui.view_footprints import FootprintsView
from .ui.view_compute import ComputeView
from .ui.view_settings import SettingsView
from .core.tray import AppTrayIcon


class MainWindow(QMainWindow):
    """客户端主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TheBoringEnglish Desktop Client")
        self.resize(config.get("window_width", 1180), config.get("window_height", 780))
        self.setMinimumSize(960, 640)

        # 托盘管理
        self.tray = AppTrayIcon(self)
        self.tray.show_window_signal.connect(self._restore_from_tray)
        self.tray.toggle_compute_signal.connect(self._toggle_tray_compute)
        self.tray.quit_signal.connect(self._force_quit)
        self.tray.show()

        self._init_ui()
        self._apply_theme(config.get("theme", "dark") == "dark")

    def _init_ui(self):
        root_widget = QWidget()
        self.setCentralWidget(root_widget)

        root_lay = QHBoxLayout(root_widget)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ── 1. 左侧现代化侧边栏 ──
        sidebar = QFrame()
        sidebar.setObjectName("sidebarContainer")
        sidebar.setFixedWidth(220)
        s_lay = QVBoxLayout(sidebar)
        s_lay.setContentsMargins(14, 20, 14, 20)
        s_lay.setSpacing(8)

        # 品牌 Logo 标题
        brand_box = QHBoxLayout()
        brand_box.setSpacing(10)
        lbl_logo = QLabel("⚡")
        lbl_logo.setStyleSheet("font-size: 22px;")
        brand_box.addWidget(lbl_logo)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(2)
        lbl_name = QLabel("TBE Client")
        lbl_name.setStyleSheet("font-size: 16px; font-weight: 700; color: #F1F5F9; letter-spacing: -0.3px;")
        lbl_sub = QLabel("本地算力与发音端")
        lbl_sub.setStyleSheet("font-size: 11px; color: #94A3B8;")
        brand_text.addWidget(lbl_name)
        brand_text.addWidget(lbl_sub)
        brand_box.addLayout(brand_text)
        brand_box.addStretch()
        s_lay.addLayout(brand_box)
        s_lay.addSpacing(16)

        # 导航按钮组
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "🏠  概览仪表盘"),
            ("tts", "🎙️  本地发音工坊"),
            ("footprints", "👣  足迹与视频"),
            ("compute", "⚡  分布式算力"),
            ("settings", "⚙️  设置与管理"),
        ]

        for view_key, title in nav_items:
            btn = QPushButton(title)
            btn.setProperty("class", "navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, vk=view_key: self.navigate_to(vk))
            s_lay.addWidget(btn)
            self.nav_buttons[view_key] = btn

        s_lay.addStretch()

        # 侧边栏底部版本与状态卡片
        user_card = QFrame()
        user_card.setProperty("class", "card")
        uc_lay = QVBoxLayout(user_card)
        uc_lay.setContentsMargins(12, 10, 12, 10)
        uc_lay.setSpacing(4)

        lbl_user = QLabel("TheBoringEnglish")
        lbl_user.setStyleSheet("font-size: 12px; font-weight: 600; color: #F1F5F9;")
        lbl_ver = QLabel("v1.0.0 Public Release")
        lbl_ver.setStyleSheet("font-size: 11px; color: #64748B;")
        uc_lay.addWidget(lbl_user)
        uc_lay.addWidget(lbl_ver)
        s_lay.addWidget(user_card)

        root_lay.addWidget(sidebar)

        # ── 2. 右侧主工作区堆栈 ──
        self.stack = QStackedWidget()

        self.view_dashboard = DashboardView()
        self.view_dashboard.navigate_signal.connect(self.navigate_to)
        self.stack.addWidget(self.view_dashboard)

        self.view_tts = TTSView()
        self.stack.addWidget(self.view_tts)

        self.view_footprints = FootprintsView()
        self.stack.addWidget(self.view_footprints)

        self.view_compute = ComputeView()
        self.stack.addWidget(self.view_compute)

        self.view_settings = SettingsView()
        self.view_settings.theme_changed_signal.connect(lambda th: self._apply_theme(th == "dark"))
        self.stack.addWidget(self.view_settings)

        root_lay.addWidget(self.stack)

        # 默认选中仪表盘
        self.navigate_to("dashboard")

    def navigate_to(self, view_key: str):
        """路由跳转"""
        mapping = {
            "dashboard": (0, self.view_dashboard),
            "tts": (1, self.view_tts),
            "footprints": (2, self.view_footprints),
            "compute": (3, self.view_compute),
            "settings": (4, self.view_settings),
        }

        if view_key in mapping:
            idx, widget = mapping[view_key]
            self.stack.setCurrentIndex(idx)
            for k, btn in self.nav_buttons.items():
                btn.setChecked(k == view_key)

    def _apply_theme(self, is_dark: bool):
        qss = generate_qss(is_dark)
        self.setStyleSheet(qss)

    def _restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _toggle_tray_compute(self):
        self.view_compute.toggle_compute()
        self.tray.update_compute_status(self.view_compute.is_computing)

    def _force_quit(self):
        if self.view_compute.is_computing:
            self.view_compute.stop_compute()
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent):
        """关闭事件拦截：根据设置判断是否最小化到托盘"""
        if config.get("minimize_to_tray", True) and self.tray.isVisible():
            self.hide()
            self.tray.showMessage(
                "TBE Client 仍在后台运行",
                "客户端已最小化至系统托盘，点击托盘图标可随时唤回窗口。",
                QIcon(),
                2000
            )
            event.ignore()
        else:
            self._force_quit()
            event.accept()
