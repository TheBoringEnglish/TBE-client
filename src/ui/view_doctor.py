# -*- coding: utf-8 -*-
"""
系统环境与网络健康诊断视图 (DoctorView)
集成在主窗口 Tab 中，无需弹窗。
支持实时检测：
- YouTube 访问连通性与握手延迟
- BBC 原声学习连通性与握手延迟
- theboringenglish.com 官网服务连通性
- Edge-TTS 微软云端神经发音连通与回包
- Kokoro 本地离线发音模型就绪状态
- FFmpeg 多媒体音视频命令
- Node.js 视频合成运行时
- 客户端 6502 本地免密与出片同步服务
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QProgressBar, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from ..core.doctor import SystemDoctorThread
from ..core.i18n import t


class DoctorView(QWidget):
    """系统与网络体检视图（内嵌于主窗口 Tab）"""

    navigate_signal = Signal(str)   # 发送导航请求到 MainWindow

    def __init__(self, parent=None):
        super().__init__(parent)
        self.doctor_thread = None
        self.item_cards = {}
        self.report_data = {}
        self._has_checked_once = False   # 只在首次显示时自动触发

        self._init_ui()

    def _init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(28, 20, 28, 20)
        root_lay.setSpacing(14)

        # ── 1. 顶部评分卡片 ──
        self.score_card = QFrame()
        self.score_card.setProperty("class", "card")
        sc_lay = QHBoxLayout(self.score_card)
        sc_lay.setContentsMargins(18, 14, 18, 14)
        sc_lay.setSpacing(16)

        score_left = QVBoxLayout()
        score_left.setSpacing(4)
        self.lbl_score_num = QLabel("等待检测...")
        self.lbl_score_num.setStyleSheet("font-size: 24px; font-weight: 800; color: #F97316;")
        self.lbl_score_sub = QLabel("点击「重新体检」或切换到此页面自动开始")
        self.lbl_score_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        score_left.addWidget(self.lbl_score_num)
        score_left.addWidget(self.lbl_score_sub)
        sc_lay.addLayout(score_left)
        sc_lay.addStretch()

        self.btn_recheck = QPushButton("重检")
        self.btn_recheck.setProperty("class", "btnSecondary")
        self.btn_recheck.setFixedHeight(32)
        self.btn_recheck.setCursor(Qt.PointingHandCursor)
        self.btn_recheck.clicked.connect(self.start_check)
        sc_lay.addWidget(self.btn_recheck)

        root_lay.addWidget(self.score_card)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 8)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: #10B981;
                border-radius: 2px;
            }
        """)
        root_lay.addWidget(self.progress_bar)

        # ── 2. 检查项滚动列表 ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        list_container = QWidget()
        list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        self.ordered_items = [
            ("youtube",    "YouTube 访问连通性",         "海外精读视频与字幕数据流"),
            ("bbc",        "BBC 学习与媒体原声",         "英伦地道原声听力与双语素材"),
            ("tbe_web",    "TheBoringEnglish 官网 API", "官网学习记录与免密一键同步通道"),
            ("edge_tts",   "Edge-TTS 在线神经发音",      "高保真真人发音合成音频流"),
            ("kokoro",     "Kokoro 本地离线发音模型",    "本地神经发音权重 (断网可用)"),
            ("ffmpeg",     "FFmpeg 编解码支持",          "本地音视频切片与音频转码"),
            ("nodejs",     "Node.js 视频合成环境",       "Remotion 高清学习视频工程渲染"),
            ("local_port", "客户端 6502 本地服务",       "浏览器网页端一键同步出片通道"),
        ]

        for item_id, title, desc in self.ordered_items:
            card = QFrame()
            card.setProperty("class", "card")
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(14, 10, 14, 10)
            c_lay.setSpacing(12)

            lbl_icon = QLabel("⏳")
            lbl_icon.setStyleSheet("font-size: 18px;")
            lbl_icon.setFixedWidth(24)
            c_lay.addWidget(lbl_icon)

            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #0F172A;")
            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet("font-size: 11px; color: #475569;")
            text_box.addWidget(lbl_title)
            text_box.addWidget(lbl_desc)
            c_lay.addLayout(text_box)
            c_lay.addStretch()

            status_box = QVBoxLayout()
            status_box.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            status_box.setSpacing(2)
            lbl_status = QLabel("等待检测...")
            lbl_status.setStyleSheet("font-size: 11.5px; font-weight: 500; color: #475569;")
            lbl_extra = QLabel("")
            lbl_extra.setStyleSheet("font-size: 10.5px; color: #64748B;")
            lbl_extra.setAlignment(Qt.AlignRight)
            status_box.addWidget(lbl_status)
            status_box.addWidget(lbl_extra)
            c_lay.addLayout(status_box)

            self.list_layout.addWidget(card)
            self.item_cards[item_id] = {
                "icon": lbl_icon,
                "title": lbl_title,
                "status": lbl_status,
                "extra": lbl_extra,
                "card": card,
                "download_link": None
            }

        self.list_layout.addStretch()
        scroll.setWidget(list_container)
        root_lay.addWidget(scroll)

        # ── 3. 底部操作栏 ──
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.btn_copy_report = QPushButton("复制")
        self.btn_copy_report.setProperty("class", "btnSecondary")
        self.btn_copy_report.setFixedHeight(32)
        self.btn_copy_report.setCursor(Qt.PointingHandCursor)
        self.btn_copy_report.clicked.connect(self._copy_report)
        bottom_bar.addWidget(self.btn_copy_report)

        bottom_bar.addStretch()

        btn_back = QPushButton("返回")
        btn_back.setProperty("class", "btnSecondary")
        btn_back.setFixedHeight(32)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.navigate_signal.emit("settings"))
        bottom_bar.addWidget(btn_back)

        root_lay.addLayout(bottom_bar)

    def showEvent(self, event):
        """第一次显示时自动触发体检"""
        super().showEvent(event)
        if not self._has_checked_once:
            self._has_checked_once = True
            QTimer.singleShot(300, self.start_check)

    def start_check(self):
        """开始全面体检"""
        if self.doctor_thread and self.doctor_thread.isRunning():
            return

        self.btn_recheck.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_score_num.setText("诊断中...")
        self.lbl_score_num.setStyleSheet("font-size: 24px; font-weight: 800; color: #F97316;")
        self.lbl_score_sub.setText("正在并发检测网络与环境依赖...")

        for item_id, card_dict in self.item_cards.items():
            card_dict["icon"].setText("⏳")
            card_dict["status"].setText("检测中...")
            card_dict["status"].setStyleSheet("font-size: 11.5px; color: #94A3B8;")
            card_dict["extra"].setText("")

        self.report_data.clear()
        self.doctor_thread = SystemDoctorThread(self)
        self.doctor_thread.item_checked_signal.connect(self._on_item_checked)
        self.doctor_thread.all_finished_signal.connect(self._on_all_finished)
        self.doctor_thread.start()

    def _on_item_checked(self, item_id: str, res: dict):
        self.report_data[item_id] = res
        card_dict = self.item_cards.get(item_id)
        if not card_dict:
            return

        self.progress_bar.setValue(self.progress_bar.value() + 1)
        status = res.get("status", "pass")
        latency = res.get("latency", 0)
        msg = res.get("msg", "")
        desc = res.get("desc", "")

        if status == "pass":
            card_dict["icon"].setText("✅")
            card_dict["status"].setText(msg)
            card_dict["status"].setStyleSheet("font-size: 11.5px; font-weight: 600; color: #10B981;")
            card_dict["extra"].setText(f"延迟: {latency} ms" if latency > 0 else desc)
        elif status == "warn":
            card_dict["icon"].setText("⚠️")
            card_dict["status"].setText(msg)
            card_dict["status"].setStyleSheet("font-size: 11.5px; font-weight: 600; color: #F59E0B;")
            card_dict["extra"].setText(desc)
        else:
            card_dict["icon"].setText("❌")
            card_dict["status"].setText(msg)
            card_dict["status"].setStyleSheet("font-size: 11.5px; font-weight: 600; color: #EF4444;")
            card_dict["extra"].setText(desc)

        download_urls = {
            "ffmpeg": ("https://ffmpeg.org/download.html", "下载 FFmpeg ↗"),
            "nodejs": ("https://nodejs.org/zh-cn/download", "下载 Node.js ↗"),
        }
        if item_id in download_urls and status in ("warn", "fail"):
            url, link_text = download_urls[item_id]
            lbl_dl = card_dict.get("download_link")
            if lbl_dl is None:
                lbl_dl = QLabel(f'<a href="{url}" style="color: #38BDF8;">{link_text}</a>')
                lbl_dl.setStyleSheet("font-size: 10.5px;")
                lbl_dl.setOpenExternalLinks(True)
                card_dict["card"].layout().itemAt(3).layout().addWidget(lbl_dl)
                card_dict["download_link"] = lbl_dl
            else:
                lbl_dl.setVisible(True)

    def _on_all_finished(self, score: int, all_results: dict):
        self.btn_recheck.setEnabled(True)
        self.progress_bar.setValue(8)

        if score >= 90:
            self.lbl_score_num.setText(f"{score} 分 · 状态极佳 🚀")
            self.lbl_score_num.setStyleSheet("font-size: 24px; font-weight: 800; color: #10B981;")
            self.lbl_score_sub.setText("所有核心网络与发音环境均运作良好，尽享畅快学习体验！")
        elif score >= 70:
            self.lbl_score_num.setText(f"{score} 分 · 基本正常 ⚠️")
            self.lbl_score_num.setStyleSheet("font-size: 24px; font-weight: 800; color: #F59E0B;")
            self.lbl_score_sub.setText("核心服务正常，部分离线模型或外网通道受限，建议按提示检查。")
        else:
            self.lbl_score_num.setText(f"{score} 分 · 需要排查 ❌")
            self.lbl_score_num.setStyleSheet("font-size: 24px; font-weight: 800; color: #EF4444;")
            self.lbl_score_sub.setText("关键网络通道或服务受阻，请检查网络连接、本地代理或梯子设置。")

    def _copy_report(self):
        lines = [
            "====================================",
            "   TheBoringEnglish 客户端体检报告",
            "====================================",
            f"健康状态: {self.lbl_score_num.text()}",
            f"诊断总结: {self.lbl_score_sub.text()}",
            "------------------------------------"
        ]
        for item_id, title, _ in self.ordered_items:
            res = self.report_data.get(item_id, {})
            status = res.get("status", "unknown").upper()
            msg = res.get("msg", "未检测")
            desc = res.get("desc", "")
            lines.append(f"[{status}] {title}: {msg} ({desc})")
        lines.append("====================================")
        QApplication.clipboard().setText("\n".join(lines))
        self.btn_copy_report.setText("已拷")
        QTimer.singleShot(2000, lambda: self.btn_copy_report.setText("复制"))

    def retranslate_ui(self):
        pass  # 预留国际化占位
