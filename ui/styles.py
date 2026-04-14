"""
暗色主题样式表 — 参照 HTML 设计稿的视觉风格.

- DARK_STYLESHEET: 全局 QApplication 级 QSS
- _BG / _INPUT_BG 等: 色板常量, feature 模块共享
- _SECTION_STYLE / _PRIMARY_BTN_STYLE 等: 局部控件样式
- _color_icon(): 生成色块图标辅助
"""

from PyQt5.QtGui import QColor, QPixmap, QIcon


# ── 色板 (v2 全新设计: 中性深灰 + 紫蓝强调) ──────────────
_BG = "#1e1e2e"          # 深紫灰主背景
_INPUT_BG = "#252535"     # 面板/输入框背景
_BORDER = "#3a3a4a"       # 边框
_TEXT = "#e0e0f0"         # 主文字 (冷白)
_DIM = "#8888a8"          # 次要文字/标签
_ACCENT = "#6c6cf0"       # 紫蓝强调 (选中/高亮/按钮)
_ACCENT_HOVER = "#7c7cff" # hover 亮色
_SUCCESS = "#22c55e"      # 成功/导出按钮
_GROUP_HEADER = "#7c7cff" # 分组标题色


_SECTION_STYLE = f"""
    QGroupBox {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 6px;
        margin-top: 16px;
        padding-top: 18px;
        color: {_GROUP_HEADER};
        font-size: 12px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
    }}
"""

_LABEL_STYLE = f"color: {_TEXT}; font-size: 13px;"
_DIM_LABEL_STYLE = f"color: {_DIM}; font-size: 12px;"

_SLIDER_STYLE = f"""
    QSlider::groove:horizontal {{
        height: 4px;
        background: {_BORDER};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 14px; height: 14px;
        margin: -5px 0;
        background: {_ACCENT};
        border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{
        background: {_ACCENT};
        border-radius: 2px;
    }}
"""

_TOOL_BTN_STYLE = f"""
    QPushButton {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        color: {_DIM};
        padding: 6px 4px;
        font-size: 12px;
        border-radius: 4px;
    }}
    QPushButton:checked {{
        background: {_ACCENT};
        color: white;
        border-color: {_ACCENT};
    }}
    QPushButton:hover:!checked {{
        background: rgba(108, 108, 240, 0.12);
    }}
"""

_PRIMARY_BTN_STYLE = f"""
    QPushButton {{
        background: {_ACCENT};
        border: none;
        color: white;
        padding: 8px 14px;
        font-size: 13px;
        font-weight: 600;
        border-radius: 5px;
    }}
    QPushButton:hover {{
        background: {_ACCENT_HOVER};
    }}
"""

_SECONDARY_BTN_STYLE = f"""
    QPushButton {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        color: {_TEXT};
        padding: 7px 12px;
        font-size: 12px;
        border-radius: 5px;
    }}
    QPushButton:hover {{
        background: rgba(255, 255, 255, 0.06);
    }}
"""

_SUCCESS_BTN_STYLE = f"""
    QPushButton {{
        background: {_SUCCESS};
        border: none;
        color: white;
        padding: 8px 12px;
        font-size: 13px;
        font-weight: 700;
        border-radius: 5px;
    }}
    QPushButton:hover {{
        background: #16a34a;
    }}
"""

_SPINBOX_STYLE = f"""
    QSpinBox {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        color: {_TEXT};
        padding: 3px 6px;
        font-size: 12px;
    }}
"""

_LINEEDIT_STYLE = f"""
    QLineEdit {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        color: {_TEXT};
        padding: 3px 6px;
        font-size: 12px;
    }}
"""

_COMBOBOX_STYLE = f"""
    QComboBox {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        color: {_TEXT};
        padding: 3px 6px;
        font-size: 12px;
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        color: {_TEXT};
        selection-background-color: {_ACCENT};
    }}
"""

_LIST_STYLE = f"""
    QListWidget {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        color: {_TEXT};
        font-size: 12px;
    }}
    QListWidget::item {{
        padding: 5px 8px;
    }}
    QListWidget::item:selected {{
        background: {_ACCENT};
        color: white;
    }}
    QListWidget::item:hover:!selected {{
        background: rgba(255, 255, 255, 0.05);
    }}
"""


def _color_icon(r: int, g: int, b: int, size: int = 12) -> QIcon:
    """生成一个纯色方块图标 (列表 / 按钮装饰用)."""
    px = QPixmap(size, size)
    px.fill(QColor(r, g, b))
    return QIcon(px)


