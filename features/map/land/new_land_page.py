"""新大陆页面 — 专门用于在已有地图上扩展新陆地。"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel,
)

from data.constants import BRUSH_MIN, BRUSH_MAX, BRUSH_DEFAULT

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
        hint = QLabel(
            "用画笔在海洋上画新陆地，画完后点「生成省份」。\n"
            "只为画的区域生成省份，旧大陆不受影响。"
        )
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # 画笔大小
        brush_box = _make_section("画笔大小")
        self._brush_label = QLabel(f"{BRUSH_DEFAULT}px")
        self._brush_label.setStyleSheet(_DIM_LABEL_STYLE)
        row = QHBoxLayout()
        lbl = QLabel("大小")
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
        info_box = _make_section("状态")
        self._pixel_label = QLabel("已画: 0 像素")
        self._pixel_label.setStyleSheet(_LABEL_STYLE)
        info_box.layout().addWidget(self._pixel_label)
        lay.addWidget(info_box)

        # 操作按钮
        action_box = _make_section("操作")

        gen_btn = QPushButton("生成省份")
        gen_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        gen_btn.setToolTip("为新画的陆地区域生成省份")
        gen_btn.clicked.connect(self.generate_requested.emit)
        action_box.layout().addWidget(gen_btn)

        clear_btn = QPushButton("清空画笔")
        clear_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        clear_btn.setToolTip("清空已画的新陆地记录（不删除已画的陆地）")
        clear_btn.clicked.connect(self.clear_mask_requested.emit)
        action_box.layout().addWidget(clear_btn)

        lay.addWidget(action_box)
        lay.addStretch()

    def _on_brush_changed(self, size: int) -> None:
        self._brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def update_pixel_count(self, count: int) -> None:
        """外部调用更新已画像素数。"""
        self._pixel_label.setText(f"已画: {count} 像素")
