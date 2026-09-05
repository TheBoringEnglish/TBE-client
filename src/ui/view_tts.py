# -*- coding: utf-8 -*-
"""
本地发音工坊视图 (TTSView)
支持自由文本输入、多角色音色试听对比、语速音调微调、异步后台合成与一键导出音频。
"""

import time
import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QComboBox, QSlider, QFrame, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal

from .components.audio_player import ModernAudioPlayer
from .components.badge import StatusBadge
from ..core.tts_engine import LocalTTSManager, SUPPORTED_VOICES
from ..config import config


# 经典示例英文语句
PRESET_SNIPPETS = [
    ("经典演说 · 乔布斯", "Stay hungry, stay foolish. Your time is limited, so don't waste it living someone else's life."),
    ("生活大爆炸 · Sheldon", "I'm not crazy. My mother had me tested! Bazinga!"),
    ("科技日常 · 硅谷", "Let's align on the architectural RFC before pushing this feature into production."),
    ("自然跟读 · 咖啡日常", "Could I please get an iced oat latte with an extra espresso shot to go?"),
]


class TTSWorkerThread(QThread):
    """异步后台语音合成线程"""
    finished_signal = Signal(object, str, float)  # (audio_bytes, error_msg, elapsed_time)

    def __init__(self, tts_mgr: LocalTTSManager, text: str, voice_id: str, speed: float, pitch: str):
        super().__init__()
        self.tts_mgr = tts_mgr
        self.text = text
        self.voice_id = voice_id
        self.speed = speed
        self.pitch = pitch

    def run(self):
        t0 = time.time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            audio_bytes, err = loop.run_until_complete(
                self.tts_mgr.synthesize(self.text, self.voice_id, self.speed, self.pitch)
            )
            elapsed = time.time() - t0
            self.finished_signal.emit(audio_bytes, err or "", elapsed)
        except Exception as e:
            elapsed = time.time() - t0
            self.finished_signal.emit(None, str(e), elapsed)
        finally:
            loop.close()


