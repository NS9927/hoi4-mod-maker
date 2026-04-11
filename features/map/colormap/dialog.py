"""
战略总览贴图颜色对话框.

3 个色块按钮 (陆/海/湖), 点击弹 QColorDialog. 实时预览.
保存到 ColormapSettings, 下次导出 colormap_dds.dds 用这些颜色.
"""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QColorDialog,
    QGroupBox,
)

from domain.managers.colormap_settings import ColormapSettings, ColormapColor


class ColormapDialog(QDialog):
    """战略总览贴图颜色编辑器."""

    def __init__(self, settings: ColormapSettings, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("战略总览贴图颜色")
        self.setMinimumSize(360, 360)

        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        tip = QLabel(
            "缩到战略视角时显示的全图色调.\n"
            "默认是地球感土褐+靛蓝, 改成任何颜色让你的架空世界更独特.\n"
            "(只影响极远视角的总览, 近景仍用地形画刷)"
        )
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #888; font-size: 11px;")
        root.addWidget(tip)

        # 三个色块行
        self._land_swatch = self._make_color_row(
            root, "陆地", self._settings.land, self._on_pick_land
        )
        self._sea_swatch = self._make_color_row(
            root, "海洋", self._settings.sea, self._on_pick_sea
        )
        self._lake_swatch = self._make_color_row(
            root, "湖泊", self._settings.lake, self._on_pick_lake
        )

        # 重置按钮
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._on_reset)
        root.addWidget(reset_btn)

        root.addStretch(1)

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        ok_btn = QPushButton("保存")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    def _make_color_row(
        self, parent_layout, label_text: str, color: ColormapColor, on_click
    ) -> QPushButton:
        row = QHBoxLayout()
        lbl = QLabel(f"{label_text}:")
        lbl.setFixedWidth(60)
        row.addWidget(lbl)

        swatch = QPushButton()
        swatch.setFixedSize(140, 32)
        swatch.clicked.connect(on_click)
        row.addWidget(swatch)
        row.addStretch(1)
        self._update_swatch(swatch, color)
        parent_layout.addLayout(row)
        return swatch

    def _update_swatch(self, swatch: QPushButton, color: ColormapColor) -> None:
        swatch.setStyleSheet(
            f"background-color: rgb({color.r}, {color.g}, {color.b});"
            f" border: 1px solid #2a3a55;"
        )
        swatch.setText(f"({color.r}, {color.g}, {color.b})")

    def _pick_color(self, current: ColormapColor) -> ColormapColor | None:
        qc = QColor(current.r, current.g, current.b)
        new_qc = QColorDialog.getColor(qc, self, "选择颜色")
        if new_qc.isValid():
            return ColormapColor(new_qc.red(), new_qc.green(), new_qc.blue())
        return None

    def _on_pick_land(self) -> None:
        c = self._pick_color(self._settings.land)
        if c:
            self._settings.land = c
            self._update_swatch(self._land_swatch, c)

    def _on_pick_sea(self) -> None:
        c = self._pick_color(self._settings.sea)
        if c:
            self._settings.sea = c
            self._update_swatch(self._sea_swatch, c)

    def _on_pick_lake(self) -> None:
        c = self._pick_color(self._settings.lake)
        if c:
            self._settings.lake = c
            self._update_swatch(self._lake_swatch, c)

    def _on_reset(self) -> None:
        defaults = ColormapSettings.default()
        self._settings.land = defaults.land
        self._settings.sea = defaults.sea
        self._settings.lake = defaults.lake
        self._update_swatch(self._land_swatch, self._settings.land)
        self._update_swatch(self._sea_swatch, self._settings.sea)
        self._update_swatch(self._lake_swatch, self._settings.lake)
