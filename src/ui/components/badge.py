# -*- coding: utf-8 -*-
"""
现代化状态胶囊徽章 (StatusBadge)
支持 success, warning, danger, info, default 等状态色。
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


class StatusBadge(QLabel):
    """状态胶囊指示器"""

    STYLES = {
        "success": ("#047857", "rgba(16, 185, 129, 0.14)", "rgba(16, 185, 129, 0.35)"),
        "warning": ("#B45309", "rgba(245, 158, 11, 0.14)", "rgba(245, 158, 11, 0.35)"),
        "danger":  ("#B91C1C", "rgba(239, 68, 68, 0.14)", "rgba(239, 68, 68, 0.35)"),
        "info":    ("#0369A1", "rgba(56, 189, 248, 0.14)", "rgba(56, 189, 248, 0.35)"),
        "default": ("#475569", "rgba(148, 163, 184, 0.14)", "rgba(148, 163, 184, 0.30)"),
    }

    def __init__(self, text: str = "", status: str = "default", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.set_status(status, text)

    def set_status(self, status: str, text: str = None):
        if text:
            self.setText(text)
        color, bg, border = self.STYLES.get(status, self.STYLES["default"])
        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: {bg};
                border-radius: 10px;
                padding: 3px 12px;
                font-size: 11.5px;
                font-weight: 600;
                border: 1px solid {border};
            }}
        """)
