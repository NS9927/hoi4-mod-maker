"""地图配置 (default.map) page — 独立 QWidget, 不依赖 ToolPanel.

可编辑: 树木调色板索引 / 河流最大等级.
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QListWidget, QScrollArea,
)

from ui.i18n import tr
from ui.styles import (
    _DIM_LABEL_STYLE, _SPINBOX_STYLE, _LIST_STYLE,
)


class DefaultMapPage(QWidget):
    """地图配置页面."""

    # 输出信号
    default_map_river_changed = pyqtSignal(int)
    default_map_tree_add_requested = pyqtSignal()
    default_map_tree_del_requested = pyqtSignal()
    default_map_tree_reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        tip = QLabel(tr("defmap_tip"))
        tip.setWordWrap(True)
        tip.setStyleSheet(_DIM_LABEL_STYLE)
        lay.addWidget(tip)

        # 河流最大等级
        river_row = QHBoxLayout()
        river_row.addWidget(QLabel(tr("defmap_river_max_label")))
        self._dm_river_max = QSpinBox()
        self._dm_river_max.setRange(1, 10)
        self._dm_river_max.setValue(5)
        self._dm_river_max.setStyleSheet(_SPINBOX_STYLE)
        self._dm_river_max.valueChanged.connect(
            lambda v: self.default_map_river_changed.emit(v)
        )
        river_row.addWidget(self._dm_river_max)
        lay.addLayout(river_row)

        # 树木调色板
        lay.addWidget(QLabel(tr("defmap_tree_palette_label")))
        self._dm_tree_list = QListWidget()
        self._dm_tree_list.setStyleSheet(_LIST_STYLE)
        self._dm_tree_list.setMaximumHeight(100)
        lay.addWidget(self._dm_tree_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton(tr("defmap_add_btn"))
        add_btn.clicked.connect(lambda: self.default_map_tree_add_requested.emit())
        del_btn = QPushButton(tr("defmap_delete_btn"))
        del_btn.clicked.connect(lambda: self.default_map_tree_del_requested.emit())
        reset_btn = QPushButton(tr("defmap_reset_btn"))
        reset_btn.clicked.connect(lambda: self.default_map_tree_reset_requested.emit())
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        btn_row.addWidget(reset_btn)
        lay.addLayout(btn_row)

        lay.addStretch(1)
        scroll.setWidget(page)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)