class TTSView(QWidget):
    """本地发音工坊"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tts_mgr = LocalTTSManager()
        self.worker: TTSWorkerThread = None
        self._init_ui()

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(28, 24, 28, 24)
        main_lay.setSpacing(16)

        # 顶部标题栏
        top_bar = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(4)

        title = QLabel("🎙️ 本地发音工坊 (TTS Studio)")
        title.setStyleSheet("font-size: 20px; font-weight: 700; letter-spacing: -0.4px;")
        header_text.addWidget(title)

        subtitle = QLabel("输入任意英语句子或段落，秒级合成母语者级纯正发音，支持离线 AI 与高保真神经音色")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")
        header_text.addWidget(subtitle)
        top_bar.addLayout(header_text)
        top_bar.addStretch()

        self.badge_engine = StatusBadge("双模发音已就绪", "success")
        top_bar.addWidget(self.badge_engine)
        main_lay.addLayout(top_bar)

        # 预设范例选择栏
        preset_row = QHBoxLayout()
        lbl_preset = QLabel("💡 试听预设范例:")
        lbl_preset.setStyleSheet("color: #94A3B8; font-weight: 500; font-size: 12.5px;")
        preset_row.addWidget(lbl_preset)

        for title_str, text_str in PRESET_SNIPPETS:
            btn_snippet = QPushButton(title_str)
            btn_snippet.setProperty("class", "btnSecondary")
            btn_snippet.clicked.connect(lambda _, t=text_str: self.text_edit.setPlainText(t))
            preset_row.addWidget(btn_snippet)

        preset_row.addStretch()
        main_lay.addLayout(preset_row)

        # 文本编辑卡片
        input_card = QFrame()
        input_card.setProperty("class", "card")
        ic_lay = QVBoxLayout(input_card)
        ic_lay.setContentsMargins(16, 14, 16, 14)
        ic_lay.setSpacing(10)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在此输入或粘贴需要发音的英文句子或文章段落...")
        self.text_edit.setPlainText("Stay hungry, stay foolish. Your time is limited, so don't waste it living someone else's life.")
        self.text_edit.setStyleSheet("font-size: 14.5px; line-height: 1.5; min-height: 110px;")
        ic_lay.addWidget(self.text_edit)

        # 底部发音控制面板（音色、语速、合成按钮）
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(16)

        # 1. 音色选择
        voice_box = QVBoxLayout()
        voice_box.setSpacing(4)
        lbl_voice = QLabel("音色角色:")
        lbl_voice.setStyleSheet("color: #94A3B8; font-size: 12px;")
        voice_box.addWidget(lbl_voice)

        self.combo_voice = QComboBox()
        default_v = config.get("tts_voice", "en-US-JennyNeural")
        cur_idx = 0
        for i, v in enumerate(SUPPORTED_VOICES):
            self.combo_voice.addItem(v["name"], v["id"])
            if v["id"] == default_v:
                cur_idx = i
        self.combo_voice.setCurrentIndex(cur_idx)
        voice_box.addWidget(self.combo_voice)
        ctrl_row.addLayout(voice_box)

        # 2. 语速调节
        speed_box = QVBoxLayout()
        speed_box.setSpacing(4)
        self.lbl_speed_val = QLabel("语速: 1.0x")
        self.lbl_speed_val.setStyleSheet("color: #94A3B8; font-size: 12px;")
        speed_box.addWidget(self.lbl_speed_val)

        speed_slider_row = QHBoxLayout()
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(5, 20)  # 0.5x ~ 2.0x
        self.slider_speed.setValue(10)     # 1.0x
        self.slider_speed.setFixedWidth(140)
        self.slider_speed.valueChanged.connect(self._on_speed_changed)
        speed_slider_row.addWidget(self.slider_speed)
        speed_box.addLayout(speed_slider_row)
        ctrl_row.addLayout(speed_box)

        ctrl_row.addStretch()

        # 3. 合成动作按钮
        self.btn_synth = QPushButton("⚡ 立即合成发音")
        self.btn_synth.setProperty("class", "btnPrimary")
        self.btn_synth.setFixedSize(150, 42)
        self.btn_synth.clicked.connect(self.start_synthesize)
        ctrl_row.addWidget(self.btn_synth)

        ic_lay.addLayout(ctrl_row)
        main_lay.addWidget(input_card)

        # 音频播放器组件
        self.player_card = ModernAudioPlayer()
        main_lay.addWidget(self.player_card)

        # 状态指示与提示条
        self.lbl_status = QLabel("就绪 · 点击「立即合成发音」试听效果")
        self.lbl_status.setStyleSheet("color: #64748B; font-size: 12px;")
        main_lay.addWidget(self.lbl_status)

        main_lay.addStretch()

    def _on_speed_changed(self, val):
        speed_val = val / 10.0
        self.lbl_speed_val.setText(f"语速: {speed_val:.1f}x")

    def start_synthesize(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入需要发音的英文文本！")
            return

        voice_id = self.combo_voice.currentData()
        speed = self.slider_speed.value() / 10.0

        self.btn_synth.setEnabled(False)
        self.btn_synth.setText("⏳ 合成中...")
        self.lbl_status.setText("正在通过本地算力引擎合成母语发音...")

        self.worker = TTSWorkerThread(self.tts_mgr, text, voice_id, speed, "+0Hz")
        self.worker.finished_signal.connect(self._on_synth_finished)
        self.worker.start()

    def _on_synth_finished(self, audio_bytes, err_msg, elapsed):
        self.btn_synth.setEnabled(True)
        self.btn_synth.setText("⚡ 立即合成发音")

        if audio_bytes:
            self.lbl_status.setText(f"✅ 合成成功！音频大小: {len(audio_bytes) // 1024} KB · 耗时: {elapsed:.2f}s")
            self.player_card.load_audio_bytes(audio_bytes, file_ext=".mp3")
            self.player_card.toggle_play()
        else:
            self.lbl_status.setText(f"❌ 合成失败: {err_msg}")
            QMessageBox.warning(self, "合成出错", f"无法生成音频: {err_msg}")
