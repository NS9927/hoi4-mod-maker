"""
地图配置 (default.map) page — 侧边栏内联版 (从 dialog.py 迁移).

可编辑: 树木调色板索引 / 河流最大等级.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QListWidget, QListWidgetItem, QInputDialog, QScrollArea,
)

from ui.styles import (
    _DIM_LABEL_STYLE, _LABEL_STYLE, _SPINBOX_STYLE, _LIST_STYLE,
    _SECONDARY_BTN_STYLE,
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

    tip = QLabel("HOI4 引擎 default.map 配置.\n修改后下次导出生效.")
    tip.setWordWrap(True)
    tip.setStyleSheet(_DIM_LABEL_STYLE)
    lay.addWidget(tip)

    # 河流最大等级
    river_row = QHBoxLayout()
    river_row.addWidget(QLabel("河流最大等级:"))
    panel._dm_river_max = QSpinBox()
    panel._dm_river_max.setRange(1, 10)
    panel._dm_river_max.setValue(5)
    panel._dm_river_max.setStyleSheet(_SPINBOX_STYLE)
    panel._dm_river_max.valueChanged.connect(
        lambda v: panel.default_map_river_changed.emit(v)
    )
    river_row.addWidget(panel._dm_river_max)
    lay.addLayout(river_row)

    # 树木调色板
    lay.addWidget(QLabel("树木调色板索引:"))
    panel._dm_tree_list = QListWidget()
    panel._dm_tree_list.setStyleSheet(_LIST_STYLE)
    panel._dm_tree_list.setMaximumHeight(100)
    lay.addWidget(panel._dm_tree_list)

    btn_row = QHBoxLayout()
    add_btn = QPushButton("添加")
    add_btn.clicked.connect(lambda: panel.default_map_tree_add_requested.emit())
    del_btn = QPushButton("删除")
    del_btn.clicked.connect(lambda: panel.default_map_tree_del_requested.emit())
    reset_btn = QPushButton("恢复默认")
    reset_btn.clicked.connect(lambda: panel.default_map_tree_reset_requested.emit())
    btn_row.addWidget(add_btn)
    btn_row.addWidget(del_btn)
    btn_row.addWidget(reset_btn)
    lay.addLayout(btn_row)

    lay.addStretch(1)
    scroll.setWidget(page)

    root = QVBoxLayout(outer)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(scroll)
    return outer
