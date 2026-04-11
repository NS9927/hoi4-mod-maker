"""
Adjacency Rules 编辑器对话框.

非模态. 左边列表展示已有 rule, 右边详情:
- name (输入)
- 4×4 表格 (contested/enemy/friend/neutral × army/navy/submarine/trade) checkbox
- required_provinces 列表 (从画布拾取或手填)
- icon_province (单个 sea 省份, 从画布拾取)

参考: features/map/logistics/adjacency_dialog.py 复用 pick_mode_changed 模式.
"""

from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QCheckBox,
    QGroupBox, QGridLayout, QFormLayout, QInputDialog, QMessageBox,
)

from domain.managers.adjacency_rule import (
    AdjacencyRuleManager, AdjacencyRule, ALL_PASS_TYPES, ALL_RELATIONS,
)


# 中文显示
_REL_LABELS = {
    "contested": "争夺中",
    "enemy": "敌国",
    "friend": "盟友",
    "neutral": "中立",
}
_PASS_LABELS = {
    "army": "陆军",
    "navy": "海军",
    "submarine": "潜艇",
    "trade": "贸易",
}


class AdjacencyRuleDialog(QDialog):
    """Adjacency rules 编辑器.

    pick_mode_changed: (开关, 字段名 'icon' / 'required_add')
    """

    pick_mode_changed = pyqtSignal(bool, str)

    def __init__(self, rule_mgr: AdjacencyRuleManager, parent=None) -> None:
        super().__init__(parent)
        self._mgr = rule_mgr
        self._current_rule: AdjacencyRule | None = None
        self._pick_target: str | None = None
        self.setWindowTitle("Adjacency Rules 编辑器")
        self.setMinimumSize(640, 540)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)

        self._build_ui()
        self._refresh_list()

    # ─────────── UI ───────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # ── 左: 列表 ──
        left = QVBoxLayout()
        left_label = QLabel("规则列表")
        left_label.setStyleSheet("color: #ccc; font-weight: bold;")
        left.addWidget(left_label)

        self._list = QListWidget()
        self._list.itemClicked.connect(self._on_select_rule)
        left.addWidget(self._list, 1)

        new_btn = QPushButton("新建...")
        new_btn.clicked.connect(self._on_new)
        left.addWidget(new_btn)
        del_btn = QPushButton("删除选中")
        del_btn.clicked.connect(self._on_delete)
        left.addWidget(del_btn)

        root.addLayout(left, 1)

        # ── 右: 详情 ──
        right = QVBoxLayout()

        tip = QLabel(
            "通行表: 4 种关系 × 4 种通行类型. 勾上=允许通过.\n"
            "required_provinces: 控制者必须同时控制这些省份才有效.\n"
            "icon: 海军视图里图标显示在哪个海省."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #888; font-size: 11px;")
        right.addWidget(tip)

        # name
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("名字:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("如 SUEZ_CANAL")
        self._name_edit.editingFinished.connect(self._on_name_changed)
        name_row.addWidget(self._name_edit)
        right.addLayout(name_row)

        # 通行表 (4×4 checkbox)
        table_box = QGroupBox("通行权限")
        grid = QGridLayout(table_box)
        grid.setSpacing(6)

        # 表头: 列 = 通行类型
        grid.addWidget(QLabel(""), 0, 0)
        for j, p in enumerate(ALL_PASS_TYPES):
            lbl = QLabel(f"<b>{_PASS_LABELS[p]}</b>")
            lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl, 0, j + 1)

        # 行 = 关系
        self._checks: dict[tuple[str, str], QCheckBox] = {}
        for i, rel in enumerate(ALL_RELATIONS):
            grid.addWidget(QLabel(_REL_LABELS[rel] + ":"), i + 1, 0)
            for j, p in enumerate(ALL_PASS_TYPES):
                cb = QCheckBox()
                cb.toggled.connect(
                    lambda checked, r=rel, pt=p: self._on_check_toggled(r, pt, checked)
                )
                grid.addWidget(cb, i + 1, j + 1, alignment=Qt.AlignCenter)
                self._checks[(rel, p)] = cb
        right.addWidget(table_box)

        # required_provinces
        req_box = QGroupBox("Required provinces (≥2)")
        req_lay = QVBoxLayout(req_box)
        self._req_list = QListWidget()
        self._req_list.setMaximumHeight(80)
        req_lay.addWidget(self._req_list)
        req_btns = QHBoxLayout()
        req_pick_btn = QPushButton("从画布拾取添加")
        req_pick_btn.clicked.connect(self._start_pick_required)
        req_btns.addWidget(req_pick_btn)
        req_input_btn = QPushButton("手填省份 ID")
        req_input_btn.clicked.connect(self._on_add_required_manually)
        req_btns.addWidget(req_input_btn)
        req_del_btn = QPushButton("删除选中")
        req_del_btn.clicked.connect(self._on_remove_required)
        req_btns.addWidget(req_del_btn)
        req_lay.addLayout(req_btns)
        right.addWidget(req_box)

        # icon
        icon_row = QHBoxLayout()
        icon_row.addWidget(QLabel("Icon 海省:"))
        self._icon_edit = QLineEdit()
        self._icon_edit.setPlaceholderText("省份 ID, -1 = 不设")
        self._icon_edit.editingFinished.connect(self._on_icon_changed)
        icon_row.addWidget(self._icon_edit)
        icon_pick_btn = QPushButton("从画布拾取")
        icon_pick_btn.clicked.connect(self._start_pick_icon)
        icon_row.addWidget(icon_pick_btn)
        right.addLayout(icon_row)

        # 状态
        self._status = QLabel("")
        self._status.setStyleSheet("color: #4a9; font-size: 11px;")
        right.addWidget(self._status)

        right.addStretch(1)

        # 底部关闭
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        right.addWidget(close_btn)

        root.addLayout(right, 2)

    # ─────────── 列表 ───────────

    def _refresh_list(self) -> None:
        self._list.clear()
        for rule in self._mgr.get_all():
            item = QListWidgetItem(rule.name)
            item.setData(Qt.UserRole, rule.name)
            self._list.addItem(item)

    def _on_select_rule(self, item: QListWidgetItem) -> None:
        name = item.data(Qt.UserRole)
        rule = self._mgr.get(name)
        if rule is None:
            return
        self._current_rule = rule
        self._load_to_form()

    def _load_to_form(self) -> None:
        if self._current_rule is None:
            return
        r = self._current_rule
        self._name_edit.blockSignals(True)
        self._name_edit.setText(r.name)
        self._name_edit.blockSignals(False)

        # 通行表
        for (rel, pt), cb in self._checks.items():
            cb.blockSignals(True)
            cb.setChecked(bool(r.get_relation(rel).get(pt, False)))
            cb.blockSignals(False)

        # required
        self._req_list.clear()
        for p in r.required_provinces:
            self._req_list.addItem(QListWidgetItem(str(p)))

        # icon
        self._icon_edit.blockSignals(True)
        self._icon_edit.setText(str(r.icon_province) if r.icon_province > 0 else "")
        self._icon_edit.blockSignals(False)

        self._status.setText(f"已加载 {r.name}")

    # ─────────── 增删 ───────────

    def _on_new(self) -> None:
        name, ok = QInputDialog.getText(self, "新建规则", "规则名 (英文大写, 如 SUEZ_CANAL):")
        if not ok:
            return
        name = name.strip()
        if not name:
            return
        if self._mgr.get(name) is not None:
            QMessageBox.warning(self, "错误", f"规则名 {name} 已存在")
            return
        self._mgr.add(AdjacencyRule(name=name))
        self._refresh_list()
        # 选中新建的
        for i in range(self._list.count()):
            if self._list.item(i).data(Qt.UserRole) == name:
                self._list.setCurrentRow(i)
                self._on_select_rule(self._list.item(i))
                break

    def _on_delete(self) -> None:
        if self._current_rule is None:
            return
        ret = QMessageBox.question(
            self, "删除", f"删除规则 {self._current_rule.name}?",
        )
        if ret != QMessageBox.Yes:
            return
        self._mgr.remove(self._current_rule.name)
        self._current_rule = None
        self._refresh_list()
        self._name_edit.clear()

    # ─────────── 字段编辑回调 ───────────

    def _on_name_changed(self) -> None:
        if self._current_rule is None:
            return
        new_name = self._name_edit.text().strip()
        if not new_name or new_name == self._current_rule.name:
            return
        if self._mgr.get(new_name) is not None:
            QMessageBox.warning(self, "错误", f"规则名 {new_name} 已存在")
            self._name_edit.setText(self._current_rule.name)
            return
        # 重命名 = 删旧加新
        old = self._current_rule.name
        self._mgr.remove(old)
        self._current_rule.name = new_name
        self._mgr.add(self._current_rule)
        self._refresh_list()

    def _on_check_toggled(self, rel: str, pt: str, checked: bool) -> None:
        if self._current_rule is None:
            return
        self._current_rule.get_relation(rel)[pt] = bool(checked)

    def _on_icon_changed(self) -> None:
        if self._current_rule is None:
            return
        text = self._icon_edit.text().strip()
        if not text:
            self._current_rule.icon_province = -1
            return
        try:
            self._current_rule.icon_province = int(text)
        except ValueError:
            QMessageBox.warning(self, "错误", "icon 必须是整数省份 ID")

    def _on_add_required_manually(self) -> None:
        if self._current_rule is None:
            return
        v, ok = QInputDialog.getInt(self, "添加省份", "省份 ID:", value=1, min=1, max=999999)
        if ok:
            self._current_rule.required_provinces.append(v)
            self._req_list.addItem(QListWidgetItem(str(v)))

    def _on_remove_required(self) -> None:
        if self._current_rule is None:
            return
        row = self._req_list.currentRow()
        if 0 <= row < len(self._current_rule.required_provinces):
            self._current_rule.required_provinces.pop(row)
            self._req_list.takeItem(row)

    # ─────────── 拾取模式 ───────────

    def _start_pick_required(self) -> None:
        if self._current_rule is None:
            self._status.setText("先选中或新建一个规则")
            return
        self._pick_target = "required_add"
        self._status.setText("点击主画布省份 → 加入 required_provinces")
        self.pick_mode_changed.emit(True, "rule_required")

    def _start_pick_icon(self) -> None:
        if self._current_rule is None:
            self._status.setText("先选中或新建一个规则")
            return
        self._pick_target = "icon"
        self._status.setText("点击主画布海省 → 设为 icon")
        self.pick_mode_changed.emit(True, "rule_icon")

    def receive_picked_province(self, pid: int) -> None:
        if self._current_rule is None:
            return
        if self._pick_target == "required_add":
            self._current_rule.required_provinces.append(pid)
            self._req_list.addItem(QListWidgetItem(str(pid)))
            self._status.setText(f"加入 required: {pid}")
        elif self._pick_target == "icon":
            self._current_rule.icon_province = pid
            self._icon_edit.setText(str(pid))
            self._status.setText(f"icon 设为 {pid}")
        self._pick_target = None
        self.pick_mode_changed.emit(False, "")

    def closeEvent(self, event) -> None:
        if self._pick_target is not None:
            self.pick_mode_changed.emit(False, "")
            self._pick_target = None
        super().closeEvent(event)
