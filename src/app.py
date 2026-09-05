# -*- coding: utf-8 -*-
"""
TBE Client 主窗口框架 (MainWindow)
极简高质感设计：
顶部导航栏仅保留：
- 左侧：品牌 Logo + "TBE Client"
- 中部胶囊导航：【⚙️ 系统设置】 (首页即包含发音引擎一键开关、账户关联与设置)、【🎬 出片历史】
- 右侧快捷键：全屏切换、深浅主题切换、语言切换 (ZH/EN)
"""

import os
import secrets
import webbrowser
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QStackedWidget, QLabel, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QCloseEvent

from .config import config
from .ui.theme import generate_qss
from .ui.view_settings import SettingsView
from .ui.view_footprints import FootprintsView
from .ui.dialog_setup import SetupWizardDialog
from .ui.dialog_doctor import SystemDoctorDialog
from .core.tray import AppTrayIcon
from .core.token_sync_server import TokenSyncServerThread
from .core.auth_api import AuthAPI
from .core.i18n import t, set_language


class MainWindow(QMainWindow):
    """客户端主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app_title"))
        self.resize(config.get("window_width", 980), config.get("window_height", 720))
        self.setMinimumSize(860, 580)

        # 托盘管理
        self.tray = AppTrayIcon(self)
        self.tray.show_window_signal.connect(self._restore_from_tray)
        self.tray.navigate_signal.connect(self._navigate_from_tray)
        self.tray.toggle_compute_signal.connect(self._toggle_tray_compute)
        self.tray.quit_signal.connect(self._force_quit)
        self.tray.show()

        # 本地服务监听 (端口 6502)
        self.token_sync_server = TokenSyncServerThread(port=6502, parent=self)
        self.token_sync_server.token_received_signal.connect(self._on_browser_token_received)
        self.token_sync_server.preview_launched_signal.connect(self._on_preview_launched)
        self.token_sync_server.start()

        self._init_ui()
        self._apply_theme(config.get("theme", "dark") == "dark")

        # 首次配置检测
        if config.get("is_first_run", True):
            self._show_first_run_wizard()

        # 自动启动发音引擎（如果配置了 auto_start_compute）
        if config.get("auto_start_compute", False):
            QTimer.singleShot(800, self.view_settings.start_engine)

    def _show_first_run_wizard(self):
        wizard = SetupWizardDialog(self)
        if wizard.exec():
            self.retranslate_all_ui()

    def _init_ui(self):
        root_widget = QWidget()
        self.setCentralWidget(root_widget)

        root_lay = QVBoxLayout(root_widget)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ── 1. 顶部 Header 全宽导航条 ──
        header_bar = QFrame()
        header_bar.setObjectName("topHeaderBar")
        header_bar.setFixedHeight(60)
        h_lay = QHBoxLayout(header_bar)
        h_lay.setContentsMargins(24, 0, 24, 0)
        h_lay.setSpacing(16)

        # 左侧 Logo 与品牌名
        brand_box = QHBoxLayout()
        brand_box.setSpacing(10)

        lbl_logo = QLabel()
        logo_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(logo_icon_path):
            pix = QPixmap(logo_icon_path).scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
        else:
            lbl_logo.setText("⚡")
            lbl_logo.setStyleSheet("font-size: 22px;")
        brand_box.addWidget(lbl_logo)

        self.lbl_name = QLabel("TBE Client")
        self.lbl_name.setStyleSheet("font-size: 15px; font-weight: 800; letter-spacing: -0.4px;")
        brand_box.addWidget(self.lbl_name)
        h_lay.addLayout(brand_box)

        h_lay.addStretch()

        # 中部：极简双选项胶囊导航 (首页设置 + 出片历史)
        self.main_pill_container = QFrame()
        self.main_pill_container.setObjectName("mainPillContainer")
        p_lay = QHBoxLayout(self.main_pill_container)
        p_lay.setContentsMargins(4, 4, 4, 4)
        p_lay.setSpacing(6)

        self.nav_buttons = {}
        nav_defs = [
            ("settings", "⚙️ 设置与发音"),
            ("footprints", "🎬 出片历史"),
        ]

        for view_key, title_text in nav_defs:
            btn = QPushButton(title_text)
            btn.setProperty("class", "navPill")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, vk=view_key: self.navigate_to(vk))
            p_lay.addWidget(btn)
            self.nav_buttons[view_key] = btn

        h_lay.addWidget(self.main_pill_container)

        h_lay.addStretch()

        # 右侧工具组 (体检 / 全屏 / 明暗主题 / 语言)
        tool_box = QHBoxLayout()
        tool_box.setSpacing(10)

        self.btn_doctor = QPushButton("🩺")
        self.btn_doctor.setProperty("class", "toolCircleBtn")
        self.btn_doctor.setToolTip("系统环境与网络健康体检")
        self.btn_doctor.setCursor(Qt.PointingHandCursor)
        self.btn_doctor.clicked.connect(self._open_doctor)
        tool_box.addWidget(self.btn_doctor)

        self.btn_fullscreen = QPushButton("⛶")
        self.btn_fullscreen.setProperty("class", "toolCircleBtn")
        self.btn_fullscreen.setToolTip("全屏 / 窗口化切换")
        self.btn_fullscreen.setCursor(Qt.PointingHandCursor)
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        tool_box.addWidget(self.btn_fullscreen)

        cur_theme = config.get("theme", "dark")
        self.btn_theme_toggle = QPushButton("☀️" if cur_theme == "dark" else "🌙")
        self.btn_theme_toggle.setProperty("class", "toolCircleBtn")
        self.btn_theme_toggle.setToolTip("切换暗黑 / 明亮主题")
        self.btn_theme_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_theme_toggle.clicked.connect(self._toggle_theme)
        tool_box.addWidget(self.btn_theme_toggle)

        cur_lang = config.get("language", "zh_CN")
        self.btn_lang_toggle = QPushButton("EN" if cur_lang == "zh_CN" else "ZH")
        self.btn_lang_toggle.setProperty("class", "toolPillBtn")
        self.btn_lang_toggle.setToolTip("Switch Language / 切换语言")
        self.btn_lang_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_lang_toggle.clicked.connect(self._toggle_language)
        tool_box.addWidget(self.btn_lang_toggle)

        h_lay.addLayout(tool_box)
        root_lay.addWidget(header_bar)

        # ── 2. 主堆栈工作区 ──
        self.stack = QStackedWidget()

        # Index 0: 首页设置与控制台 (SettingsView)
        self.view_settings = SettingsView()
        self.view_settings.theme_changed_signal.connect(lambda th: self._apply_theme(th == "dark"))
        self.view_settings.language_changed_signal.connect(self._on_language_changed)
        self.view_settings.engine_state_signal.connect(self._on_engine_state_changed)
        # 将浏览器同步按钮重新绑定到 app.py 的带 nonce 版本（安全加固）
        self.view_settings.btn_browser_sync.clicked.disconnect()
        self.view_settings.btn_browser_sync.clicked.connect(self._open_browser_sync)
        self.stack.addWidget(self.view_settings)

        # Index 1: 出片历史 (FootprintsView)
        self.view_footprints = FootprintsView()
        self.stack.addWidget(self.view_footprints)

        root_lay.addWidget(self.stack)

        # 默认选中“设置与发音”
        self.navigate_to("settings")

    def _open_doctor(self):
        diag = SystemDoctorDialog(self)
        diag.exec()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _toggle_theme(self):
        is_dark = config.get("theme", "dark") == "dark"
        new_theme = "light" if is_dark else "dark"
        config.set("theme", new_theme)
        config.save()
        self.btn_theme_toggle.setText("☀️" if new_theme == "dark" else "🌙")
        self._apply_theme(new_theme == "dark")
        self.view_settings.combo_theme.blockSignals(True)
        self.view_settings.combo_theme.setCurrentIndex(0 if new_theme == "dark" else 1)
        self.view_settings.combo_theme.blockSignals(False)

    def _toggle_language(self):
        cur_lang = config.get("language", "zh_CN")
        new_lang = "en_US" if cur_lang == "zh_CN" else "zh_CN"
        set_language(new_lang)
        config.set("language", new_lang)
        config.save()
        self.btn_lang_toggle.setText("EN" if new_lang == "zh_CN" else "ZH")
        self.view_settings.combo_lang.blockSignals(True)
        self.view_settings.combo_lang.setCurrentIndex(0 if new_lang == "zh_CN" else 1)
        self.view_settings.combo_lang.blockSignals(False)
        self.retranslate_all_ui()

    def _on_engine_state_changed(self, is_running: bool):
        self.tray.update_compute_status(is_running)

    def navigate_to(self, view_key: str):
        mapping = {
            "settings": 0,
            "dashboard": 0,
            "engine": 0,
            "footprints": 1,
        }
        target_idx = mapping.get(view_key, 0)
        self.stack.setCurrentIndex(target_idx)
        active_key = "settings" if target_idx == 0 else "footprints"
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == active_key)

    def _on_language_changed(self, lang_code: str):
        self.btn_lang_toggle.setText("EN" if lang_code == "zh_CN" else "ZH")
        self.retranslate_all_ui()

    def retranslate_all_ui(self):
        is_zh = config.get("language", "zh_CN") == "zh_CN"
        self.setWindowTitle("TheBoringEnglish 桌面客户端" if is_zh else "TheBoringEnglish Client")
        self.nav_buttons["settings"].setText("⚙️ 设置与发音" if is_zh else "⚙️ Settings & Engine")
        self.nav_buttons["footprints"].setText("🎬 出片历史" if is_zh else "🎬 Video History")
        self.view_settings.retranslate_ui()
        self.view_footprints.retranslate_ui()
        self.tray.retranslate_ui()

    def _apply_theme(self, is_dark: bool):
        qss = generate_qss(is_dark)
        self.setStyleSheet(qss)

    def _restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _navigate_from_tray(self, view_key: str):
        self._restore_from_tray()
        self.navigate_to(view_key)

    def _toggle_tray_compute(self):
        self.view_settings.toggle_engine()

    def _open_browser_sync(self):
        """生成一次性 nonce 并传递给浏览器同步页面，加固安全验证"""
        if self.view_settings._sync_in_progress:
            self.view_settings.cancel_browser_sync()
            self.token_sync_server.set_nonce("")
            return

        self.view_settings.start_browser_sync()

        server_url = self.view_settings.input_server.text().strip() or "https://theboringenglish.com"
        if not server_url.startswith("http"):
            server_url = "https://" + server_url
        server_url = server_url.rstrip("/")

        # 生成一次性 nonce 并注册到本地服务
        nonce = secrets.token_urlsafe(16)
        self.token_sync_server.set_nonce(nonce)

        sep = "&" if "?" in server_url else "?"
        url = f"{server_url}/settings{sep}client_port=6502&nonce={nonce}"
        webbrowser.open(url)

    def _on_browser_token_received(self, token: str):
        if not token:
            return
        ok, msg, user_info = AuthAPI.link_with_token(token)
        if ok:
            self.view_settings.input_token.setText(token)
            username = (user_info or {}).get("username", "User")
            self.view_settings.on_sync_success(username)
            if self.tray and self.tray.isVisible():
                self.tray.showMessage("TheBoringEnglish", f"🎉 账户关联成功: {username}", QIcon(), 3000)
        else:
            self.view_settings.on_sync_failed(f"Token 校验失败: {msg}")

    def _on_preview_launched(self, title: str):
        self.view_footprints.load_history()
        if self.tray and self.tray.isVisible():
            self.tray.showMessage("TheBoringEnglish", f"🎬 已调起足迹视频预览: {title}", QIcon(), 3000)

    def _force_quit(self):
        if hasattr(self, "token_sync_server") and self.token_sync_server:
            self.token_sync_server.stop()
            # 等待线程真正结束，确保端口释放
            self.token_sync_server.wait(3000)
        if self.view_settings.is_computing:
            self.view_settings.stop_engine()
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent):
        if config.get("minimize_to_tray", True) and self.tray.isVisible():
            self.hide()
            self.tray.showMessage("TheBoringEnglish", "客户端已最小化至托盘后台运行", QIcon(), 2000)
            event.ignore()
        else:
            self._force_quit()
            event.accept()