DARK_STYLESHEET = """
/* 全局 — v2 中性深灰 + 紫蓝 */
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #e0e0f0;
    font-family: "Microsoft YaHei", "Noto Sans SC", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* 菜单栏 */
QMenuBar {
    background-color: #18182a;
    border-bottom: 1px solid #3a3a4a;
    padding: 3px;
    font-size: 13px;
}
QMenuBar::item {
    padding: 5px 14px;
    background: transparent;
    color: #e0e0f0;
}
QMenuBar::item:selected {
    background: rgba(108, 108, 240, 0.25);
    border-radius: 4px;
}
QMenu {
    background-color: #252535;
    border: 1px solid #3a3a4a;
    padding: 4px;
}
QMenu::item {
    padding: 7px 28px;
    border-radius: 3px;
    font-size: 13px;
}
QMenu::item:selected {
    background: rgba(108, 108, 240, 0.3);
}
QMenu::separator {
    height: 1px;
    background: #3a3a4a;
    margin: 4px 8px;
}

/* 状态栏 */
QStatusBar {
    background-color: #18182a;
    border-top: 1px solid #3a3a4a;
    font-size: 12px;
    color: #8888a8;
}
QStatusBar::item {
    border: none;
}

/* 工具面板 */
QGroupBox {
    background-color: #252535;
    border: 1px solid #3a3a4a;
    border-radius: 6px;
    margin-top: 8px;
    padding: 8px;
    padding-top: 24px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #7c7cff;
    font-size: 12px;
    font-weight: bold;
}

/* 按钮 */
QPushButton {
    background-color: #1e1e2e;
    border: 1px solid #3a3a4a;
    border-radius: 5px;
    padding: 7px 14px;
    color: #e0e0f0;
    font-size: 13px;
    min-height: 22px;
}
QPushButton:hover {
    border-color: #6c6cf0;
    background: rgba(108, 108, 240, 0.1);
}
QPushButton:pressed {
    background: rgba(108, 108, 240, 0.2);
}
QPushButton:checked {
    background: #6c6cf0;
    border-color: #6c6cf0;
    color: white;
}
QPushButton#btnPrimary {
    background: #6c6cf0;
    border-color: #6c6cf0;
    color: white;
    font-weight: 500;
}
QPushButton#btnPrimary:hover {
    background: #7c7cff;
}
QPushButton#btnSuccess {
    background: #22c55e;
    border-color: #22c55e;
    color: white;
    font-weight: 500;
}
QPushButton#btnSuccess:hover {
    background: #16a34a;
}

/* 单选按钮 */
QRadioButton {
    spacing: 6px;
    padding: 3px;
    font-size: 12px;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid #3a3a4a;
    background: #1e1e2e;
}
QRadioButton::indicator:checked {
    background: #6c6cf0;
    border-color: #6c6cf0;
}

/* 滑块 */
QSlider::groove:horizontal {
    height: 4px;
    background: #3a3a4a;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background: #6c6cf0;
}
QSlider::handle:horizontal:hover {
    background: #8c8cff;
}

/* 数值输入 */
QSpinBox, QDoubleSpinBox {
    background: #1e1e2e;
    border: 1px solid #3a3a4a;
    border-radius: 4px;
    padding: 5px 8px;
    color: #e0e0f0;
    font-size: 13px;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: #252535;
    border: none;
    width: 16px;
}

/* 标签 */
QLabel {
    color: #e0e0f0;
    font-size: 13px;
}
QLabel#labelDim {
    color: #8888a8;
    font-size: 12px;
}

/* 滚动条 */
QScrollBar:vertical {
    width: 6px;
    background: #1e1e2e;
}
QScrollBar::handle:vertical {
    background: #3a3a4a;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #8888a8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    height: 6px;
    background: #1e1e2e;
}
QScrollBar::handle:horizontal {
    background: #3a3a4a;
    border-radius: 3px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #8888a8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* 对话框 */
QDialog {
    background-color: #252535;
}
QMessageBox {
    background-color: #252535;
}
QInputDialog {
    background-color: #252535;
}

/* 工具提示 */
QToolTip {
    background: #252535;
    border: 1px solid #6c6cf0;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0f0;
    font-size: 11px;
}

/* Graphics View */
QGraphicsView {
    border: none;
    background: #161625;
}
"""
