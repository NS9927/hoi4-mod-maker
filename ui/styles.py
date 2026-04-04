"""
暗色主题样式表 — 参照 HTML 设计稿的视觉风格
"""

DARK_STYLESHEET = """
/* 全局 */
QMainWindow, QWidget {
    background-color: #0a0e17;
    color: #e2e8f0;
    font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif;
    font-size: 12px;
}

/* 菜单栏 */
QMenuBar {
    background-color: #111827;
    border-bottom: 1px solid #2a3a55;
    padding: 2px;
    font-size: 12px;
}
QMenuBar::item {
    padding: 4px 12px;
    background: transparent;
    color: #e2e8f0;
}
QMenuBar::item:selected {
    background: rgba(59, 130, 246, 0.3);
    border-radius: 4px;
}
QMenu {
    background-color: #1a2235;
    border: 1px solid #2a3a55;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 3px;
}
QMenu::item:selected {
    background: rgba(59, 130, 246, 0.3);
}
QMenu::separator {
    height: 1px;
    background: #2a3a55;
    margin: 4px 8px;
}

/* 状态栏 */
QStatusBar {
    background-color: #111827;
    border-top: 1px solid #2a3a55;
    font-size: 11px;
    color: #8892a8;
}
QStatusBar::item {
    border: none;
}

/* 工具面板 */
QGroupBox {
    background-color: #1a2235;
    border: 1px solid #2a3a55;
    border-radius: 6px;
    margin-top: 8px;
    padding: 8px;
    padding-top: 24px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #8892a8;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* 按钮 */
QPushButton {
    background-color: #0d1525;
    border: 1px solid #2a3a55;
    border-radius: 4px;
    padding: 6px 12px;
    color: #e2e8f0;
    font-size: 12px;
    min-height: 20px;
}
QPushButton:hover {
    border-color: #3b82f6;
    background: rgba(59, 130, 246, 0.1);
}
QPushButton:pressed {
    background: rgba(59, 130, 246, 0.2);
}
QPushButton:checked {
    background: #3b82f6;
    border-color: #3b82f6;
    color: white;
}
QPushButton#btnPrimary {
    background: #3b82f6;
    border-color: #3b82f6;
    color: white;
    font-weight: 500;
}
QPushButton#btnPrimary:hover {
    background: #2563eb;
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
    border: 2px solid #2a3a55;
    background: #0d1525;
}
QRadioButton::indicator:checked {
    background: #3b82f6;
    border-color: #3b82f6;
}

/* 滑块 */
QSlider::groove:horizontal {
    height: 4px;
    background: #2a3a55;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background: #3b82f6;
}
QSlider::handle:horizontal:hover {
    background: #60a5fa;
}

/* 数值输入 */
QSpinBox, QDoubleSpinBox {
    background: #0d1525;
    border: 1px solid #2a3a55;
    border-radius: 4px;
    padding: 4px 6px;
    color: #e2e8f0;
    font-size: 12px;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: #1a2235;
    border: none;
    width: 16px;
}

/* 标签 */
QLabel {
    color: #e2e8f0;
    font-size: 12px;
}
QLabel#labelDim {
    color: #8892a8;
    font-size: 11px;
}

/* 滚动条 */
QScrollBar:vertical {
    width: 6px;
    background: #0a0e17;
}
QScrollBar::handle:vertical {
    background: #2a3a55;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #8892a8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    height: 6px;
    background: #0a0e17;
}
QScrollBar::handle:horizontal {
    background: #2a3a55;
    border-radius: 3px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #8892a8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* 对话框 */
QDialog {
    background-color: #1a2235;
}
QMessageBox {
    background-color: #1a2235;
}
QInputDialog {
    background-color: #1a2235;
}

/* 工具提示 */
QToolTip {
    background: #1a2235;
    border: 1px solid #3b82f6;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e2e8f0;
    font-size: 11px;
}

/* Graphics View */
QGraphicsView {
    border: none;
    background: #050a12;
}
"""
