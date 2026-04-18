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

from ui.i18n import tr


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

# 显示用名称 (tr key)
_LABELS: dict[str, str] = {
    "undo": "shortcut_undo",
    "redo": "shortcut_redo",
    "save": "shortcut_save",
    "open": "shortcut_open",
    "new": "shortcut_new",
    "export": "shortcut_export",
    "mode_land": "shortcut_mode_land",
    "mode_province": "shortcut_mode_province",
    "mode_terrain": "shortcut_mode_terrain",
    "mode_height": "shortcut_mode_height",
    "mode_river": "shortcut_mode_river",
    "mode_state": "shortcut_mode_state",
    "mode_country": "shortcut_mode_country",
    "mode_continent": "shortcut_mode_continent",
    "tool_brush": "shortcut_tool_brush",
    "tool_eraser": "shortcut_tool_eraser",
    "tool_fill": "shortcut_tool_fill",
    "tool_transform": "shortcut_tool_transform",
    "tool_pan": "shortcut_tool_pan",
    "delete": "shortcut_delete",
    "zoom_fit": "shortcut_zoom_fit",
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
    dlg.setWindowTitle(tr("shortcut_dlg_title"))
    dlg.resize(480, 520)

    layout = QVBoxLayout(dlg)

    table = QTableWidget()
    table.setColumnCount(3)
    table.setHorizontalHeaderLabels([tr("shortcut_col_function"), tr("shortcut_col_current"), tr("shortcut_col_new")])
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
        label_text = tr(_LABELS.get(name, name))
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
