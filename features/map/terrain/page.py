"""terrain feature 页面 — 按 provincial terrain type 分组显示全部 graphical terrain 变体.

每个按钮带 atlas0.dds 的真实贴图缩略图，让制作者直观看到游戏里的材质。
"""

import os

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QPen, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QButtonGroup,
)

from data.terrain_types import (
    TERRAIN_TYPES, PAINTABLE_GROUPS, GRAPHICAL_TERRAINS,
)

from ui.styles import (
    _DIM, _PRIMARY_BTN_STYLE, _TOOL_BTN_STYLE,
)

# 从 vanilla atlas0.dds 提取的每个 texture tile 的真实平均色 (RGB)
_ATLAS_COLORS: dict[int, tuple[int, int, int]] = {
    0:  (129, 140, 102),
    1:  (153, 159, 119),
    2:  (147, 150, 116),
    3:  (139, 137, 115),
    4:  (77,   96,  83),
    5:  (106, 128, 106),
    6:  (135, 157, 149),
    7:  (131, 133, 120),
    8:  (133, 147, 118),
    9:  (185, 176, 128),
    10: (134, 121, 105),
    11: (105,  98,  95),
    12: (195, 184, 133),
    13: (156, 135, 103),
    14: (154, 137, 112),
    15: (90,   79,  68),
}


# 分组显示顺序
_GROUP_ORDER = ["plains", "forest", "hills", "mountain", "desert", "marsh", "jungle", "urban"]

# 分组中文名
_GROUP_CN = {
    "plains": "平原", "forest": "森林", "hills": "丘陵", "mountain": "山地",
    "desert": "沙漠", "marsh": "沼泽", "jungle": "丛林", "urban": "城市",
}

# atlas 贴图缩略图目录
_TILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "..", "..", "..", "data", "atlas_tiles")


def build_page(panel) -> QWidget:
    """构建 terrain 页. panel 是 ToolPanel 实例."""
    page = QWidget()
    outer = QVBoxLayout(page)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(4)

    # 编辑模式切换: 按省份 vs 画笔
    mode_row = QHBoxLayout()
    panel._terrain_mode_group = QButtonGroup(panel)
    panel._terrain_mode_group.setExclusive(True)
    province_btn = QPushButton("按省份")
    province_btn.setCheckable(True)
    province_btn.setChecked(True)
    province_btn.setStyleSheet(_TOOL_BTN_STYLE)
    province_btn.setMinimumWidth(60)
    panel._terrain_mode_group.addButton(province_btn, 0)
    mode_row.addWidget(province_btn)
    brush_btn = QPushButton("画笔")
    brush_btn.setCheckable(True)
    brush_btn.setStyleSheet(_TOOL_BTN_STYLE)
    brush_btn.setMinimumWidth(60)
    panel._terrain_mode_group.addButton(brush_btn, 1)
    mode_row.addWidget(brush_btn)
    panel._terrain_mode_group.idClicked.connect(
        lambda mid: panel.terrain_brush_mode_changed.emit(mid == 1)
    )
    outer.addLayout(mode_row)

    # 提示
    hint = QLabel("按省份: 点选地形后点击省份分配（同时设外观+属性）\n画笔: 逐像素画地形贴图（只影响外观）")
    hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
    hint.setWordWrap(True)
    outer.addWidget(hint)

    # 可滚动区域
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("QScrollArea { border: none; }")
    scroll_content = QWidget()
    lay = QVBoxLayout(scroll_content)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)

    for group_type in _GROUP_ORDER:
        variants = PAINTABLE_GROUPS.get(group_type, [])
        if not variants:
            continue

        group_name = _GROUP_CN.get(group_type, group_type)
        box = panel._make_section(f"{group_name} ({len(variants)})")
        # 加粗分组边框
        box.setStyleSheet(box.styleSheet() + """
            QGroupBox {
                border: 2px solid #555;
            }
        """)
        grid = QGridLayout()
        grid.setSpacing(4)

        for i, gt in enumerate(variants):
            btn = QPushButton(gt.name_cn)
            btn.setToolTip(
                f"索引: {gt.palette_index}  贴图: {gt.texture}\n"
                f"类型: {gt.type}  ID: {gt.id}"
            )

            # 加载 atlas 贴图缩略图作为图标 (带黑框)
            tile_path = os.path.normpath(
                os.path.join(_TILES_DIR, f"texture_{gt.texture}.png")
            )
            if os.path.exists(tile_path):
                pix = QPixmap(tile_path)
                # 画黑框
                painter = QPainter(pix)
                painter.setPen(QPen(QColor(0, 0, 0), 2))
                painter.drawRect(0, 0, pix.width() - 1, pix.height() - 1)
                painter.end()
                btn.setIcon(QIcon(pix))
                btn.setIconSize(QSize(40, 40))

            # 用 atlas 贴图的真实平均色做背景
            r, g, b = _ATLAS_COLORS.get(gt.texture, (128, 128, 128))
            if gt.perm_snow:
                r = min(255, r + 50)
                g = min(255, g + 50)
                b = min(255, b + 70)
            brightness = r * 0.299 + g * 0.587 + b * 0.114
            fg = "#000000" if brightness > 130 else "#ffffff"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgb({r},{g},{b});
                    border: 2px solid transparent;
                    color: {fg};
                    padding: 4px 6px;
                    font-size: 12px;
                    font-weight: 600;
                    border-radius: 4px;
                    min-height: 44px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    border-color: white;
                }}
            """)
            btn.clicked.connect(
                lambda _, idx=gt.palette_index: panel.terrain_index_changed.emit(idx)
            )
            grid.addWidget(btn, i, 0)  # 一列布局，图标+文字更清楚

        box.layout().addLayout(grid)
        lay.addWidget(box)

    lay.addStretch()
    scroll.setWidget(scroll_content)
    outer.addWidget(scroll)

    # 自动生成
    auto_btn = QPushButton("从陆地自动生成")
    auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    auto_btn.clicked.connect(panel.auto_terrain_requested.emit)
    outer.addWidget(auto_btn)

    return page
