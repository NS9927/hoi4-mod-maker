"""新大陆页面 — 专门用于在已有地图上扩展新陆地。"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel,
)

from data.constants import BRUSH_MIN, BRUSH_MAX, BRUSH_DEFAULT
from ui.i18n import tr

from ui.styles import (
    make_section as _make_section,
    _DIM, _LABEL_STYLE, _DIM_LABEL_STYLE, _SLIDER_STYLE,
    _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
)


class NewLandPage(QWidget):
    """新大陆画笔页面：画新陆地 → 生成省份 → 清空。"""

    brush_size_changed = pyqtSignal(int)
    generate_requested = pyqtSignal()
    clear_mask_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)

        # 说明
        hint = QLabel(tr("new_land_hint"))
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # 画笔大小
        brush_box = _make_section(tr("new_land_section_brush"))
        self._brush_label = QLabel(f"{BRUSH_DEFAULT}px")
        self._brush_label.setStyleSheet(_DIM_LABEL_STYLE)
        row = QHBoxLayout()
        lbl = QLabel(tr("new_land_size_label"))
        lbl.setStyleSheet(_LABEL_STYLE)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(self._brush_label)
        brush_box.layout().addLayout(row)

        self._brush_slider = QSlider(Qt.Orientation.Horizontal)
        self._brush_slider.setRange(BRUSH_MIN, BRUSH_MAX)
        self._brush_slider.setValue(BRUSH_DEFAULT)
        self._brush_slider.setStyleSheet(_SLIDER_STYLE)
        self._brush_slider.valueChanged.connect(self._on_brush_changed)
        brush_box.layout().addWidget(self._brush_slider)
        lay.addWidget(brush_box)

        # 已画像素
        info_box = _make_section(tr("new_land_section_status"))
        self._pixel_label = QLabel(tr("new_land_pixel_count"))
        self._pixel_label.setStyleSheet(_LABEL_STYLE)
        info_box.layout().addWidget(self._pixel_label)
        lay.addWidget(info_box)

        # 操作按钮
        action_box = _make_section(tr("new_land_section_actions"))

        gen_btn = QPushButton(tr("new_land_generate"))
        gen_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        gen_btn.setToolTip(tr("new_land_generate_tip"))
        gen_btn.clicked.connect(self.generate_requested.emit)
        action_box.layout().addWidget(gen_btn)

        clear_btn = QPushButton(tr("new_land_clear"))
        clear_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        clear_btn.setToolTip(tr("new_land_clear_tip"))
        clear_btn.clicked.connect(self.clear_mask_requested.emit)
        action_box.layout().addWidget(clear_btn)

        lay.addWidget(action_box)
        lay.addStretch()

    def _on_brush_changed(self, size: int) -> None:
        self._brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def update_pixel_count(self, count: int) -> None:
        """外部调用更新已画像素数。"""
        self._pixel_label.setText(tr("new_land_pixel_painted_fmt", count))
