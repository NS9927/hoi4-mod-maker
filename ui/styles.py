"""
Fluent 色板与工具函数。
不再包含任何 QSS —— 全部采用 QFluentWidgets 默认圆角风格。
"""

from PyQt5.QtGui import QColor, QPixmap, QIcon


# ── Fluent 色板 (暗色模式) ──────────────────────────
_BG = "#1e1e2e"
_INPUT_BG = "#2a2a3a"
_BORDER = "#4a4a5e"
_TEXT = "#f0f0ff"
_DIM = "#b0b0c8"
_ACCENT = "#8080ff"
_ACCENT_HOVER = "#9090ff"
_SUBTLE_BG = "#252535"
_SUBTLE_BG2 = "#2a2a3a"
_SUCCESS = "#22c55e"
_WARNING = "#f59e0b"
_ERROR = "#ef4444"
_GROUP_HEADER = "#7c7cff"


# ── 轻量标签样式 (仅颜色+字号，非 QSS 块) ──────────
_LABEL_STYLE = f"color: {_TEXT}; font-size: 15px;"
_DIM_LABEL_STYLE = f"color: {_DIM}; font-size: 15px;"


def make_section(title: str):
    """创建 QGroupBox 分组容器。不设 QSS，使用 Fluent 默认外观。"""
    from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
    box = QGroupBox(title)
    box.setLayout(QVBoxLayout())
    box.layout().setContentsMargins(10, 14, 10, 10)
    box.layout().setSpacing(8)
    return box


def _color_icon(r: int, g: int, b: int, size: int = 12) -> QIcon:
    """生成一个纯色方块图标 (列表 / 按钮装饰用)."""
    px = QPixmap(size, size)
    px.fill(QColor(r, g, b))
    return QIcon(px)


# ── 基础暗色 QSS (仅原生 Qt 控件背景) ──────────────
# Fluent 控件由 QFluentWidgets 自带主题管理,
# 这里只覆盖非 Fluent 原生控件的暗色背景.
DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
}
QDialog, QMessageBox, QInputDialog, QProgressDialog {
    background-color: #252535;
}
QMenuBar {
    background-color: #18182a;
    border-bottom: 1px solid #3a3a4a;
}
QMenuBar::item:selected {
    background: rgba(108, 108, 240, 0.25);
    border-radius: 4px;
}
QMenu {
    background-color: #252535;
    border: 1px solid #3a3a4a;
}
QMenu::item:selected {
    background: rgba(108, 108, 240, 0.3);
}
QMenu::separator {
    height: 1px;
    background: #3a3a4a;
    margin: 4px 8px;
}
QStatusBar {
    background-color: #18182a;
    border-top: 1px solid #3a3a4a;
}
QScrollBar:vertical {
    background: #1e1e2e;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #3a3a4a;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #1e1e2e;
    height: 10px;
}
QScrollBar::handle:horizontal {
    background: #3a3a4a;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QToolTip {
    background: #252535;
    border: 1px solid #6c6cf0;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0f0;
}
QGraphicsView {
    border: none;
    background: #161625;
}
"""
