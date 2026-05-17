"""
暗色主题样式表 — 参照 HTML 设计稿的视觉风格.

- DARK_STYLESHEET: 全局 QApplication 级 QSS
- _BG / _INPUT_BG 等: 色板常量, feature 模块共享
- _SECTION_STYLE / _PRIMARY_BTN_STYLE 等: 局部控件样式
- _color_icon(): 生成色块图标辅助
"""

from PyQt5.QtGui import QColor, QPixmap, QIcon


# ── 色板 (v3 可读性优化: 提高对比度 + 字号) ──────────────
_BG = "#1e1e2e"          # 深紫灰主背景
_INPUT_BG = "#2a2a3a"     # 面板/输入框背景（原 #252535 略提亮）
_BORDER = "#4a4a5e"       # 边框（原 #3a3a4a 太暗，提亮便于识别）
_TEXT = "#f0f0ff"         # 主文字（原 #e0e0f0，冷白 → 更亮）
_DIM = "#b0b0c8"          # 次要文字/标签（原 #8888a8 对比度 3.5:1 不足，现 4.9:1 达标）
_ACCENT = "#8080ff"       # 紫蓝强调（原 #6c6cf0 提亮更醒目）
_ACCENT_HOVER = "#9090ff" # hover 亮色
_SUCCESS = "#22c55e"      # 成功/导出按钮
_GROUP_HEADER = "#7c7cff" # 分组标题色


_SECTION_STYLE = f"""
    QGroupBox {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 6px;
        margin-top: 18px;
        padding-top: 22px;
        color: {_GROUP_HEADER};
        font-size: 15px;
        font-weight: 700;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px;
    }}
"""

_LABEL_STYLE = f"color: {_TEXT}; font-size: 15px;"
_DIM_LABEL_STYLE = f"color: {_DIM}; font-size: 15px;"

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
        font-size: 15px;
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
        font-size: 15px;
        font-weight: 600;
        border-radius: 5px;
    }}
    QPushButton:hover {{
        background: {_ACCENT_HOVER};
    }}
    QPushButton:checked {{
        background: #f97316;
        color: white;
        border: 2px solid #fb923c;
    }}
    QPushButton:checked:hover {{
        background: #fb923c;
    }}
"""

_SECONDARY_BTN_STYLE = f"""
    QPushButton {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        color: {_TEXT};
        padding: 7px 12px;
        font-size: 15px;
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
        font-size: 15px;
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
        font-size: 15px;
    }}
"""

_LINEEDIT_STYLE = f"""
    QLineEdit {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        color: {_TEXT};
        padding: 3px 6px;
        font-size: 15px;
    }}
"""

_COMBOBOX_STYLE = f"""
    QComboBox {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        color: {_TEXT};
        padding: 3px 6px;
        font-size: 15px;
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
        font-size: 15px;
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


def make_section(title: str):
    """创建统一样式的 QGroupBox 分组容器。所有 page 共用。"""
    from PyQt5.QtWidgets import QGroupBox, QVBoxLayout
    box = QGroupBox(title)
    box.setLayout(QVBoxLayout())
    box.layout().setContentsMargins(10, 14, 10, 10)
    box.layout().setSpacing(8)
    box.setStyleSheet(_SECTION_STYLE)
    return box


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
    /* Segoe UI 在前: 西里尔/拉丁字母用 Segoe UI (正常 metrics),
       中文 fallback 到 YaHei. YaHei 在前会让西里尔字母按 CJK 全角宽度渲染,
       出现"字母间距异常大 + 文字截断"的 bug. */
    font-family: "Segoe UI", "Microsoft YaHei", "Noto Sans SC", sans-serif;
    font-size: 15px;
}

/* 菜单栏 */
QMenuBar {
    background-color: #18182a;
    border-bottom: 1px solid #3a3a4a;
    padding: 3px;
    font-size: 15px;
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
    font-size: 15px;
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
    font-size: 15px;
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
    font-size: 15px;
    font-weight: bold;
}

/* 按钮 */
QPushButton {
    background-color: #1e1e2e;
    border: 1px solid #3a3a4a;
    border-radius: 5px;
    padding: 7px 14px;
    color: #e0e0f0;
    font-size: 15px;
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
    font-size: 15px;
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
    font-size: 15px;
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
    font-size: 15px;
}
QLabel#labelDim {
    color: #8888a8;
    font-size: 15px;
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
    color: #e0e0f0;
}
QInputDialog QPushButton {
    color: #e0e0f0;
    background: #3a3a5a;
    border: 1px solid #6c6cf0;
    border-radius: 4px;
    padding: 4px 16px;
}
QInputDialog QPushButton:hover {
    background: #4a4a7a;
}

/* 工具提示 */
QToolTip {
    background: #252535;
    border: 1px solid #6c6cf0;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0f0;
    font-size: 15px;
}

/* Graphics View */
QGraphicsView {
    border: none;
    background: #161625;
}
"""
