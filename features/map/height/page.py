"""height feature 页面 — 独立 QWidget, 不依赖 ToolPanel."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QSlider, QLabel, QGridLayout,
)

from ui.styles import (
    make_section as _make_section,
    _DIM, _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE, _SLIDER_STYLE,
    _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
)




class HeightPage(QWidget):
    """高度编辑页面."""

    # 输出信号
    height_value_changed = pyqtSignal(int)
    auto_height_requested = pyqtSignal()
    smooth_height_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)

        # 提示
        hint = QLabel("点击省份设高度。改地形会自动联动高度\n彩色显示: 蓝=海 绿=平原 棕=山 白=雪顶")
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # 高度值
        height_box = _make_section("高度值")
        val_row = QHBoxLayout()
        vlbl = QLabel("高度:")
        vlbl.setStyleSheet(_LABEL_STYLE)
        val_row.addWidget(vlbl)
        self._height_value_label = QLabel("120")
        self._height_value_label.setStyleSheet(_DIM_LABEL_STYLE)
        val_row.addStretch()
        val_row.addWidget(self._height_value_label)
        height_box.layout().addLayout(val_row)

        self._height_slider = QSlider(Qt.Orientation.Horizontal)
        self._height_slider.setRange(0, 255)
        self._height_slider.setValue(120)
        self._height_slider.setStyleSheet(_SLIDER_STYLE)
        self._height_slider.valueChanged.connect(self._on_height_value)
        height_box.layout().addWidget(self._height_slider)
        lay.addWidget(height_box)

        # 预设按钮
        preset_box = _make_section("预设")
        preset_grid = QGridLayout()
        preset_grid.setSpacing(4)
        presets = [
            ("海底", 40), ("海平面", 95), ("平地", 120),
            ("丘陵", 160), ("山地", 220),
        ]
        for i, (name, val) in enumerate(presets):
            btn = QPushButton(f"{name}({val})")
            btn.setStyleSheet(_SECONDARY_BTN_STYLE)
            btn.clicked.connect(lambda _, v=val: self._apply_height_preset(v))
            preset_grid.addWidget(btn, i // 3, i % 3)
        preset_box.layout().addLayout(preset_grid)
        lay.addWidget(preset_box)

        # 操作按钮
        auto_btn = QPushButton("从地形自动生成")
        auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        auto_btn.clicked.connect(self.auto_height_requested.emit)
        lay.addWidget(auto_btn)

        smooth_btn = QPushButton("平滑")
        smooth_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        smooth_btn.clicked.connect(self.smooth_height_requested.emit)
        lay.addWidget(smooth_btn)

        lay.addStretch()

    # ── 槽函数 ──
    def _on_height_value(self, value: int) -> None:
        self._height_value_label.setText(str(value))
        self.height_value_changed.emit(value)

    def _apply_height_preset(self, value: int) -> None:
        self._height_slider.setValue(value)
