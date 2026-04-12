"""
总览贴图颜色 page — 侧边栏内联版 (从 dialog.py 迁移).

3 个色块选择器 (陆/海/湖) + 重置按钮.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QColorDialog, QScrollArea,
)
from PyQt5.QtGui import QColor

from ui.styles import _DIM_LABEL_STYLE, _LABEL_STYLE


def build_page(panel) -> QWidget:
    outer = QWidget()
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; }")

    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    tip = QLabel("战略视角缩放时的全图底色(colormap).\n"
                 "这是 HOI4 缩到最远时看到的颜色贴图，\n"
                 "分别设置陆地/海洋/湖泊的底色.\n"
                 "改颜色后下次导出生效.")
    tip.setWordWrap(True)
    tip.setStyleSheet(_DIM_LABEL_STYLE)
    lay.addWidget(tip)

    # 三个色块
    for label_text, attr_name in [("陆地:", "land"), ("海洋:", "sea"), ("湖泊:", "lake")]:
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setFixedWidth(50)
        lbl.setStyleSheet(_LABEL_STYLE)
        row.addWidget(lbl)
        swatch = QPushButton()
        swatch.setFixedSize(100, 28)
        swatch.setProperty("color_attr", attr_name)
        swatch.clicked.connect(lambda checked=False, s=swatch, a=attr_name: _pick_color(panel, s, a))
        row.addWidget(swatch)
        row.addStretch(1)
        lay.addLayout(row)
        setattr(panel, f"_colormap_{attr_name}_swatch", swatch)

    reset_btn = QPushButton("恢复默认")
    reset_btn.clicked.connect(lambda: panel.colormap_reset_requested.emit())
    lay.addWidget(reset_btn)

    lay.addStretch(1)
    scroll.setWidget(page)

    root = QVBoxLayout(outer)
    root.setContentsMargins(0, 0, 0, 0)
    root.addWidget(scroll)
    return outer


def _pick_color(panel, swatch, attr_name: str):
    """弹颜色选择器, 选完发信号."""
    qc = QColorDialog.getColor(QColor(128, 128, 128), panel, f"选择{attr_name}颜色")
    if qc.isValid():
        panel.colormap_color_changed.emit(attr_name, qc.red(), qc.green(), qc.blue())
        swatch.setStyleSheet(
            f"background-color: rgb({qc.red()}, {qc.green()}, {qc.blue()});"
            f" border: 1px solid #3a3a4a;"
        )
