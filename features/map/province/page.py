"""province feature 页面 — 独立 QWidget, 不依赖 ToolPanel.

默认点击 = 查看省份数据
合并/扩张 需要手动开启，操作完自动关闭回到查看模式。
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel,
)

from ui.styles import (
    make_section as _make_section,
    _DIM, _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE,
    _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
)
from ui.i18n import tr




class ProvincePage(QWidget):
    """省份编辑页面."""

    # 输出信号
    split_province_requested = pyqtSignal()
    lasso_province_toggled = pyqtSignal(bool)
    merge_mode_toggled = pyqtSignal(bool)
    regen_mode_toggled = pyqtSignal(bool)
    regen_execute_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)

        # 提示 (动态更新)
        self._province_hint = QLabel(tr("province_hint_default"))
        self._province_hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        self._province_hint.setWordWrap(True)
        lay.addWidget(self._province_hint)

        # ── 省份信息 ──
        info_box = _make_section(tr("province_section_info"))
        il = info_box.layout()

        self._prov_labels: dict[str, QLabel] = {}
        for key, display in [
            ("id", tr("province_info_id")),
            ("type", tr("province_info_type")),
            ("terrain", tr("province_info_terrain")),
            ("pixels", tr("province_info_pixels")),
            ("coastal", tr("province_info_coastal")),
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
            self._prov_labels[key] = val_lbl

        lay.addWidget(info_box)

        # ── 工具按钮 ──
        tools_box = _make_section(tr("province_section_tools"))

        # 合并按钮 (toggle)
        self._merge_btn = QPushButton(tr("province_btn_merge"))
        self._merge_btn.setCheckable(True)
        self._merge_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        self._merge_btn.setToolTip(tr("province_btn_merge_tip"))
        tools_box.layout().addWidget(self._merge_btn)

        # 扩张按钮 (toggle)
        self._expand_btn = QPushButton(tr("province_btn_expand"))
        self._expand_btn.setCheckable(True)
        self._expand_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        self._expand_btn.setToolTip(tr("province_btn_expand_tip"))
        tools_box.layout().addWidget(self._expand_btn)

        # 切割按钮 (普通)
        self._split_btn = QPushButton(tr("province_btn_split"))
        self._split_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        self._split_btn.setToolTip(tr("province_btn_split_tip"))
        tools_box.layout().addWidget(self._split_btn)

        lay.addWidget(tools_box)

        # ── 增量生成 ──
        regen_box = _make_section(tr("province_section_regen"))

        self._regen_btn = QPushButton(tr("province_btn_select_area"))
        self._regen_btn.setCheckable(True)
        self._regen_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        self._regen_btn.setToolTip(tr("province_btn_select_area_tip"))
        regen_box.layout().addWidget(self._regen_btn)

        self._regen_exec_btn = QPushButton(tr("province_btn_regen_exec"))
        self._regen_exec_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        self._regen_exec_btn.setToolTip(tr("province_btn_regen_exec_tip"))
        regen_box.layout().addWidget(self._regen_exec_btn)

        lay.addWidget(regen_box)

        # ── 信号连接 ──
        self._merge_btn.toggled.connect(self._on_merge_toggled)
        self._expand_btn.toggled.connect(self._on_expand_toggled)
        self._split_btn.clicked.connect(self.split_province_requested.emit)
        self._regen_btn.toggled.connect(self._on_regen_toggled)
        self._regen_exec_btn.clicked.connect(self.regen_execute_requested.emit)

        lay.addStretch()

    # ── 槽函数 ──
    def _on_merge_toggled(self, on: bool) -> None:
        # 合并和扩张互斥
        if on and self._expand_btn.isChecked():
            self._expand_btn.setChecked(False)
        self.merge_mode_toggled.emit(on)
        if on:
            self._province_hint.setText(tr("province_hint_merge"))
        else:
            self._province_hint.setText(tr("province_hint_click_info"))

    def _on_expand_toggled(self, on: bool) -> None:
        if on and self._merge_btn.isChecked():
            self._merge_btn.setChecked(False)
        if on and self._regen_btn.isChecked():
            self._regen_btn.setChecked(False)
        self.lasso_province_toggled.emit(on)
        if on:
            self._province_hint.setText(tr("province_hint_expand"))
        else:
            self._province_hint.setText(tr("province_hint_click_info"))

    def _on_regen_toggled(self, on: bool) -> None:
        if on and self._merge_btn.isChecked():
            self._merge_btn.setChecked(False)
        if on and self._expand_btn.isChecked():
            self._expand_btn.setChecked(False)
        self.regen_mode_toggled.emit(on)
        if on:
            self._province_hint.setText(tr("province_hint_regen"))
        else:
            self._province_hint.setText(tr("province_hint_click_info"))

    # ── 公共更新方法 ──
    def update_province_info(
        self, pid: int, ptype: str, terrain: str, pixels: int, coastal: bool
    ) -> None:
        """更新省份信息面板"""
        self._prov_labels["id"].setText(str(pid))
        self._prov_labels["type"].setText(ptype)
        self._prov_labels["terrain"].setText(terrain)
        self._prov_labels["pixels"].setText(str(pixels))
        self._prov_labels["coastal"].setText(tr("province_coastal_yes") if coastal else tr("province_coastal_no"))
