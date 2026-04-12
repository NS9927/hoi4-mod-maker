"""
欢迎页面 — 启动时显示，提供新建/打开/最近项目入口。
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QDialog,
    QSpinBox, QDialogButtonBox, QFormLayout,
)
from PyQt5.QtCore import pyqtSignal, Qt, QSettings
from PyQt5.QtGui import QFont


# ── 色板 (与 ui/styles.py 保持一致) ──
_BG = "#1e1e2e"
_INPUT_BG = "#252535"
_BORDER = "#3a3a4a"
_TEXT = "#e0e0f0"
_DIM = "#8888a8"
_ACCENT = "#6c6cf0"
_ACCENT_HOVER = "#7c7cff"

_MAX_RECENT = 10


def _load_recent_projects() -> list[str]:
    """从 QSettings 读取最近项目列表。"""
    settings = QSettings("HOI4MapMaker", "RecentProjects")
    paths = settings.value("paths", [])
    if isinstance(paths, str):
        return [paths] if paths else []
    return list(paths or [])


def save_recent_project(path: str) -> None:
    """添加路径到最近项目列表（去重、限数量）。"""
    recent = _load_recent_projects()
    if path in recent:
        recent.remove(path)
    recent.insert(0, path)
    recent = recent[:_MAX_RECENT]
    settings = QSettings("HOI4MapMaker", "RecentProjects")
    settings.setValue("paths", recent)


class _SizePickerDialog(QDialog):
    """地图尺寸选择对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("选择地图尺寸")
        self.setFixedSize(300, 160)

        layout = QFormLayout(self)

        self._width_spin = QSpinBox()
        self._width_spin.setRange(256, 16384)
        self._width_spin.setValue(5632)
        self._width_spin.setSingleStep(256)
        layout.addRow("宽度:", self._width_spin)

        self._height_spin = QSpinBox()
        self._height_spin.setRange(256, 16384)
        self._height_spin.setValue(2048)
        self._height_spin.setSingleStep(256)
        layout.addRow("高度:", self._height_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    @property
    def chosen_size(self) -> tuple[int, int]:
        return self._width_spin.value(), self._height_spin.value()


class WelcomePage(QWidget):
    """启动欢迎页，新建/打开/最近项目。"""

    new_project_requested = pyqtSignal(int, int)   # width, height
    open_project_requested = pyqtSignal()
    open_recent_requested = pyqtSignal(str)         # path

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background: {_BG};")
        self._init_ui()

    def _init_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.setSpacing(16)

        # 标题
        title = QLabel("HOI4 地图制作工具")
        title_font = QFont("Microsoft YaHei", 28, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {_TEXT}; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.addWidget(title)

        # 版本
        version = QLabel("v1.0")
        version.setStyleSheet(f"color: {_DIM}; font-size: 14px; background: transparent;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.addWidget(version)

        center.addSpacing(24)

        # 按钮样式
        btn_style = f"""
            QPushButton {{
                background: {_INPUT_BG};
                border: 1px solid {_BORDER};
                color: {_TEXT};
                padding: 12px 32px;
                font-size: 15px;
                border-radius: 6px;
                min-width: 200px;
            }}
            QPushButton:hover {{
                border-color: {_ACCENT};
                background: rgba(108, 108, 240, 0.12);
            }}
        """

        btn_new = QPushButton("新建项目")
        btn_new.setStyleSheet(btn_style)
        btn_new.clicked.connect(self._on_new)
        center.addWidget(btn_new, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_open = QPushButton("打开项目")
        btn_open.setStyleSheet(btn_style)
        btn_open.clicked.connect(lambda: self.open_project_requested.emit())
        center.addWidget(btn_open, alignment=Qt.AlignmentFlag.AlignCenter)

        center.addSpacing(12)

        # 最近项目
        recent_label = QLabel("最近项目")
        recent_label.setStyleSheet(f"color: {_DIM}; font-size: 12px; background: transparent;")
        recent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.addWidget(recent_label)

        self._recent_list = QListWidget()
        self._recent_list.setFixedSize(360, 180)
        self._recent_list.setStyleSheet(f"""
            QListWidget {{
                background: {_INPUT_BG};
                border: 1px solid {_BORDER};
                border-radius: 6px;
                color: {_TEXT};
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
            }}
            QListWidget::item:selected {{
                background: {_ACCENT};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background: rgba(255, 255, 255, 0.05);
            }}
        """)
        self._recent_list.itemDoubleClicked.connect(self._on_recent_clicked)
        center.addWidget(self._recent_list, alignment=Qt.AlignmentFlag.AlignCenter)

        self._populate_recent()
        outer.addLayout(center)

    def _populate_recent(self) -> None:
        self._recent_list.clear()
        for path in _load_recent_projects():
            item = QListWidgetItem(path)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self._recent_list.addItem(item)
        if self._recent_list.count() == 0:
            empty = QListWidgetItem("(无最近项目)")
            empty.setFlags(Qt.ItemFlag.NoItemFlags)
            self._recent_list.addItem(empty)

    def _on_new(self) -> None:
        dlg = _SizePickerDialog(self)
        if dlg.exec_() == QDialog.DialogCode.Accepted:
            w, h = dlg.chosen_size
            self.new_project_requested.emit(w, h)

    def _on_recent_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.open_recent_requested.emit(path)
