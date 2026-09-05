# -*- coding: utf-8 -*-
"""
现代化原生音频播放控制器 (ModernAudioPlayer)
基于 PySide6 QMediaPlayer 实现，支持实时波形拖拽、播放/暂停、播放计时与一键另存为。
"""

import os
import tempfile
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, QLabel, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class ModernAudioPlayer(QFrame):
    """现代流线型音频播放条"""

    exported_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.current_audio_bytes: bytes = b""
        self.temp_file_path: str = ""

        self._init_player()
        self._init_ui()

    def _init_player(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)

        # 播放/暂停 按钮
        self.btn_play = QPushButton("▶ 播放")
        self.btn_play.setProperty("class", "btnPrimary")
        self.btn_play.setFixedWidth(84)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setEnabled(False)
        lay.addWidget(self.btn_play)

        # 进度滑块
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self._on_slider_moved)
        self.slider.setEnabled(False)
        lay.addWidget(self.slider)

        # 时间显示
        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setStyleSheet("color: #94A3B8; font-size: 12px; font-family: monospace;")
        lay.addWidget(self.lbl_time)

        # 导出/另存为 按钮
        self.btn_export = QPushButton("💾 导出音频")
        self.btn_export.setProperty("class", "btnSecondary")
        self.btn_export.clicked.connect(self._export_audio)
        self.btn_export.setEnabled(False)
        lay.addWidget(self.btn_export)

    def load_audio_bytes(self, audio_bytes: bytes, file_ext: str = ".mp3"):
        """加载内存中的音频数据并准备播放"""
        self.current_audio_bytes = audio_bytes
        if not audio_bytes:
            self.btn_play.setEnabled(False)
            self.slider.setEnabled(False)
            self.btn_export.setEnabled(False)
            self.lbl_time.setText("00:00 / 00:00")
            return

        # 写入临时文件供 QMediaPlayer 读取
        try:
            fd, tmp = tempfile.mkstemp(suffix=file_ext)
            with os.fdopen(fd, "wb") as f:
                f.write(audio_bytes)
            self.temp_file_path = tmp
            self.player.setSource(QUrl.fromLocalFile(tmp))
            self.btn_play.setEnabled(True)
            self.slider.setEnabled(True)
            self.btn_export.setEnabled(True)
        except Exception as e:
            print(f"[Player] 载入音频失败: {e}")

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.btn_play.setText("⏸ 暂停")
        else:
            self.btn_play.setText("▶ 播放")

    def _on_position_changed(self, position):
        if not self.slider.isSliderDown():
            self.slider.setValue(position)
        self._update_time_label(position, self.player.duration())

    def _on_duration_changed(self, duration):
        self.slider.setRange(0, duration)
        self._update_time_label(self.player.position(), duration)

    def _on_slider_moved(self, position):
        self.player.setPosition(position)

    def _update_time_label(self, current_ms, total_ms):
        c_sec = int(current_ms / 1000)
        t_sec = int(total_ms / 1000)
        c_str = f"{c_sec // 60:02d}:{c_sec % 60:02d}"
        t_str = f"{t_sec // 60:02d}:{t_sec % 60:02d}"
        self.lbl_time.setText(f"{c_str} / {t_str}")

    def _export_audio(self):
        if not self.current_audio_bytes:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "导出音频文件", "tbe_speech.mp3", "Audio Files (*.mp3 *.wav)"
        )
        if save_path:
            try:
                with open(save_path, "wb") as f:
                    f.write(self.current_audio_bytes)
                QMessageBox.information(self, "导出成功", f"音频已保存至:\n{save_path}")
                self.exported_signal.emit(save_path)
            except Exception as e:
                QMessageBox.warning(self, "导出失败", f"保存出错: {e}")
