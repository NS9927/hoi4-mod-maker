"""height feature 页面 (从 tool_panel 提取).

原始代码是 ToolPanel._build_height_page, 为了按 feature 组织
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
    """构建 height 页. panel 是 ToolPanel 实例."""
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    # 提示
    hint = QLabel("点击省份设高度。改地形会自动联动高度\n彩色显示: 蓝=海 绿=平原 棕=山 白=雪顶")
    hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
    hint.setWordWrap(True)
    lay.addWidget(hint)

    # 高度值
    height_box = panel._make_section("高度值")
    val_row = QHBoxLayout()
    vlbl = QLabel("高度:")
    vlbl.setStyleSheet(_LABEL_STYLE)
    val_row.addWidget(vlbl)
    panel._height_value_label = QLabel("120")
    panel._height_value_label.setStyleSheet(_DIM_LABEL_STYLE)
    val_row.addStretch()
    val_row.addWidget(panel._height_value_label)
    height_box.layout().addLayout(val_row)

    panel._height_slider = QSlider(Qt.Orientation.Horizontal)
    panel._height_slider.setRange(0, 255)
    panel._height_slider.setValue(120)
    panel._height_slider.setStyleSheet(_SLIDER_STYLE)
    panel._height_slider.valueChanged.connect(panel._on_height_value)
    height_box.layout().addWidget(panel._height_slider)
    lay.addWidget(height_box)

    # 预设按钮
    preset_box = panel._make_section("预设")
    preset_grid = QGridLayout()
    preset_grid.setSpacing(4)
    presets = [
        ("海底", 40), ("海平面", 95), ("平地", 120),
        ("丘陵", 160), ("山地", 220),
    ]
    for i, (name, val) in enumerate(presets):
        btn = QPushButton(f"{name}({val})")
        btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        btn.clicked.connect(lambda _, v=val: panel._apply_height_preset(v))
        preset_grid.addWidget(btn, i // 3, i % 3)
    preset_box.layout().addLayout(preset_grid)
    lay.addWidget(preset_box)

    # 操作按钮
    auto_btn = QPushButton("从地形自动生成")
    auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    auto_btn.clicked.connect(panel.auto_height_requested.emit)
    lay.addWidget(auto_btn)

    smooth_btn = QPushButton("平滑")
    smooth_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
    smooth_btn.clicked.connect(panel.smooth_height_requested.emit)
    lay.addWidget(smooth_btn)

    lay.addStretch()
    return page
