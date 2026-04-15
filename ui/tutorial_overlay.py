"""
教程遮罩层 — 半透明暗色覆盖全窗口，高亮指定区域，显示指示文字。
"""
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QPainterPath, QRegion


_ACCENT = "#6c6cf0"
_BG = "#1e1e2e"


class TutorialOverlay(QWidget):
    """全窗口遮罩，挖洞高亮目标控件，旁边显示提示。"""

    skip_requested = pyqtSignal()
    next_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        self._target_rect: QRect | None = None
        self._allow_click_through = True

        # 底部指示面板
        self._panel = QWidget(self)
        self._panel.setStyleSheet(f"""
            QWidget#tutorialPanel {{
                background: #2a2a3e;
                border-top: 3px solid {_ACCENT};
                border-left: none;
                border-right: none;
                border-bottom: none;
            }}
        """)
        self._panel.setObjectName("tutorialPanel")
        panel_lay = QVBoxLayout(self._panel)
        panel_lay.setContentsMargins(24, 16, 24, 14)
        panel_lay.setSpacing(10)

        # 步骤标签
        self._step_label = QLabel()
        self._step_label.setStyleSheet(f"color: {_ACCENT}; font-size: 13px; font-weight: bold; background: transparent;")
        panel_lay.addWidget(self._step_label)

        # 指示文字
        self._msg = QLabel()
        self._msg.setStyleSheet("color: white; font-size: 14px; line-height: 1.5; background: transparent;")
        self._msg.setWordWrap(True)
        panel_lay.addWidget(self._msg, 1)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._skip_btn = QPushButton("跳过教程")
        self._skip_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid #3a3a4a;
                color: #8888a8;
                padding: 6px 16px;
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{ color: #e0e0f0; border-color: {_ACCENT}; }}
        """)
        self._skip_btn.clicked.connect(self.skip_requested.emit)
        btn_row.addWidget(self._skip_btn)

        btn_row.addStretch()

        self._next_btn = QPushButton("下一步 →")
        self._next_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_ACCENT};
                border: none;
                color: white;
                padding: 6px 20px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #7c7cff; }}
        """)
        self._next_btn.clicked.connect(self.next_requested.emit)
        btn_row.addWidget(self._next_btn)

        panel_lay.addLayout(btn_row)

        self._panel.setMinimumHeight(140)
        self._panel.setMaximumHeight(220)
        self.hide()

    def show_step(self, step_text: str, message: str,
                  target: QWidget | None = None,
                  show_next: bool = True) -> None:
        """显示一个教程步骤。"""
        self._step_label.setText(step_text)
        self._msg.setText(message)
        self._next_btn.setVisible(show_next)

        # 计算目标控件在主窗口坐标系中的位置
        if target and target.isVisible():
            pos = target.mapTo(self.parentWidget(), QPoint(0, 0))
            self._target_rect = QRect(pos, target.size())
        else:
            self._target_rect = None

        self.raise_()
        self.show()
        # 刷新面板位置 + 挖洞 mask
        self.resizeEvent(None)
        self._update_mask()
        self.update()

    def set_next_text(self, text: str) -> None:
        self._next_btn.setText(text)

    def _update_mask(self) -> None:
        """用 setMask 在目标区域真正挖洞，让鼠标事件穿透到下层控件。"""
        full = QRegion(self.rect())
        if self._target_rect:
            expanded = self._target_rect.adjusted(-4, -4, 4, 4)
            hole = QRegion(expanded)
            self.setMask(full - hole)
        else:
            self.clearMask()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        pw = self.width()
        ph = self.height()
        # 让面板自适应内容高度
        panel_h = self._panel.sizeHint().height()
        panel_h = max(panel_h, self._panel.minimumHeight())
        panel_h = min(panel_h, self._panel.maximumHeight())
        self._panel.setGeometry(0, ph - panel_h, pw, panel_h)
        self._update_mask()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 半透明暗色覆盖（mask 已挖洞，这里直接画全区域）
        painter.fillRect(self.rect(), QColor(0, 0, 0, 140))

        # 目标边框高亮（画在遮罩边缘）
        if self._target_rect:
            expanded = self._target_rect.adjusted(-4, -4, 4, 4)
            painter.setPen(QColor(_ACCENT))
            painter.drawRoundedRect(expanded, 4, 4)

        # 底部面板区域用实色背景
        painter.fillRect(self._panel.geometry(), QColor("#2a2a3e"))

    def mousePressEvent(self, event) -> None:
        """遮罩区域拦截点击，目标区域已通过 setMask 挖洞穿透。"""
        event.accept()
