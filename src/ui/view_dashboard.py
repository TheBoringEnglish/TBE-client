# -*- coding: utf-8 -*-
"""
概览与系统仪表盘视图 (DashboardView)
展示节点健康状态、关键算力统计、快速操作入口与系统环境自检。
"""

import sys
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from .components.stat_card import StatCard
from .components.badge import StatusBadge
from ..config import config
from ..core.tts_engine import LocalTTSManager
from ..core.remotion_bridge import RemotionBridge


class DashboardView(QWidget):
    """现代仪表盘视图"""

    navigate_signal = Signal(str)  # 页面跳转信号: "tts", "footprints", "compute", "settings"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tts_mgr = LocalTTSManager()
        self.remotion_bridge = RemotionBridge()
        self._init_ui()

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(28, 24, 28, 24)
        main_lay.setSpacing(20)

        # 顶部欢迎与标题栏
        top_bar = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(4)

        title = QLabel("欢迎使用 TheBoringEnglish 本地客户端")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #F1F5F9; letter-spacing: -0.5px;")
        header_text.addWidget(title)

        subtitle = QLabel("本地高质量 AI 神经发音 · 学习足迹一键视频预览 · 分布式算力节点")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")
        header_text.addWidget(subtitle)
        top_bar.addLayout(header_text)
        top_bar.addStretch()

        self.badge_cloud = StatusBadge("云端未连接", "warning")
        top_bar.addWidget(self.badge_cloud)
        main_lay.addLayout(top_bar)

        # 核心指标卡片 (4 列布局)
        stats_grid = QGridLayout()
        stats_grid.setSpacing(14)

        self.card_tts = StatCard("本地发音引擎", "就绪", "Edge-TTS + 离线神经网络", "#10B981")
        self.card_remotion = StatCard("Remotion 视频", "检测中...", "端口 6402 视频服务", "#38BDF8")
        self.card_compute = StatCard("算力挂机状态", "就绪", "点击开启分布式代跑", "#F97316")
        self.card_footprints = StatCard("学习足迹", "3 条精选", "本地示例就绪，可一键出片", "#A855F7")

        stats_grid.addWidget(self.card_tts, 0, 0)
        stats_grid.addWidget(self.card_remotion, 0, 1)
        stats_grid.addWidget(self.card_compute, 0, 2)
        stats_grid.addWidget(self.card_footprints, 0, 3)
        main_lay.addLayout(stats_grid)

        # 快速入口区 (Quick Actions)
        quick_frame = QFrame()
        quick_frame.setProperty("class", "card")
        q_lay = QVBoxLayout(quick_frame)
        q_lay.setContentsMargins(20, 18, 20, 18)
        q_lay.setSpacing(14)

        q_title = QLabel("🚀 核心功能快捷入口")
        q_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #F1F5F9;")
        q_lay.addWidget(q_title)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(12)

        btn_go_tts = QPushButton("🎙️ 进入本地发音工坊")
        btn_go_tts.setProperty("class", "btnPrimary")
        btn_go_tts.clicked.connect(lambda: self.navigate_signal.emit("tts"))
        actions_row.addWidget(btn_go_tts)

        btn_go_fp = QPushButton("🎬 浏览足迹并一键预览视频")
        btn_go_fp.setProperty("class", "btnSecondary")
        btn_go_fp.clicked.connect(lambda: self.navigate_signal.emit("footprints"))
        actions_row.addWidget(btn_go_fp)

        btn_go_compute = QPushButton("⚡ 开启算力挂机代跑")
        btn_go_compute.setProperty("class", "btnSecondary")
        btn_go_compute.clicked.connect(lambda: self.navigate_signal.emit("compute"))
        actions_row.addWidget(btn_go_compute)

        actions_row.addStretch()
        q_lay.addLayout(actions_row)
        main_lay.addWidget(quick_frame)

        # 系统环境自检表格卡片
        env_frame = QFrame()
        env_frame.setProperty("class", "card")
        e_lay = QVBoxLayout(env_frame)
        e_lay.setContentsMargins(20, 18, 20, 18)
        e_lay.setSpacing(12)

        e_title_row = QHBoxLayout()
        e_title = QLabel("🔍 本地运行环境诊断与组件自检")
        e_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #F1F5F9;")
        e_title_row.addWidget(e_title)
        e_title_row.addStretch()

        btn_refresh = QPushButton("🔄 重新检测")
        btn_refresh.setProperty("class", "btnSecondary")
        btn_refresh.clicked.connect(self.refresh_diagnostics)
        e_title_row.addWidget(btn_refresh)
        e_lay.addLayout(e_title_row)

        self.env_content = QVBoxLayout()
        self.env_content.setSpacing(8)
        e_lay.addLayout(self.env_content)

        main_lay.addWidget(env_frame)
        main_lay.addStretch()

        # 初始运行一次环境诊断
        self.refresh_diagnostics()

    def refresh_diagnostics(self):
        """刷新环境状态"""
        # 清空旧的项目
        while self.env_content.count():
            item = self.env_content.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        diagnostics = []

        # 1. Python 环境
        diagnostics.append(("Python 运行环境", f"{sys.version.split()[0]} ({sys.platform})", "success", "正常"))

        # 2. FFmpeg 检测
        has_ffmpeg = bool(shutil.which("ffmpeg"))
        diagnostics.append(("系统 FFmpeg", "已安装 (支持视频剪辑与音频转换)" if has_ffmpeg else "未安装至环境变量", "success" if has_ffmpeg else "warning", "就绪" if has_ffmpeg else "可选"))

        # 3. Kokoro 离线模型
        kokoro_ready, kokoro_msg = self.tts_mgr.is_kokoro_model_ready()
        diagnostics.append(("Kokoro 本地离线模型", kokoro_msg, "success" if kokoro_ready else "info", "已就绪" if kokoro_ready else "待下载"))

        # 4. Remotion 视频服务检测
        remotion_ok, remotion_msg = self.remotion_bridge.check_health()
        self.card_remotion.update_value("在线" if remotion_ok else "未拉起", remotion_msg)
        diagnostics.append(("Remotion 视频渲染服务", remotion_msg, "success" if remotion_ok else "warning", "在线" if remotion_ok else "离线"))

        # 5. 云端授权状态
        is_logged = config.is_logged_in
        if is_logged:
            self.badge_cloud.set_status("success", "云端已认证")
        else:
            self.badge_cloud.set_status("default", "游客/离线模式")

        # 渲染检查列表
        for name, desc, status_type, status_text in diagnostics:
            row = QHBoxLayout()
            lbl_name = QLabel(f"• {name}")
            lbl_name.setStyleSheet("font-weight: 500; color: #F1F5F9; min-width: 170px;")
            row.addWidget(lbl_name)

            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet("color: #94A3B8;")
            row.addWidget(lbl_desc)
            row.addStretch()

            badge = StatusBadge(status_text, status_type)
            row.addWidget(badge)
            self.env_content.addLayout(row)
