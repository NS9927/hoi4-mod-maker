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
    ridge_mode_toggled = pyqtSignal(bool)       # 山脉画线模式开关
    ridge_peak_changed = pyqtSignal(int)         # 山峰高度
    ridge_falloff_changed = pyqtSignal(int)      # 衰减距离
    ridge_preview_requested = pyqtSignal()       # 请求刷新预览
    ridge_confirmed = pyqtSignal()               # 确认应用山脉
    ridge_cancelled = pyqtSignal()               # 取消山脉

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)

        # ═══════ 🏔 顶部：一键智能生成高度（推荐）═══════
        from ui.styles import _ACCENT
        auto_top_box = _make_section(tr("height_auto_top_section"))
        auto_top_layout = auto_top_box.layout()

        auto_top_btn = QPushButton(tr("height_auto_top_btn"))
        auto_top_btn.setMinimumHeight(44)
        auto_top_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: {_ACCENT};"
            f"  color: white;"
            f"  border: none;"
            f"  border-radius: 6px;"
            f"  font-size: 15px;"
            f"  font-weight: 600;"
            f"  padding: 8px;"
            f"}}"
            f"QPushButton:hover {{ background: #9090ff; }}"
        )
        auto_top_btn.setToolTip(tr("height_auto_top_tooltip"))
        auto_top_btn.clicked.connect(self.auto_height_requested.emit)
        auto_top_layout.addWidget(auto_top_btn)

        auto_top_tip = QLabel(tr("height_auto_top_tip"))
        auto_top_tip.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 4px 2px;")
        auto_top_tip.setWordWrap(True)
        auto_top_layout.addWidget(auto_top_tip)

        lay.addWidget(auto_top_box)

        # ── 使用说明 ──
        hint = QLabel(tr("height_hint"))
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # ── 详细参数（原智能生成区）──
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

        # ── 山脉画线 ──
        ridge_box = _make_section(tr("height_section_ridge"))
        rl = ridge_box.layout()

        ridge_hint = QLabel(tr("height_ridge_hint"))
        ridge_hint.setStyleSheet(f"color: {_DIM}; font-size: 11px;")
        ridge_hint.setWordWrap(True)
        rl.addWidget(ridge_hint)

        self._ridge_btn = QPushButton(tr("height_btn_ridge"))
        self._ridge_btn.setCheckable(True)
        self._ridge_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        self._ridge_btn.toggled.connect(self.ridge_mode_toggled.emit)
        rl.addWidget(self._ridge_btn)

        # 山峰高度
        rpk_row = QHBoxLayout()
        rpk_lbl = QLabel(tr("height_label_ridge_peak"))
        rpk_lbl.setStyleSheet(_LABEL_STYLE)
        rpk_row.addWidget(rpk_lbl)
        self._ridge_peak_label = QLabel("220")
        self._ridge_peak_label.setStyleSheet(_DIM_LABEL_STYLE)
        rpk_row.addStretch()
        rpk_row.addWidget(self._ridge_peak_label)
        rl.addLayout(rpk_row)

        self._ridge_peak_slider = QSlider(Qt.Orientation.Horizontal)
        self._ridge_peak_slider.setRange(100, 255)
        self._ridge_peak_slider.setValue(220)
        self._ridge_peak_slider.setStyleSheet(_SLIDER_STYLE)
        self._ridge_peak_slider.valueChanged.connect(
            lambda v: (self._ridge_peak_label.setText(str(v)), self.ridge_peak_changed.emit(v))
        )
        rl.addWidget(self._ridge_peak_slider)

        # 衰减距离
        rfo_row = QHBoxLayout()
        rfo_lbl = QLabel(tr("height_label_ridge_falloff"))
        rfo_lbl.setStyleSheet(_LABEL_STYLE)
        rfo_row.addWidget(rfo_lbl)
        self._ridge_falloff_label = QLabel("80px")
        self._ridge_falloff_label.setStyleSheet(_DIM_LABEL_STYLE)
        rfo_row.addStretch()
        rfo_row.addWidget(self._ridge_falloff_label)
        rl.addLayout(rfo_row)

        self._ridge_falloff_slider = QSlider(Qt.Orientation.Horizontal)
        self._ridge_falloff_slider.setRange(20, 300)
        self._ridge_falloff_slider.setValue(80)
        self._ridge_falloff_slider.setStyleSheet(_SLIDER_STYLE)
        self._ridge_falloff_slider.valueChanged.connect(
            lambda v: (self._ridge_falloff_label.setText(f"{v}px"), self.ridge_falloff_changed.emit(v))
        )
        rl.addWidget(self._ridge_falloff_slider)

        # 确认/取消按钮（画完线后显示）
        self._ridge_confirm_row = QWidget()
        cr = QHBoxLayout(self._ridge_confirm_row)
        cr.setContentsMargins(0, 8, 0, 0)
        cr.setSpacing(8)

        self._ridge_cancel_btn = QPushButton(tr("btn_cancel"))
        self._ridge_cancel_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        self._ridge_cancel_btn.clicked.connect(self.ridge_cancelled.emit)
        cr.addWidget(self._ridge_cancel_btn)

        self._ridge_confirm_btn = QPushButton(tr("height_btn_ridge_confirm"))
        self._ridge_confirm_btn.setStyleSheet(
            "QPushButton { background: #22c55e; color: white; padding: 8px;"
            " border-radius: 4px; font-weight: bold; font-size: 13px; }"
            "QPushButton:hover { background: #2ad66a; }"
        )
        self._ridge_confirm_btn.clicked.connect(self.ridge_confirmed.emit)
        cr.addWidget(self._ridge_confirm_btn)

        rl.addWidget(self._ridge_confirm_row)
        self._ridge_confirm_row.hide()

        # 滑块变化时请求刷新预览
        self._ridge_peak_slider.valueChanged.connect(lambda _: self._on_ridge_param_changed())
        self._ridge_falloff_slider.valueChanged.connect(lambda _: self._on_ridge_param_changed())

        lay.addWidget(ridge_box)

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

    def show_ridge_confirm(self) -> None:
        """画完线后显示确认/取消按钮。"""
        self._ridge_confirm_row.show()

    def hide_ridge_confirm(self) -> None:
        """隐藏确认/取消按钮。"""
        self._ridge_confirm_row.hide()

    def _on_ridge_param_changed(self) -> None:
        """滑块变化时，如果确认按钮可见（预览中），请求刷新预览。"""
        if self._ridge_confirm_row.isVisible():
            self.ridge_preview_requested.emit()
