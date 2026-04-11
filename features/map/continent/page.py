"""
大陆分区 page — 侧边栏内联版 (从 dialog.py 迁移).

功能: 大陆列表 CRUD + 拾取省份指派.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QInputDialog, QMessageBox, QScrollArea,
)

from ui.styles import (
    _DIM_LABEL_STYLE, _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
    _SECTION_STYLE, _LABEL_STYLE, _LIST_STYLE,
)


def build_page(panel) -> QWidget:
    """构建大陆分区页. panel 是 ToolPanel 实例."""
    outer = QWidget()
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; }")

    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    tip = QLabel("定义大陆 + 把省份指派到大陆.\nHOI4 的 continent.txt 和 definition.csv 用.")
    tip.setWordWrap(True)
    tip.setStyleSheet(_DIM_LABEL_STYLE)
    lay.addWidget(tip)

    # 大陆列表
    panel._continent_list = QListWidget()
    panel._continent_list.setStyleSheet(_LIST_STYLE)
    panel._continent_list.setMaximumHeight(150)
    lay.addWidget(panel._continent_list)

    btn_row = QHBoxLayout()
    add_btn = QPushButton("添加")
    add_btn.clicked.connect(lambda: _on_add_continent(panel))
    rename_btn = QPushButton("重命名")
    rename_btn.clicked.connect(lambda: _on_rename_continent(panel))
    remove_btn = QPushButton("删除")
    remove_btn.clicked.connect(lambda: _on_remove_continent(panel))
    btn_row.addWidget(add_btn)
    btn_row.addWidget(rename_btn)
    btn_row.addWidget(remove_btn)
    lay.addLayout(btn_row)

    # 拾取按钮
    panel._continent_pick_btn = QPushButton("开始指派省份")
    panel._continent_pick_btn.setCheckable(True)
    panel._continent_pick_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    panel._continent_pick_btn.toggled.connect(
        lambda on: panel.continent_pick_toggled.emit(on)
    )
    lay.addWidget(panel._continent_pick_btn)

    panel._continent_status = QLabel("")
    panel._continent_status.setStyleSheet("color: #6c6cf0; font-size: 11px;")
    lay.addWidget(panel._continent_status)

    lay.addStretch(1)
    scroll.setWidget(page)

    root = QVBoxLayout(outer)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(scroll)
    return outer


def _on_add_continent(panel):
    from PyQt5.QtWidgets import QInputDialog
    name, ok = QInputDialog.getText(panel, "添加大陆", "大陆名 (英文):")
    if ok and name.strip():
        panel.continent_add_requested.emit(name.strip())

def _on_rename_continent(panel):
    from PyQt5.QtWidgets import QInputDialog
    item = panel._continent_list.currentItem()
    if item is None:
        return
    old = item.text().split(".")[1].strip().split("(")[0].strip() if "." in item.text() else ""
    name, ok = QInputDialog.getText(panel, "重命名", "新名字:", text=old)
    if ok and name.strip():
        row = panel._continent_list.currentRow()
        panel.continent_rename_requested.emit(row, name.strip())

def _on_remove_continent(panel):
    row = panel._continent_list.currentRow()
    if row >= 0:
        panel.continent_remove_requested.emit(row)
