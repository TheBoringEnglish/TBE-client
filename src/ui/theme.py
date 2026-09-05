# -*- coding: utf-8 -*-
"""
现代化大厂级双主题配色系统与 QSS 样式表引擎
灵感融合 Linear、Notion 与 CapCut 桌面端美学：极简微渐变、圆润倒角、柔光描边与高辨识度状态强调色。
"""

from typing import Dict


class Palette:
    """主题色彩调色盘"""

    DARK = {
        "bg_app": "#090B10",
        "bg_header": "#0E111A",
        "bg_sidebar": "#10131C",
        "bg_card": "#131722",
        "bg_card_hover": "#1A1F2E",
        "bg_pill_container": "rgba(255, 255, 255, 0.05)",
        "bg_pill_active": "#FFFFFF",
        "text_pill_active": "#0F172A",
        "bg_input": "#0C0E15",
        "border": "rgba(255, 255, 255, 0.09)",
        "border_focus": "#F97316",
        "border_subtle": "rgba(255, 255, 255, 0.05)",
        "text_main": "#F8FAFC",
        "text_sub": "#94A3B8",
        "text_muted": "#64748B",
        "primary": "#F97316",
        "primary_hover": "#EA580C",
        "primary_pressed": "#C2410C",
        "primary_light": "rgba(249, 115, 22, 0.14)",
        "success": "#10B981",
        "success_bg": "rgba(16, 185, 129, 0.12)",
        "warning": "#F59E0B",
        "warning_bg": "rgba(245, 158, 11, 0.12)",
        "danger": "#EF4444",
        "danger_bg": "rgba(239, 68, 68, 0.12)",
        "info": "#38BDF8",
        "info_bg": "rgba(56, 189, 248, 0.12)",
    }

    LIGHT = {
        "bg_app": "#F4F6F9",
        "bg_header": "#FFFFFF",
        "bg_sidebar": "#FFFFFF",
        "bg_card": "#FFFFFF",
        "bg_card_hover": "#F8FAFC",
        "bg_pill_container": "#ECEFF3",
        "bg_pill_active": "#0F172A",
        "text_pill_active": "#FFFFFF",
        "bg_input": "#FFFFFF",
        "border": "#E2E8F0",
        "border_focus": "#F97316",
        "border_subtle": "#EDF2F7",
        "text_main": "#0F172A",
        "text_sub": "#475569",
        "text_muted": "#94A3B8",
        "primary": "#F97316",
        "primary_hover": "#EA580C",
        "primary_pressed": "#C2410C",
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
    """根据主题生成现代简约、参考 Antigravity-Manager 质感的 QSS 样式表"""
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

    /* ════════════ 顶部全宽导航栏 Header ════════════ */
    #topHeaderBar {{
        background-color: {p['bg_header']};
        border-bottom: 1px solid {p['border']};
    }}

    /* 药丸胶囊容器 (Main & Sub Pill Containers) */
    #mainPillContainer, #subPillContainer {{
        background-color: {p['bg_pill_container']};
        border-radius: 20px;
        padding: 3px;
    }}

    /* 主导航胶囊按钮 */
    QPushButton.navPill {{
        border: none;
        border-radius: 17px;
        padding: 6px 18px;
        font-size: 13px;
        font-weight: 500;
        color: {p['text_sub']};
        background-color: transparent;
    }}

    QPushButton.navPill:hover {{
        color: {p['text_main']};
        background-color: rgba(255, 255, 255, 0.06);
    }}

    QPushButton.navPill:checked {{
        background-color: {p['bg_pill_active']};
        color: {p['text_pill_active']};
        font-weight: 700;
    }}

    /* 二级子导航胶囊按钮 (Sub Tab Pill) */
    QPushButton.subTabPill {{
        border: none;
        border-radius: 15px;
        padding: 5px 15px;
        font-size: 12.5px;
        font-weight: 500;
        color: {p['text_sub']};
        background-color: transparent;
    }}

    QPushButton.subTabPill:hover {{
        color: {p['text_main']};
    }}

    QPushButton.subTabPill:checked {{
        background-color: {p['bg_card']};
        color: {p['primary']};
        font-weight: 600;
        border: 1px solid {p['border']};
    }}

    /* 顶部右侧圆形/胶囊工具小按钮 */
    QPushButton.toolCircleBtn {{
        border: 1px solid {p['border']};
        border-radius: 16px;
        background-color: {p['bg_pill_container']};
        color: {p['text_main']};
        font-size: 13px;
        font-weight: 600;
        min-width: 32px;
        max-width: 32px;
        min-height: 32px;
        max-height: 32px;
        padding: 0px;
    }}

    QPushButton.toolCircleBtn:hover {{
        background-color: {p['bg_card_hover']};
        border-color: {p['primary']};
    }}

    QPushButton.toolPillBtn {{
        border: 1px solid {p['border']};
        border-radius: 16px;
        background-color: {p['bg_pill_container']};
        color: {p['text_main']};
        font-size: 12px;
        font-weight: 700;
        padding: 4px 12px;
        height: 24px;
    }}

    QPushButton.toolPillBtn:hover {{
        background-color: {p['bg_card_hover']};
        border-color: {p['primary']};
    }}

    /* ════════════ 大圆角现代卡片 ════════════ */
    QFrame.card {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 16px;
    }}

    QFrame.card:hover {{
        border-color: {p['border_subtle']};
    }}

    /* 社交/功能徽章小卡片 (About/Community Grid Card) */
    QFrame.socialCard {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 14px;
    }}

    QFrame.socialCard:hover {{
        background-color: {p['bg_card_hover']};
        border-color: {p['primary']};
    }}

    /* 足迹视频生成历史记录卡片 (Footprint Generated Video Card) */
    QFrame.recordCard {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 14px;
    }}

    QFrame.recordCard:hover {{
        background-color: {p['bg_card_hover']};
        border-color: {p['border_subtle']};
    }}

    /* ════════════ 按钮设计系统 ════════════ */
    QPushButton.btnPrimary {{
        background-color: {p['primary']};
        color: #FFFFFF;
        border: 1px solid {p['primary']};
        border-radius: 18px;
        padding: 8px 20px;
        font-weight: 600;
        font-size: 13px;
    }}

    QPushButton.btnPrimary:hover {{
        background-color: {p['primary_hover']};
        border-color: {p['primary_hover']};
    }}

    QPushButton.btnPrimary:pressed {{
        background-color: {p['primary_pressed']};
        border-color: {p['primary_pressed']};
        padding-top: 9px;
    }}

    QPushButton.btnSuccess {{
        background-color: {p['success']};
        color: #FFFFFF;
        border: 1px solid {p['success']};
        border-radius: 16px;
        padding: 6px 18px;
        font-weight: 600;
        font-size: 13px;
    }}

    QPushButton.btnSuccess:hover {{
        background-color: #059669;
        border-color: #059669;
    }}

    QPushButton.btnPrimary:disabled {{
        background-color: {p['border']};
        color: {p['text_muted']};
        border-color: {p['border']};
    }}

    QPushButton.btnSecondary {{
        background-color: {p['bg_pill_container']};
        color: {p['text_main']};
        border: 1px solid {p['border']};
        border-radius: 16px;
        padding: 7px 16px;
        font-weight: 500;
        font-size: 13px;
    }}

    QPushButton.btnSecondary:hover {{
        background-color: {p['bg_card_hover']};
        border-color: {p['text_muted']};
    }}

    QPushButton.btnSecondary:pressed {{
        background-color: {p['border']};
    }}

    /* ════════════ 输入框与富文本 ════════════ */
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
        background-color: {p['bg_input']};
    }}

    QLineEdit:disabled, QTextEdit:disabled {{
        background-color: {p['border_subtle']};
        color: {p['text_muted']};
    }}

    /* 下拉选择框 */
    QComboBox {{
        background-color: {p['bg_card']};
        color: {p['text_main']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 6px 12px;
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
        color: {p['text_main']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 4px;
        selection-background-color: {p['primary_light']};
        selection-color: {p['primary']};
        outline: none;
    }}

    /* ════════════ 细致平滑滚动条 ════════════ */
    QScrollBar:vertical {{
        border: none;
        background-color: transparent;
        width: 6px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {p['border']};
        min-height: 28px;
        border-radius: 3px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {p['text_muted']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        height: 0px;
        background: transparent;
    }}

    /* ════════════ 进度条 ════════════ */
    QProgressBar {{
        border: 1px solid {p['border']};
        border-radius: 5px;
        text-align: center;
        background-color: {p['bg_input']};
        height: 8px;
        color: {p['text_sub']};
        font-size: 10px;
    }}

    QProgressBar::chunk {{
        background-color: {p['primary']};
        border-radius: 4px;
    }}

    /* ════════════ 滑块 QSlider ════════════ */
    QSlider::groove:horizontal {{
        border: none;
        height: 4px;
        background: {p['border']};
        border-radius: 2px;
    }}

    QSlider::sub-page:horizontal {{
        background: {p['primary']};
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background: #FFFFFF;
        border: 2px solid {p['primary']};
        width: 14px;
        margin-top: -5px;
        margin-bottom: -5px;
        border-radius: 7px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {p['primary_light']};
        border-width: 3px;
    }}

    /* ════════════ 列表与列表项 ════════════ */
    QListWidget {{
        background-color: {p['bg_card']};
        border: 1px solid {p['border']};
        border-radius: 10px;
        padding: 6px;
        outline: none;
    }}

    QListWidget::item {{
        border-radius: 8px;
        padding: 9px 12px;
        margin-bottom: 3px;
        color: {p['text_main']};
    }}

    QListWidget::item:hover {{
        background-color: {p['bg_card_hover']};
    }}

    QListWidget::item:selected {{
        background-color: {p['primary_light']};
        color: {p['primary']};
        font-weight: 600;
    }}

    /* ════════════ 复选框 QCheckBox ════════════ */
    QCheckBox {{
        spacing: 8px;
        color: {p['text_main']};
    }}

    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {p['border']};
        background-color: {p['bg_input']};
    }}

    QCheckBox::indicator:hover {{
        border-color: {p['primary']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {p['primary']};
        border-color: {p['primary']};
    }}
    """
