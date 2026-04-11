"""
地图配置 (default.map) 对话框.

可编辑字段:
- 树木调色板索引 (trees.bmp 哪些 palette ID 算树)
- 河流最大宽度等级
- (省份数自动)
"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton,
    QFormLayout, QListWidget, QListWidgetItem, QInputDialog, QMessageBox,
)

from domain.managers.default_map_settings import DefaultMapSettings


class DefaultMapDialog(QDialog):
    """地图配置编辑器."""

    def __init__(
        self,
        settings: DefaultMapSettings,
        province_count: int = 0,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._province_count = province_count
        self.setWindowTitle("地图配置 (default.map)")
        self.setMinimumSize(380, 420)

        self._build_ui()
        self._refresh_tree_list()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        tip = QLabel(
            "default.map 是 HOI4 引擎的地图加载配置.\n"
            "大部分字段是文件名 (vanilla 标准, 不可改).\n"
            "可调的是树木调色板索引和河流上限."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(tip)

        form = QFormLayout()
        form.setSpacing(8)

        # 省份数 (只读)
        prov_lbl = QLabel(f"{self._province_count} (自动)")
        form.addRow("总省份数:", prov_lbl)

        # 河流最大等级
        self._river_max = QSpinBox()
        self._river_max.setRange(1, 10)
        self._river_max.setValue(self._settings.river_max_level)
        form.addRow("河流最大等级:", self._river_max)

        root.addLayout(form)

        # 树木调色板索引 (列表 + 增删)
        tree_lbl = QLabel("<b>树木调色板索引</b> (trees.bmp 这些 palette ID 算树):")
        tree_lbl.setStyleSheet("color: #ccc;")
        root.addWidget(tree_lbl)

        self._tree_list = QListWidget()
        self._tree_list.setMaximumHeight(140)
        root.addWidget(self._tree_list)

        tree_btn_row = QHBoxLayout()
        add_btn = QPushButton("添加索引")
        add_btn.clicked.connect(self._on_add_tree_index)
        del_btn = QPushButton("删除选中")
        del_btn.clicked.connect(self._on_del_tree_index)
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._on_reset_tree_indices)
        tree_btn_row.addWidget(add_btn)
        tree_btn_row.addWidget(del_btn)
        tree_btn_row.addWidget(reset_btn)
        tree_btn_row.addStretch(1)
        root.addLayout(tree_btn_row)

        root.addStretch(1)

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        ok_btn = QPushButton("保存")
        ok_btn.clicked.connect(self._on_accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    def _refresh_tree_list(self) -> None:
        self._tree_list.clear()
        for idx in self._settings.tree_palette_indices:
            self._tree_list.addItem(QListWidgetItem(str(idx)))

    def _on_add_tree_index(self) -> None:
        v, ok = QInputDialog.getInt(
            self, "添加索引", "Palette 索引 (1-13):",
            value=4, min=1, max=13,
        )
        if ok and v not in self._settings.tree_palette_indices:
            self._settings.tree_palette_indices.append(v)
            self._settings.tree_palette_indices.sort()
            self._refresh_tree_list()

    def _on_del_tree_index(self) -> None:
        row = self._tree_list.currentRow()
        if 0 <= row < len(self._settings.tree_palette_indices):
            self._settings.tree_palette_indices.pop(row)
            self._refresh_tree_list()

    def _on_reset_tree_indices(self) -> None:
        self._settings.tree_palette_indices = [3, 4, 7, 10]
        self._refresh_tree_list()

    def _on_accept(self) -> None:
        self._settings.river_max_level = int(self._river_max.value())
        self.accept()
