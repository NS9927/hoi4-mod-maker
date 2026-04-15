"""height feature 页面 — 高度图编辑。

流程: 画完陆海 → 点「智能生成」自动算高度 → 用画笔微调 → 切地形模式生成地形。
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QGridLayout, QSpinBox,
)

from ui.styles import (
    make_section as _make_section,
    _DIM, _LABEL_STYLE, _DIM_LABEL_STYLE, _SLIDER_STYLE,
    _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE, _SPINBOX_STYLE,
)
from ui.i18n import tr


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

        # ── 使用说明 ──
        hint = QLabel(tr("height_hint"))
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # ── 智能生成 ──
        gen_box = _make_section(tr("height_section_auto_gen"))
        gl = gen_box.layout()

        auto_btn = QPushButton(tr("height_btn_auto_gen"))
        auto_btn.setStyleSheet(
            "QPushButton { background: #6c6cf0; color: white; padding: 10px;"
            " font-size: 14px; font-weight: bold; border-radius: 5px; border: none; }"
            "QPushButton:hover { background: #7c7cff; }"
        )
        auto_btn.setToolTip(tr("height_btn_auto_gen_tip"))
        auto_btn.clicked.connect(self.auto_height_requested.emit)
        gl.addWidget(auto_btn)

        # 种子
        seed_row = QHBoxLayout()
        seed_lbl = QLabel(tr("height_label_seed"))
        seed_lbl.setStyleSheet(_LABEL_STYLE)
        seed_row.addWidget(seed_lbl)
        self._height_seed_spin = QSpinBox()
        self._height_seed_spin.setRange(0, 99999)
        self._height_seed_spin.setValue(42)
        self._height_seed_spin.setStyleSheet(_SPINBOX_STYLE)
        seed_row.addWidget(self._height_seed_spin)
        rand_btn = QPushButton(tr("height_btn_random"))
        rand_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        rand_btn.setMaximumWidth(60)
        rand_btn.clicked.connect(self._randomize_seed)
        seed_row.addWidget(rand_btn)
        gl.addLayout(seed_row)

        # 山脉强度
        mt_row = QHBoxLayout()
        mt_lbl = QLabel(tr("height_label_mountain"))
        mt_lbl.setStyleSheet(_LABEL_STYLE)
        mt_row.addWidget(mt_lbl)
        self._mountain_label = QLabel("200")
        self._mountain_label.setStyleSheet(_DIM_LABEL_STYLE)
        mt_row.addStretch()
        mt_row.addWidget(self._mountain_label)
        gl.addLayout(mt_row)

        self._mountain_slider = QSlider(Qt.Orientation.Horizontal)
        self._mountain_slider.setRange(50, 400)
        self._mountain_slider.setValue(200)
        self._mountain_slider.setStyleSheet(_SLIDER_STYLE)
        self._mountain_slider.valueChanged.connect(
            lambda v: self._mountain_label.setText(str(v))
        )
        gl.addWidget(self._mountain_slider)

        smooth_btn = QPushButton(tr("height_btn_smooth"))
        smooth_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        smooth_btn.setToolTip(tr("height_btn_smooth_tip"))
        smooth_btn.clicked.connect(self.smooth_height_requested.emit)
        gl.addWidget(smooth_btn)

        lay.addWidget(gen_box)

        # ── 手动画笔 ──
        brush_box = _make_section(tr("height_section_brush"))
        bl = brush_box.layout()

        brush_hint = QLabel(tr("height_brush_hint"))
        brush_hint.setStyleSheet(f"color: {_DIM}; font-size: 11px;")
        brush_hint.setWordWrap(True)
        bl.addWidget(brush_hint)

        val_row = QHBoxLayout()
        vlbl = QLabel(tr("height_label_value"))
        vlbl.setStyleSheet(_LABEL_STYLE)
        val_row.addWidget(vlbl)
        self._height_value_label = QLabel("120")
        self._height_value_label.setStyleSheet(_DIM_LABEL_STYLE)
        val_row.addStretch()
        val_row.addWidget(self._height_value_label)
        bl.addLayout(val_row)

        self._height_slider = QSlider(Qt.Orientation.Horizontal)
        self._height_slider.setRange(0, 255)
        self._height_slider.setValue(120)
        self._height_slider.setStyleSheet(_SLIDER_STYLE)
        self._height_slider.valueChanged.connect(self._on_height_value)
        bl.addWidget(self._height_slider)

        # 快捷预设
        preset_row = QHBoxLayout()
        preset_row.setSpacing(4)
        for name, val in [(tr("height_preset_seabed"), 40), (tr("height_preset_sealevel"), 95), (tr("height_preset_flat"), 110),
                          (tr("height_preset_hills"), 150), (tr("height_preset_mountain"), 200)]:
            btn = QPushButton(name)
            btn.setStyleSheet(_SECONDARY_BTN_STYLE + "QPushButton { padding: 4px 6px; font-size: 11px; }")
            btn.setToolTip(tr("height_preset_tip", val))
            btn.clicked.connect(lambda _, v=val: self._height_slider.setValue(v))
            preset_row.addWidget(btn)
        bl.addLayout(preset_row)

        lay.addWidget(brush_box)

        # ── 高度参考 ──
        ref_box = _make_section(tr("height_section_ref"))
        ref_lbl = QLabel(tr("height_ref_text"))
        ref_lbl.setStyleSheet(f"color: {_DIM}; font-size: 11px;")
        ref_box.layout().addWidget(ref_lbl)
        lay.addWidget(ref_box)

        lay.addStretch()

    # ── 槽函数 ──
    def _on_height_value(self, value: int) -> None:
        self._height_value_label.setText(str(value))
        self.height_value_changed.emit(value)

    def _randomize_seed(self) -> None:
        import random
        self._height_seed_spin.setValue(random.randint(0, 99999))

    def get_height_config(self):
        """返回当前 UI 参数构建的 HeightGenConfig。"""
        from services.terrain_service import HeightGenConfig
        return HeightGenConfig(
            noise_amplitude=float(self._mountain_slider.value()),
            seed=self._height_seed_spin.value(),
        )
