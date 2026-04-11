"""
大陆编辑器对话框 — 增删改大陆名, 并把省份指派到选定大陆.

用法: 打开对话框 → 选中一个大陆 → 进入"拾取模式" → 在主画布点击省份
(主窗口拦截点击事件并调用 continent_mgr.assign_province)
"""

from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QInputDialog, QMessageBox,
)


class ContinentDialog(QDialog):
    """非模态, 允许用户一边看画布一边点省份指派大陆."""

    # 用户进入/退出拾取模式; 主窗口用来切换画布点击行为
    pick_mode_changed = pyqtSignal(bool, int)  # (开/关, 大陆索引 0-based)

    def __init__(self, continent_mgr, parent=None):
        super().__init__(parent)
        self._mgr = continent_mgr
        self._pick_on = False
        self.setWindowTitle("大陆编辑器")
        self.setMinimumSize(340, 420)
        # 非模态: 不阻塞主窗口点击
        self.setWindowFlags(self.windowFlags() | Qt.Tool)

        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        tip = QLabel(
            "用法：\n"
            "1. 添加大陆（每个 MOD 至少 1 个）\n"
            "2. 选中大陆后点『开始指派』\n"
            "3. 在主画布点击陆地省份 → 该省份归入该大陆\n"
            "4. 再次点击按钮结束指派"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #888; font-size: 11px;")
        lay.addWidget(tip)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_rename)
        lay.addWidget(self._list, 1)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self._on_add)
        rename_btn = QPushButton("重命名")
        rename_btn.clicked.connect(self._on_rename)
        remove_btn = QPushButton("删除")
        remove_btn.clicked.connect(self._on_remove)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(rename_btn)
        btn_row.addWidget(remove_btn)
        lay.addLayout(btn_row)

        self._pick_btn = QPushButton("开始指派省份")
        self._pick_btn.setCheckable(True)
        self._pick_btn.toggled.connect(self._on_pick_toggled)
        lay.addWidget(self._pick_btn)

        self._status = QLabel("")
        self._status.setStyleSheet("color: #4a9; font-size: 11px;")
        lay.addWidget(self._status)

    def _refresh_list(self) -> None:
        self._list.clear()
        for i, name in enumerate(self._mgr.names):
            count = sum(
                1 for ci in self._mgr._province_continent.values() if ci == i
            )
            item = QListWidgetItem(f"{i + 1}. {name}  ({count} 省)")
            item.setData(Qt.UserRole, i)
            self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def current_index(self) -> int:
        """返回当前选中的大陆索引 (0-based), 无选中返回 -1."""
        item = self._list.currentItem()
        if item is None:
            return -1
        return int(item.data(Qt.UserRole))

    # ─────────── 大陆 CRUD ───────────

    def _on_add(self) -> None:
        name, ok = QInputDialog.getText(self, "添加大陆", "大陆名 (英文, 不含空格):")
        if not ok or not name.strip():
            return
        try:
            self._mgr.add_continent(name.strip())
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
            return
        self._refresh_list()

    def _on_rename(self) -> None:
        idx = self.current_index()
        if idx < 0:
            return
        old = self._mgr.get_name(idx)
        name, ok = QInputDialog.getText(
            self, "重命名大陆", "新名字:", text=old
        )
        if not ok or not name.strip():
            return
        try:
            self._mgr.rename_continent(idx, name.strip())
        except (ValueError, IndexError) as e:
            QMessageBox.warning(self, "错误", str(e))
            return
        self._refresh_list()

    def _on_remove(self) -> None:
        idx = self.current_index()
        if idx < 0:
            return
        if self._mgr.count() <= 1:
            QMessageBox.warning(self, "错误", "必须至少保留 1 个大陆")
            return
        name = self._mgr.get_name(idx)
        ret = QMessageBox.question(
            self, "删除大陆",
            f"删除「{name}」? 指向它的省份会改回首个大陆.",
        )
        if ret != QMessageBox.Yes:
            return
        try:
            self._mgr.remove_continent(idx)
        except (ValueError, IndexError) as e:
            QMessageBox.warning(self, "错误", str(e))
            return
        self._refresh_list()

    # ─────────── 拾取模式 ───────────

    def _on_pick_toggled(self, on: bool) -> None:
        idx = self.current_index()
        if on and idx < 0:
            self._pick_btn.setChecked(False)
            QMessageBox.warning(self, "错误", "请先选中一个大陆")
            return
        self._pick_on = on
        if on:
            self._pick_btn.setText("停止指派")
            name = self._mgr.get_name(idx)
            self._status.setText(f"正在指派到：{name} — 点击主画布省份")
        else:
            self._pick_btn.setText("开始指派省份")
            self._status.setText("")
        self.pick_mode_changed.emit(on, idx)

    def notify_assigned(self, pid: int) -> None:
        """主窗口指派一个省份后回调, 刷新省数显示."""
        self._refresh_list()
        idx = self.current_index()
        if 0 <= idx:
            name = self._mgr.get_name(idx)
            self._status.setText(f"已指派省份 {pid} → {name}")

    def closeEvent(self, event) -> None:
        # 关闭时自动退出拾取模式
        if self._pick_on:
            self.pick_mode_changed.emit(False, -1)
            self._pick_on = False
        super().closeEvent(event)
