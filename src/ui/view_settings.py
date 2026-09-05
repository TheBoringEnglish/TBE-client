# -*- coding: utf-8 -*-
"""
设置中心与模型管理视图 (SettingsView)
支持云端/本地服务器切换、用户安全授权 Token 管理、Kokoro 离线模型一键下载、导出目录选择与主题切换。
"""

import os
import urllib.request
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFrame, QFileDialog, QMessageBox, QCheckBox, QComboBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread

from .components.badge import StatusBadge
from ..config import config
from ..core.tts_engine import LocalTTSManager


class ModelDownloadWorker(QThread):
    """模型后台静默下载线程"""
    progress_signal = Signal(int, str)
    finished_signal = Signal(bool, str)

    def __init__(self, target_dir: str):
        super().__init__()
        self.target_dir = target_dir

    def run(self):
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            files = [
                ("kokoro-v1.0.fp16-gpu.onnx", "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.fp16-gpu.onnx"),
                ("voices-v1.0.bin", "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin")
            ]

            total_files = len(files)
            for idx, (filename, url) in enumerate(files):
                dest = os.path.join(self.target_dir, filename)
                self.progress_signal.emit(int((idx / total_files) * 100), f"正在下载 {filename}...")

                def reporthook(count, block_size, total_size):
                    if total_size > 0:
                        p = int((count * block_size / total_size) * 100)
                        file_progress = int(((idx + p / 100) / total_files) * 100)
                        self.progress_signal.emit(file_progress, f"下载中 {filename}: {p}%")

                urllib.request.urlretrieve(url, dest, reporthook=reporthook)

            self.progress_signal.emit(100, "下载完成！")
            self.finished_signal.emit(True, "Kokoro 离线模型与音色库已成功安装！")
        except Exception as e:
            self.finished_signal.emit(False, f"下载失败: {str(e)}")


