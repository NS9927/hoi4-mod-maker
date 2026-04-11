"""
State 详情对话框 — 编辑一个 State 的进阶字段:
- impassable / controller / local_supplies
- resources (6 种战略资源)
- buildings (state 级建筑等级)
- extra_cores / claims (TAG 列表)

省份级建筑 (bunker/coastal_bunker/naval_base) 暂未在此 UI 暴露,
需按省份编辑, 下个迭代做专门的省份建筑工具.
"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox,
    QPushButton, QGroupBox, QListWidget, QInputDialog, QTabWidget, QWidget,
)


# HOI4 战略资源
RESOURCE_NAMES = ["oil", "aluminium", "rubber", "tungsten", "steel", "chromium"]
RESOURCE_LABELS = {
    "oil": "石油", "aluminium": "铝", "rubber": "橡胶",
    "tungsten": "钨", "steel": "钢", "chromium": "铬",
}

# HOI4 state 级建筑 (value 0 = 不写)
STATE_BUILDINGS = [
    "infrastructure",
    "arms_factory",
    "industrial_complex",
    "dockyard",
    "air_base",
    "anti_air_building",
    "radar_station",
    "synthetic_refinery",
    "fuel_silo",
    "nuclear_reactor",
    "rocket_site",
    "mass_transit",
    "supply_node",
]
BUILDING_LABELS = {
    "infrastructure": "基础设施 (0-5)",
    "arms_factory": "军工厂",
    "industrial_complex": "民用工厂",
    "dockyard": "船坞",
    "air_base": "空军基地 (0-10)",
    "anti_air_building": "防空 (0-5)",
    "radar_station": "雷达站 (0-4)",
    "synthetic_refinery": "合成炼油厂",
    "fuel_silo": "燃料储存",
    "nuclear_reactor": "核反应堆 (0-3)",
    "rocket_site": "火箭发射井 (0-10)",
    "mass_transit": "大众运输 (0-3)",
    "supply_node": "补给节点 (0-1)",
}
BUILDING_MAX = {
    "infrastructure": 5,
    "air_base": 10,
    "anti_air_building": 5,
    "radar_station": 4,
    "nuclear_reactor": 3,
    "rocket_site": 10,
    "mass_transit": 3,
    "supply_node": 1,
    # 其他默认 30 (vanilla 实际上限视 state_category 而定)
}


class StateDetailDialog(QDialog):
    """编辑单个 State 的进阶字段. 模态."""

    def __init__(self, state, country_tags: list[str], parent=None):
        super().__init__(parent)
        self._state = state
        self._country_tags = country_tags
        self.setWindowTitle(f"State 详情 — {state.name} (ID {state.id})")
        self.setMinimumSize(500, 540)

        self._build_ui()
        self._load_from_state()

    # ─────────── UI 构建 ───────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        tabs = QTabWidget()
        root.addWidget(tabs, 1)

        tabs.addTab(self._build_basic_tab(), "基础")
        tabs.addTab(self._build_resources_tab(), "资源")
        tabs.addTab(self._build_buildings_tab(), "建筑")
        tabs.addTab(self._build_cores_tab(), "核心 / 宣称")

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

    def _build_basic_tab(self) -> QWidget:
        w = QWidget()
        lay = QFormLayout(w)

        self._name_edit = QLineEdit()
        lay.addRow("名字:", self._name_edit)

        self._manpower_spin = QSpinBox()
        self._manpower_spin.setRange(0, 100_000_000)
        self._manpower_spin.setSingleStep(10000)
        lay.addRow("人口:", self._manpower_spin)

        self._impassable_check = QCheckBox("不可通行 (impassable)")
        lay.addRow("", self._impassable_check)

        self._controller_combo = QComboBox()
        self._controller_combo.addItem("(同 owner)", "")
        for tag in self._country_tags:
            self._controller_combo.addItem(tag, tag)
        lay.addRow("初始控制者:", self._controller_combo)

        self._supplies_spin = QDoubleSpinBox()
        self._supplies_spin.setRange(0.0, 100.0)
        self._supplies_spin.setSingleStep(0.5)
        self._supplies_spin.setDecimals(2)
        lay.addRow("本地补给加成:", self._supplies_spin)

        return w

    def _build_resources_tab(self) -> QWidget:
        w = QWidget()
        lay = QGridLayout(w)
        lay.setColumnStretch(0, 0)
        lay.setColumnStretch(1, 1)
        lay.addWidget(QLabel("<b>6 种战略资源, 0 表示不写</b>"), 0, 0, 1, 2)

        self._resource_spins: dict[str, QSpinBox] = {}
        for i, key in enumerate(RESOURCE_NAMES):
            lay.addWidget(QLabel(f"{RESOURCE_LABELS[key]} ({key}):"), i + 1, 0)
            spin = QSpinBox()
            spin.setRange(0, 10000)
            lay.addWidget(spin, i + 1, 1)
            self._resource_spins[key] = spin
        lay.setRowStretch(len(RESOURCE_NAMES) + 1, 1)
        return w

    def _build_buildings_tab(self) -> QWidget:
        w = QWidget()
        lay = QGridLayout(w)
        lay.addWidget(
            QLabel(
                "<b>State 级建筑等级</b><br>"
                "<span style='color:#888'>0 = 按 state_category 默认值; 其他值会覆盖默认</span>"
            ),
            0, 0, 1, 2,
        )
        self._building_spins: dict[str, QSpinBox] = {}
        for i, key in enumerate(STATE_BUILDINGS):
            lay.addWidget(QLabel(BUILDING_LABELS.get(key, key) + ":"), i + 1, 0)
            spin = QSpinBox()
            spin.setRange(0, BUILDING_MAX.get(key, 30))
            lay.addWidget(spin, i + 1, 1)
            self._building_spins[key] = spin

        # 省份级建筑入口
        last_row = len(STATE_BUILDINGS) + 1
        lay.addWidget(QLabel(""), last_row, 0)  # 空行
        prov_btn = QPushButton("编辑省份级建筑 (bunker / 海防 / 海军基地)...")
        prov_btn.clicked.connect(self._on_edit_province_buildings)
        lay.addWidget(prov_btn, last_row + 1, 0, 1, 2)
        lay.setRowStretch(last_row + 2, 1)
        return w

    def _on_edit_province_buildings(self) -> None:
        """打开省份级建筑对话框."""
        from features.map.state.province_buildings_dialog import (
            ProvinceBuildingsDialog,
        )
        # 用 state.provinces 作为全部省份列表 (省份内部已经过滤过 land)
        land_pids = list(self._state.provinces)
        dlg = ProvinceBuildingsDialog(self._state, land_pids, parent=self)
        dlg.exec_()

    def _build_cores_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        # 额外核心
        cores_box = QGroupBox("额外核心 (owner 自动是核心, 这里填其他国家)")
        cores_lay = QVBoxLayout(cores_box)
        self._cores_list = QListWidget()
        cores_lay.addWidget(self._cores_list)
        row = QHBoxLayout()
        add_core_btn = QPushButton("添加...")
        add_core_btn.clicked.connect(self._on_add_core)
        del_core_btn = QPushButton("删除选中")
        del_core_btn.clicked.connect(self._on_del_core)
        row.addWidget(add_core_btn)
        row.addWidget(del_core_btn)
        cores_lay.addLayout(row)
        lay.addWidget(cores_box)

        # 宣称
        claims_box = QGroupBox("宣称 (add_claim_by)")
        claims_lay = QVBoxLayout(claims_box)
        self._claims_list = QListWidget()
        claims_lay.addWidget(self._claims_list)
        row2 = QHBoxLayout()
        add_claim_btn = QPushButton("添加...")
        add_claim_btn.clicked.connect(self._on_add_claim)
        del_claim_btn = QPushButton("删除选中")
        del_claim_btn.clicked.connect(self._on_del_claim)
        row2.addWidget(add_claim_btn)
        row2.addWidget(del_claim_btn)
        claims_lay.addLayout(row2)
        lay.addWidget(claims_box)

        return w

    # ─────────── 加载/保存 ───────────

    def _load_from_state(self) -> None:
        s = self._state
        self._name_edit.setText(s.name)
        self._manpower_spin.setValue(int(s.manpower or 0))
        self._impassable_check.setChecked(bool(getattr(s, "impassable", False)))

        ctl = getattr(s, "controller_tag", "") or ""
        idx = self._controller_combo.findData(ctl)
        self._controller_combo.setCurrentIndex(idx if idx >= 0 else 0)

        self._supplies_spin.setValue(float(getattr(s, "local_supplies", 0.0) or 0.0))

        # 资源
        res = getattr(s, "resources", {}) or {}
        for key, spin in self._resource_spins.items():
            spin.setValue(int(res.get(key, 0) or 0))

        # 建筑
        bld = getattr(s, "buildings", {}) or {}
        for key, spin in self._building_spins.items():
            spin.setValue(int(bld.get(key, 0) or 0))

        # 核心 / 宣称
        self._cores_list.clear()
        for tag in getattr(s, "extra_cores", []) or []:
            self._cores_list.addItem(tag)
        self._claims_list.clear()
        for tag in getattr(s, "claims", []) or []:
            self._claims_list.addItem(tag)

    def _on_accept(self) -> None:
        s = self._state
        s.name = self._name_edit.text().strip() or f"STATE_{s.id}"
        s.manpower = int(self._manpower_spin.value())
        s.impassable = bool(self._impassable_check.isChecked())
        s.controller_tag = self._controller_combo.currentData() or ""
        s.local_supplies = float(self._supplies_spin.value())

        s.resources = {
            k: int(spin.value())
            for k, spin in self._resource_spins.items()
            if int(spin.value()) > 0
        }
        s.buildings = {
            k: int(spin.value())
            for k, spin in self._building_spins.items()
            if int(spin.value()) > 0
        }
        s.extra_cores = [
            self._cores_list.item(i).text() for i in range(self._cores_list.count())
        ]
        s.claims = [
            self._claims_list.item(i).text() for i in range(self._claims_list.count())
        ]

        self.accept()

    # ─────────── 核心 / 宣称 操作 ───────────

    def _ask_tag(self, title: str) -> str:
        if self._country_tags:
            tag, ok = QInputDialog.getItem(
                self, title, "选择国家 TAG:", self._country_tags, 0, True
            )
        else:
            tag, ok = QInputDialog.getText(self, title, "输入国家 TAG (3 字母):")
        return tag.strip().upper() if ok else ""

    def _on_add_core(self) -> None:
        tag = self._ask_tag("添加核心")
        if not tag:
            return
        # 去重
        existing = [self._cores_list.item(i).text() for i in range(self._cores_list.count())]
        if tag in existing:
            return
        self._cores_list.addItem(tag)

    def _on_del_core(self) -> None:
        row = self._cores_list.currentRow()
        if row >= 0:
            self._cores_list.takeItem(row)

    def _on_add_claim(self) -> None:
        tag = self._ask_tag("添加宣称")
        if not tag:
            return
        existing = [self._claims_list.item(i).text() for i in range(self._claims_list.count())]
        if tag in existing:
            return
        self._claims_list.addItem(tag)

    def _on_del_claim(self) -> None:
        row = self._claims_list.currentRow()
        if row >= 0:
            self._claims_list.takeItem(row)
