"""land feature 页面 — 独立 QWidget, 不依赖 ToolPanel."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QSlider, QLabel, QButtonGroup,
    QSpinBox, QGridLayout,
)

from data.constants import (
    TILE_LAND, TILE_SEA, TILE_LAKE,
    BRUSH_MIN, BRUSH_MAX, BRUSH_DEFAULT,
)

from ui.styles import (
    make_section as _make_section,
    _DIM, _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE, _SLIDER_STYLE,
    _TOOL_BTN_STYLE, _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
    _SPINBOX_STYLE, _color_icon,
)




class LandPage(QWidget):
    """陆地/海洋/湖泊绘制页面."""

    # 输出信号
    tool_changed = pyqtSignal(str)
    tile_type_changed = pyqtSignal(int)
    brush_size_changed = pyqtSignal(int)
    generate_provinces_requested = pyqtSignal(int)
    validate_requested = pyqtSignal()
    quick_init_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)

        # 提示
        hint = QLabel("画陆地/海洋/湖泊。画笔涂色，填充灌满区域，变换可框选移动/缩放/旋转")
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # 工具按钮
        tools_box = _make_section("工具")
        tl = QHBoxLayout()
        self._land_tool_group = QButtonGroup(self)
        self._land_tool_group.setExclusive(True)
        for tid, label in [("brush", "画笔"), ("eraser", "橡皮"),
                           ("fill", "填充"), ("transform", "变换"), ("pan", "平移")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("tool_id", tid)
            btn.setStyleSheet(_TOOL_BTN_STYLE)
            btn.setMinimumWidth(48)
            if tid == "fill":
                btn.setToolTip("点击一个区域，自动填满相同类型的连通区域")
            elif tid == "transform":
                btn.setToolTip("框选区域后可移动/缩放/旋转。Enter确认，ESC取消")
            self._land_tool_group.addButton(btn)
            tl.addWidget(btn)
            if tid == "brush":
                btn.setChecked(True)
        self._land_tool_group.buttonClicked.connect(
            lambda b: self.tool_changed.emit(b.property("tool_id"))
        )
        tools_box.layout().addLayout(tl)
        lay.addWidget(tools_box)

        # 画笔大小
        brush_box = _make_section("画笔大小")
        self._land_brush_label = QLabel(f"{BRUSH_DEFAULT}px")
        self._land_brush_label.setStyleSheet(_DIM_LABEL_STYLE)
        row = QHBoxLayout()
        lbl = QLabel("大小:")
        lbl.setStyleSheet(_LABEL_STYLE)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(self._land_brush_label)
        brush_box.layout().addLayout(row)

        self._land_brush_slider = QSlider(Qt.Orientation.Horizontal)
        self._land_brush_slider.setRange(BRUSH_MIN, BRUSH_MAX)
        self._land_brush_slider.setValue(BRUSH_DEFAULT)
        self._land_brush_slider.setStyleSheet(_SLIDER_STYLE)
        self._land_brush_slider.valueChanged.connect(self._on_land_brush)
        brush_box.layout().addWidget(self._land_brush_slider)
        lay.addWidget(brush_box)

        # 地块类型
        tile_box = _make_section("大陆绘制")
        for tile_id, label, color in [
            (TILE_LAND, "画陆地", (139, 172, 101)),
            (TILE_SEA,  "画海洋", (68, 105, 156)),
            (TILE_LAKE, "画湖泊", (100, 160, 210)),
        ]:
            btn = QPushButton(f"  {label}")
            btn.setIcon(_color_icon(*color))
            btn.setStyleSheet(_SECONDARY_BTN_STYLE)
            btn.clicked.connect(lambda _, t=tile_id: self._on_tile_click(t))
            tile_box.layout().addWidget(btn)
        lay.addWidget(tile_box)

        # 生成省份
        gen_box = _make_section("省份生成")
        gen_btn = QPushButton("生成省份")
        gen_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        gen_btn.clicked.connect(self._on_generate_provinces)
        gen_box.layout().addWidget(gen_btn)

        spin_row = QHBoxLayout()
        spin_lbl = QLabel("省份数量:")
        spin_lbl.setStyleSheet(_LABEL_STYLE)
        spin_row.addWidget(spin_lbl)
        self._province_count_spin = QSpinBox()
        self._province_count_spin.setRange(100, 20000)
        self._province_count_spin.setSingleStep(500)
        self._province_count_spin.setValue(12000)
        self._province_count_spin.setStyleSheet(_SPINBOX_STYLE)
        spin_row.addWidget(self._province_count_spin)
        gen_box.layout().addLayout(spin_row)

        # 海洋省份密度
        sea_row = QHBoxLayout()
        sea_lbl = QLabel("海洋密度:")
        sea_lbl.setStyleSheet(_LABEL_STYLE)
        sea_row.addWidget(sea_lbl)
        self._sea_density_label = QLabel("15%")
        self._sea_density_label.setStyleSheet(_DIM_LABEL_STYLE)
        sea_row.addStretch()
        sea_row.addWidget(self._sea_density_label)
        gen_box.layout().addLayout(sea_row)

        self._sea_density_slider = QSlider(Qt.Orientation.Horizontal)
        self._sea_density_slider.setRange(5, 100)
        self._sea_density_slider.setValue(15)
        self._sea_density_slider.setStyleSheet(_SLIDER_STYLE)
        self._sea_density_slider.valueChanged.connect(
            lambda v: self._sea_density_label.setText(f"{v}%")
        )
        gen_box.layout().addWidget(self._sea_density_slider)

        # 湖泊省份密度
        lake_row = QHBoxLayout()
        lake_lbl = QLabel("湖泊密度:")
        lake_lbl.setStyleSheet(_LABEL_STYLE)
        lake_row.addWidget(lake_lbl)
        self._lake_density_label = QLabel("30%")
        self._lake_density_label.setStyleSheet(_DIM_LABEL_STYLE)
        lake_row.addStretch()
        lake_row.addWidget(self._lake_density_label)
        gen_box.layout().addLayout(lake_row)

        self._lake_density_slider = QSlider(Qt.Orientation.Horizontal)
        self._lake_density_slider.setRange(10, 100)
        self._lake_density_slider.setValue(30)
        self._lake_density_slider.setStyleSheet(_SLIDER_STYLE)
        self._lake_density_slider.valueChanged.connect(
            lambda v: self._lake_density_label.setText(f"{v}%")
        )
        gen_box.layout().addWidget(self._lake_density_slider)

        validate_btn = QPushButton("验证省份")
        validate_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        validate_btn.clicked.connect(self.validate_requested.emit)
        gen_box.layout().addWidget(validate_btn)

        quick_init_btn = QPushButton("一键初始化（州+战略区+国家）")
        quick_init_btn.setStyleSheet(
            "QPushButton { background: #22c55e; color: white; padding: 8px;"
            " border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #2ad66a; }"
        )
        quick_init_btn.setToolTip("自动生成州、战略区域、默认国家，一步到位可导出")
        quick_init_btn.clicked.connect(self.quick_init_requested.emit)
        gen_box.layout().addWidget(quick_init_btn)

        lay.addWidget(gen_box)

        # ── 原版地图参考 ──
        vanilla_box = _make_section("原版地图参考")
        v_opacity_row = QHBoxLayout()
        v_olbl = QLabel("透明度:")
        v_olbl.setStyleSheet(_LABEL_STYLE)
        v_opacity_row.addWidget(v_olbl)
        self._vanilla_ref_opacity_label = QLabel("30%")
        self._vanilla_ref_opacity_label.setStyleSheet(_DIM_LABEL_STYLE)
        v_opacity_row.addStretch()
        v_opacity_row.addWidget(self._vanilla_ref_opacity_label)
        vanilla_box.layout().addLayout(v_opacity_row)

        self._vanilla_ref_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._vanilla_ref_opacity_slider.setRange(0, 100)
        self._vanilla_ref_opacity_slider.setValue(30)
        self._vanilla_ref_opacity_slider.setStyleSheet(_SLIDER_STYLE)
        self._vanilla_ref_opacity_slider.valueChanged.connect(
            lambda v: self._vanilla_ref_opacity_label.setText(f"{v}%")
        )
        vanilla_box.layout().addWidget(self._vanilla_ref_opacity_slider)
        self._vanilla_ref_toggle = QPushButton("隐藏")
        self._vanilla_ref_toggle.setCheckable(True)
        self._vanilla_ref_toggle.setStyleSheet(_SECONDARY_BTN_STYLE)
        self._vanilla_ref_toggle.toggled.connect(
            lambda on: (self._vanilla_ref_toggle.setText("显示" if on else "隐藏"))
        )
        vanilla_box.layout().addWidget(self._vanilla_ref_toggle)
        lay.addWidget(vanilla_box)

        # ── 自定义参考图 ──
        ref_box = _make_section("自定义参考图")
        opacity_row = QHBoxLayout()
        olbl = QLabel("透明度:")
        olbl.setStyleSheet(_LABEL_STYLE)
        opacity_row.addWidget(olbl)
        self._ref_opacity_label = QLabel("40%")
        self._ref_opacity_label.setStyleSheet(_DIM_LABEL_STYLE)
        opacity_row.addStretch()
        opacity_row.addWidget(self._ref_opacity_label)
        ref_box.layout().addLayout(opacity_row)

        self._ref_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._ref_opacity_slider.setRange(0, 100)
        self._ref_opacity_slider.setValue(40)
        self._ref_opacity_slider.setStyleSheet(_SLIDER_STYLE)
        self._ref_opacity_slider.valueChanged.connect(
            lambda v: self._ref_opacity_label.setText(f"{v}%")
        )
        ref_box.layout().addWidget(self._ref_opacity_slider)

        # 缩放控制
        scale_row = QHBoxLayout()
        slbl = QLabel("缩放:")
        slbl.setStyleSheet(_LABEL_STYLE)
        scale_row.addWidget(slbl)
        self._ref_scale_label = QLabel("100%")
        self._ref_scale_label.setStyleSheet(_DIM_LABEL_STYLE)
        scale_row.addStretch()
        scale_row.addWidget(self._ref_scale_label)
        ref_box.layout().addLayout(scale_row)

        self._ref_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self._ref_scale_slider.setRange(10, 500)
        self._ref_scale_slider.setValue(100)
        self._ref_scale_slider.setStyleSheet(_SLIDER_STYLE)
        self._ref_scale_slider.valueChanged.connect(
            lambda v: self._ref_scale_label.setText(f"{v}%")
        )
        ref_box.layout().addWidget(self._ref_scale_slider)

        # 铺满地图按钮
        self._ref_fit_btn = QPushButton("铺满地图")
        self._ref_fit_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        ref_box.layout().addWidget(self._ref_fit_btn)

        # 显示/隐藏
        self._ref_toggle = QPushButton("隐藏")
        self._ref_toggle.setCheckable(True)
        self._ref_toggle.setStyleSheet(_SECONDARY_BTN_STYLE)
        self._ref_toggle.toggled.connect(
            lambda on: self._ref_toggle.setText("显示" if on else "隐藏")
        )
        ref_box.layout().addWidget(self._ref_toggle)

        lay.addWidget(ref_box)

        lay.addStretch()

    # ── 槽函数 ──
    def _on_land_brush(self, size: int) -> None:
        self._land_brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def _on_tile_click(self, tile_type: int) -> None:
        self.tile_type_changed.emit(tile_type)
        # 自动切换到画笔工具
        for btn in self._land_tool_group.buttons():
            if btn.property("tool_id") == "brush":
                btn.setChecked(True)
                self.tool_changed.emit("brush")
                break

    def _on_generate_provinces(self) -> None:
        count = self._province_count_spin.value()
        self.generate_provinces_requested.emit(count)

    def get_generation_params(self) -> dict:
        """返回省份生成的所有参数。"""
        return {
            "target_count": self._province_count_spin.value(),
            "sea_scale": self._sea_density_slider.value() / 100.0,
            "lake_scale": self._lake_density_slider.value() / 100.0,
        }
