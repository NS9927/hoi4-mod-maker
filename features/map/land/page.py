"""land feature 页面 (从 tool_panel 提取).

原始代码是 ToolPanel._build_land_page, 为了按 feature 组织
UI 搬到这里. panel 参数就是原来的 panel, 需要访问 panel._xxx 内部状态.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QSlider, QLabel, QButtonGroup,
    QSpinBox, QFrame, QStackedWidget, QGridLayout,
    QSizePolicy, QListWidget, QListWidgetItem, QComboBox,
    QLineEdit, QColorDialog,
)
from PyQt5.QtGui import QColor, QPixmap, QIcon, QBrush

from data.constants import (
    TILE_LAND, TILE_SEA, TILE_LAKE,
    BRUSH_MIN, BRUSH_MAX, BRUSH_DEFAULT,
)
from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX
from domain.managers.state import StateManager
from domain.managers.country import RULING_PARTIES
from domain.managers.river import PAINTABLE_RIVER_TYPES, RIVER_PALETTE

from ui.styles import (
    _BG, _INPUT_BG, _BORDER, _TEXT, _DIM, _ACCENT, _SUCCESS,
    _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE, _SLIDER_STYLE,
    _TOOL_BTN_STYLE, _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
    _SUCCESS_BTN_STYLE, _SPINBOX_STYLE, _LINEEDIT_STYLE,
    _COMBOBOX_STYLE, _LIST_STYLE, _color_icon,
)


def build_page(panel) -> QWidget:
    """构建 land 页. panel 是 ToolPanel 实例."""
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    # 提示
    hint = QLabel("画陆地/海洋/湖泊。画笔涂色，填充灌满区域，变换可框选移动/缩放/旋转")
    hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
    hint.setWordWrap(True)
    lay.addWidget(hint)

    # 工具按钮
    tools_box = panel._make_section("工具")
    tl = QHBoxLayout()
    panel._land_tool_group = QButtonGroup(panel)
    panel._land_tool_group.setExclusive(True)
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
        panel._land_tool_group.addButton(btn)
        tl.addWidget(btn)
        if tid == "brush":
            btn.setChecked(True)
    panel._land_tool_group.buttonClicked.connect(
        lambda b: panel.tool_changed.emit(b.property("tool_id"))
    )
    tools_box.layout().addLayout(tl)
    lay.addWidget(tools_box)

    # 画笔大小
    brush_box = panel._make_section("画笔大小")
    panel._land_brush_label = QLabel(f"{BRUSH_DEFAULT}px")
    panel._land_brush_label.setStyleSheet(_DIM_LABEL_STYLE)
    row = QHBoxLayout()
    lbl = QLabel("大小:")
    lbl.setStyleSheet(_LABEL_STYLE)
    row.addWidget(lbl)
    row.addStretch()
    row.addWidget(panel._land_brush_label)
    brush_box.layout().addLayout(row)

    panel._land_brush_slider = QSlider(Qt.Orientation.Horizontal)
    panel._land_brush_slider.setRange(BRUSH_MIN, BRUSH_MAX)
    panel._land_brush_slider.setValue(BRUSH_DEFAULT)
    panel._land_brush_slider.setStyleSheet(_SLIDER_STYLE)
    panel._land_brush_slider.valueChanged.connect(panel._on_land_brush)
    brush_box.layout().addWidget(panel._land_brush_slider)
    lay.addWidget(brush_box)

    # 地块类型
    tile_box = panel._make_section("大陆绘制")
    for tile_id, label, color in [
        (TILE_LAND, "画陆地", (139, 172, 101)),
        (TILE_SEA,  "画海洋", (68, 105, 156)),
        (TILE_LAKE, "画湖泊", (100, 160, 210)),
    ]:
        btn = QPushButton(f"  {label}")
        btn.setIcon(_color_icon(*color))
        btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        btn.clicked.connect(lambda _, t=tile_id: panel._on_tile_click(t))
        tile_box.layout().addWidget(btn)
    lay.addWidget(tile_box)

    # 生成省份
    gen_box = panel._make_section("省份生成")
    gen_btn = QPushButton("生成省份")
    gen_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    gen_btn.clicked.connect(panel._on_generate_provinces)
    gen_box.layout().addWidget(gen_btn)

    spin_row = QHBoxLayout()
    spin_lbl = QLabel("省份数量:")
    spin_lbl.setStyleSheet(_LABEL_STYLE)
    spin_row.addWidget(spin_lbl)
    panel._province_count_spin = QSpinBox()
    panel._province_count_spin.setRange(100, 20000)
    panel._province_count_spin.setSingleStep(500)
    panel._province_count_spin.setValue(12000)
    panel._province_count_spin.setStyleSheet(_SPINBOX_STYLE)
    spin_row.addWidget(panel._province_count_spin)
    gen_box.layout().addLayout(spin_row)

    validate_btn = QPushButton("验证省份")
    validate_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
    validate_btn.clicked.connect(panel.validate_requested.emit)
    gen_box.layout().addWidget(validate_btn)
    lay.addWidget(gen_box)

    # ── 原版地图参考 ──
    vanilla_box = panel._make_section("原版地图参考")
    v_opacity_row = QHBoxLayout()
    v_olbl = QLabel("透明度:")
    v_olbl.setStyleSheet(_LABEL_STYLE)
    v_opacity_row.addWidget(v_olbl)
    panel._vanilla_ref_opacity_label = QLabel("30%")
    panel._vanilla_ref_opacity_label.setStyleSheet(_DIM_LABEL_STYLE)
    v_opacity_row.addStretch()
    v_opacity_row.addWidget(panel._vanilla_ref_opacity_label)
    vanilla_box.layout().addLayout(v_opacity_row)

    panel._vanilla_ref_opacity_slider = QSlider(Qt.Orientation.Horizontal)
    panel._vanilla_ref_opacity_slider.setRange(0, 100)
    panel._vanilla_ref_opacity_slider.setValue(30)
    panel._vanilla_ref_opacity_slider.setStyleSheet(_SLIDER_STYLE)
    panel._vanilla_ref_opacity_slider.valueChanged.connect(
        lambda v: panel._vanilla_ref_opacity_label.setText(f"{v}%")
    )
    vanilla_box.layout().addWidget(panel._vanilla_ref_opacity_slider)
    panel._vanilla_ref_toggle = QPushButton("隐藏")
    panel._vanilla_ref_toggle.setCheckable(True)
    panel._vanilla_ref_toggle.setStyleSheet(_SECONDARY_BTN_STYLE)
    panel._vanilla_ref_toggle.toggled.connect(
        lambda on: (panel._vanilla_ref_toggle.setText("显示" if on else "隐藏"))
    )
    vanilla_box.layout().addWidget(panel._vanilla_ref_toggle)
    lay.addWidget(vanilla_box)

    # ── 自定义参考图 ──
    ref_box = panel._make_section("自定义参考图")
    opacity_row = QHBoxLayout()
    olbl = QLabel("透明度:")
    olbl.setStyleSheet(_LABEL_STYLE)
    opacity_row.addWidget(olbl)
    panel._ref_opacity_label = QLabel("40%")
    panel._ref_opacity_label.setStyleSheet(_DIM_LABEL_STYLE)
    opacity_row.addStretch()
    opacity_row.addWidget(panel._ref_opacity_label)
    ref_box.layout().addLayout(opacity_row)

    panel._ref_opacity_slider = QSlider(Qt.Orientation.Horizontal)
    panel._ref_opacity_slider.setRange(0, 100)
    panel._ref_opacity_slider.setValue(40)
    panel._ref_opacity_slider.setStyleSheet(_SLIDER_STYLE)
    panel._ref_opacity_slider.valueChanged.connect(
        lambda v: panel._ref_opacity_label.setText(f"{v}%")
    )
    ref_box.layout().addWidget(panel._ref_opacity_slider)

    # 缩放控制
    scale_row = QHBoxLayout()
    slbl = QLabel("缩放:")
    slbl.setStyleSheet(_LABEL_STYLE)
    scale_row.addWidget(slbl)
    panel._ref_scale_label = QLabel("100%")
    panel._ref_scale_label.setStyleSheet(_DIM_LABEL_STYLE)
    scale_row.addStretch()
    scale_row.addWidget(panel._ref_scale_label)
    ref_box.layout().addLayout(scale_row)

    panel._ref_scale_slider = QSlider(Qt.Orientation.Horizontal)
    panel._ref_scale_slider.setRange(10, 500)  # 10% ~ 500%
    panel._ref_scale_slider.setValue(100)
    panel._ref_scale_slider.setStyleSheet(_SLIDER_STYLE)
    panel._ref_scale_slider.valueChanged.connect(
        lambda v: panel._ref_scale_label.setText(f"{v}%")
    )
    ref_box.layout().addWidget(panel._ref_scale_slider)

    # 铺满地图按钮
    fit_btn = QPushButton("铺满地图")
    fit_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
    ref_box.layout().addWidget(fit_btn)
    panel._ref_fit_btn = fit_btn

    # 显示/隐藏
    panel._ref_toggle = QPushButton("隐藏")
    panel._ref_toggle.setCheckable(True)
    panel._ref_toggle.setStyleSheet(_SECONDARY_BTN_STYLE)
    panel._ref_toggle.toggled.connect(
        lambda on: panel._ref_toggle.setText("显示" if on else "隐藏")
    )
    ref_box.layout().addWidget(panel._ref_toggle)

    lay.addWidget(ref_box)

    lay.addStretch()
    return page
