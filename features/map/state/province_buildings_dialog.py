"""
每省建筑等级编辑对话框.

HOI4 允许在 state 内对**具体省份**配置某些建筑 (vs. state 级统计建筑):
- bunker — 陆地防御工事
- coastal_bunker — 沿海防御工事
- naval_base — 海军基地 (必须沿海)

数据存在 StateData.province_buildings: dict[pid, dict[building_name, level]]
导出到 history/states/*.txt 的 buildings 块里的嵌套 `pid = { building = level }` 格式.

参考: 参考/State modding.txt 省份级建筑字段
"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton,
    QScrollArea, QWidget, QGridLayout, QFrame,
)


# 允许的省份级建筑类型 + 等级上限
# 参考 common/buildings/00_buildings.txt
_PROVINCE_BUILDINGS = [
    ("bunker", "陆防", 5),
    ("coastal_bunker", "海防", 5),
    ("naval_base", "海军基地", 10),
]


class ProvinceBuildingsDialog(QDialog):
    """为选定 state 的每个陆地省份配置 bunker / coastal_bunker / naval_base."""

    def __init__(self, state, land_province_ids: list[int], parent=None) -> None:
        super().__init__(parent)
        self._state = state
        self._land_pids = list(land_province_ids)
        self.setWindowTitle(f"省份建筑 — {state.name} (ID {state.id})")
        self.setMinimumSize(440, 480)

        # 用来收集每行的 spinbox 引用: {(pid, building): spin}
        self._spins: dict[tuple[int, str], QSpinBox] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        tip = QLabel(
            "为 state 内每个陆地省份单独配置防御建筑.\n"
            "0 = 不建. bunker 适用所有陆地, coastal_bunker 和 naval_base 应只给沿海省份."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(tip)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #2a3a55; }")

        inner = QWidget()
        grid = QGridLayout(inner)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)

        # 表头
        grid.addWidget(QLabel("<b>省份 ID</b>"), 0, 0)
        for i, (_, display, _max) in enumerate(_PROVINCE_BUILDINGS):
            grid.addWidget(QLabel(f"<b>{display}</b>"), 0, i + 1)

        # 每个 land 省份一行
        for row, pid in enumerate(self._land_pids, start=1):
            grid.addWidget(QLabel(str(pid)), row, 0)
            current_map = self._state.province_buildings.get(pid, {})
            for col, (bname, _display, bmax) in enumerate(_PROVINCE_BUILDINGS):
                spin = QSpinBox()
                spin.setRange(0, bmax)
                spin.setValue(int(current_map.get(bname, 0)))
                spin.setFixedWidth(60)
                grid.addWidget(spin, row, col + 1)
                self._spins[(pid, bname)] = spin

        grid.setRowStretch(len(self._land_pids) + 1, 1)
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

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

    def _on_accept(self) -> None:
        """把 spin 值写回 state.province_buildings."""
        new_pb: dict[int, dict[str, int]] = {}
        for (pid, bname), spin in self._spins.items():
            v = int(spin.value())
            if v > 0:
                new_pb.setdefault(pid, {})[bname] = v
        self._state.province_buildings = new_pb
        self.accept()
