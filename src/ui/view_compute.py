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
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import Qt, QTimer, Signal

from .components.badge import StatusBadge
from .components.stat_card import StatCard
from ..core.ws_worker import ComputeWorkerThread
from ..core.i18n import t
from ..config import config


class ComputeView(QWidget):
    """本地发音引擎控制台视图"""

    state_changed_signal = Signal(bool, int)  # (is_running, completed_count)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker: ComputeWorkerThread = None
        self.is_computing = False
        self.start_timestamp = 0
        self.completed_count = 0

        self._init_ui()

        # 运行计时器
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

        self.lbl_title = QLabel(t("engine_title"))
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: 700; letter-spacing: -0.4px;")
        header_text.addWidget(self.lbl_title)

        self.lbl_subtitle = QLabel(t("engine_sub"))
        self.lbl_subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")
        header_text.addWidget(self.lbl_subtitle)
        top_bar.addLayout(header_text)
        top_bar.addStretch()

        self.badge_status = StatusBadge(t("engine_stopped"), "default")
        top_bar.addWidget(self.badge_status)

        # 核心发音引擎开关按钮
        self.btn_toggle = QPushButton(t("engine_start"))
        self.btn_toggle.setProperty("class", "btnPrimary")
        self.btn_toggle.setFixedSize(160, 40)
        self.btn_toggle.clicked.connect(self.toggle_compute)
        top_bar.addWidget(self.btn_toggle)

        main_lay.addLayout(top_bar)

        # 核心统计卡片
        stats_grid = QGridLayout()
        stats_grid.setSpacing(14)

        self.card_completed = StatCard(t("stat_today_completed"), "0", "Edge-TTS / Kokoro", "#10B981")
        self.card_uptime = StatCard(t("stat_uptime"), "00:00:00", "7x24h 毫秒级原声发音", "#38BDF8")
        self.card_threads = StatCard(t("stat_threads"), f"{config.get('compute_threads', 2)} Threads", "多线程并发引擎", "#F97316")

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
        self.c_title = QLabel(t("console_title"))
        self.c_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        c_top.addWidget(self.c_title)
        c_top.addStretch()

        self.cb_autoscroll = QCheckBox(t("autoscroll"))
        self.cb_autoscroll.setChecked(True)
        self.cb_autoscroll.setStyleSheet("color: #94A3B8;")
        c_top.addWidget(self.cb_autoscroll)

        self.btn_clear = QPushButton(t("clear_log"))
        self.btn_clear.setProperty("class", "btnSecondary")
        self.btn_clear.clicked.connect(self._clear_logs)
        c_top.addWidget(self.btn_clear)
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

        # 底部后台挂机提示
        self.lbl_bottom_hint = QLabel(t("tray_hint"))
        self.lbl_bottom_hint.setStyleSheet("color: #64748B; font-size: 11.5px;")
        main_lay.addWidget(self.lbl_bottom_hint)

    def retranslate_ui(self):
        """语言切换时动态刷新界面文本"""
        self.lbl_title.setText(t("engine_title"))
        self.lbl_subtitle.setText(t("engine_sub"))
        self.c_title.setText(t("console_title"))
        self.cb_autoscroll.setText(t("autoscroll"))
        self.btn_clear.setText(t("clear_log"))
        self.lbl_bottom_hint.setText(t("tray_hint"))
        if self.is_computing:
            self.btn_toggle.setText(t("engine_stop"))
            self.badge_status.set_status("success", t("engine_running"))
        else:
            self.btn_toggle.setText(t("engine_start"))
            self.badge_status.set_status("default", t("engine_stopped"))
        self.card_completed.lbl_title.setText(t("stat_today_completed"))
        self.card_uptime.lbl_title.setText(t("stat_uptime"))
        self.card_threads.lbl_title.setText(t("stat_threads"))

    def toggle_compute(self):
        """开启或暂停本地发音引擎"""
        if self.is_computing:
            self.stop_compute()
        else:
            self.start_compute()

    def start_compute(self):
        self.is_computing = True
        self.start_timestamp = time.time()
        self.btn_toggle.setText(t("engine_stop"))
        self.badge_status.set_status("warning", "Connecting...")

        self.worker = ComputeWorkerThread()
        self.worker.log_signal.connect(self._append_log)
        self.worker.status_signal.connect(self._on_worker_status)
        self.worker.task_done_signal.connect(self._on_task_done)
        self.worker.start()

        self.timer.start(1000)
        self.state_changed_signal.emit(True, self.completed_count)

    def stop_compute(self):
        self.is_computing = False
        self.btn_toggle.setText(t("engine_start"))
        self.badge_status.set_status("default", t("engine_stopped"))

        if self.worker:
            self.worker.stop()
            self.worker = None

        self.timer.stop()
        self._append_log(f"[{time.strftime('%H:%M:%S')}] 🛑 本地发音引擎已停机")
        self.state_changed_signal.emit(False, self.completed_count)

    def _on_worker_status(self, code: str, text: str):
        if code == "running":
            self.badge_status.set_status("success", t("engine_running"))
        elif code == "connecting":
            self.badge_status.set_status("warning", text)
        elif code == "reconnecting":
            self.badge_status.set_status("danger", text)
        else:
            self.badge_status.set_status("default", text)

    def _on_task_done(self, info: dict):
        total = info.get("total", 0)
        self.completed_count = total
        self.card_completed.update_value(str(total))
        self.state_changed_signal.emit(self.is_computing, self.completed_count)

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
            self.log_console.moveCursor(QTextCursor.MoveOperation.End)

    def _clear_logs(self):
        self.log_console.clear()
