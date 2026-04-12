"""river feature 页面 (从 tool_panel 提取).

原始代码是 ToolPanel._build_river_page, 为了按 feature 组织
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
from domain.managers.river import (
    RIVER_MARKER_TYPES, RIVER_WIDTH_TYPES, RIVER_PALETTE,
    PAINTABLE_RIVER_TYPES,
)

from ui.styles import (
    _BG, _INPUT_BG, _BORDER, _TEXT, _DIM, _ACCENT, _SUCCESS,
    _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE, _SLIDER_STYLE,
    _TOOL_BTN_STYLE, _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
    _SUCCESS_BTN_STYLE, _SPINBOX_STYLE, _LINEEDIT_STYLE,
    _COMBOBOX_STYLE, _LIST_STYLE, _color_icon,
)


def build_page(panel) -> QWidget:
    """构建 river 页. panel 是 ToolPanel 实例."""
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    # 提示
    hint = QLabel("河流规则: 必须1像素宽，只走上下左右(不能斜走)\n"
                  "每条河需要1个源头(绿)。红=支流汇入 黄=分叉\n"
                  "画笔大小仅影响橡皮擦范围，河流本身必须1像素宽")
    hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
    hint.setWordWrap(True)
    lay.addWidget(hint)

    # 工具按钮
    tools_box = panel._make_section("工具")
    tl = QHBoxLayout()
    panel._river_tool_group = QButtonGroup(panel)
    panel._river_tool_group.setExclusive(True)
    for tid, label in [("brush", "画笔"), ("eraser", "橡皮"), ("pan", "平移")]:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setProperty("tool_id", tid)
        btn.setStyleSheet(_TOOL_BTN_STYLE)
        btn.setMinimumWidth(48)
        panel._river_tool_group.addButton(btn)
        tl.addWidget(btn)
        if tid == "brush":
            btn.setChecked(True)
    panel._river_tool_group.buttonClicked.connect(
        lambda b: panel.tool_changed.emit(b.property("tool_id"))
    )
    tools_box.layout().addLayout(tl)
    lay.addWidget(tools_box)

    # 画笔大小
    brush_box = panel._make_section("画笔大小")
    panel._river_brush_label = QLabel("3px")
    panel._river_brush_label.setStyleSheet(_DIM_LABEL_STYLE)
    row = QHBoxLayout()
    lbl = QLabel("大小:")
    lbl.setStyleSheet(_LABEL_STYLE)
    row.addWidget(lbl)
    row.addStretch()
    row.addWidget(panel._river_brush_label)
    brush_box.layout().addLayout(row)

    panel._river_brush_slider = QSlider(Qt.Orientation.Horizontal)
    panel._river_brush_slider.setRange(1, 20)
    panel._river_brush_slider.setValue(3)
    panel._river_brush_slider.setStyleSheet(_SLIDER_STYLE)
    panel._river_brush_slider.valueChanged.connect(panel._on_river_brush)
    brush_box.layout().addWidget(panel._river_brush_slider)
    lay.addWidget(brush_box)

    # 标记类型 (单像素)
    marker_box = panel._make_section("标记 (单像素)")
    mgrid = QGridLayout()
    mgrid.setSpacing(4)

    for i, (idx, name) in enumerate(RIVER_MARKER_TYPES):
        r, g, b = RIVER_PALETTE[idx]
        btn = _make_river_btn(name, r, g, b)
        btn.clicked.connect(lambda _, ix=idx: panel.river_type_changed.emit(ix))
        mgrid.addWidget(btn, 0, i)

    marker_box.layout().addLayout(mgrid)
    lay.addWidget(marker_box)

    # 河流宽度画笔
    width_box = panel._make_section("宽度画笔")
    wgrid = QGridLayout()
    wgrid.setSpacing(4)

    for i, (idx, name) in enumerate(RIVER_WIDTH_TYPES):
        r, g, b = RIVER_PALETTE[idx]
        btn = _make_river_btn(name, r, g, b)
        btn.clicked.connect(lambda _, ix=idx: panel.river_type_changed.emit(ix))
        wgrid.addWidget(btn, i // 3, i % 3)

    width_box.layout().addLayout(wgrid)
    lay.addWidget(width_box)

    # 验证按钮
    validate_btn = QPushButton("验证河流")
    validate_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
    validate_btn.clicked.connect(panel.validate_river_requested.emit)
    lay.addWidget(validate_btn)

    lay.addStretch()
    return page


def _make_river_btn(name: str, r: int, g: int, b: int) -> QPushButton:
    """创建河流类型按钮."""
    btn = QPushButton(name)
    brightness = r * 0.299 + g * 0.587 + b * 0.114
    fg = "#000000" if brightness > 140 else "#ffffff"
    btn.setStyleSheet(f"""
        QPushButton {{
            background: rgb({r},{g},{b});
            border: 2px solid transparent;
            color: {fg};
            padding: 6px 2px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
            min-width: 55px;
        }}
        QPushButton:hover {{
            border-color: white;
        }}
    """)
    return btn
