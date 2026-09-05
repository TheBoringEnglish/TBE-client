# -*- coding: utf-8 -*-
"""
足迹出片历史记录与管理视图 (FootprintsView)
由 theboringenglish.com 网页端学习足迹调起生成，本地自动归档出片历史，随时回看与重新预览。
"""

import webbrowser
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer

from .components.badge import StatusBadge
from ..core.video_history import VideoHistoryManager
from ..core.remotion_bridge import RemotionBridge
from ..core.i18n import t
from ..config import config


class FootprintsView(QWidget):
    """足迹视频出片历史管理"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.remotion_bridge = RemotionBridge()
        self.records = []
        self._init_ui()
        self.load_history()

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(36, 24, 36, 24)
        main_lay.setSpacing(16)

        # ── 1. 顶部操作栏 ──
        top_bar = QHBoxLayout()
        self.lbl_title = QLabel("出片历史")
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: 700; letter-spacing: -0.4px;")
        top_bar.addWidget(self.lbl_title)
        top_bar.addStretch()

        self.btn_web_footprints = QPushButton("打开网页端足迹")
        self.btn_web_footprints.setProperty("class", "btnPrimary")
        self.btn_web_footprints.setCursor(Qt.PointingHandCursor)
        self.btn_web_footprints.clicked.connect(self._open_web_footprints)
        top_bar.addWidget(self.btn_web_footprints)

        self.btn_sync = QPushButton("刷新")
        self.btn_sync.setProperty("class", "btnSecondary")
        self.btn_sync.setCursor(Qt.PointingHandCursor)
        self.btn_sync.clicked.connect(self.load_history)
        top_bar.addWidget(self.btn_sync)

        main_lay.addLayout(top_bar)

        # ── 2. 统计与提示栏 ──
        stat_bar = QHBoxLayout()
        self.lbl_list_count = QLabel("共 0 条视频记录")
        self.lbl_list_count.setStyleSheet("font-size: 12.5px; color: #94A3B8;")
        stat_bar.addWidget(self.lbl_list_count)
        stat_bar.addStretch()

        self.badge_status = StatusBadge("就绪", "success")
        stat_bar.addWidget(self.badge_status)
        main_lay.addLayout(stat_bar)

        # ── 3. 滚动容器与历史卡片 ──
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)

        self.scroll_area.setWidget(self.scroll_content)
        main_lay.addWidget(self.scroll_area)

    def _open_web_footprints(self):
        base_url = config.get("server_url", "https://theboringenglish.com").rstrip("/")
        webbrowser.open(f"{base_url}/history")

    def load_history(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.records = VideoHistoryManager.load_history()
        is_zh = config.get("language", "zh_CN") == "zh_CN"
        self.lbl_list_count.setText(f"共 {len(self.records)} 条视频记录" if is_zh else f"Total {len(self.records)} videos")

        if not self.records:
            self._render_empty_state()
            return

        for rec in self.records:
            card = self._create_record_card(rec)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _render_empty_state(self):
        empty_frame = QFrame()
        empty_frame.setProperty("class", "card")
        e_lay = QVBoxLayout(empty_frame)
        e_lay.setContentsMargins(40, 40, 40, 40)
        e_lay.setAlignment(Qt.AlignCenter)
        e_lay.setSpacing(12)

        ico = QLabel("🎬")
        ico.setStyleSheet("font-size: 36px;")
        ico.setAlignment(Qt.AlignCenter)
        e_lay.addWidget(ico)

        t_lbl = QLabel("暂无生成记录")
        t_lbl.setStyleSheet("font-size: 15px; font-weight: 700;")
        t_lbl.setAlignment(Qt.AlignCenter)
        e_lay.addWidget(t_lbl)

        d_lbl = QLabel("在 theboringenglish.com 网页端学习足迹中点击「一键 Remotion 预览」，将在此自动归档。")
        d_lbl.setStyleSheet("font-size: 12.5px; color: #94A3B8;")
        d_lbl.setAlignment(Qt.AlignCenter)
        e_lay.addWidget(d_lbl)

        btn_go = QPushButton("前往网页端足迹")
        btn_go.setProperty("class", "btnPrimary")
        btn_go.setFixedWidth(160)
        btn_go.clicked.connect(self._open_web_footprints)
        e_lay.addWidget(btn_go, alignment=Qt.AlignCenter)

        self.cards_layout.addWidget(empty_frame)
        self.cards_layout.addStretch()

    def _create_record_card(self, rec: dict) -> QFrame:
        card = QFrame()
        card.setProperty("class", "recordCard")
        c_lay = QHBoxLayout(card)
        c_lay.setContentsMargins(18, 14, 18, 14)
        c_lay.setSpacing(14)

        info_box = QVBoxLayout()
        info_box.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        lbl_title = QLabel(rec.get("title", "未命名视频"))
        lbl_title.setStyleSheet("font-size: 14.5px; font-weight: 700; color: #F8FAFC;")
        # 修复：长标题超出卡片宽度时换行，避免布局被撑破
        lbl_title.setWordWrap(True)
        lbl_title.setMaximumWidth(520)
        title_row.addWidget(lbl_title)

        status_badge = StatusBadge("已就绪", "success")
        title_row.addWidget(status_badge)
        title_row.addStretch()
        info_box.addLayout(title_row)

        meta_str = f"时间: {rec.get('generated_at')}   |   模板: {rec.get('template_name', rec.get('project_id'))}   |   时长: {rec.get('duration')}   |   来源: {rec.get('source')}"
        lbl_meta = QLabel(meta_str)
        lbl_meta.setStyleSheet("font-size: 11.5px; color: #94A3B8;")
        info_box.addWidget(lbl_meta)

        c_lay.addLayout(info_box)
        c_lay.addStretch()

        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        btn_preview = QPushButton("浏览器预览")
        btn_preview.setProperty("class", "btnPrimary")
        btn_preview.setCursor(Qt.PointingHandCursor)
        btn_preview.clicked.connect(lambda: self._reopen_preview(rec))
        btn_box.addWidget(btn_preview)

        btn_copy = QPushButton("📋")
        btn_copy.setProperty("class", "toolCircleBtn")
        btn_copy.setToolTip("复制预览链接")
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.clicked.connect(lambda: self._copy_preview_link(rec, btn_copy))
        btn_box.addWidget(btn_copy)

        btn_del = QPushButton("🗑️")
        btn_del.setProperty("class", "toolCircleBtn")
        btn_del.setToolTip("删除记录")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.clicked.connect(lambda: self._delete_record(rec.get("id")))
        btn_box.addWidget(btn_del)

        c_lay.addLayout(btn_box)
        return card

    def _reopen_preview(self, rec: dict):
        project_id = rec.get("project_id", "remotion_text1")
        port = rec.get("port", 3000)
        self.remotion_bridge.launch_preview(project_id=project_id, port=port)

    def _copy_preview_link(self, rec: dict, btn: QPushButton):
        """复制预览链接到剪贴板，并短暂提示用户"""
        url = rec.get("preview_url") or f"http://localhost:{rec.get('port', 3000)}"
        QApplication.clipboard().setText(url)
        original_text = btn.toolTip()
        btn.setText("✅")
        QTimer.singleShot(1800, lambda: btn.setText("📋"))

    def _delete_record(self, record_id: str):
        if QMessageBox.question(self, "确认", "确定删除该记录？", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            VideoHistoryManager.delete_record(record_id)
            self.load_history()

    def retranslate_ui(self):
        """仅更新顶部标签文字，不重建卡片（避免触发磁盘 I/O + UI 重建）"""
        is_zh = config.get("language", "zh_CN") == "zh_CN"
        self.lbl_title.setText("出片历史" if is_zh else "Video History")
        self.btn_web_footprints.setText("打开网页端足迹" if is_zh else "Open Web History")
        self.btn_sync.setText("刷新" if is_zh else "Refresh")
        # 仅更新记录数量文本，不重建卡片
        count = len(self.records)
        self.lbl_list_count.setText(
            f"共 {count} 条视频记录" if is_zh else f"Total {count} videos"
        )
