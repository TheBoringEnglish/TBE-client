# -*- coding: utf-8 -*-
"""
现代化统计指标卡片 (StatCard)
展示标题、大号数字指标、描述副标题以及渐变质感装饰。
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt


class StatCard(QFrame):
    """带高级质感的数据指标卡片"""

    def __init__(self, title: str, value: str, subtext: str = "", accent_color: str = "#F97316", parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.accent_color = accent_color

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(6)

        # 顶部标题栏
        top_row = QHBoxLayout()
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("color: #94A3B8; font-size: 12.5px; font-weight: 500;")
        top_row.addWidget(self.lbl_title)
        top_row.addStretch()

        # 装饰小光标
        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background-color: {accent_color}; border-radius: 4px;")
        top_row.addWidget(dot)
        lay.addLayout(top_row)

        # 主指标数值
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("font-size: 24px; font-weight: 700; letter-spacing: -0.5px;")
        lay.addWidget(self.lbl_value)

        # 底部描述
        if subtext:
            self.lbl_subtext = QLabel(subtext)
            self.lbl_subtext.setStyleSheet("color: #64748B; font-size: 11.5px; opacity: 0.85;")
            lay.addWidget(self.lbl_subtext)
        else:
            self.lbl_subtext = None

    def update_value(self, new_value: str, subtext: str = None):
        self.lbl_value.setText(new_value)
        if subtext and self.lbl_subtext:
            self.lbl_subtext.setText(subtext)
