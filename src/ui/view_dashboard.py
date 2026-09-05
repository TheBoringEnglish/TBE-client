# -*- coding: utf-8 -*-
"""
概览与系统仪表盘视图 (DashboardView)
展示节点健康状态、关键算力统计、TheBoringEnglish 官网与 TBE-YouTube 浏览器扩展推荐生态、系统环境自检。
"""

import sys
import shutil
import webbrowser
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from .components.stat_card import StatCard
from .components.badge import StatusBadge
from ..config import config
from ..core.tts_engine import LocalTTSManager
from ..core.remotion_bridge import RemotionBridge
from ..core.video_history import VideoHistoryManager
from ..core.i18n import t


class DashboardView(QWidget):
    """现代仪表盘视图"""

    navigate_signal = Signal(str)  # 页面跳转信号: "engine", "footprints", "settings"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tts_mgr = LocalTTSManager()
        self.remotion_bridge = RemotionBridge()
        self._init_ui()

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(28, 24, 28, 24)
        main_lay.setSpacing(18)

        # 顶部欢迎与标题栏
        top_bar = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(4)

        self.lbl_title = QLabel(t("dash_welcome"))
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: 700; letter-spacing: -0.4px;")
        header_text.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel(t("dash_sub"))
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")
        header_text.addWidget(self.lbl_subtitle)
        top_bar.addLayout(header_text)
        top_bar.addStretch()

        self.badge_cloud = StatusBadge(t("status_cloud_guest"), "default")
        top_bar.addWidget(self.badge_cloud)
        main_lay.addLayout(top_bar)

        # 核心指标卡片 (4 列布局)
        stats_grid = QGridLayout()
        stats_grid.setSpacing(14)

        self.card_tts = StatCard(t("card_engine_title"), t("ready"), t("card_engine_sub"), "#10B981")
        self.card_remotion = StatCard(t("card_remotion_title"), t("card_remotion_val"), t("card_remotion_sub"), "#38BDF8")
        self.card_engine_run = StatCard(t("card_engine_run_title"), t("engine_stopped"), t("stat_today_completed") + ": 0", "#F97316")
        history_count = len(VideoHistoryManager.load_history())
        self.card_footprints = StatCard(t("card_footprints_title"), f"{history_count} 部视频", t("card_footprints_sub"), "#A855F7")

        stats_grid.addWidget(self.card_tts, 0, 0)
        stats_grid.addWidget(self.card_remotion, 0, 1)
        stats_grid.addWidget(self.card_engine_run, 0, 2)
        stats_grid.addWidget(self.card_footprints, 0, 3)
        main_lay.addLayout(stats_grid)

        # ── 平台生态精选推荐卡片 (双列卡片: 官方平台 + YouTube 插件) ──
        eco_grid = QGridLayout()
        eco_grid.setSpacing(14)

        # 1. TheBoringEnglish 官网一键直达卡片
        web_card = QFrame()
        web_card.setProperty("class", "card")
        wc_lay = QVBoxLayout(web_card)
        wc_lay.setContentsMargins(18, 16, 18, 16)
        wc_lay.setSpacing(10)

        self.lbl_wc_title = QLabel(t("promo_web_title"))
        self.lbl_wc_title.setStyleSheet("font-size: 14.5px; font-weight: 700; color: #F97316;")
        wc_lay.addWidget(self.lbl_wc_title)

        self.lbl_wc_desc = QLabel(t("promo_web_desc"))
        self.lbl_wc_desc.setWordWrap(True)
        self.lbl_wc_desc.setStyleSheet("color: #94A3B8; font-size: 12.5px; line-height: 1.4;")
        wc_lay.addWidget(self.lbl_wc_desc)

        wc_lay.addStretch()
        self.btn_open_web = QPushButton(t("btn_open_web"))
        self.btn_open_web.setProperty("class", "btnPrimary")
        self.btn_open_web.clicked.connect(self._open_official_web)
        wc_lay.addWidget(self.btn_open_web)
        eco_grid.addWidget(web_card, 0, 0)

        # 2. TBE-YouTube 浏览器扩展卡片
        yt_card = QFrame()
        yt_card.setProperty("class", "card")
        yc_lay = QVBoxLayout(yt_card)
        yc_lay.setContentsMargins(18, 16, 18, 16)
        yc_lay.setSpacing(10)

        self.lbl_yc_title = QLabel(t("promo_yt_title"))
        self.lbl_yc_title.setStyleSheet("font-size: 14.5px; font-weight: 700; color: #38BDF8;")
        yc_lay.addWidget(self.lbl_yc_title)

        self.lbl_yc_desc = QLabel(t("promo_yt_desc"))
        self.lbl_yc_desc.setWordWrap(True)
        self.lbl_yc_desc.setStyleSheet("color: #94A3B8; font-size: 12.5px; line-height: 1.4;")
        yc_lay.addWidget(self.lbl_yc_desc)

        yc_lay.addStretch()
        self.btn_open_yt = QPushButton(t("btn_open_yt"))
        self.btn_open_yt.setProperty("class", "btnSecondary")
        self.btn_open_yt.clicked.connect(self._open_youtube_ext)
        yc_lay.addWidget(self.btn_open_yt)
        eco_grid.addWidget(yt_card, 0, 1)

        main_lay.addLayout(eco_grid)

        # 系统环境自检表格卡片
        env_frame = QFrame()
        env_frame.setProperty("class", "card")
        e_lay = QVBoxLayout(env_frame)
        e_lay.setContentsMargins(18, 16, 18, 16)
        e_lay.setSpacing(12)

        e_title_row = QHBoxLayout()
        self.lbl_diag_title = QLabel(t("diag_title"))
        self.lbl_diag_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        e_title_row.addWidget(self.lbl_diag_title)
        e_title_row.addStretch()

        self.btn_refresh = QPushButton(t("diag_refresh"))
        self.btn_refresh.setProperty("class", "btnSecondary")
        self.btn_refresh.clicked.connect(self.refresh_diagnostics)
        e_title_row.addWidget(self.btn_refresh)
        e_lay.addLayout(e_title_row)

        self.env_content = QVBoxLayout()
        self.env_content.setSpacing(10)
        e_lay.addLayout(self.env_content)

        main_lay.addWidget(env_frame)
        main_lay.addStretch()

        # 初始运行一次环境诊断
        self.refresh_diagnostics()

    def _open_official_web(self):
        """一键在默认浏览器打开官网"""
        base_url = config.get("server_url", "https://theboringenglish.com")
        webbrowser.open(base_url)

    def _open_youtube_ext(self):
        """一键打开 TBE-YouTube 浏览器扩展介绍或安装主页"""
        base_url = config.get("server_url", "https://theboringenglish.com")
        webbrowser.open(f"{base_url}/extension")

    def retranslate_ui(self):
        """多语言热切换刷新界面"""
        self.lbl_title.setText(t("dash_welcome"))
        self.lbl_subtitle.setText(t("dash_sub"))
        self.lbl_wc_title.setText(t("promo_web_title"))
        self.lbl_wc_desc.setText(t("promo_web_desc"))
        self.btn_open_web.setText(t("btn_open_web"))
        self.lbl_yc_title.setText(t("promo_yt_title"))
        self.lbl_yc_desc.setText(t("promo_yt_desc"))
        self.btn_open_yt.setText(t("btn_open_yt"))
        self.lbl_diag_title.setText(t("diag_title"))
        self.btn_refresh.setText(t("diag_refresh"))
        self.card_tts.update_value(t("ready"), t("card_engine_sub"))
        self.refresh_diagnostics()

    def refresh_diagnostics(self):
        """刷新环境状态"""
        while self.env_content.count():
            item = self.env_content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        diagnostics = []

        # 1. Python 环境
        diagnostics.append(("Python Environment", f"{sys.version.split()[0]} ({sys.platform})", "success", t("ready")))

        # 2. FFmpeg 检测
        has_ffmpeg = bool(shutil.which("ffmpeg"))
        diagnostics.append(("System FFmpeg", "Installed & detected" if has_ffmpeg else "Not found in PATH", "success" if has_ffmpeg else "warning", t("ready") if has_ffmpeg else "Optional"))

        # 3. Kokoro 离线模型
        kokoro_ready, kokoro_msg = self.tts_mgr.is_kokoro_model_ready()
        diagnostics.append(("Kokoro Offline AI Model", kokoro_msg, "success" if kokoro_ready else "info", t("ready") if kokoro_ready else "Pending"))

        # 4. Remotion 视频服务检测
        remotion_ok, remotion_msg = self.remotion_bridge.check_health()
        self.card_remotion.update_value(t("online") if remotion_ok else t("offline"), remotion_msg)
        diagnostics.append(("Remotion Video Bridge", remotion_msg, "success" if remotion_ok else "warning", t("online") if remotion_ok else t("offline")))

        # 更新足迹出片数量
        history_count = len(VideoHistoryManager.load_history())
        self.card_footprints.update_value(f"{history_count} 部视频", t("card_footprints_sub"))

        # 5. 云端授权状态
        is_logged = config.is_logged_in
        if is_logged:
            user_info = config.get("user_info") or {}
            vip_mark = " [VIP]" if user_info.get("is_vip") else ""
            self.badge_cloud.set_status("success", f"{t('status_cloud_ok')}{vip_mark}")
        else:
            self.badge_cloud.set_status("default", t("status_cloud_guest"))

        # 渲染检查列表
        for name, desc, status_type, status_text in diagnostics:
            row = QHBoxLayout()
            lbl_name = QLabel(f"• {name}")
            lbl_name.setStyleSheet("font-weight: 500; min-width: 170px;")
            row.addWidget(lbl_name)

            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet("color: #94A3B8;")
            row.addWidget(lbl_desc)
            row.addStretch()

            badge = StatusBadge(status_text, status_type)
            row.addWidget(badge)
            self.env_content.addLayout(row)

