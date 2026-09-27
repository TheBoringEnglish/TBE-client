# -*- coding: utf-8 -*-
"""
客户端主设置与控制台视图 (SettingsView)
整合发音引擎一键开关、账号关联、发音偏好（引擎/音色/语速）与高级选项。
布局极简紧凑，移除重复的偏好设置卡片（语言/主题改由顶部图标控制）。
"""

import os
import sys
import asyncio
import tempfile
import subprocess
import urllib.request
import webbrowser
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFrame, QFileDialog, QMessageBox, QCheckBox, QComboBox, QProgressBar,
    QScrollArea, QSlider, QTextEdit, QApplication
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer

from .components.badge import StatusBadge
from ..config import config
from ..core.tts_engine import LocalTTSManager, SUPPORTED_VOICES
from ..core.auth_api import AuthAPI
from ..core.ws_worker import ComputeWorkerThread
from ..core.i18n import t, set_language


class ModelDownloadWorker(QThread):
    """Kokoro 离线模型后台下载（流式分块，支持取消）"""
    progress_signal = Signal(int, str)
    finished_signal = Signal(bool, str)

    def __init__(self, target_dir: str):
        super().__init__()
        self.target_dir = target_dir
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            import requests as _req
            has_requests = True
        except ImportError:
            has_requests = False

        try:
            os.makedirs(self.target_dir, exist_ok=True)
            files = [
                ("kokoro-v1.0.fp16-gpu.onnx", "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.fp16-gpu.onnx"),
                ("voices-v1.0.bin", "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin")
            ]
            total = len(files)
            for idx, (filename, url) in enumerate(files):
                if self._cancelled:
                    self.finished_signal.emit(False, "下载已取消")
                    return

                dest = os.path.join(self.target_dir, filename)
                self.progress_signal.emit(int((idx / total) * 100), f"正在下载 {filename}...")

                if has_requests:
                    resp = _req.get(url, stream=True, timeout=30)
                    resp.raise_for_status()
                    total_size = int(resp.headers.get("content-length", 0))
                    downloaded = 0
                    with open(dest, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            if self._cancelled:
                                self.finished_signal.emit(False, "下载已取消")
                                return
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    p = int(downloaded / total_size * 100)
                                    fp = int(((idx + p / 100) / total) * 100)
                                    self.progress_signal.emit(fp, f"下载中 {filename}: {p}%")
                else:
                    def reporthook(count, block_size, total_size,
                                   _idx=idx, _fname=filename, _total=total):
                        if total_size > 0:
                            p = int((count * block_size / total_size) * 100)
                            fp = int(((_idx + p / 100) / _total) * 100)
                            self.progress_signal.emit(fp, f"下载中 {_fname}: {p}%")
                    urllib.request.urlretrieve(url, dest, reporthook=reporthook)

            self.progress_signal.emit(100, "下载完成！")
            self.finished_signal.emit(True, "Kokoro 离线模型已就绪！")
        except Exception as e:
            self.finished_signal.emit(False, f"下载失败: {str(e)}")


class TTSPreviewWorker(QThread):
    """TTS 试听后台线程"""
    finished_signal = Signal(bytes, str)

    def __init__(self, text: str, voice_id: str, speed: float):
        super().__init__()
        self.text = text
        self.voice_id = voice_id
        self.speed = speed

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tts = LocalTTSManager()
            audio, err = loop.run_until_complete(
                tts.synthesize(self.text, self.voice_id, self.speed)
            )
            self.finished_signal.emit(audio or b"", err or "")
        except Exception as e:
            self.finished_signal.emit(b"", str(e))
        finally:
            loop.close()


class SettingsView(QWidget):
    """客户端主控台与系统设置"""

    theme_changed_signal = Signal(str)
    language_changed_signal = Signal(str)
    engine_state_signal = Signal(bool)
    auth_state_changed_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_api = AuthAPI()
        self.tts_mgr = LocalTTSManager()
        self.worker = None
        self.is_computing = False
        self.dl_worker = None
        self.tts_preview_worker = None
        self._sync_in_progress = False
        self._sync_countdown = 45
        self._sync_timer = None
        self._init_ui()

    def _init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        content.setFocusPolicy(Qt.ClickFocus)
        lay = QVBoxLayout(content)
        lay.setContentsMargins(14, 10, 14, 12)
        lay.setSpacing(8)

        # ── 1. 顶部标题与快速保存 ──
        top_bar = QHBoxLayout()
        self.lbl_title = QLabel("系统设置")
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; letter-spacing: -0.3px;")
        top_bar.addWidget(self.lbl_title)
        top_bar.addStretch()

        self.btn_save_all = QPushButton("保存")
        self.btn_save_all.setProperty("class", "btnPrimary")
        self.btn_save_all.setCursor(Qt.PointingHandCursor)
        self.btn_save_all.setStyleSheet("padding: 3px 14px; font-size: 12px; height: 26px; border-radius: 13px;")
        self.btn_save_all.clicked.connect(self._save_all_settings)
        top_bar.addWidget(self.btn_save_all)
        lay.addLayout(top_bar)

        # ── 2. 本地发音引擎卡片 ──
        engine_card = QFrame()
        engine_card.setProperty("class", "card")
        ec_lay = QVBoxLayout(engine_card)
        ec_lay.setContentsMargins(14, 10, 14, 10)
        ec_lay.setSpacing(6)

        ec_ctrl = QHBoxLayout()
        ec_ctrl.setSpacing(10)

        ec_info = QVBoxLayout()
        ec_info.setSpacing(2)
        self.lbl_engine_name = QLabel("⚡ 本地发音引擎")
        self.lbl_engine_name.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A;")
        ec_info.addWidget(self.lbl_engine_name)

        self.lbl_engine_desc = QLabel("启用后作为本地算力节点，为浏览器及云端精读提供毫秒级原声发音。")
        self.lbl_engine_desc.setStyleSheet("font-size: 11.5px; color: #475569;")
        ec_info.addWidget(self.lbl_engine_desc)
        ec_ctrl.addLayout(ec_info)
        ec_ctrl.addStretch()

        self.badge_engine = StatusBadge("已停用", "default")
        ec_ctrl.addWidget(self.badge_engine)

        self.btn_engine_toggle = QPushButton("启动")
        self.btn_engine_toggle.setProperty("class", "btnSuccess")
        self.btn_engine_toggle.setFixedSize(64, 26)
        self.btn_engine_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_engine_toggle.clicked.connect(self.toggle_engine)
        ec_ctrl.addWidget(self.btn_engine_toggle)
        ec_lay.addLayout(ec_ctrl)

        # 复选框行（自动启动 + 最小化至托盘）
        cb_row = QHBoxLayout()
        cb_row.setSpacing(16)
        self.cb_auto_start = QCheckBox("自动启动引擎")
        self.cb_auto_start.setChecked(config.get("auto_start_compute", False))
        self.cb_auto_start.setStyleSheet("font-size: 11.5px; color: #334155; font-weight: 500;")
        cb_row.addWidget(self.cb_auto_start)

        self.cb_tray = QCheckBox("关闭时最小化至托盘")
        self.cb_tray.setChecked(config.get("minimize_to_tray", True))
        self.cb_tray.setStyleSheet("font-size: 11.5px; color: #334155; font-weight: 500;")
        cb_row.addWidget(self.cb_tray)
        cb_row.addStretch()
        ec_lay.addLayout(cb_row)

        # 日志折叠
        self.btn_toggle_log = QPushButton("日志 ▶")
        self.btn_toggle_log.setProperty("class", "btnSecondary")
        self.btn_toggle_log.setStyleSheet("text-align: left; padding: 2px 8px; font-size: 11px;")
        self.btn_toggle_log.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_log.clicked.connect(self._toggle_log_panel)
        ec_lay.addWidget(self.btn_toggle_log)

        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.document().setMaximumBlockCount(200)
        self.log_panel.setVisible(False)
        self.log_panel.setFixedHeight(100)
        self.log_panel.setStyleSheet(
            "font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 11px; "
            "background-color: #0F172A; color: #F1F5F9; border-radius: 8px; padding: 6px;"
        )
        self.log_panel.setPlaceholderText("发音引擎启动后，日志将在此实时显示...")
        ec_lay.addWidget(self.log_panel)

        self.lbl_task_count = QLabel("今日已完成发音任务: 0 条")
        self.lbl_task_count.setStyleSheet("font-size: 11px; color: #475569;")
        self.lbl_task_count.setVisible(False)
        ec_lay.addWidget(self.lbl_task_count)

        lay.addWidget(engine_card)

        # ── 3. 账户关联卡片（紧凑高集成） ──
        acc_card = QFrame()
        acc_card.setProperty("class", "card")
        ac_lay = QVBoxLayout(acc_card)
        ac_lay.setContentsMargins(14, 10, 14, 10)
        ac_lay.setSpacing(6)

        acc_header = QHBoxLayout()
        acc_header.setSpacing(8)
        self.lbl_acc_title = QLabel("👤 账户关联")
        self.lbl_acc_title.setStyleSheet("font-size: 13px; font-weight: 700;")
        acc_header.addWidget(self.lbl_acc_title)
        acc_header.addStretch()

        self.badge_acc = StatusBadge("未关联", "default")
        acc_header.addWidget(self.badge_acc)

        self.btn_logout = QPushButton("注销")
        self.btn_logout.setProperty("class", "btnSecondary")
        self.btn_logout.setFixedHeight(24)
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet("padding: 2px 10px; font-size: 11px; border-radius: 12px;")
        self.btn_logout.clicked.connect(self._do_account_logout)
        self.btn_logout.setVisible(False)
        acc_header.addWidget(self.btn_logout)

        ac_lay.addLayout(acc_header)

        self.btn_browser_sync = QPushButton("同步")
        self.btn_browser_sync.setProperty("class", "btnPrimary")
        self.btn_browser_sync.setFixedHeight(30)
        self.btn_browser_sync.setCursor(Qt.PointingHandCursor)
        self.btn_browser_sync.clicked.connect(self._open_browser_sync)
        ac_lay.addWidget(self.btn_browser_sync)

        self.lbl_sync_hint = QLabel()
        self.lbl_sync_hint.setWordWrap(True)
        self.lbl_sync_hint.setVisible(False)
        ac_lay.addWidget(self.lbl_sync_hint)

        self.btn_toggle_manual = QPushButton("手动 ▼")
        self.btn_toggle_manual.setProperty("class", "btnSecondary")
        self.btn_toggle_manual.setStyleSheet(
            "text-align: left; padding: 2px 6px; font-size: 11px; "
            "border: none; background: transparent; color: #94A3B8;"
        )
        self.btn_toggle_manual.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_manual.clicked.connect(self._toggle_manual_frame)
        ac_lay.addWidget(self.btn_toggle_manual)

        self.manual_frame = QFrame()
        self.manual_frame.setVisible(False)
        mf_lay = QHBoxLayout(self.manual_frame)
        mf_lay.setContentsMargins(0, 2, 0, 0)
        mf_lay.setSpacing(6)

        self.input_token = QLineEdit(config.get("token", ""))
        self.input_token.setEchoMode(QLineEdit.Password)
        self.input_token.setPlaceholderText("粘贴 Authorization Token...")
        mf_lay.addWidget(self.input_token)

        self.btn_verify_token = QPushButton("绑定")
        self.btn_verify_token.setProperty("class", "btnSecondary")
        self.btn_verify_token.setCursor(Qt.PointingHandCursor)
        self.btn_verify_token.clicked.connect(self._do_token_link)
        mf_lay.addWidget(self.btn_verify_token)
        ac_lay.addWidget(self.manual_frame)

        lay.addWidget(acc_card)

        # ── 4. 发音偏好卡片（含引擎选择器）──
        tts_card = QFrame()
        tts_card.setProperty("class", "card")
        tc_lay = QVBoxLayout(tts_card)
        tc_lay.setContentsMargins(14, 10, 14, 10)
        tc_lay.setSpacing(6)

        tts_header = QHBoxLayout()
        self.lbl_tts_title = QLabel("🎙️ 发音偏好")
        self.lbl_tts_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #0F172A;")
        tts_header.addWidget(self.lbl_tts_title)
        tts_header.addStretch()
        tc_lay.addLayout(tts_header)

        # 引擎选择行
        engine_row = QHBoxLayout()
        engine_row.setSpacing(8)
        lbl_engine_sel = QLabel("发音引擎:")
        lbl_engine_sel.setStyleSheet("font-size: 12px; color: #475569; font-weight: 600;")
        engine_row.addWidget(lbl_engine_sel)

        saved_engine = config.get("tts_engine", "edge")

        self.btn_engine_edge = QPushButton("Edge-TTS (在线高清)")
        self.btn_engine_edge.setProperty("class", "enginePill")
        self.btn_engine_edge.setCheckable(True)
        self.btn_engine_edge.setCursor(Qt.PointingHandCursor)
        self.btn_engine_edge.setChecked(saved_engine == "edge")
        self.btn_engine_edge.clicked.connect(lambda: self._on_tts_engine_changed("edge"))
        engine_row.addWidget(self.btn_engine_edge)

        self.btn_engine_kokoro = QPushButton("Kokoro (本地离线)")
        self.btn_engine_kokoro.setProperty("class", "enginePill")
        self.btn_engine_kokoro.setCheckable(True)
        self.btn_engine_kokoro.setCursor(Qt.PointingHandCursor)
        self.btn_engine_kokoro.setChecked(saved_engine == "kokoro")
        self.btn_engine_kokoro.clicked.connect(lambda: self._on_tts_engine_changed("kokoro"))
        engine_row.addWidget(self.btn_engine_kokoro)

        engine_row.addStretch()
        tc_lay.addLayout(engine_row)

        # Kokoro 未就绪提示（默认隐藏）
        self.lbl_kokoro_hint = QLabel()
        self.lbl_kokoro_hint.setWordWrap(True)
        self.lbl_kokoro_hint.setStyleSheet("font-size: 11.5px; color: #EA580C; font-weight: 500;")
        self.lbl_kokoro_hint.setVisible(False)
        tc_lay.addWidget(self.lbl_kokoro_hint)

        # 音色选择行
        voice_row = QHBoxLayout()
        voice_row.setSpacing(10)
        lbl_voice = QLabel("音色:")
        lbl_voice.setStyleSheet("font-size: 12px; color: #475569; font-weight: 600;")
        lbl_voice.setFixedWidth(40)
        voice_row.addWidget(lbl_voice)
        self.combo_voice = QComboBox()
        # 禁用滚轮滚动切换，防止浏览时误变音色
        self.combo_voice.wheelEvent = lambda event: event.ignore()
        self.combo_voice.setFocusPolicy(Qt.ClickFocus)
        saved_voice = config.get("tts_voice", "en-US-JennyNeural")
        voice_row.addWidget(self.combo_voice)
        tc_lay.addLayout(voice_row)

        # 初始化音色列表
        self._populate_voices(saved_engine, saved_voice)

        # 语速滑块行
        speed_row = QHBoxLayout()
        speed_row.setSpacing(10)
        lbl_speed = QLabel("语速:")
        lbl_speed.setStyleSheet("font-size: 12px; color: #475569; font-weight: 600;")
        lbl_speed.setFixedWidth(40)
        speed_row.addWidget(lbl_speed)
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setMinimum(50)
        self.slider_speed.setMaximum(200)
        saved_speed = config.get("tts_speed", 1.0)
        self.slider_speed.setValue(int(saved_speed * 100))
        self.slider_speed.setTickPosition(QSlider.TicksBelow)
        self.slider_speed.setTickInterval(25)
        self.slider_speed.valueChanged.connect(self._on_speed_changed)
        speed_row.addWidget(self.slider_speed)
        self.lbl_speed_val = QLabel(f"{saved_speed:.1f}x")
        self.lbl_speed_val.setStyleSheet("font-size: 12px; font-weight: 600; color: #0F172A; min-width: 32px;")
        speed_row.addWidget(self.lbl_speed_val)
        tc_lay.addLayout(speed_row)

        # 试听行
        preview_row = QHBoxLayout()
        preview_row.setSpacing(8)
        self.input_tts_text = QLineEdit("The quick brown fox jumps over the lazy dog.")
        self.input_tts_text.setPlaceholderText("输入要试听的英文句子...")
        preview_row.addWidget(self.input_tts_text)
        self.btn_tts_preview = QPushButton("试听")
        self.btn_tts_preview.setProperty("class", "btnSecondary")
        self.btn_tts_preview.setFixedWidth(60)
        self.btn_tts_preview.setCursor(Qt.PointingHandCursor)
        self.btn_tts_preview.clicked.connect(self._do_tts_preview)
        preview_row.addWidget(self.btn_tts_preview)
        tc_lay.addLayout(preview_row)

        lay.addWidget(tts_card)

        # ── 5. 高级设置折叠 ──
        self.btn_toggle_adv = QPushButton("高级 ▼")
        self.btn_toggle_adv.setProperty("class", "btnSecondary")
        self.btn_toggle_adv.setStyleSheet("text-align: left; padding: 4px 10px; font-size: 11.5px;")
        self.btn_toggle_adv.clicked.connect(self._toggle_advanced)
        lay.addWidget(self.btn_toggle_adv)

        self.adv_card = QFrame()
        self.adv_card.setProperty("class", "card")
        self.adv_card.setVisible(False)
        af_lay = QVBoxLayout(self.adv_card)
        af_lay.setContentsMargins(14, 10, 14, 10)
        af_lay.setSpacing(6)

        # 服务地址
        r_srv = QHBoxLayout()
        lbl_s = QLabel("服务端:")
        lbl_s.setFixedWidth(80)
        lbl_s.setStyleSheet("color: #475569; font-size: 12px; font-weight: 500;")
        self.input_server = QLineEdit(config.get("server_url", "https://theboringenglish.com"))
        r_srv.addWidget(lbl_s)
        r_srv.addWidget(self.input_server)
        af_lay.addLayout(r_srv)

        # Remotion 地址
        r_rem = QHBoxLayout()
        lbl_r = QLabel("Remotion:")
        lbl_r.setFixedWidth(80)
        lbl_r.setStyleSheet("color: #475569; font-size: 12px; font-weight: 500;")
        self.input_remotion = QLineEdit(config.get("remotion_url", "http://localhost:6402"))
        r_rem.addWidget(lbl_r)
        r_rem.addWidget(self.input_remotion)
        af_lay.addLayout(r_rem)

        # 模型目录
        r_mdl = QHBoxLayout()
        lbl_m = QLabel("模型目录:")
        lbl_m.setFixedWidth(80)
        lbl_m.setStyleSheet("color: #475569; font-size: 12px; font-weight: 500;")
        self.input_models_dir = QLineEdit(config.get("models_dir"))
        r_mdl.addWidget(lbl_m)
        r_mdl.addWidget(self.input_models_dir)
        btn_br = QPushButton("浏览")
        btn_br.setProperty("class", "btnSecondary")
        btn_br.clicked.connect(self._browse_models_dir)
        r_mdl.addWidget(btn_br)
        af_lay.addLayout(r_mdl)

        # 离线模型下载
        dl_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        dl_row.addWidget(self.progress_bar)

        self.btn_download_model = QPushButton("下载")
        self.btn_download_model.setProperty("class", "btnSecondary")
        self.btn_download_model.clicked.connect(self._start_download_model)
        dl_row.addWidget(self.btn_download_model)
        af_lay.addLayout(dl_row)

        lay.addWidget(self.adv_card)
        lay.addStretch()

        scroll.setWidget(content)
        root_lay.addWidget(scroll)

        self._refresh_account_ui()
        # 清除任何子控件的默认聚焦，避免下拉框或输入框呈现选中状态
        content.setFocus()

    # ─── TTS 引擎切换 ───────────────────────────────────────────────

    def _populate_voices(self, engine: str, saved_voice: str = ""):
        """根据引擎类型填充音色下拉列表"""
        self.combo_voice.blockSignals(True)
        self.combo_voice.clear()
        target_type = "edge" if engine == "edge" else "kokoro"
        cur_idx = 0
        for i, v in enumerate(SUPPORTED_VOICES):
            if v["type"] == target_type:
                self.combo_voice.addItem(v["name"], v["id"])
                if v["id"] == saved_voice:
                    cur_idx = self.combo_voice.count() - 1
        self.combo_voice.setCurrentIndex(cur_idx)
        self.combo_voice.blockSignals(False)

    def _on_tts_engine_changed(self, engine: str):
        """切换 TTS 引擎，联动刷新音色列表"""
        self.btn_engine_edge.setChecked(engine == "edge")
        self.btn_engine_kokoro.setChecked(engine == "kokoro")
        config.set("tts_engine", engine, auto_save=False)

        self._populate_voices(engine, config.get("tts_voice", "en-US-JennyNeural"))

        # Kokoro 未就绪提示
        if engine == "kokoro":
            ready, msg = self.tts_mgr.is_kokoro_model_ready()
            if not ready:
                self.lbl_kokoro_hint.setText(
                    f"⚠️ Kokoro 离线模型未就绪：{msg}。"
                    "请展开「高级设置」下载模型，或切换回 Edge-TTS。"
                )
                self.lbl_kokoro_hint.setVisible(True)
            else:
                self.lbl_kokoro_hint.setVisible(False)
        else:
            self.lbl_kokoro_hint.setVisible(False)

    # ─── 引擎开关 ────────────────────────────────────────────────────

    def toggle_engine(self):
        if self.is_computing:
            self.stop_engine()
        else:
            self.start_engine()

    def start_engine(self):
        self.is_computing = True
        self.btn_engine_toggle.setText("停止")
        self.btn_engine_toggle.setStyleSheet(
            "background-color: #EF4444; border-color: #EF4444; color: #FFFFFF;"
        )
        self.btn_engine_toggle.style().unpolish(self.btn_engine_toggle)
        self.btn_engine_toggle.style().polish(self.btn_engine_toggle)
        self.badge_engine.set_status("success", "运行中")
        self.lbl_task_count.setVisible(True)

        self.worker = ComputeWorkerThread()
        self.worker.log_signal.connect(self._on_engine_log)
        self.worker.status_signal.connect(self._on_engine_status)
        self.worker.task_done_signal.connect(self._on_task_done)
        self.worker.finished.connect(self._on_worker_truly_finished)
        self.worker.start()
        self.engine_state_signal.emit(True)

    def stop_engine(self):
        self.is_computing = False
        self.btn_engine_toggle.setEnabled(False)
        self.btn_engine_toggle.setText("停止中...")
        if self.worker:
            self.worker._is_running = False
            self.worker.quit()
        else:
            self._cleanup_engine_ui()
        self.engine_state_signal.emit(False)

    def _on_worker_truly_finished(self):
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        self._cleanup_engine_ui()

    def _cleanup_engine_ui(self):
        self.btn_engine_toggle.setEnabled(True)
        self.btn_engine_toggle.setText("启动")
        self.btn_engine_toggle.setStyleSheet("")
        self.btn_engine_toggle.setProperty("class", "btnSuccess")
        self.btn_engine_toggle.style().unpolish(self.btn_engine_toggle)
        self.btn_engine_toggle.style().polish(self.btn_engine_toggle)
        self.badge_engine.set_status("default", "已停用")

    def _on_engine_log(self, line: str):
        self.log_panel.append(line)
        sb = self.log_panel.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_engine_status(self, status_code: str, status_text: str):
        if status_code == "running":
            self.badge_engine.set_status("success", status_text)
        elif status_code in ("reconnecting", "connecting"):
            self.badge_engine.set_status("warning", status_text)
        elif status_code == "stopped":
            self.badge_engine.set_status("default", "已停用")

    def _on_task_done(self, info: dict):
        total = info.get("total", 0)
        self.lbl_task_count.setText(f"今日已完成发音任务: {total} 条")

    def _toggle_log_panel(self):
        show = not self.log_panel.isVisible()
        self.log_panel.setVisible(show)
        self.lbl_task_count.setVisible(show and self.is_computing)
        self.btn_toggle_log.setText("日志 ▼" if show else "日志 ▶")

    def _toggle_advanced(self):
        show = not self.adv_card.isVisible()
        self.adv_card.setVisible(show)
        self.btn_toggle_adv.setText("高级 ▲" if show else "高级 ▼")

    # ─── 账户关联 ────────────────────────────────────────────────────

    def _toggle_manual_frame(self):
        show = not self.manual_frame.isVisible()
        self.manual_frame.setVisible(show)
        self.btn_toggle_manual.setText("收起 ▲" if show else "手动 ▼")
        if show:
            self.input_token.setFocus()

    def start_browser_sync(self):
        self._sync_in_progress = True
        self._sync_countdown = 45
        self.btn_browser_sync.setText(f"授权 ({self._sync_countdown}s)")
        self.lbl_sync_hint.setText("💡 请在打开的网页中登录，客户端将自动同步绑定。")
        self.lbl_sync_hint.setStyleSheet("font-size: 11px; color: #818CF8; padding-top: 2px;")
        self.lbl_sync_hint.setVisible(True)
        if self._sync_timer is None:
            self._sync_timer = QTimer(self)
            self._sync_timer.timeout.connect(self._on_sync_timer_tick)
        self._sync_timer.start(1000)

    def _on_sync_timer_tick(self):
        self._sync_countdown -= 1
        if self._sync_countdown > 0:
            self.btn_browser_sync.setText(f"授权 ({self._sync_countdown}s)")
        else:
            self.on_sync_failed("未检测到浏览器授权回传（可能受本地防火墙或网络阻拦）")

    def cancel_browser_sync(self):
        self._sync_in_progress = False
        if self._sync_timer and self._sync_timer.isActive():
            self._sync_timer.stop()
        self.btn_browser_sync.setText("同步")
        self.btn_browser_sync.setStyleSheet("")
        self.lbl_sync_hint.setVisible(False)

    def on_sync_success(self, username: str = "User"):
        self.cancel_browser_sync()
        self._refresh_account_ui()
        self.auth_state_changed_signal.emit()
        QMessageBox.information(self, "成功", f"🎉 账户关联成功！欢迎回来，{username}")

    def on_sync_failed(self, reason: str):
        self.cancel_browser_sync()
        self.lbl_sync_hint.setText(
            f"⚠️ {reason}\n已为您切换为手动模式，请粘贴 API Token："
        )
        self.lbl_sync_hint.setStyleSheet("font-size: 11px; color: #F59E0B; padding-top: 2px;")
        self.lbl_sync_hint.setVisible(True)
        self.manual_frame.setVisible(True)
        self.btn_toggle_manual.setText("收起 ▲")
        self.input_token.setFocus()

    def _open_browser_sync(self):
        if self._sync_in_progress:
            self.cancel_browser_sync()
            return
        self.start_browser_sync()
        server_url = self.input_server.text().strip() or "https://theboringenglish.com"
        if not server_url.startswith("http"):
            server_url = "https://" + server_url
        server_url = server_url.rstrip("/")
        sep = "&" if "?" in server_url else "?"
        webbrowser.open(f"{server_url}/settings{sep}client_port=6502")

    def _refresh_account_ui(self):
        if config.is_logged_in:
            user_info = config.get("user_info") or {}
            username = user_info.get("username") or "User"
            self.badge_acc.set_status("success", f"已绑定: {username}")
            self.btn_browser_sync.setVisible(False)
            self.lbl_sync_hint.setVisible(False)
            self.btn_toggle_manual.setVisible(False)
            self.manual_frame.setVisible(False)
            self.btn_logout.setVisible(True)
        else:
            self.badge_acc.set_status("default", "未关联")
            self.btn_browser_sync.setVisible(True)
            self.btn_toggle_manual.setVisible(True)
            self.btn_logout.setVisible(False)
            if not self.lbl_sync_hint.isVisible():
                self.manual_frame.setVisible(False)
                self.btn_toggle_manual.setText("手动绑定 ▼")

    def _do_token_link(self):
        token = self.input_token.text().strip()
        if not token:
            QMessageBox.warning(self, "提示", "请输入授权 Token")
            return
        self.btn_verify_token.setEnabled(False)
        self.btn_verify_token.setText("验证中...")
        ok, msg, user_info = AuthAPI.link_with_token(token)
        self.btn_verify_token.setEnabled(True)
        self.btn_verify_token.setText("绑定")
        if ok:
            self._refresh_account_ui()
            self.auth_state_changed_signal.emit()
            username = (user_info or {}).get("username", "User")
            QMessageBox.information(self, "成功", f"账户绑定成功！欢迎，{username}")
        else:
            QMessageBox.warning(self, "绑定失败", f"Token 校验失败：{msg}")

    def _do_account_logout(self):
        config.clear_auth()
        self.input_token.setText("")
        self._refresh_account_ui()
        self.auth_state_changed_signal.emit()
        QMessageBox.information(self, "提示", "已解除账户绑定。")

    # ─── 速度 / 试听 ──────────────────────────────────────────────────

    def _on_speed_changed(self, value: int):
        self.lbl_speed_val.setText(f"{value / 100.0:.1f}x")

    def _do_tts_preview(self):
        text = self.input_tts_text.text().strip() or "The quick brown fox jumps over the lazy dog."
        voice_id = self.combo_voice.currentData() or "en-US-JennyNeural"
        speed = self.slider_speed.value() / 100.0

        self.btn_tts_preview.setEnabled(False)
        self.btn_tts_preview.setText("生成中...")

        if self.tts_preview_worker and self.tts_preview_worker.isRunning():
            self.tts_preview_worker.quit()

        self.tts_preview_worker = TTSPreviewWorker(text, voice_id, speed)
        self.tts_preview_worker.finished_signal.connect(self._on_tts_preview_done)
        self.tts_preview_worker.start()

    def _on_tts_preview_done(self, audio_bytes: bytes, error: str):
        self.btn_tts_preview.setEnabled(True)
        self.btn_tts_preview.setText("试听")
        if error or not audio_bytes:
            QMessageBox.warning(self, "试听失败", f"发音合成失败：{error or '未获得音频数据'}")
            return
        suffix = ".wav" if audio_bytes[:4] == b"RIFF" else ".mp3"
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tf:
                tf.write(audio_bytes)
                tmp_path = tf.name
            if sys.platform == "win32":
                os.startfile(tmp_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", tmp_path])
            else:
                subprocess.Popen(["xdg-open", tmp_path])
        except Exception as e:
            QMessageBox.warning(self, "播放失败", f"无法播放音频：{e}")

    # ─── 高级设置 ─────────────────────────────────────────────────────

    def _browse_models_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择模型存放目录", self.input_models_dir.text())
        if d:
            self.input_models_dir.setText(d)

    def _start_download_model(self):
        target = os.path.join(self.input_models_dir.text(), "kokoro")
        self.btn_download_model.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        if self.dl_worker and self.dl_worker.isRunning():
            self.dl_worker.cancel()
            self.dl_worker.wait(3000)

        self.dl_worker = ModelDownloadWorker(target)
        self.dl_worker.progress_signal.connect(lambda v, m: self.progress_bar.setValue(v))
        self.dl_worker.finished_signal.connect(self._on_dl_finished)
        self.dl_worker.start()

    def _on_dl_finished(self, ok, msg):
        self.btn_download_model.setEnabled(True)
        self.btn_download_model.setText("下载模型")
        self.progress_bar.setVisible(False)
        if ok:
            QMessageBox.information(self, "成功", msg)
            # 下载完成后刷新 Kokoro 提示状态
            if config.get("tts_engine", "edge") == "kokoro":
                self._on_tts_engine_changed("kokoro")
        else:
            QMessageBox.warning(self, "失败", msg)

    def _save_all_settings(self):
        """批量写入配置"""
        config.set("server_url", self.input_server.text().strip(), auto_save=False)
        config.set("remotion_url", self.input_remotion.text().strip(), auto_save=False)
        config.set("models_dir", self.input_models_dir.text().strip(), auto_save=False)
        config.set("minimize_to_tray", self.cb_tray.isChecked(), auto_save=False)
        config.set("auto_start_compute", self.cb_auto_start.isChecked(), auto_save=False)
        config.set("tts_engine", "edge" if self.btn_engine_edge.isChecked() else "kokoro", auto_save=False)
        config.set("tts_voice", self.combo_voice.currentData(), auto_save=False)
        config.set("tts_speed", self.slider_speed.value() / 100.0, auto_save=False)

        if config.save():
            QMessageBox.information(self, "成功", "设置已保存！")
        else:
            QMessageBox.warning(self, "失败", "配置保存失败，请检查文件写入权限！")

    # ─── 国际化 ───────────────────────────────────────────────────────

    def retranslate_ui(self):
        is_zh = config.get("language", "zh_CN") == "zh_CN"
        self.lbl_title.setText("系统设置" if is_zh else "Settings")
        self.btn_save_all.setText("保存" if is_zh else "Save")
        self.lbl_engine_name.setText("⚡ 本地发音引擎" if is_zh else "⚡ Speech Engine")
        self.lbl_engine_desc.setText(
            "启用后作为本地算力节点，为浏览器及云端精读提供毫秒级原声发音。" if is_zh
            else "Runs local node for instant native speech synthesis."
        )
        self.cb_auto_start.setText("自动启动引擎" if is_zh else "Auto-start engine")
        self.cb_tray.setText("关闭时最小化至托盘" if is_zh else "Minimize to tray")
        if not self.is_computing:
            self.btn_engine_toggle.setText("启动" if is_zh else "Start")
            self.badge_engine.set_status("default", "已停用" if is_zh else "Stopped")
        else:
            self.btn_engine_toggle.setText("停止" if is_zh else "Stop")
            self.badge_engine.set_status("success", "运行中" if is_zh else "Running")

        self.lbl_acc_title.setText("👤 账户关联" if is_zh else "👤 Account Link")
        self.btn_browser_sync.setText("同步" if is_zh else "Link")
        self.btn_logout.setText("注销" if is_zh else "Unlink")
        self.btn_verify_token.setText("绑定" if is_zh else "Bind")

        self.lbl_tts_title.setText("🎙️ 发音偏好" if is_zh else "🎙️ Speech Preferences")
        self._refresh_account_ui()
