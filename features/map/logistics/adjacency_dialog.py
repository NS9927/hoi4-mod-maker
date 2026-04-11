"""
相邻关系 (adjacency) 编辑器对话框.

非模态, 用户流程:
1. 打开对话框 → 列表显示已有 adjacency
2. 点"新建" 填起点/终点/类型
3. 点"拾取起点省份" → 进入 pick 模式, 主窗拦截画布点击填入省份 ID
4. 再点"拾取终点省份" → 第二次拦截
5. 点"保存" 加入列表

主窗口用 `pick_mode_changed` 信号切换画布拦截, 用 `province_picked` 回调填字段.
"""

from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QComboBox, QMessageBox,
    QGroupBox, QFormLayout,
)

from domain.managers.adjacency import AdjacencyManager, AdjacencyEntry


class AdjacencyDialog(QDialog):
    """相邻关系编辑器.

    pick_mode_changed 信号参数: (开关, 目标字段名) — 字段名 'from' / 'to' / 'through'
    主窗口收到 True 时开始拦截画布点击, 下次 click 调 receive_picked_province.
    """

    pick_mode_changed = pyqtSignal(bool, str)

    def __init__(self, adjacency_mgr: AdjacencyManager, parent=None) -> None:
        super().__init__(parent)
        self._mgr = adjacency_mgr
        self._pick_target: str | None = None  # 'from' / 'to' / 'through'
        self.setWindowTitle("相邻关系编辑器")
        self.setMinimumSize(400, 520)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)

        self._build_ui()
        self._refresh_list()

    # ─────────── UI ───────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        tip = QLabel(
            "海峡 (sea): 跨海连接两个省 (必须指定 through 海省)\n"
            "不可通行 (impassable): 阻塞两省的直接相邻\n"
            "使用流程: 填字段 → 拾取省份 → 保存"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(tip)

        # 列表
        self._list = QListWidget()
        self._list.setMaximumHeight(150)
        self._list.itemClicked.connect(self._on_item_clicked)
        root.addWidget(self._list)

        del_btn = QPushButton("删除选中")
        del_btn.clicked.connect(self._on_delete)
        root.addWidget(del_btn)

        # 编辑区
        edit_box = QGroupBox("新建 / 编辑")
        form = QFormLayout(edit_box)
        form.setSpacing(6)

        # 起点
        from_row = QHBoxLayout()
        self._from_edit = QLineEdit()
        self._from_edit.setPlaceholderText("省份 ID")
        from_row.addWidget(self._from_edit)
        from_pick = QPushButton("从画布拾取")
        from_pick.clicked.connect(lambda: self._start_pick("from"))
        from_row.addWidget(from_pick)
        form.addRow("起点省份:", from_row)

        # 终点
        to_row = QHBoxLayout()
        self._to_edit = QLineEdit()
        self._to_edit.setPlaceholderText("省份 ID")
        to_row.addWidget(self._to_edit)
        to_pick = QPushButton("从画布拾取")
        to_pick.clicked.connect(lambda: self._start_pick("to"))
        to_row.addWidget(to_pick)
        form.addRow("终点省份:", to_row)

        # 类型
        self._type_combo = QComboBox()
        self._type_combo.addItem("海峡/运河 (sea)", "sea")
        self._type_combo.addItem("不可通行 (impassable)", "impassable")
        form.addRow("类型:", self._type_combo)

        # through (仅 sea)
        through_row = QHBoxLayout()
        self._through_edit = QLineEdit()
        self._through_edit.setPlaceholderText("途经海省 ID (sea 类型)")
        through_row.addWidget(self._through_edit)
        through_pick = QPushButton("从画布拾取")
        through_pick.clicked.connect(lambda: self._start_pick("through"))
        through_row.addWidget(through_pick)
        form.addRow("途经省份:", through_row)

        # comment
        self._comment_edit = QLineEdit()
        self._comment_edit.setPlaceholderText("备注 (可选)")
        form.addRow("备注:", self._comment_edit)

        root.addWidget(edit_box)

        # 状态 + 保存/清空
        self._status = QLabel("")
        self._status.setStyleSheet("color: #4a9; font-size: 11px;")
        root.addWidget(self._status)

        btn_row = QHBoxLayout()
        clear_btn = QPushButton("清空字段")
        clear_btn.clicked.connect(self._clear_form)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch(1)
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    # ─────────── 列表 ───────────

    def _refresh_list(self) -> None:
        self._list.clear()
        for e in self._mgr.get_all():
            label = f"[{e.type}] {e.from_id} → {e.to_id}"
            if e.through_id >= 0:
                label += f" (via {e.through_id})"
            if e.comment:
                label += f"  # {e.comment}"
            item = QListWidgetItem(label)
            self._list.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """点列表项 → 回填到编辑区方便修改."""
        row = self._list.row(item)
        entries = self._mgr.get_all()
        if 0 <= row < len(entries):
            e = entries[row]
            self._from_edit.setText(str(e.from_id))
            self._to_edit.setText(str(e.to_id))
            self._through_edit.setText(str(e.through_id) if e.through_id >= 0 else "")
            idx = self._type_combo.findData(e.type)
            if idx >= 0:
                self._type_combo.setCurrentIndex(idx)
            self._comment_edit.setText(e.comment)

    def _on_delete(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        entries = self._mgr.get_all()
        if 0 <= row < len(entries):
            e = entries[row]
            self._mgr.remove(e.from_id, e.to_id, e.type)
            self._refresh_list()

    # ─────────── 表单 ───────────

    def _clear_form(self) -> None:
        self._from_edit.clear()
        self._to_edit.clear()
        self._through_edit.clear()
        self._comment_edit.clear()
        self._type_combo.setCurrentIndex(0)

    def _on_save(self) -> None:
        try:
            from_id = int(self._from_edit.text().strip())
            to_id = int(self._to_edit.text().strip())
        except ValueError:
            QMessageBox.warning(self, "错误", "起点/终点必须是整数省份 ID")
            return
        t = self._type_combo.currentData()
        through_text = self._through_edit.text().strip()
        through_id = int(through_text) if through_text else -1

        entry = AdjacencyEntry(
            from_id=from_id,
            to_id=to_id,
            type=t,
            through_id=through_id if t == "sea" else -1,
            comment=self._comment_edit.text().strip(),
        )
        self._mgr.add(entry)
        self._refresh_list()
        self._status.setText(f"已保存: {from_id} → {to_id} ({t})")

    # ─────────── 拾取模式 ───────────

    def _start_pick(self, target: str) -> None:
        """target ∈ {'from','to','through'}"""
        self._pick_target = target
        self._status.setText(f"拾取模式: 点击主画布省份填入 {target}")
        self.pick_mode_changed.emit(True, target)

    def receive_picked_province(self, pid: int) -> None:
        """主窗口拦截到画布点击后回调此方法."""
        if self._pick_target == "from":
            self._from_edit.setText(str(pid))
        elif self._pick_target == "to":
            self._to_edit.setText(str(pid))
        elif self._pick_target == "through":
            self._through_edit.setText(str(pid))
        self._status.setText(f"已填入 {self._pick_target} = {pid}")
        self._pick_target = None
        self.pick_mode_changed.emit(False, "")

    def closeEvent(self, event) -> None:
        if self._pick_target is not None:
            self.pick_mode_changed.emit(False, "")
            self._pick_target = None
        super().closeEvent(event)
