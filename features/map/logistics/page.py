"""
后勤 feature 侧边栏页面.

三个 section:
1. 相邻关系 (adjacencies) — 海峡/运河/不可通行
2. 铁路 (railways) — 画线 + 等级 1-5
3. 补给节点 (supply nodes) — 点击放置

每个 section 有一个按钮打开对应对话框. 对话框都是非模态,
用"拾取模式" 信号让主窗口拦截画布点击 (参考 continent dialog 范式).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
    QListWidget, QGroupBox,
)
from PyQt5.QtCore import Qt

from ui.styles import (
    _DIM, _BORDER, _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE,
    _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE, _SPINBOX_STYLE, _LIST_STYLE,
)


def build_page(panel) -> QWidget:
    """构建后勤页. panel 是 ToolPanel 实例."""
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(10)

    tip = QLabel("后勤系统管理: 海峡 / 铁路 / 补给节点\n"
                 "相邻关系: 定义海峡通道/运河/不可通行区域\n"
                 "铁路: 连接省份的补给线路(1-5级)\n"
                 "补给节点: 陆地省份上的物资中转站")
    tip.setStyleSheet(_DIM_LABEL_STYLE)
    tip.setWordWrap(True)
    lay.addWidget(tip)

    # ── 相邻关系 ──
    adj_box = _make_section("相邻关系 (海峡 / 运河 / 阻塞)")
    adj_lay = adj_box.layout()

    panel._logi_adj_status = QLabel("0 条")
    panel._logi_adj_status.setStyleSheet(_DIM_LABEL_STYLE)
    adj_lay.addWidget(panel._logi_adj_status)

    adj_btn = QPushButton("打开相邻关系编辑器...")
    adj_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    adj_btn.clicked.connect(lambda: panel.open_adjacency_dialog_requested.emit())
    adj_lay.addWidget(adj_btn)

    lay.addWidget(adj_box)

    # ── 铁路 ──
    rail_box = _make_section("铁路")
    rail_lay = rail_box.layout()

    panel._logi_rail_status = QLabel("0 条")
    panel._logi_rail_status.setStyleSheet(_DIM_LABEL_STYLE)
    rail_lay.addWidget(panel._logi_rail_status)

    rail_level_row = QHBoxLayout()
    rl_lbl = QLabel("画笔等级:")
    rl_lbl.setStyleSheet(_LABEL_STYLE)
    rail_level_row.addWidget(rl_lbl)
    panel._logi_rail_level = QSpinBox()
    panel._logi_rail_level.setRange(1, 5)
    panel._logi_rail_level.setValue(3)
    panel._logi_rail_level.setStyleSheet(_SPINBOX_STYLE)
    panel._logi_rail_level.valueChanged.connect(
        lambda v: panel.logistics_railway_level_changed.emit(v)
    )
    rail_level_row.addWidget(panel._logi_rail_level)
    rail_lay.addLayout(rail_level_row)

    panel._logi_rail_draw_btn = QPushButton("启用铁路画笔")
    panel._logi_rail_draw_btn.setCheckable(True)
    panel._logi_rail_draw_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    panel._logi_rail_draw_btn.toggled.connect(
        lambda on: panel.logistics_railway_draw_toggled.emit(on)
    )
    rail_lay.addWidget(panel._logi_rail_draw_btn)

    rail_list_btn = QPushButton("铁路列表...")
    rail_list_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
    rail_list_btn.clicked.connect(lambda: panel.open_railway_list_requested.emit())
    rail_lay.addWidget(rail_list_btn)

    lay.addWidget(rail_box)

    # ── 补给节点 ──
    sup_box = _make_section("补给节点")
    sup_lay = sup_box.layout()

    panel._logi_sup_status = QLabel("0 个")
    panel._logi_sup_status.setStyleSheet(_DIM_LABEL_STYLE)
    sup_lay.addWidget(panel._logi_sup_status)

    panel._logi_sup_toggle_btn = QPushButton("启用补给点拾取")
    panel._logi_sup_toggle_btn.setCheckable(True)
    panel._logi_sup_toggle_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    panel._logi_sup_toggle_btn.toggled.connect(
        lambda on: panel.logistics_supply_pick_toggled.emit(on)
    )
    sup_lay.addWidget(panel._logi_sup_toggle_btn)

    hint = QLabel("开启后点击陆地省份: 切换该省是否为补给节点")
    hint.setStyleSheet(_DIM_LABEL_STYLE)
    hint.setWordWrap(True)
    sup_lay.addWidget(hint)

    lay.addWidget(sup_box)

    lay.addStretch(1)
    return page


def _make_section(title: str) -> QGroupBox:
    box = QGroupBox(title)
    box.setStyleSheet(_SECTION_STYLE)
    inner = QVBoxLayout(box)
    inner.setContentsMargins(8, 12, 8, 8)
    inner.setSpacing(6)
    return box
