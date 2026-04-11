"""province feature 页面 — 傻瓜式交互.

默认点击 = 查看省份数据
合并/扩张 需要手动开启，操作完自动关闭回到查看模式。
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel,
)

from ui.styles import (
    _DIM, _ACCENT,
    _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE,
    _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
)


def build_page(panel) -> QWidget:
    """构建 province 页. panel 是 ToolPanel 实例."""
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    # 提示 (动态更新)
    hint = QLabel("点击查看省份信息。合并/扩张/切割需先点对应按钮开启")
    hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
    hint.setWordWrap(True)
    lay.addWidget(hint)
    panel._province_hint = hint

    # ── 省份信息 ──
    info_box = panel._make_section("省份信息")
    il = info_box.layout()

    panel._prov_labels: dict[str, QLabel] = {}
    for key, display in [
        ("id", "省份 ID"),
        ("type", "类型"),
        ("terrain", "地形"),
        ("pixels", "像素数"),
        ("coastal", "沿海"),
    ]:
        row = QHBoxLayout()
        name_lbl = QLabel(f"{display}:")
        name_lbl.setStyleSheet(_LABEL_STYLE)
        val_lbl = QLabel("—")
        val_lbl.setStyleSheet(_DIM_LABEL_STYLE)
        val_lbl.setAlignment(Qt.AlignRight)
        row.addWidget(name_lbl)
        row.addStretch()
        row.addWidget(val_lbl)
        il.addLayout(row)
        panel._prov_labels[key] = val_lbl

    lay.addWidget(info_box)

    # ── 工具按钮 ──
    tools_box = panel._make_section("省份操作")

    # 合并按钮 (toggle)
    merge_btn = QPushButton("合并省份")
    merge_btn.setCheckable(True)
    merge_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
    merge_btn.setToolTip("开启后：点第一个省份，再点第二个省份，自动合并并关闭")
    tools_box.layout().addWidget(merge_btn)
    panel._merge_btn = merge_btn

    # 扩张按钮 (toggle)
    expand_btn = QPushButton("扩张省份")
    expand_btn.setCheckable(True)
    expand_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
    expand_btn.setToolTip("开启后：点击省份后拖动扩张边界，松手自动关闭")
    tools_box.layout().addWidget(expand_btn)
    panel._expand_btn = expand_btn

    # 切割按钮 (普通)
    split_btn = QPushButton("切割选中省份")
    split_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    split_btn.setToolTip("先点击选中一个省份，再点此按钮切割")
    tools_box.layout().addWidget(split_btn)
    panel._split_btn = split_btn

    lay.addWidget(tools_box)

    # ── 信号连接 ──
    # 合并和扩张互斥: 开一个关另一个
    def _on_merge_toggled(on: bool) -> None:
        if on and expand_btn.isChecked():
            expand_btn.setChecked(False)
        panel.merge_mode_toggled.emit(on)
        if on:
            panel._province_hint.setText("合并模式：点第一个省份，再点第二个")
        else:
            panel._province_hint.setText("点击省份查看信息")

    def _on_expand_toggled(on: bool) -> None:
        if on and merge_btn.isChecked():
            merge_btn.setChecked(False)
        panel.lasso_province_toggled.emit(on)
        if on:
            panel._province_hint.setText("扩张模式：点击省份后拖动扩张")
        else:
            panel._province_hint.setText("点击省份查看信息")

    merge_btn.toggled.connect(_on_merge_toggled)
    expand_btn.toggled.connect(_on_expand_toggled)
    split_btn.clicked.connect(panel.split_province_requested.emit)

    lay.addStretch()
    return page
