# -*- coding: utf-8 -*-
"""
TBE Client 首次启动/安装引导向导 (SetupWizardDialog)
引导新用户选择语言与本地数据目录，配置完成后无缝进入主界面。
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QFileDialog, QFrame
)
from PySide6.QtCore import Qt
from ..config import config
from ..core.i18n import t, set_language


class SetupWizardDialog(QDialog):
    """初次使用配置向导弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("wiz_title"))
        self.resize(520, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 26)
        layout.setSpacing(18)

        # 头部欢迎
        top_box = QVBoxLayout()
        top_box.setSpacing(4)

        self.lbl_welcome = QLabel(f"🚀 {t('wiz_welcome')}")
        self.lbl_welcome.setStyleSheet("font-size: 19px; font-weight: 700; color: #F97316;")
        top_box.addWidget(self.lbl_welcome)

        self.lbl_desc = QLabel(t("wiz_desc"))
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("font-size: 13px; color: #94A3B8; line-height: 1.4;")
        top_box.addWidget(self.lbl_desc)
        layout.addLayout(top_box)

        # 核心设置卡片
        card = QFrame()
        card.setProperty("class", "card")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(18, 16, 18, 16)
        c_lay.setSpacing(14)

        # 1. 语言选择
        self.lbl_lang = QLabel(t("wiz_lang_sel"))
        self.lbl_lang.setStyleSheet("font-weight: 600; font-size: 13px;")
        c_lay.addWidget(self.lbl_lang)

        self.combo_lang = QComboBox()
        self.combo_lang.addItem("🇨🇳 简体中文 (Simplified Chinese)", "zh_CN")
        self.combo_lang.addItem("🇺🇸 English (United States)", "en_US")
        cur_lang = config.get("language", "zh_CN")
        self.combo_lang.setCurrentIndex(0 if cur_lang == "zh_CN" else 1)
        self.combo_lang.currentIndexChanged.connect(self._on_lang_changed)
        c_lay.addWidget(self.combo_lang)

        # 2. 存储路径选择
        self.lbl_path = QLabel(t("wiz_path_sel"))
        self.lbl_path.setStyleSheet("font-weight: 600; font-size: 13px;")
        c_lay.addWidget(self.lbl_path)

        p_row = QHBoxLayout()
        self.input_path = QLineEdit(config.get("models_dir"))
        p_row.addWidget(self.input_path)

        self.btn_browse = QPushButton(t("browse"))
        self.btn_browse.setProperty("class", "btnSecondary")
        self.btn_browse.clicked.connect(self._browse_path)
        p_row.addWidget(self.btn_browse)
        c_lay.addLayout(p_row)

        layout.addWidget(card)
        layout.addStretch()

        # 底部按钮
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self.btn_start = QPushButton(t("wiz_start_btn"))
        self.btn_start.setProperty("class", "btnPrimary")
        self.btn_start.setFixedHeight(38)
        self.btn_start.clicked.connect(self._finish_setup)
        bottom_row.addWidget(self.btn_start)
        layout.addLayout(bottom_row)

    def _on_lang_changed(self, idx):
        code = self.combo_lang.currentData()
        set_language(code)
        self.setWindowTitle(t("wiz_title"))
        self.lbl_welcome.setText(f"🚀 {t('wiz_welcome')}")
        self.lbl_desc.setText(t("wiz_desc"))
        self.lbl_lang.setText(t("wiz_lang_sel"))
        self.lbl_path.setText(t("wiz_path_sel"))
        self.btn_browse.setText(t("browse"))
        self.btn_start.setText(t("wiz_start_btn"))

    def _browse_path(self):
        d = QFileDialog.getExistingDirectory(self, t("browse"), self.input_path.text())
        if d:
            self.input_path.setText(d)

    def _finish_setup(self):
        lang = self.combo_lang.currentData()
        models_dir = self.input_path.text().strip()

        set_language(lang)
        if models_dir:
            config.set("models_dir", models_dir)
            os.makedirs(models_dir, exist_ok=True)

        config.set("is_first_run", False)
        self.accept()
