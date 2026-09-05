# -*- coding: utf-8 -*-
"""
系统环境与网络健康诊断对话框 (SystemDoctorDialog)
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
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QProgressBar, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtCore import QUrl

from ..core.doctor import SystemDoctorThread
from ..core.i18n import t


class SystemDoctorDialog(QDialog):
    """系统与网络体检对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("doctor_title"))
        self.resize(620, 680)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.doctor_thread = None
        self.item_cards = {}
        self.report_data = {}

        self._init_ui()
        # 弹窗打开后稍延迟自动启动体检
        QTimer.singleShot(200, self.start_check)

    def _init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(24, 20, 24, 20)
        root_lay.setSpacing(16)

        # ── 1. 顶部 Header 与综合状态评分卡片 ──
        self.score_card = QFrame()
        self.score_card.setProperty("class", "card")
        self.score_card.setStyleSheet("border-radius: 16px; padding: 12px;")
        sc_lay = QHBoxLayout(self.score_card)
        sc_lay.setContentsMargins(18, 14, 18, 14)
        sc_lay.setSpacing(16)

        # 左侧健康图标与评分
        score_left = QVBoxLayout()
        score_left.setSpacing(4)
        self.lbl_score_num = QLabel("诊断中...")
        self.lbl_score_num.setStyleSheet("font-size: 26px; font-weight: 800; color: #F97316;")
        self.lbl_score_sub = QLabel("正在并发检测网络与环境依赖...")
        self.lbl_score_sub.setStyleSheet("font-size: 12.5px; color: #94A3B8;")
        score_left.addWidget(self.lbl_score_num)
        score_left.addWidget(self.lbl_score_sub)
        sc_lay.addLayout(score_left)

        sc_lay.addStretch()

        # 重新体检按钮
        self.btn_recheck = QPushButton(t("doctor_recheck"))
        self.btn_recheck.setProperty("class", "btnSecondary")
        self.btn_recheck.setFixedHeight(36)
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
        self.list_layout.setSpacing(10)

        # 预设 8 个检查项卡片骨架
        self.ordered_items = [
            ("youtube", "YouTube 访问连通性", "海外精读视频与字幕数据流"),
            ("bbc", "BBC 学习与媒体原声", "英伦地道原声听力与双语素材"),
            ("tbe_web", "TheBoringEnglish 官网 API", "官网学习记录与免密一键同步通道"),
            ("edge_tts", "Edge-TTS 在线神经发音", "高保真真人发音合成音频流"),
            ("kokoro", "Kokoro 本地离线发音模型", "本地神经发音权重 (断网可用)"),
            ("ffmpeg", "多媒体 FFmpeg 编解码支持", "本地音视频切片与音频转码"),
            ("nodejs", "Node.js 视频合成环境", "Remotion 高清学习视频工程渲染"),
            ("local_port", "客户端 6502 本地服务", "浏览器网页端一键同步出片通道"),
        ]

        for item_id, title, desc in self.ordered_items:
            card = QFrame()
            card.setProperty("class", "card")
            card.setStyleSheet("border-radius: 12px; padding: 6px 12px;")
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(14, 10, 14, 10)
            c_lay.setSpacing(12)

            lbl_icon = QLabel("⏳")
            lbl_icon.setStyleSheet("font-size: 18px;")
            c_lay.addWidget(lbl_icon)

            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("font-size: 13.5px; font-weight: 600;")
            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet("font-size: 11.5px; color: #94A3B8;")
            text_box.addWidget(lbl_title)
            text_box.addWidget(lbl_desc)
            c_lay.addLayout(text_box)

            c_lay.addStretch()

            # 右侧状态徽章与延迟
            status_box = QVBoxLayout()
            status_box.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            status_box.setSpacing(2)
            lbl_status = QLabel("等待检测...")
            lbl_status.setStyleSheet("font-size: 12px; font-weight: 500; color: #94A3B8;")
            lbl_extra = QLabel("")
            lbl_extra.setStyleSheet("font-size: 11px; color: #64748B;")
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
                "download_link": None  # 必要时动态添加
            }

        self.list_layout.addStretch()
        scroll.setWidget(list_container)
        root_lay.addWidget(scroll)

        # ── 3. 底部操作栏 ──
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(12)

        self.btn_copy_report = QPushButton("📋 复制体检报告")
        self.btn_copy_report.setProperty("class", "btnSecondary")
        self.btn_copy_report.setFixedHeight(36)
        self.btn_copy_report.setCursor(Qt.PointingHandCursor)
        self.btn_copy_report.clicked.connect(self._copy_report)
        bottom_bar.addWidget(self.btn_copy_report)

        bottom_bar.addStretch()

        self.btn_close = QPushButton("完成")
        self.btn_close.setProperty("class", "btnPrimary")
        self.btn_close.setFixedHeight(36)
        self.btn_close.setFixedWidth(100)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(self.btn_close)

        root_lay.addLayout(bottom_bar)

    def start_check(self):
        """开始执行全面体检"""
        if self.doctor_thread and self.doctor_thread.isRunning():
            return

        self.btn_recheck.setEnabled(False)
        self.progress_bar.setValue(0)
        self.lbl_score_num.setText("诊断中...")
        self.lbl_score_num.setStyleSheet("font-size: 26px; font-weight: 800; color: #F97316;")
        self.lbl_score_sub.setText("正在并发检测网络与环境依赖...")

        # 重置卡片状态
        for item_id, card_dict in self.item_cards.items():
            card_dict["icon"].setText("⏳")
            card_dict["status"].setText("检测中...")
            card_dict["status"].setStyleSheet("font-size: 12px; color: #94A3B8;")
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
            card_dict["status"].setStyleSheet("font-size: 12px; font-weight: 600; color: #10B981;")
            if latency > 0:
                card_dict["extra"].setText(f"延迟: {latency} ms")
            else:
                card_dict["extra"].setText(desc)
        elif status == "warn":
            card_dict["icon"].setText("⚠️")
            card_dict["status"].setText(msg)
            card_dict["status"].setStyleSheet("font-size: 12px; font-weight: 600; color: #F59E0B;")
            card_dict["extra"].setText(desc)
        else:
            card_dict["icon"].setText("❌")
            card_dict["status"].setText(msg)
            card_dict["status"].setStyleSheet("font-size: 12px; font-weight: 600; color: #EF4444;")
            card_dict["extra"].setText(desc)

        # 对 FFmpeg / Node.js 的 warn/fail 状态，显示快捷下载链接
        download_urls = {
            "ffmpeg": ("https://ffmpeg.org/download.html", "📥 下载 FFmpeg"),
            "nodejs": ("https://nodejs.org/zh-cn/download", "📥 下载 Node.js"),
        }
        if item_id in download_urls and status in ("warn", "fail"):
            url, link_text = download_urls[item_id]
            lbl_dl = card_dict.get("download_link")
            if lbl_dl is None:
                # 首次创建链接标签，插入到 status_box 层
                lbl_dl = QLabel(f'<a href="{url}" style="color: #38BDF8;">{link_text} ↗</a>')
                lbl_dl.setStyleSheet("font-size: 11px;")
                lbl_dl.setOpenExternalLinks(True)
                # 将标签添加到卡片布局的主布局中
                card_dict["card"].layout().itemAt(3).layout().addWidget(lbl_dl)
                card_dict["download_link"] = lbl_dl
            else:
                lbl_dl.setVisible(True)

    def _on_all_finished(self, score: int, all_results: dict):
        self.btn_recheck.setEnabled(True)
        self.progress_bar.setValue(8)

        if score >= 90:
            self.lbl_score_num.setText(f"{score} 分 · 状态极佳 🚀")
            self.lbl_score_num.setStyleSheet("font-size: 26px; font-weight: 800; color: #10B981;")
            self.lbl_score_sub.setText("所有核心网络与发音环境均运作良好，尽享畅快学习体验！")
        elif score >= 70:
            self.lbl_score_num.setText(f"{score} 分 · 基本正常 ⚠️")
            self.lbl_score_num.setStyleSheet("font-size: 26px; font-weight: 800; color: #F59E0B;")
            self.lbl_score_sub.setText("核心服务正常，部分离线模型或外网通道受限，建议按提示检查。")
        else:
            self.lbl_score_num.setText(f"{score} 分 · 需要排查 ❌")
            self.lbl_score_num.setStyleSheet("font-size: 26px; font-weight: 800; color: #EF4444;")
            self.lbl_score_sub.setText("关键网络通道或服务受阻，请检查网络连接、本地代理或梯子设置。")

    def _copy_report(self):
        """将体检结果格式化并写入系统剪贴板"""
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
        full_text = "\n".join(lines)
        QApplication.clipboard().setText(full_text)
        self.btn_copy_report.setText("✅ 已复制到剪贴板")
        QTimer.singleShot(2000, lambda: self.btn_copy_report.setText("📋 复制体检报告"))