class SettingsView(QWidget):
    """设置与管理中心"""

    theme_changed_signal = Signal(str)  # "dark" or "light"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tts_mgr = LocalTTSManager()
        self.dl_worker = None
        self._init_ui()

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(28, 24, 28, 24)
        main_lay.setSpacing(16)

        # 顶部标题栏
        top_bar = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(4)

        title = QLabel("⚙️ 系统设置与模型管理 (Settings)")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #F1F5F9;")
        header_text.addWidget(title)

        subtitle = QLabel("管理服务器通信链路、用户安全凭证、离线语音模型及软件外观偏好")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")
        header_text.addWidget(subtitle)
        top_bar.addLayout(header_text)
        top_bar.addStretch()

        btn_save_all = QPushButton("💾 保存全部配置")
        btn_save_all.setProperty("class", "btnPrimary")
        btn_save_all.clicked.connect(self._save_all_settings)
        top_bar.addWidget(btn_save_all)
        main_lay.addLayout(top_bar)

        # ── 卡片 1: 服务端连接与认证凭据 ──
        net_card = QFrame()
        net_card.setProperty("class", "card")
        nc_lay = QVBoxLayout(net_card)
        nc_lay.setContentsMargins(18, 16, 18, 16)
        nc_lay.setSpacing(12)

        lbl_net_title = QLabel("🌐 服务端与云端同步设置")
        lbl_net_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #F1F5F9;")
        nc_lay.addWidget(lbl_net_title)

        # Server URL
        row_srv = QHBoxLayout()
        lbl_srv = QLabel("TBE 服务地址:")
        lbl_srv.setFixedWidth(110)
        lbl_srv.setStyleSheet("color: #94A3B8;")
        self.input_server = QLineEdit(config.get("server_url", "https://theboringenglish.com"))
        row_srv.addWidget(lbl_srv)
        row_srv.addWidget(self.input_server)

        btn_preset_cloud = QPushButton("官方云端")
        btn_preset_cloud.setProperty("class", "btnSecondary")
        btn_preset_cloud.clicked.connect(lambda: self.input_server.setText("https://theboringenglish.com"))
        row_srv.addWidget(btn_preset_cloud)

        btn_preset_local = QPushButton("本地自建")
        btn_preset_local.setProperty("class", "btnSecondary")
        btn_preset_local.clicked.connect(lambda: self.input_server.setText("http://localhost:6401"))
        row_srv.addWidget(btn_preset_local)
        nc_lay.addLayout(row_srv)

        # User Token
        row_token = QHBoxLayout()
        lbl_token = QLabel("用户授权 Token:")
        lbl_token.setFixedWidth(110)
        lbl_token.setStyleSheet("color: #94A3B8;")
        self.input_token = QLineEdit(config.get("token", ""))
        self.input_token.setEchoMode(QLineEdit.Password)
        self.input_token.setPlaceholderText("在此粘贴从 TheBoringEnglish 网站获取的用户身份 Token...")
        row_token.addWidget(lbl_token)
        row_token.addWidget(self.input_token)

        self.btn_toggle_echo = QPushButton("👁 显示")
        self.btn_toggle_echo.setProperty("class", "btnSecondary")
        self.btn_toggle_echo.clicked.connect(self._toggle_token_echo)
        row_token.addWidget(self.btn_toggle_echo)
        nc_lay.addLayout(row_token)

        # Remotion Service URL
        row_remotion = QHBoxLayout()
        lbl_rem = QLabel("Remotion 服务:")
        lbl_rem.setFixedWidth(110)
        lbl_rem.setStyleSheet("color: #94A3B8;")
        self.input_remotion = QLineEdit(config.get("remotion_url", "http://localhost:6402"))
        row_remotion.addWidget(lbl_rem)
        row_remotion.addWidget(self.input_remotion)
        nc_lay.addLayout(row_remotion)

        main_lay.addWidget(net_card)

        # ── 卡片 2: 离线 AI 语音模型管理 ──
        model_card = QFrame()
        model_card.setProperty("class", "card")
        mc_lay = QVBoxLayout(model_card)
        mc_lay.setContentsMargins(18, 16, 18, 16)
        mc_lay.setSpacing(12)

        mc_title_row = QHBoxLayout()
        mc_title = QLabel("🧠 Kokoro 本地离线神经模型")
        mc_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #F1F5F9;")
        mc_title_row.addWidget(mc_title)
        mc_title_row.addStretch()

        self.badge_model = StatusBadge("检测中", "default")
        mc_title_row.addWidget(self.badge_model)
        mc_lay.addLayout(mc_title_row)

        row_mdl_path = QHBoxLayout()
        lbl_mp = QLabel("模型存放路径:")
        lbl_mp.setFixedWidth(110)
        lbl_mp.setStyleSheet("color: #94A3B8;")
        self.input_model_dir = QLineEdit(config.get("models_dir"))
        row_mdl_path.addWidget(lbl_mp)
        row_mdl_path.addWidget(self.input_model_dir)

        btn_browse_mdl = QPushButton("浏览...")
        btn_browse_mdl.setProperty("class", "btnSecondary")
        btn_browse_mdl.clicked.connect(self._browse_model_dir)
        row_mdl_path.addWidget(btn_browse_mdl)
        mc_lay.addLayout(row_mdl_path)

        # 下载进度与下载按钮
        dl_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        dl_row.addWidget(self.progress_bar)

        self.btn_download_model = QPushButton("📥 一键下载离线模型 (约 300MB)")
        self.btn_download_model.setProperty("class", "btnPrimary")
        self.btn_download_model.clicked.connect(self._start_download_model)
        dl_row.addWidget(self.btn_download_model)
        mc_lay.addLayout(dl_row)

        self.lbl_dl_status = QLabel("支持纯离线断网运行，零延迟高保真发音")
        self.lbl_dl_status.setStyleSheet("color: #64748B; font-size: 11.5px;")
        mc_lay.addWidget(self.lbl_dl_status)

        main_lay.addWidget(model_card)

        # ── 卡片 3: 本地输出与外观偏好 ──
        pref_card = QFrame()
        pref_card.setProperty("class", "card")
        pc_lay = QVBoxLayout(pref_card)
        pc_lay.setContentsMargins(18, 16, 18, 16)
        pc_lay.setSpacing(12)

        lbl_pref_title = QLabel("🎨 外观与行为设置")
        lbl_pref_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #F1F5F9;")
        pc_lay.addWidget(lbl_pref_title)

        row_theme = QHBoxLayout()
        lbl_th = QLabel("界面主题风格:")
        lbl_th.setFixedWidth(110)
        lbl_th.setStyleSheet("color: #94A3B8;")
        self.combo_theme = QComboBox()
        self.combo_theme.addItem("深邃暗黑 (Dark Modern)", "dark")
        self.combo_theme.addItem("极简透亮 (Light Minimal)", "light")
        self.combo_theme.setCurrentIndex(0 if config.get("theme", "dark") == "dark" else 1)
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        row_theme.addWidget(lbl_th)
        row_theme.addWidget(self.combo_theme)
        row_theme.addStretch()
        pc_lay.addLayout(row_theme)

        row_tray = QHBoxLayout()
        self.cb_tray = QCheckBox("关闭窗口时最小化至系统托盘，保持后台静默挂机")
        self.cb_tray.setChecked(config.get("minimize_to_tray", True))
        self.cb_tray.setStyleSheet("color: #F1F5F9;")
        row_tray.addWidget(self.cb_tray)
        pc_lay.addLayout(row_tray)

        main_lay.addWidget(pref_card)
        main_lay.addStretch()

        self._refresh_model_status()

    def _toggle_token_echo(self):
        if self.input_token.echoMode() == QLineEdit.Password:
            self.input_token.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_echo.setText("🔒 隐藏")
        else:
            self.input_token.setEchoMode(QLineEdit.Password)
            self.btn_toggle_echo.setText("👁 显示")

    def _browse_model_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择模型存放目录", self.input_model_dir.text())
        if d:
            self.input_model_dir.setText(d)
            self._refresh_model_status()

    def _refresh_model_status(self):
        ready, msg = self.tts_mgr.is_kokoro_model_ready()
        if ready:
            self.badge_model.set_status("success", "已安装")
            self.btn_download_model.setText("✅ 模型已就绪 (点击可重新校验)")
        else:
            self.badge_model.set_status("info", "未安装")
            self.btn_download_model.setText("📥 一键下载离线模型 (约 300MB)")

    def _start_download_model(self):
        target_kokoro = os.path.join(self.input_model_dir.text(), "kokoro")
        self.btn_download_model.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.dl_worker = ModelDownloadWorker(target_kokoro)
        self.dl_worker.progress_signal.connect(self._on_dl_progress)
        self.dl_worker.finished_signal.connect(self._on_dl_finished)
        self.dl_worker.start()

    def _on_dl_progress(self, val, text):
        self.progress_bar.setValue(val)
        self.lbl_dl_status.setText(text)

    def _on_dl_finished(self, ok, msg):
        self.btn_download_model.setEnabled(True)
        self.progress_bar.setVisible(False)
        if ok:
            QMessageBox.information(self, "成功", msg)
            self._refresh_model_status()
        else:
            QMessageBox.warning(self, "下载失败", msg)

    def _on_theme_changed(self):
        new_theme = self.combo_theme.currentData()
        config.set("theme", new_theme)
        self.theme_changed_signal.emit(new_theme)

    def _save_all_settings(self):
        config.set("server_url", self.input_server.text().strip())
        config.set("token", self.input_token.text().strip())
        config.set("remotion_url", self.input_remotion.text().strip())
        config.set("models_dir", self.input_model_dir.text().strip())
        config.set("theme", self.combo_theme.currentData())
        config.set("minimize_to_tray", self.cb_tray.isChecked())

        if config.save():
            QMessageBox.information(self, "保存成功", "所有配置已安全保存至本地主目录！")
        else:
            QMessageBox.warning(self, "错误", "配置保存失败，请检查文件写入权限！")
