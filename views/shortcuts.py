"""
可配置快捷键管理器 — 支持持久化到 QSettings。
"""
from __future__ import annotations

from typing import Callable

from PyQt5.QtWidgets import (
    QShortcut, QWidget, QDialog, QVBoxLayout,
    QTableWidget, QTableWidgetItem, QDialogButtonBox,
    QHeaderView, QKeySequenceEdit, QAbstractItemView,
)
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QKeySequence


# ── 默认快捷键映射 ──
_DEFAULTS: dict[str, str] = {
    "undo": "Ctrl+Z",
    "redo": "Ctrl+Y",
    "save": "Ctrl+S",
    "open": "Ctrl+O",
    "new": "Ctrl+N",
    "export": "Ctrl+E",
    "mode_land": "1",
    "mode_province": "2",
    "mode_terrain": "3",
    "mode_height": "4",
    "mode_river": "5",
    "mode_state": "6",
    "mode_country": "7",
    "mode_continent": "8",
    "tool_brush": "B",
    "tool_eraser": "E",
    "tool_fill": "F",
    "tool_transform": "T",
    "tool_pan": "P",
    "delete": "Delete",
    "zoom_fit": "Ctrl+0",
}

# 显示用中文名
_LABELS: dict[str, str] = {
    "undo": "撤销",
    "redo": "重做",
    "save": "保存项目",
    "open": "打开项目",
    "new": "新建项目",
    "export": "导出MOD",
    "mode_land": "大陆模式",
    "mode_province": "省份模式",
    "mode_terrain": "地形模式",
    "mode_height": "高度模式",
    "mode_river": "河流模式",
    "mode_state": "State模式",
    "mode_country": "国家模式",
    "mode_continent": "大洲模式",
    "tool_brush": "画笔工具",
    "tool_eraser": "橡皮擦",
    "tool_fill": "填充工具",
    "tool_transform": "变换工具",
    "tool_pan": "平移工具",
    "delete": "删除",
    "zoom_fit": "适应窗口",
}


class ShortcutManager:
    """可配置快捷键管理器。"""

    DEFAULTS = _DEFAULTS

    def __init__(self) -> None:
        self._bindings: dict[str, str] = dict(_DEFAULTS)
        self._callbacks: dict[str, Callable] = {}
        self._shortcuts: list[QShortcut] = []
        self._load_from_settings()

    def register(self, name: str, callback: Callable) -> None:
        """注册一个动作回调。"""
        self._callbacks[name] = callback

    def rebind(self, name: str, key: str) -> None:
        """修改快捷键绑定。"""
        self._bindings[name] = key
        self._save_to_settings()

    def get_binding(self, name: str) -> str:
        """获取当前绑定的按键。"""
        return self._bindings.get(name, "")

    def get_all_bindings(self) -> dict[str, str]:
        """返回所有绑定（副本）。"""
        return dict(self._bindings)

    def apply_to_window(self, window: QWidget) -> None:
        """将所有快捷键绑定到窗口上。先清除旧的。"""
        for sc in self._shortcuts:
            sc.setEnabled(False)
            sc.deleteLater()
        self._shortcuts.clear()

        for name, key in self._bindings.items():
            cb = self._callbacks.get(name)
            if cb is None or not key:
                continue
            shortcut = QShortcut(QKeySequence(key), window)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(cb)
            self._shortcuts.append(shortcut)

    def _load_from_settings(self) -> None:
        settings = QSettings("HOI4MapMaker", "Shortcuts")
        for name in _DEFAULTS:
            val = settings.value(f"shortcut/{name}")
            if val:
                self._bindings[name] = val

    def _save_to_settings(self) -> None:
        settings = QSettings("HOI4MapMaker", "Shortcuts")
        for name, key in self._bindings.items():
            settings.setValue(f"shortcut/{name}", key)


def show_shortcut_dialog(parent: QWidget, shortcut_mgr: ShortcutManager) -> None:
    """弹出快捷键设置对话框，允许编辑并保存。"""
    dlg = QDialog(parent)
    dlg.setWindowTitle("快捷键设置")
    dlg.resize(480, 520)

    layout = QVBoxLayout(dlg)

    table = QTableWidget()
    table.setColumnCount(3)
    table.setHorizontalHeaderLabels(["功能", "当前快捷键", "新快捷键"])
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.verticalHeader().setVisible(False)

    bindings = shortcut_mgr.get_all_bindings()
    names = list(bindings.keys())
    table.setRowCount(len(names))

    editors: list[tuple[str, QKeySequenceEdit]] = []

    for row, name in enumerate(names):
        # 功能名
        label_text = _LABELS.get(name, name)
        label_item = QTableWidgetItem(label_text)
        label_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        table.setItem(row, 0, label_item)

        # 当前按键
        key_item = QTableWidgetItem(bindings[name])
        key_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        table.setItem(row, 1, key_item)

        # 编辑器
        editor = QKeySequenceEdit()
        editor.setKeySequence(QKeySequence(bindings[name]))
        table.setCellWidget(row, 2, editor)
        editors.append((name, editor))

    layout.addWidget(table)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok
        | QDialogButtonBox.StandardButton.Cancel
        | QDialogButtonBox.StandardButton.RestoreDefaults
    )
    layout.addWidget(buttons)

    def _restore_defaults() -> None:
        for row_idx, (nm, ed) in enumerate(editors):
            default_key = _DEFAULTS.get(nm, "")
            ed.setKeySequence(QKeySequence(default_key))
            table.item(row_idx, 1).setText(default_key)

    buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
        _restore_defaults
    )
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)

    if dlg.exec_() == QDialog.DialogCode.Accepted:
        for name, editor in editors:
            new_key = editor.keySequence().toString()
            shortcut_mgr.rebind(name, new_key)
        # 重新应用到窗口
        shortcut_mgr.apply_to_window(parent)
