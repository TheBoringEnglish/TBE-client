# -*- coding: utf-8 -*-
"""
现代化大厂级双主题配色系统与 QSS 样式表引擎
灵感融合 Linear、Notion 与 CapCut 桌面端美学：极简微渐变、圆润倒角、柔光描边与高辨识度状态强调色。
"""

from typing import Dict


class Palette:
    """主题色彩调色盘"""

    DARK = {
        "bg_app": "#0D0F14",
        "bg_sidebar": "#13161F",
        "bg_card": "#181B26",
        "bg_card_hover": "#212534",
        "bg_input": "#0A0C10",
        "border": "#272C3D",
        "border_focus": "#F97316",
        "text_main": "#F1F5F9",
        "text_sub": "#94A3B8",
        "text_muted": "#64748B",
        "primary": "#F97316",
        "primary_hover": "#EA580C",
        "primary_light": "rgba(249, 115, 22, 0.15)",
        "success": "#10B981",
        "success_bg": "rgba(16, 185, 129, 0.15)",
        "warning": "#F59E0B",
        "warning_bg": "rgba(245, 158, 11, 0.15)",
        "danger": "#EF4444",
        "danger_bg": "rgba(239, 68, 68, 0.15)",
        "info": "#38BDF8",
        "info_bg": "rgba(56, 189, 248, 0.15)",
    }

    LIGHT = {
        "bg_app": "#F8FAFC",
        "bg_sidebar": "#FFFFFF",
        "bg_card": "#FFFFFF",
        "bg_card_hover": "#F1F5F9",
        "bg_input": "#FFFFFF",
        "border": "#E2E8F0",
        "border_focus": "#F97316",
        "text_main": "#0F172A",
        "text_sub": "#475569",
        "text_muted": "#94A3B8",
        "primary": "#F97316",
        "primary_hover": "#EA580C",
        "primary_light": "rgba(249, 115, 22, 0.12)",
        "success": "#059669",
        "success_bg": "#ECFDF5",
        "warning": "#D97706",
        "warning_bg": "#FFFBEB",
        "danger": "#DC2626",
        "danger_bg": "#FEF2F2",
        "info": "#0284C7",
        "info_bg": "#F0F9FF",
    }


def generate_qss(is_dark: bool = True) -> str:
    """根据主题生成完整的现代化 QSS 样式表"""
    p = Palette.DARK if is_dark else Palette.LIGHT

    return f"""
    /* ════════════ 全局基础 ════════════ */
    QWidget {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
        font-size: 13px;
        color: {p['text_main']};
        background-color: transparent;
    }}

    QMainWindow, QDialog {{
        background-color: {p['bg_app']};
    }}

    /* ════════════ 侧边栏与卡片容器 ════════════ */
    #sidebarContainer {{
        background-color: {p['bg_sidebar']};
        border-right: 1px solid {p['border']};
    }}

    QFrame.card {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 12px;
    }}

    QFrame.card:hover {{
        border-color: {p['border_focus']};
    }}

    /* ════════════ 侧边栏导航按钮 ════════════ */
    QPushButton.navButton {{
        text-align: left;
        padding: 11px 16px;
        border-radius: 9px;
        border: none;
        color: {p['text_sub']};
        font-weight: 500;
        font-size: 13.5px;
        background-color: transparent;
    }}

    QPushButton.navButton:hover {{
        background-color: {p['primary_light']};
        color: {p['primary']};
    }}

    QPushButton.navButton:checked {{
        background-color: {p['primary']};
        color: #FFFFFF;
        font-weight: 600;
    }}

    /* ════════════ 核心动作按钮 ════════════ */
    QPushButton.btnPrimary {{
        background-color: {p['primary']};
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 600;
        font-size: 13px;
    }}

    QPushButton.btnPrimary:hover {{
        background-color: {p['primary_hover']};
    }}

    QPushButton.btnPrimary:pressed {{
        background-color: {p['primary_hover']};
        padding-top: 9px;
    }}

    QPushButton.btnPrimary:disabled {{
        background-color: {p['border']};
        color: {p['text_muted']};
    }}

    QPushButton.btnSecondary {{
        background-color: transparent;
        color: {p['text_main']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 7px 16px;
        font-weight: 500;
        font-size: 13px;
    }}

    QPushButton.btnSecondary:hover {{
        background-color: {p['bg_card_hover']};
        border-color: {p['text_muted']};
    }}

    /* ════════════ 输入框与下拉选择框 ════════════ */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {p['bg_input']};
        color: {p['text_main']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 8px 12px;
        selection-background-color: {p['primary']};
        selection-color: #FFFFFF;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {p['border_focus']};
    }}

    QComboBox {{
        background-color: {p['bg_card']};
        color: {p['text_main']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 7px 12px;
        min-width: 140px;
    }}

    QComboBox:hover {{
        border-color: {p['border_focus']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 4px;
        selection-background-color: {p['primary']};
        selection-color: #FFFFFF;
    }}

    /* ════════════ 滚动条 ════════════ */
    QScrollBar:vertical {{
        border: none;
        background-color: transparent;
        width: 7px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {p['border']};
        min-height: 24px;
        border-radius: 3px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {p['text_muted']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* ════════════ 进度条 ════════════ */
    QProgressBar {{
        border: 1px solid {p['border']};
        border-radius: 6px;
        text-align: center;
        background-color: {p['bg_input']};
        height: 10px;
        color: {p['text_sub']};
        font-size: 10px;
    }}

    QProgressBar::chunk {{
        background-color: {p['primary']};
        border-radius: 5px;
    }}

    /* ════════════ 滑块 QSlider ════════════ */
    QSlider::groove:horizontal {{
        border: none;
        height: 5px;
        background: {p['border']};
        border-radius: 2.5px;
    }}

    QSlider::sub-page:horizontal {{
        background: {p['primary']};
        border-radius: 2.5px;
    }}

    QSlider::handle:horizontal {{
        background: #FFFFFF;
        border: 2px solid {p['primary']};
        width: 15px;
        margin-top: -5px;
        margin-bottom: -5px;
        border-radius: 7.5px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {p['primary']};
    }}

    /* ════════════ 列表与表格 ════════════ */
    QListWidget, QTableWidget {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 10px;
        padding: 4px;
    }}

    QListWidget::item {{
        border-radius: 6px;
        padding: 8px 12px;
    }}

    QListWidget::item:hover {{
        background-color: {p['bg_card_hover']};
    }}

    QListWidget::item:selected {{
        background-color: {p['primary_light']};
        color: {p['primary']};
    }}
    """
