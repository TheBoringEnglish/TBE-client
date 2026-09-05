# -*- coding: utf-8 -*-
"""
学习足迹与一键 Remotion 视频预览视图 (FootprintsView)
打通用户在 TheBoringEnglish 的日常精读、跟读与生词足迹，一键转换为 Remotion 动画工程并拉起实时浏览器预览。
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QListWidget, QListWidgetItem, QSplitter, QTextEdit, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt

from .components.badge import StatusBadge
from ..core.footprint_api import FootprintAPI
from ..core.remotion_bridge import RemotionBridge


class FootprintsView(QWidget):
    """学习足迹与 Remotion 视频制作中心"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fp_api = FootprintAPI()
        self.remotion_bridge = RemotionBridge()
        self.footprints = []
        self.current_selected_fp = None
        self._init_ui()
        self.load_footprints()

    def _init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(28, 24, 28, 24)
        main_lay.setSpacing(16)

        # 顶部标题栏
        top_bar = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(4)

        title = QLabel("👣 学习足迹与一键 Remotion 视频 (Footprints & Video)")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #F1F5F9;")
        header_text.addWidget(title)

        subtitle = QLabel("选择任意历史学习记录，一键渲染为精美动态视频，本地无需复杂命令即可在浏览器实时预览")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")
        header_text.addWidget(subtitle)
        top_bar.addLayout(header_text)
        top_bar.addStretch()

        self.badge_sync = StatusBadge("未同步", "default")
        top_bar.addWidget(self.badge_sync)

        btn_sync = QPushButton("🔄 同步云端足迹")
        btn_sync.setProperty("class", "btnSecondary")
        btn_sync.clicked.connect(self.load_footprints)
        top_bar.addWidget(btn_sync)
        main_lay.addLayout(top_bar)

        # 中间左右分割器 (左边足迹列表，右边详细内容与 Remotion 预览配置)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #272C3D; width: 1px; }")

        # ── 左侧：足迹卡片列表 ──
        left_widget = QWidget()
        l_lay = QVBoxLayout(left_widget)
        l_lay.setContentsMargins(0, 0, 10, 0)
        l_lay.setSpacing(10)

        lbl_list_title = QLabel("我的学习历史档案:")
        lbl_list_title.setStyleSheet("font-weight: 600; color: #94A3B8; font-size: 13px;")
        l_lay.addWidget(lbl_list_title)

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_item_selected)
        l_lay.addWidget(self.list_widget)
        splitter.addWidget(left_widget)

        # ── 右侧：内容预览与 Remotion 出片操作 ──
        right_widget = QWidget()
        r_lay = QVBoxLayout(right_widget)
        r_lay.setContentsMargins(10, 0, 0, 0)
        r_lay.setSpacing(12)

        self.lbl_detail_title = QLabel("请在左侧选择一条学习足迹")
        self.lbl_detail_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #F1F5F9;")
        r_lay.addWidget(self.lbl_detail_title)

        self.lbl_detail_meta = QLabel("")
        self.lbl_detail_meta.setStyleSheet("font-size: 12px; color: #94A3B8;")
        r_lay.addWidget(self.lbl_detail_meta)

        # 段落预览框
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setPlaceholderText("足迹中英句子与意群对齐数据将在此展示...")
        self.text_preview.setStyleSheet("font-size: 13.5px; line-height: 1.6;")
        r_lay.addWidget(self.text_preview)

        # 底部 Remotion 一键出片卡片
        action_card = QFrame()
        action_card.setProperty("class", "card")
        ac_lay = QVBoxLayout(action_card)
        ac_lay.setContentsMargins(16, 14, 16, 14)
        ac_lay.setSpacing(10)

        ac_title_row = QHBoxLayout()
        ac_title = QLabel("🎬 Remotion 视频预览控制台")
        ac_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #F1F5F9;")
        ac_title_row.addWidget(ac_title)
        ac_title_row.addStretch()

        self.badge_remotion_status = StatusBadge("未拉起", "info")
        ac_title_row.addWidget(self.badge_remotion_status)
        ac_lay.addLayout(ac_title_row)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(12)

        lbl_tpl = QLabel("选择视频模板:")
        lbl_tpl.setStyleSheet("color: #94A3B8;")
        ctrl_row.addWidget(lbl_tpl)

        self.combo_template = QComboBox()
        projects = self.remotion_bridge.get_projects()
        for p in projects:
            self.combo_template.addItem(p["name"], (p["id"], p.get("port", 3000)))
        ctrl_row.addWidget(self.combo_template)

        ctrl_row.addStretch()

        # 核心一键预览按钮
        self.btn_preview = QPushButton("🚀 一键 Remotion 预览")
        self.btn_preview.setProperty("class", "btnPrimary")
        self.btn_preview.setFixedSize(170, 40)
        self.btn_preview.clicked.connect(self._start_remotion_preview)
        ctrl_row.addWidget(self.btn_preview)

        ac_lay.addLayout(ctrl_row)

        self.lbl_remotion_hint = QLabel("提示：点击将自动格式化足迹素材，并在本地浏览器启动 Remotion 实时渲染预览")
        self.lbl_remotion_hint.setStyleSheet("color: #64748B; font-size: 11.5px;")
        ac_lay.addWidget(self.lbl_remotion_hint)

        r_lay.addWidget(action_card)
        splitter.addWidget(right_widget)

        # 设置左右比例 35% : 65%
        splitter.setStretchFactor(0, 35)
        splitter.setStretchFactor(1, 65)
        main_lay.addWidget(splitter)

    def load_footprints(self):
        """同步并更新足迹列表"""
        items, is_cloud, msg = self.fp_api.fetch_user_footprints()
        self.footprints = items

        self.badge_sync.set_status("success" if is_cloud else "default", "云端已同步" if is_cloud else "本地示例数据")

        self.list_widget.clear()
        for fp in items:
            title = fp.get("title", "未命名")
            date = fp.get("date", "")
            sc = fp.get("sentence_count", 0)

            item = QListWidgetItem(f"📄 {title}\n    📅 {date}  ·  {sc} 句意群")
            self.list_widget.addItem(item)

        if items:
            self.list_widget.setCurrentRow(0)

    def _on_item_selected(self, row: int):
        if row < 0 or row >= len(self.footprints):
            return

        fp = self.footprints[row]
        self.current_selected_fp = fp

        self.lbl_detail_title.setText(fp.get("title", ""))
        self.lbl_detail_meta.setText(f"类型: {fp.get('type')}  |  来源: {fp.get('source')}  |  预计视频时长: {fp.get('duration')}")

        # 格式化预览段落
        segments = fp.get("segments", [])
        text_content = []
        for i, s in enumerate(segments, 1):
            en = s.get("en", "")
            cn = s.get("cn", "")
            kw_list = [k.get("word") for k in (s.get("keywords") or []) if k.get("word")]
            kw_str = f" [重点词: {', '.join(kw_list)}]" if kw_list else ""
            text_content.append(f"【第 {i} 句】{en}\n  译文: {cn}{kw_str}\n")

        self.text_preview.setPlainText("\n".join(text_content))

    def _start_remotion_preview(self):
        """执行一键 Remotion 预览"""
        if not self.current_selected_fp:
            QMessageBox.warning(self, "提示", "请先在左侧选择需要制作视频的学习足迹！")
            return

        selected_data = self.combo_template.currentData()
        if not selected_data:
            project_id = "remotion_text1"
            port = 3000
        else:
            project_id, port = selected_data

        fp = self.current_selected_fp
        title = fp.get("title", "TBE Study Footprint")
        segments = fp.get("segments", [])

        self.lbl_remotion_hint.setText(f"正在转换数据并拉起 Remotion Studio ({project_id} @ 端口 {port})...")
        self.badge_remotion_status.set_status("warning", "拉起中...")

        # 转换并拉起
        ok, msg = self.remotion_bridge.launch_preview(
            project_id=project_id,
            port=port,
            payload_data={"title": title, "segments": segments}
        )

        if ok:
            self.badge_remotion_status.set_status("success", "已拉起预览")
            self.lbl_remotion_hint.setText(f"✅ {msg}")
        else:
            self.badge_remotion_status.set_status("danger", "拉起失败")
            self.lbl_remotion_hint.setText(f"❌ {msg}")
            QMessageBox.warning(self, "Remotion 提示", msg)
