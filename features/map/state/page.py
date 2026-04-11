"""state feature 页面 (从 tool_panel 提取).

原始代码是 ToolPanel._build_state_page, 为了按 feature 组织
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
    """构建 state 页. panel 是 ToolPanel 实例."""
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    # 自动分组按钮
    auto_btn = QPushButton("自动分组")
    auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    auto_btn.clicked.connect(panel._on_auto_states)
    lay.addWidget(auto_btn)

    # 每State省份数
    spin_row = QHBoxLayout()
    spin_lbl = QLabel("每State省份数:")
    spin_lbl.setStyleSheet(_LABEL_STYLE)
    spin_row.addWidget(spin_lbl)
    panel._state_per_spin = QSpinBox()
    panel._state_per_spin.setRange(5, 30)
    panel._state_per_spin.setValue(15)
    panel._state_per_spin.setStyleSheet(_SPINBOX_STYLE)
    spin_row.addWidget(panel._state_per_spin)
    lay.addLayout(spin_row)

    # State 列表
    list_box = panel._make_section("State 列表")
    panel._state_list = QListWidget()
    panel._state_list.setStyleSheet(_LIST_STYLE)
    panel._state_list.setMaximumHeight(200)
    panel._state_list.currentRowChanged.connect(panel._on_state_list_clicked)
    list_box.layout().addWidget(panel._state_list)
    lay.addWidget(list_box)

    # State 属性面板
    info_box = panel._make_section("State 属性")
    il = info_box.layout()

    # 名称
    name_row = QHBoxLayout()
    name_lbl = QLabel("名称:")
    name_lbl.setStyleSheet(_LABEL_STYLE)
    name_row.addWidget(name_lbl)
    panel._state_name_edit = QLineEdit()
    panel._state_name_edit.setStyleSheet(_LINEEDIT_STYLE)
    panel._state_name_edit.editingFinished.connect(panel._on_state_name_changed)
    name_row.addWidget(panel._state_name_edit)
    il.addLayout(name_row)

    # 人口
    mp_row = QHBoxLayout()
    mp_lbl = QLabel("人口:")
    mp_lbl.setStyleSheet(_LABEL_STYLE)
    mp_row.addWidget(mp_lbl)
    panel._state_manpower_spin = QSpinBox()
    panel._state_manpower_spin.setRange(0, 100000000)
    panel._state_manpower_spin.setSingleStep(10000)
    panel._state_manpower_spin.setStyleSheet(_SPINBOX_STYLE)
    panel._state_manpower_spin.valueChanged.connect(panel._on_state_manpower_changed)
    mp_row.addWidget(panel._state_manpower_spin)
    il.addLayout(mp_row)

    # 类别
    cat_row = QHBoxLayout()
    cat_lbl = QLabel("类别:")
    cat_lbl.setStyleSheet(_LABEL_STYLE)
    cat_row.addWidget(cat_lbl)
    panel._state_category_combo = QComboBox()
    panel._state_category_combo.setStyleSheet(_COMBOBOX_STYLE)
    panel._state_category_combo.addItems(StateManager.CATEGORIES)
    panel._state_category_combo.currentTextChanged.connect(panel._on_state_category_changed)
    cat_row.addWidget(panel._state_category_combo)
    il.addLayout(cat_row)

    lay.addWidget(info_box)

    # 详情按钮 (资源/建筑/核心/宣称)
    detail_btn = QPushButton("详情... (资源/建筑/核心/宣称)")
    detail_btn.clicked.connect(panel._on_state_detail_clicked)
    lay.addWidget(detail_btn)

    # 提示
    hint = QLabel("选中State后点击省份可移入。双击State打开详情编辑资源/建筑/VP")
    hint.setStyleSheet(f"color: {_DIM}; font-size: 11px; padding: 8px;")
    hint.setWordWrap(True)
    lay.addWidget(hint)

    lay.addStretch()
    return page
