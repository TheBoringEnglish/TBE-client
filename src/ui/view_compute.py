# -*- coding: utf-8 -*-
"""
分布式算力节点与挂机代跑视图 (ComputeView)
支持一键开启本地算力代跑、实时控制台日志滚动、节点任务吞吐统计与后台静默挂机。
"""

import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QPlainTextEdit, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, QTimer

from .components.badge import StatusBadge
from .components.stat_card import StatCard
from ..core.ws_worker import ComputeWorkerThread
from ..config import config


class ComputeView(QWidget):
    """算力挂机代跑视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: ComputeWorkerThread = None
        self.is_computing = False
        self.start_timestamp = 0

        self._init_ui()

        # 挂机计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_uptime)

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(28, 24, 28, 24)
        main_lay.setSpacing(16)

        # 顶部标题栏
        top_bar = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(4)

        title = QLabel("⚡ 分布式算力节点 (Compute Node)")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #F1F5F9;")
        header_text.addWidget(title)

        subtitle = QLabel("利用闲置显卡/CPU 算力参与本地或社区 TTS 发音代跑，积累贡献值并享受极速体验")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")
        header_text.addWidget(subtitle)
        top_bar.addLayout(header_text)
        top_bar.addStretch()

        self.badge_status = StatusBadge("未启动", "default")
        top_bar.addWidget(self.badge_status)

        # 核心算力开关按钮
        self.btn_toggle = QPushButton("▶ 开启算力代跑")
        self.btn_toggle.setProperty("class", "btnPrimary")
        self.btn_toggle.setFixedSize(150, 38)
        self.btn_toggle.clicked.connect(self.toggle_compute)
        top_bar.addWidget(self.btn_toggle)

        main_lay.addLayout(top_bar)

        # 核心统计卡片
        stats_grid = QGridLayout()
        stats_grid.setSpacing(14)

        self.card_completed = StatCard("今日完成任务", "0", "TTS 音频生成与切片", "#10B981")
        self.card_uptime = StatCard("本次在线时长", "00:00:00", "连续稳定挂机", "#38BDF8")
        self.card_threads = StatCard("计算并发度", f"{config.get('compute_threads', 2)} 线程", "可在设置中调整资源分配", "#F97316")

        stats_grid.addWidget(self.card_completed, 0, 0)
        stats_grid.addWidget(self.card_uptime, 0, 1)
        stats_grid.addWidget(self.card_threads, 0, 2)
        main_lay.addLayout(stats_grid)

        # 实时终端日志卡片
        console_frame = QFrame()
        console_frame.setProperty("class", "card")
        c_lay = QVBoxLayout(console_frame)
        c_lay.setContentsMargins(16, 14, 16, 14)
        c_lay.setSpacing(10)

        c_top = QHBoxLayout()
        c_title = QLabel("📋 算力任务分发实时流水日志")
        c_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #F1F5F9;")
        c_top.addWidget(c_title)
        c_top.addStretch()

        self.cb_autoscroll = QCheckBox("自动滚屏")
        self.cb_autoscroll.setChecked(True)
        self.cb_autoscroll.setStyleSheet("color: #94A3B8;")
        c_top.addWidget(self.cb_autoscroll)

        btn_clear = QPushButton("清空日志")
        btn_clear.setProperty("class", "btnSecondary")
        btn_clear.clicked.connect(self._clear_logs)
        c_top.addWidget(btn_clear)
        c_lay.addLayout(c_top)

        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #080A0E;
                color: #38BDF8;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #1E2330;
                line-height: 1.4;
            }
        """)
        c_lay.addWidget(self.log_console)
        main_lay.addWidget(console_frame)

        # 底部挂机提示
        bottom_hint = QLabel("💡 提示：开启后您可以直接最小化本软件，客户端将在系统托盘后台静默运行，不影响您的日常办公。")
        bottom_hint.setStyleSheet("color: #64748B; font-size: 11.5px;")
        main_lay.addWidget(bottom_hint)

    def toggle_compute(self):
        """开启或暂停算力挂机"""
        if self.is_computing:
            self.stop_compute()
        else:
            self.start_compute()

    def start_compute(self):
        self.is_computing = True
        self.start_timestamp = time.time()
        self.btn_toggle.setText("⏸ 停止算力代跑")
        self.badge_status.set_status("warning", "连接中...")

        self.worker = ComputeWorkerThread()
        self.worker.log_signal.connect(self._append_log)
        self.worker.status_signal.connect(self._on_worker_status)
        self.worker.task_done_signal.connect(self._on_task_done)
        self.worker.start()

        self.timer.start(1000)

    def stop_compute(self):
        self.is_computing = False
        self.btn_toggle.setText("▶ 开启算力代跑")
        self.badge_status.set_status("default", "已停止")

        if self.worker:
            self.worker.stop()
            self.worker = None

        self.timer.stop()
        self._append_log(f"[{time.strftime('%H:%M:%S')}] 🛑 算力节点已安全停机")

    def _on_worker_status(self, code: str, text: str):
        if code == "running":
            self.badge_status.set_status("success", "运行中")
        elif code == "connecting":
            self.badge_status.set_status("warning", "正在连接")
        elif code == "reconnecting":
            self.badge_status.set_status("danger", "重连中")
        else:
            self.badge_status.set_status("default", text)

    def _on_task_done(self, info: dict):
        total = info.get("total", 0)
        self.card_completed.update_value(str(total))

    def _update_uptime(self):
        if not self.is_computing or self.start_timestamp == 0:
            return
        diff = int(time.time() - self.start_timestamp)
        h = diff // 3600
        m = (diff % 3600) // 60
        s = diff % 60
        self.card_uptime.update_value(f"{h:02d}:{m:02d}:{s:02d}")

    def _append_log(self, msg: str):
        self.log_console.appendPlainText(msg)
        if self.cb_autoscroll.isChecked():
            self.log_console.moveCursor(self.log_console.textCursor().End)

    def _clear_logs(self):
        self.log_console.clear()
