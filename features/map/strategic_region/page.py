"""
战略区域 page — 侧边栏内联版 (从 dialog.py 迁移).

功能: region 列表 + 自动生成 + 编辑 (名字/weather/naval_terrain) + 拾取省份.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QComboBox, QScrollArea,
)

from domain.managers.strategic_region import PRESET_LABELS

from ui.styles import (
    _DIM_LABEL_STYLE, _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
    _LABEL_STYLE, _LIST_STYLE, _COMBOBOX_STYLE, _LINEEDIT_STYLE,
)


def build_page(panel) -> QWidget:
    outer = QWidget()
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; }")

    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)

    tip = QLabel("战略区域: 省份分组 + 天气 + 海军地形.\n"
                 "建议先点'自动生成'按 State 创建初始分组，\n"
                 "再手动调整。每个区域可设天气和海军地形类型.\n"
                 "用拾取模式点省份可移入选中的区域.")
    tip.setWordWrap(True)
    tip.setStyleSheet(_DIM_LABEL_STYLE)
    lay.addWidget(tip)

    auto_btn = QPushButton("自动生成 (按 State 分组)")
    auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    auto_btn.clicked.connect(lambda: panel.strategic_region_auto_requested.emit())
    lay.addWidget(auto_btn)

    # Region 列表
    panel._sr_list = QListWidget()
    panel._sr_list.setStyleSheet(_LIST_STYLE)
    panel._sr_list.setMaximumHeight(150)
    panel._sr_list.currentRowChanged.connect(
        lambda row: panel.strategic_region_selected.emit(row)
    )
    lay.addWidget(panel._sr_list)

    btn_row = QHBoxLayout()
    new_btn = QPushButton("新建")
    new_btn.clicked.connect(lambda: panel.strategic_region_new_requested.emit())
    del_btn = QPushButton("删除")
    del_btn.clicked.connect(lambda: panel.strategic_region_delete_requested.emit())
    btn_row.addWidget(new_btn)
    btn_row.addWidget(del_btn)
    lay.addLayout(btn_row)

    # 编辑字段
    name_row = QHBoxLayout()
    name_row.addWidget(QLabel("名字:"))
    panel._sr_name_edit = QLineEdit()
    panel._sr_name_edit.setStyleSheet(_LINEEDIT_STYLE)
    panel._sr_name_edit.editingFinished.connect(
        lambda: panel.strategic_region_name_changed.emit(panel._sr_name_edit.text())
    )
    name_row.addWidget(panel._sr_name_edit)
    lay.addLayout(name_row)

    weather_row = QHBoxLayout()
    weather_row.addWidget(QLabel("天气:"))
    panel._sr_weather_combo = QComboBox()
    panel._sr_weather_combo.setStyleSheet(_COMBOBOX_STYLE)
    for key, label in PRESET_LABELS.items():
        panel._sr_weather_combo.addItem(label, key)
    panel._sr_weather_combo.currentIndexChanged.connect(
        lambda idx: panel.strategic_region_weather_changed.emit(
            panel._sr_weather_combo.currentData() or "temperate"
        )
    )
    weather_row.addWidget(panel._sr_weather_combo)
    lay.addLayout(weather_row)

    naval_row = QHBoxLayout()
    naval_row.addWidget(QLabel("Naval:"))
    panel._sr_naval_combo = QComboBox()
    panel._sr_naval_combo.setStyleSheet(_COMBOBOX_STYLE)
    panel._sr_naval_combo.addItem("(无)", "")
    for nt in ("ocean", "deep_ocean", "shallow_sea"):
        panel._sr_naval_combo.addItem(nt, nt)
    panel._sr_naval_combo.currentIndexChanged.connect(
        lambda idx: panel.strategic_region_naval_changed.emit(
            panel._sr_naval_combo.currentData() or ""
        )
    )
    naval_row.addWidget(panel._sr_naval_combo)
    lay.addLayout(naval_row)

    panel._sr_prov_count = QLabel("省份: 0")
    panel._sr_prov_count.setStyleSheet(_DIM_LABEL_STYLE)
    lay.addWidget(panel._sr_prov_count)

    panel._sr_pick_btn = QPushButton("开始拾取省份")
    panel._sr_pick_btn.setCheckable(True)
    panel._sr_pick_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    panel._sr_pick_btn.toggled.connect(
        lambda on: panel.strategic_region_pick_toggled.emit(on)
    )
    lay.addWidget(panel._sr_pick_btn)

    lay.addStretch(1)
    scroll.setWidget(page)

    root = QVBoxLayout(outer)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(scroll)
    return outer
