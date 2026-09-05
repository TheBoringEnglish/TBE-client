# -*- coding: utf-8 -*-
"""
客户端主设置与控制台视图 (SettingsView)
整合原首页仪表盘、发音引擎一键开关、账号关联、偏好设置与高级选项。
布局极简扁平，直接呈现核心功能，移除冗长叙述。
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
from .dialog_doctor import SystemDoctorDialog
from ..config import config
from ..core.tts_engine import LocalTTSManager, SUPPORTED_VOICES
from ..core.auth_api import AuthAPI
from ..core.ws_worker import ComputeWorkerThread
from ..core.i18n import t, set_language


class ModelDownloadWorker(QThread):
    """Kokoro 离线模型后台下载（流式分块，修复闭包 bug，支持取消）"""
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
                    # 流式分块下载，支持进度和取消
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
                    # 降级 urlretrieve：通过默认参数固化外层变量，修复闭包 bug
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
    """TTS 试听后台线程（避免阻塞主线程）"""
    finished_signal = Signal(bytes, str)  # (audio_bytes, error_msg)

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

        # 滚动容器，确保小屏幕完整显示
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(36, 20, 36, 24)
        lay.setSpacing(16)

        # ── 1. 顶部状态与快速保存 ──
        top_bar = QHBoxLayout()
        self.lbl_title = QLabel("系统设置")
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: 700; letter-spacing: -0.4px;")
        top_bar.addWidget(self.lbl_title)
        top_bar.addStretch()

        self.btn_save_all = QPushButton("保存配置")
        self.btn_save_all.setProperty("class", "btnPrimary")
        self.btn_save_all.setCursor(Qt.PointingHandCursor)
        self.btn_save_all.clicked.connect(self._save_all_settings)
        top_bar.addWidget(self.btn_save_all)
        lay.addLayout(top_bar)

        # ── 2. 本地发音引擎开关卡片 ──
        engine_card = QFrame()
        engine_card.setProperty("class", "card")
        ec_lay = QVBoxLayout(engine_card)
        ec_lay.setContentsMargins(24, 18, 24, 18)
        ec_lay.setSpacing(10)

        # 控制行
        ec_ctrl = QHBoxLayout()
        ec_ctrl.setSpacing(16)

        ec_info = QVBoxLayout()
        ec_info.setSpacing(4)
        self.lbl_engine_name = QLabel("⚡ 本地发音引擎")
        self.lbl_engine_name.setStyleSheet("font-size: 15px; font-weight: 700;")
        ec_info.addWidget(self.lbl_engine_name)

        self.lbl_engine_desc = QLabel("启用后作为本地算力节点，为浏览器及云端精读提供毫秒级原声发音。")
        self.lbl_engine_desc.setStyleSheet("font-size: 12px; color: #94A3B8;")
        ec_info.addWidget(self.lbl_engine_desc)
        ec_ctrl.addLayout(ec_info)
        ec_ctrl.addStretch()

        self.badge_engine = StatusBadge("已停用", "default")
        ec_ctrl.addWidget(self.badge_engine)

        self.btn_engine_toggle = QPushButton("启动引擎")
        self.btn_engine_toggle.setProperty("class", "btnSuccess")
        self.btn_engine_toggle.setFixedSize(110, 36)
        self.btn_engine_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_engine_toggle.clicked.connect(self.toggle_engine)
        ec_ctrl.addWidget(self.btn_engine_toggle)
        ec_lay.addLayout(ec_ctrl)

        # 自动启动复选框
        self.cb_auto_start = QCheckBox("启动客户端时自动启用发音引擎")
        self.cb_auto_start.setChecked(config.get("auto_start_compute", False))
        self.cb_auto_start.setStyleSheet("font-size: 12px; color: #94A3B8;")
        ec_lay.addWidget(self.cb_auto_start)

        # 日志折叠面板
        self.btn_toggle_log = QPushButton("▶  展开引擎日志")
        self.btn_toggle_log.setProperty("class", "btnSecondary")
        self.btn_toggle_log.setStyleSheet("text-align: left; padding: 5px 12px; font-size: 11.5px;")
        self.btn_toggle_log.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_log.clicked.connect(self._toggle_log_panel)
        ec_lay.addWidget(self.btn_toggle_log)

        self.log_panel = QTextEdit()
        self.log_panel.setReadOnly(True)
        self.log_panel.document().setMaximumBlockCount(200)
        self.log_panel.setVisible(False)
        self.log_panel.setFixedHeight(140)
        self.log_panel.setStyleSheet(
            "font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 11.5px; "
            "background-color: rgba(0,0,0,0.3); border-radius: 8px; padding: 8px;"
        )
        self.log_panel.setPlaceholderText("发音引擎启动后，调度日志将在此实时显示...")
        ec_lay.addWidget(self.log_panel)

        self.lbl_task_count = QLabel("今日已完成发音任务: 0 条")
        self.lbl_task_count.setStyleSheet("font-size: 11.5px; color: #64748B;")
        self.lbl_task_count.setVisible(False)
        ec_lay.addWidget(self.lbl_task_count)

        lay.addWidget(engine_card)

        # ── 3. 账户关联卡片 ──
        acc_card = QFrame()
        acc_card.setProperty("class", "card")
        ac_lay = QVBoxLayout(acc_card)
        ac_lay.setContentsMargins(24, 20, 24, 20)
        ac_lay.setSpacing(14)

        acc_header = QHBoxLayout()
        self.lbl_acc_title = QLabel("👤 官方账户关联")
        self.lbl_acc_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        acc_header.addWidget(self.lbl_acc_title)
        acc_header.addStretch()

        self.badge_acc = StatusBadge("未关联", "default")
        acc_header.addWidget(self.badge_acc)
        ac_lay.addLayout(acc_header)

        # 浏览器一键同步主按钮
        self.btn_browser_sync = QPushButton("🌐 在浏览器打开官网一键同步")
        self.btn_browser_sync.setProperty("class", "btnPrimary")
        self.btn_browser_sync.setFixedHeight(40)
        self.btn_browser_sync.setCursor(Qt.PointingHandCursor)
        self.btn_browser_sync.clicked.connect(self._open_browser_sync)
        ac_lay.addWidget(self.btn_browser_sync)

        # 动态同步提示标签（等待中/降级提示）
        self.lbl_sync_hint = QLabel()
        self.lbl_sync_hint.setWordWrap(True)
        self.lbl_sync_hint.setVisible(False)
        ac_lay.addWidget(self.lbl_sync_hint)

        # 手动粘贴折叠切换按钮（次级操作，低视觉干扰）
        self.btn_toggle_manual = QPushButton("遇到了同步问题？手动粘贴 Token ▼")
        self.btn_toggle_manual.setProperty("class", "btnSecondary")
        self.btn_toggle_manual.setStyleSheet("text-align: left; padding: 4px 10px; font-size: 11.5px; border: none; background: transparent; color: #94A3B8;")
        self.btn_toggle_manual.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_manual.clicked.connect(self._toggle_manual_frame)
        ac_lay.addWidget(self.btn_toggle_manual)

        # 手动输入区域（默认折叠隐藏，仅在降级或用户手动点击时展开）
        self.manual_frame = QFrame()
        self.manual_frame.setVisible(False)
        mf_lay = QHBoxLayout(self.manual_frame)
        mf_lay.setContentsMargins(0, 4, 0, 0)
        mf_lay.setSpacing(10)

        self.input_token = QLineEdit(config.get("token", ""))
        self.input_token.setEchoMode(QLineEdit.Password)
        self.input_token.setPlaceholderText("手动粘贴 Authorization Token...")
        mf_lay.addWidget(self.input_token)

        self.btn_verify_token = QPushButton("绑定 Token")
        self.btn_verify_token.setProperty("class", "btnSecondary")
        self.btn_verify_token.setCursor(Qt.PointingHandCursor)
        self.btn_verify_token.clicked.connect(self._do_token_link)
        mf_lay.addWidget(self.btn_verify_token)
        ac_lay.addWidget(self.manual_frame)

        self.btn_logout = QPushButton("解除绑定")
        self.btn_logout.setProperty("class", "btnSecondary")
        self.btn_logout.setFixedHeight(34)
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.clicked.connect(self._do_account_logout)
        self.btn_logout.setVisible(False)
        ac_lay.addWidget(self.btn_logout)

        lay.addWidget(acc_card)

        # ── 3.5 发音偏好卡片 (TTS Preferences) ──
        tts_card = QFrame()
        tts_card.setProperty("class", "card")
        tc_lay = QVBoxLayout(tts_card)
        tc_lay.setContentsMargins(24, 20, 24, 20)
        tc_lay.setSpacing(14)

        self.lbl_tts_title = QLabel("🎙️ 发音偏好设置")
        self.lbl_tts_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        tc_lay.addWidget(self.lbl_tts_title)

        # 音色选择
        voice_row = QHBoxLayout()
        voice_row.setSpacing(12)
        lbl_voice = QLabel("发音音色：")
        lbl_voice.setStyleSheet("font-size: 12px; color: #94A3B8;")
        lbl_voice.setFixedWidth(80)
        voice_row.addWidget(lbl_voice)
        self.combo_voice = QComboBox()
        saved_voice = config.get("tts_voice", "en-US-JennyNeural")
        for v in SUPPORTED_VOICES:
            self.combo_voice.addItem(v["name"], v["id"])
            if v["id"] == saved_voice:
                self.combo_voice.setCurrentIndex(self.combo_voice.count() - 1)
        voice_row.addWidget(self.combo_voice)
        tc_lay.addLayout(voice_row)

        # 语速滑块
        speed_row = QHBoxLayout()
        speed_row.setSpacing(12)
        lbl_speed = QLabel("语速调节：")
        lbl_speed.setStyleSheet("font-size: 12px; color: #94A3B8;")
        lbl_speed.setFixedWidth(80)
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
        self.lbl_speed_val.setStyleSheet("font-size: 12.5px; font-weight: 600; min-width: 36px;")
        speed_row.addWidget(self.lbl_speed_val)
        tc_lay.addLayout(speed_row)

        # 试听行
        preview_row = QHBoxLayout()
        preview_row.setSpacing(10)
        self.input_tts_text = QLineEdit("The quick brown fox jumps over the lazy dog.")
        self.input_tts_text.setPlaceholderText("输入要试听的英文句子...")
        preview_row.addWidget(self.input_tts_text)
        self.btn_tts_preview = QPushButton("🔊 试听")
        self.btn_tts_preview.setProperty("class", "btnSecondary")
        self.btn_tts_preview.setFixedWidth(84)
        self.btn_tts_preview.setCursor(Qt.PointingHandCursor)
        self.btn_tts_preview.clicked.connect(self._do_tts_preview)
        preview_row.addWidget(self.btn_tts_preview)
        tc_lay.addLayout(preview_row)

        lay.addWidget(tts_card)

        # ── 4. 常用偏好卡片 (语言、主题、托盘) ──
        pref_card = QFrame()
        pref_card.setProperty("class", "card")
        pc_lay = QVBoxLayout(pref_card)
        pc_lay.setContentsMargins(24, 20, 24, 20)
        pc_lay.setSpacing(14)

        self.lbl_pref_title = QLabel("⚙️ 偏好设置")
        self.lbl_pref_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        pc_lay.addWidget(self.lbl_pref_title)

        pref_grid = QHBoxLayout()
        pref_grid.setSpacing(28)

        # 语言
        l_box = QVBoxLayout()
        l_box.setSpacing(6)
        self.lbl_lang_sel = QLabel("界面语言")
        self.lbl_lang_sel.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("🇨🇳 简体中文", "zh_CN")
        self.combo_lang.addItem("🇺🇸 English", "en_US")
        cur_lang = config.get("language", "zh_CN")
        self.combo_lang.setCurrentIndex(0 if cur_lang == "zh_CN" else 1)
        self.combo_lang.currentIndexChanged.connect(self._on_lang_changed)
        l_box.addWidget(self.lbl_lang_sel)
        l_box.addWidget(self.combo_lang)
        pref_grid.addLayout(l_box)

        # 主题
        th_box = QVBoxLayout()
        th_box.setSpacing(6)
        self.lbl_th_sel = QLabel("主题外观")
        self.lbl_th_sel.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.combo_theme = QComboBox()
        self.combo_theme.addItem("深邃暗黑", "dark")
        self.combo_theme.addItem("极简明亮", "light")
        self.combo_theme.setCurrentIndex(0 if config.get("theme", "dark") == "dark" else 1)
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        th_box.addWidget(self.lbl_th_sel)
        th_box.addWidget(self.combo_theme)
        pref_grid.addLayout(th_box)

        pref_grid.addStretch()
        pc_lay.addLayout(pref_grid)

        self.cb_tray = QCheckBox("关闭窗口时最小化至托盘并在后台运行")
        self.cb_tray.setChecked(config.get("minimize_to_tray", True))
        pc_lay.addWidget(self.cb_tray)

        # 环境与网络体检按钮
        doc_row = QHBoxLayout()
        doc_row.setSpacing(12)
        self.btn_open_doctor = QPushButton("🩺 系统环境与网络健康体检")
        self.btn_open_doctor.setProperty("class", "btnSecondary")
        self.btn_open_doctor.setFixedHeight(36)
        self.btn_open_doctor.setCursor(Qt.PointingHandCursor)
        self.btn_open_doctor.clicked.connect(self._open_doctor_dialog)
        doc_row.addWidget(self.btn_open_doctor)

        self.lbl_doctor_hint = QLabel("一键排查 YouTube、BBC、Edge-TTS、Kokoro 模型与本地服务状态")
        self.lbl_doctor_hint.setStyleSheet("font-size: 12px; color: #94A3B8;")
        doc_row.addWidget(self.lbl_doctor_hint)
        doc_row.addStretch()
        pc_lay.addLayout(doc_row)

        lay.addWidget(pref_card)

        # ── 5. 高级设置折叠卡片 ──
        self.btn_toggle_adv = QPushButton("展开高级设置 ▼")
        self.btn_toggle_adv.setProperty("class", "btnSecondary")
        self.btn_toggle_adv.setStyleSheet("text-align: left; padding: 8px 14px; font-size: 12px;")
        self.btn_toggle_adv.clicked.connect(self._toggle_advanced)
        lay.addWidget(self.btn_toggle_adv)

        self.adv_card = QFrame()
        self.adv_card.setProperty("class", "card")
        self.adv_card.setVisible(False)
        af_lay = QVBoxLayout(self.adv_card)
        af_lay.setContentsMargins(24, 18, 24, 18)
        af_lay.setSpacing(12)

        # 服务地址
        r_srv = QHBoxLayout()
        lbl_s = QLabel("服务端接口:")
        lbl_s.setFixedWidth(110)
        lbl_s.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.input_server = QLineEdit(config.get("server_url", "https://theboringenglish.com"))
        r_srv.addWidget(lbl_s)
        r_srv.addWidget(self.input_server)
        af_lay.addLayout(r_srv)

        # Remotion 地址
        r_rem = QHBoxLayout()
        lbl_r = QLabel("Remotion 接口:")
        lbl_r.setFixedWidth(110)
        lbl_r.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.input_remotion = QLineEdit(config.get("remotion_url", "http://localhost:6402"))
        r_rem.addWidget(lbl_r)
        r_rem.addWidget(self.input_remotion)
        af_lay.addLayout(r_rem)

        # 模型目录
        r_mdl = QHBoxLayout()
        lbl_m = QLabel("离线模型目录:")
        lbl_m.setFixedWidth(110)
        lbl_m.setStyleSheet("color: #94A3B8; font-size: 12px;")
        self.input_models_dir = QLineEdit(config.get("models_dir"))
        r_mdl.addWidget(lbl_m)
        r_mdl.addWidget(self.input_models_dir)
        btn_br = QPushButton("浏览...")
        btn_br.setProperty("class", "btnSecondary")
        btn_br.clicked.connect(self._browse_models_dir)
        r_mdl.addWidget(btn_br)
        af_lay.addLayout(r_mdl)

        # 离线模型下载
        dl_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        dl_row.addWidget(self.progress_bar)

        self.btn_download_model = QPushButton("下载/校验 Kokoro 离线模型")
        self.btn_download_model.setProperty("class", "btnSecondary")
        self.btn_download_model.clicked.connect(self._start_download_model)
        dl_row.addWidget(self.btn_download_model)
        af_lay.addLayout(dl_row)

        lay.addWidget(self.adv_card)
        lay.addStretch()

        scroll.setWidget(content)
        root_lay.addWidget(scroll)

        self._refresh_account_ui()

    # ── 业务逻辑 ──
    def toggle_engine(self):
        """发音引擎一键开关"""
        if self.is_computing:
            self.stop_engine()
        else:
            self.start_engine()

    def start_engine(self):
        self.is_computing = True
        self.btn_engine_toggle.setText("停用引擎")
        self.btn_engine_toggle.setStyleSheet("background-color: #EF4444; border-color: #EF4444; color: #FFFFFF;")
        # 修复 PySide6 QSS 动态 property 刷新缺陷
        self.btn_engine_toggle.style().unpolish(self.btn_engine_toggle)
        self.btn_engine_toggle.style().polish(self.btn_engine_toggle)
        self.badge_engine.set_status("success", "运行中")
        self.lbl_task_count.setVisible(True)

        self.worker = ComputeWorkerThread()
        # 连接所有信号到 UI
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
            # 不立即置 None，等 finished 信号触发后安全清理
            self.worker.quit()
        else:
            self._cleanup_engine_ui()
        self.engine_state_signal.emit(False)

    def _on_worker_truly_finished(self):
        """引擎线程 finished 信号回调 — 安全清理线程对象"""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        self._cleanup_engine_ui()

    def _cleanup_engine_ui(self):
        self.btn_engine_toggle.setEnabled(True)
        self.btn_engine_toggle.setText("启动引擎")
        self.btn_engine_toggle.setStyleSheet("")
        self.btn_engine_toggle.setProperty("class", "btnSuccess")
        self.btn_engine_toggle.style().unpolish(self.btn_engine_toggle)
        self.btn_engine_toggle.style().polish(self.btn_engine_toggle)
        self.badge_engine.set_status("default", "已停用")

    def _on_engine_log(self, line: str):
        """追加引擎日志到面板，文档自动限制最多 200 行"""
        self.log_panel.append(line)
        sb = self.log_panel.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_engine_status(self, status_code: str, status_text: str):
        """更新引擎徽章状态"""
        if status_code == "running":
            self.badge_engine.set_status("success", status_text)
        elif status_code in ("reconnecting", "connecting"):
            self.badge_engine.set_status("warning", status_text)
        elif status_code == "stopped":
            self.badge_engine.set_status("default", "已停用")

    def _on_task_done(self, info: dict):
        """更新任务完成计数"""
        total = info.get("total", 0)
        self.lbl_task_count.setText(f"今日已完成发音任务: {total} 条")

    def _toggle_log_panel(self):
        show = not self.log_panel.isVisible()
        self.log_panel.setVisible(show)
        self.lbl_task_count.setVisible(show and self.is_computing)
        self.btn_toggle_log.setText("▼  收起引擎日志" if show else "▶  展开引擎日志")

    def _toggle_advanced(self):
        show = not self.adv_card.isVisible()
        self.adv_card.setVisible(show)
        self.btn_toggle_adv.setText("折叠高级设置 ▲" if show else "展开高级设置 ▼")

    def _toggle_manual_frame(self):
        show = not self.manual_frame.isVisible()
        self.manual_frame.setVisible(show)
        self.btn_toggle_manual.setText("收起手动输入 ▲" if show else "遇到了同步问题？手动粘贴 Token ▼")
        if show:
            self.input_token.setFocus()

    def start_browser_sync(self):
        """进入浏览器同步等待状态，倒计时 45 秒"""
        self._sync_in_progress = True
        self._sync_countdown = 45
        self.btn_browser_sync.setText(f"⏳ 等待浏览器授权中... ({self._sync_countdown}s, 点击取消)")
        self.lbl_sync_hint.setText("💡 正在等待浏览器同步授权... 请在打开的网页中登录，客户端将自动同步绑定。")
        self.lbl_sync_hint.setStyleSheet("font-size: 11.5px; color: #818CF8; padding-top: 2px;")
        self.lbl_sync_hint.setVisible(True)
        if self._sync_timer is None:
            self._sync_timer = QTimer(self)
            self._sync_timer.timeout.connect(self._on_sync_timer_tick)
        self._sync_timer.start(1000)

    def _on_sync_timer_tick(self):
        self._sync_countdown -= 1
        if self._sync_countdown > 0:
            self.btn_browser_sync.setText(f"⏳ 等待浏览器授权中... ({self._sync_countdown}s, 点击取消)")
        else:
            self.on_sync_failed("未检测到浏览器授权回传（可能受本地防火墙或网络阻拦）")

    def cancel_browser_sync(self):
        """取消或重置浏览器同步等待"""
        self._sync_in_progress = False
        if self._sync_timer and self._sync_timer.isActive():
            self._sync_timer.stop()
        self.btn_browser_sync.setText("🌐 在浏览器打开官网一键同步")
        self.btn_browser_sync.setStyleSheet("")
        self.lbl_sync_hint.setVisible(False)

    def on_sync_success(self, username: str = "User"):
        """同步成功回调：停止等待，更新 UI 状态"""
        self.cancel_browser_sync()
        self._refresh_account_ui()
        QMessageBox.information(self, "同步成功", f"🎉 官方账户关联成功！欢迎回来，{username}")

    def on_sync_failed(self, reason: str):
        """同步失败或超时回调：自动平滑降级，展开手动粘贴模式"""
        self.cancel_browser_sync()
        self.lbl_sync_hint.setText(f"⚠️ {reason}\n已为您切换为手动粘贴模式，请从网页复制 API Token 粘贴至下方：")
        self.lbl_sync_hint.setStyleSheet("font-size: 11.5px; color: #F59E0B; padding-top: 2px; line-height: 1.4;")
        self.lbl_sync_hint.setVisible(True)
        self.manual_frame.setVisible(True)
        self.btn_toggle_manual.setText("收起手动输入 ▲")
        self.input_token.setFocus()

    def _open_browser_sync(self):
        # 默认由外部 app.py 重新绑定处理（支持 nonce 注册），若独立运行则提供基础降级支持
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
                self.btn_toggle_manual.setText("遇到了同步问题？手动粘贴 Token ▼")

    def _do_token_link(self):
        """手动 Token 绑定 — 修复：使用 AuthAPI.link_with_token 而非不存在的 verify_token"""
        token = self.input_token.text().strip()
        if not token:
            QMessageBox.warning(self, "提示", "请输入授权 Token")
            return

        self.btn_verify_token.setEnabled(False)
        self.btn_verify_token.setText("验证中...")

        ok, msg, user_info = AuthAPI.link_with_token(token)

        self.btn_verify_token.setEnabled(True)
        self.btn_verify_token.setText("绑定 Token")

        if ok:
            self._refresh_account_ui()
            username = (user_info or {}).get("username", "User")
            QMessageBox.information(self, "成功", f"账户绑定成功！欢迎，{username}")
        else:
            QMessageBox.warning(self, "绑定失败", f"Token 校验失败：{msg}")

    def _do_account_logout(self):
        """解除账户绑定 — 修复：使用统一 clear_auth() 而非手动置空"""
        config.clear_auth()
        self.input_token.setText("")
        self._refresh_account_ui()
        QMessageBox.information(self, "提示", "已解除账户绑定。")

    def _on_lang_changed(self):
        new_lang = self.combo_lang.currentData()
        set_language(new_lang)
        config.set("language", new_lang, auto_save=False)
        config.save()
        self.language_changed_signal.emit(new_lang)
        self.retranslate_ui()

    def _on_theme_changed(self):
        new_theme = self.combo_theme.currentData()
        config.set("theme", new_theme, auto_save=False)
        config.save()
        self.theme_changed_signal.emit(new_theme)

    def _on_speed_changed(self, value: int):
        self.lbl_speed_val.setText(f"{value / 100.0:.1f}x")

    def _do_tts_preview(self):
        """TTS 音色试听"""
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
        self.btn_tts_preview.setText("🔊 试听")
        if error or not audio_bytes:
            QMessageBox.warning(self, "试听失败", f"发音合成失败：{error or '未获得音频数据'}")
            return
        suffix = ".wav" if audio_bytes[:4] == b"RIFF" else ".mp3"
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tf:
                tf.write(audio_bytes)
                tmp_path = tf.name
            if sys.platform == "win32":
                os.startfile(tmp_path)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", tmp_path])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", tmp_path])
        except Exception as e:
            QMessageBox.warning(self, "播放失败", f"无法播放音频：{e}")

    def _browse_models_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择模型存放目录", self.input_models_dir.text())
        if d:
            self.input_models_dir.setText(d)

    def _start_download_model(self):
        target = os.path.join(self.input_models_dir.text(), "kokoro")
        self.btn_download_model.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.dl_worker = ModelDownloadWorker(target)
        self.dl_worker.progress_signal.connect(lambda v, m: self.progress_bar.setValue(v))
        self.dl_worker.finished_signal.connect(self._on_dl_finished)
        self.dl_worker.start()

    def _on_dl_finished(self, ok, msg):
        self.btn_download_model.setEnabled(True)
        self.progress_bar.setVisible(False)
        if ok:
            QMessageBox.information(self, "成功", msg)
        else:
            QMessageBox.warning(self, "失败", msg)

    def _start_download_model(self):
        target = os.path.join(self.input_models_dir.text(), "kokoro")
        self.btn_download_model.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        if self.dl_worker and self.dl_worker.isRunning():
            self.dl_worker.cancel()
            self.dl_worker.wait(3000)

        self.dl_worker = ModelDownloadWorker(target)
        self.dl_worker.progress_signal.connect(lambda v, m: (
            self.progress_bar.setValue(v)
        ))
        self.dl_worker.finished_signal.connect(self._on_dl_finished)
        self.dl_worker.start()

    def _on_dl_finished(self, ok, msg):
        self.btn_download_model.setEnabled(True)
        self.btn_download_model.setText("下载/校验 Kokoro 离线模型")
        self.progress_bar.setVisible(False)
        if ok:
            QMessageBox.information(self, "成功", msg)
        else:
            QMessageBox.warning(self, "失败", msg)

    def _save_all_settings(self):
        """批量写入配置，最后统一 save() 减少磁盘写入次数"""
        config.set("server_url", self.input_server.text().strip(), auto_save=False)
        config.set("remotion_url", self.input_remotion.text().strip(), auto_save=False)
        config.set("models_dir", self.input_models_dir.text().strip(), auto_save=False)
        config.set("theme", self.combo_theme.currentData(), auto_save=False)
        config.set("language", self.combo_lang.currentData(), auto_save=False)
        config.set("minimize_to_tray", self.cb_tray.isChecked(), auto_save=False)
        config.set("auto_start_compute", self.cb_auto_start.isChecked(), auto_save=False)
        config.set("tts_voice", self.combo_voice.currentData(), auto_save=False)
        config.set("tts_speed", self.slider_speed.value() / 100.0, auto_save=False)
        # token 由绑定/解绑流程维护，不在此覆盖

        if config.save():
            QMessageBox.information(self, "成功", "设置已成功保存！")
        else:
            QMessageBox.warning(self, "失败", "配置保存失败，请检查文件写入权限！")

    def retranslate_ui(self):
        is_zh = config.get("language", "zh_CN") == "zh_CN"
        self.lbl_title.setText("系统设置" if is_zh else "Settings")
        self.btn_save_all.setText("保存配置" if is_zh else "Save")
        self.lbl_engine_name.setText("⚡ 本地发音引擎" if is_zh else "⚡ Speech Engine")
        self.lbl_engine_desc.setText(
            "启用后作为本地算力节点，为浏览器及云端精读提供毫秒级原声发音。" if is_zh
            else "Runs local node for instant native speech synthesis."
        )
        self.cb_auto_start.setText(
            "启动客户端时自动启用发音引擎" if is_zh else "Auto-start engine on launch"
        )
        if not self.is_computing:
            self.btn_engine_toggle.setText("启动引擎" if is_zh else "Start Engine")
            self.badge_engine.set_status("default", "已停用" if is_zh else "Stopped")
        else:
            self.btn_engine_toggle.setText("停用引擎" if is_zh else "Stop Engine")
            self.badge_engine.set_status("success", "运行中" if is_zh else "Running")

        self.lbl_acc_title.setText("👤 官方账户关联" if is_zh else "👤 Account Link")
        self.btn_browser_sync.setText("在浏览器打开官网一键同步" if is_zh else "Open Browser to Link")
        self.btn_logout.setText("解除绑定" if is_zh else "Unlink")
        self.btn_verify_token.setText("绑定 Token" if is_zh else "Verify Token")

        self.lbl_tts_title.setText("🎙️ 发音偏好设置" if is_zh else "🎙️ Speech Preferences")
        self.lbl_pref_title.setText("⚙️ 偏好设置" if is_zh else "⚙️ Preferences")
        self.lbl_lang_sel.setText("界面语言" if is_zh else "Language")
        self.lbl_th_sel.setText("主题外观" if is_zh else "Theme")
        self.cb_tray.setText(
            "关闭窗口时最小化至托盘并在后台运行" if is_zh else "Minimize to tray on window close"
        )
        self.btn_open_doctor.setText(
            "🩺 系统环境与网络健康体检" if is_zh else "🩺 System & Network Health Doctor"
        )
        self.lbl_doctor_hint.setText(
            "一键排查 YouTube、BBC、Edge-TTS、Kokoro 模型与本地服务状态" if is_zh
            else "Check YouTube, BBC, Edge-TTS, Kokoro and local services"
        )
        self._refresh_account_ui()

    def _open_doctor_dialog(self):
        diag = SystemDoctorDialog(self)
        diag.exec()
