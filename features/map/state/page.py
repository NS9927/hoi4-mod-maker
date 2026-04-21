"""state feature 页面 — 独立 QWidget, 不依赖 ToolPanel."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QSpinBox, QListWidget, QListWidgetItem,
    QComboBox, QLineEdit, QCheckBox,
)

from domain.managers.state import StateManager

from ui.i18n import tr
from ui.styles import (
    make_section as _make_section,
    _DIM, _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE,
    _PRIMARY_BTN_STYLE, _SPINBOX_STYLE, _LINEEDIT_STYLE,
    _COMBOBOX_STYLE, _LIST_STYLE,
)




class StatePage(QWidget):
    """州编辑页面."""

    # 输出信号
    auto_states_requested = pyqtSignal(int)
    state_selected = pyqtSignal(int)
    state_property_changed = pyqtSignal(int, str, object)
    state_detail_requested = pyqtSignal(int)
    batch_create_state_toggled = pyqtSignal(bool)
    batch_create_state_confirmed = pyqtSignal()
    assign_mode_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_state_id = 0
        self._init_ui()

    def _init_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)

        # ── 快速开始 ──
        quick_box = _make_section(tr("state_quick_section"))
        ql = quick_box.layout()
        auto_row = QHBoxLayout()
        auto_btn = QPushButton(tr("state_auto_btn"))
        auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        auto_btn.clicked.connect(self._on_auto_states)
        auto_row.addWidget(auto_btn, 2)
        spin_lbl = QLabel(tr("state_per_spin_label"))
        spin_lbl.setStyleSheet(_LABEL_STYLE)
        auto_row.addWidget(spin_lbl)
        self._state_per_spin = QSpinBox()
        self._state_per_spin.setRange(5, 30)
        self._state_per_spin.setValue(15)
        self._state_per_spin.setStyleSheet(_SPINBOX_STYLE)
        auto_row.addWidget(self._state_per_spin, 1)
        ql.addLayout(auto_row)
        lay.addWidget(quick_box)

        # ── 手动编辑 ──
        edit_box = _make_section(tr("state_edit_section"))
        el = edit_box.layout()

        self._assign_chk = QCheckBox(tr("state_assign_drag_label"))
        self._assign_chk.setChecked(False)
        self._assign_chk.setStyleSheet(
            "QCheckBox { color: #f0f0ff; font-size: 13px; font-weight: 600; padding: 6px; }"
            "QCheckBox:checked { color: #86efac; }"
        )
        self._assign_chk.toggled.connect(self.assign_mode_changed)
        el.addWidget(self._assign_chk)

        batch_row = QHBoxLayout()
        self._batch_btn = QPushButton(tr("state_batch_select_btn_short"))
        self._batch_btn.setCheckable(True)
        self._batch_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        self._batch_btn.setToolTip(tr("state_batch_select_tip"))
        self._batch_btn.toggled.connect(self.batch_create_state_toggled.emit)
        batch_row.addWidget(self._batch_btn)

        self._batch_confirm_btn = QPushButton(tr("state_batch_confirm_btn_short"))
        self._batch_confirm_btn.setStyleSheet(
            "QPushButton { background: #22c55e; color: white; padding: 6px;"
            " border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #2ad66a; }"
        )
        self._batch_confirm_btn.clicked.connect(self.batch_create_state_confirmed.emit)
        batch_row.addWidget(self._batch_confirm_btn)
        el.addLayout(batch_row)
        lay.addWidget(edit_box)

        # ── 州列表 ──
        list_box = _make_section(tr("state_list_section"))
        self._state_list = QListWidget()
        self._state_list.setStyleSheet(_LIST_STYLE)
        self._state_list.setMinimumHeight(200)
        self._state_list.currentRowChanged.connect(self._on_state_list_clicked)
        list_box.layout().addWidget(self._state_list)
        lay.addWidget(list_box)

        # ── 选中州属性 ──
        info_box = _make_section(tr("state_props_section"))
        il = info_box.layout()

        name_row = QHBoxLayout()
        name_lbl = QLabel(tr("state_name_label"))
        name_lbl.setStyleSheet(_LABEL_STYLE)
        name_row.addWidget(name_lbl)
        self._state_name_edit = QLineEdit()
        self._state_name_edit.setStyleSheet(_LINEEDIT_STYLE)
        self._state_name_edit.editingFinished.connect(self._on_state_name_changed)
        name_row.addWidget(self._state_name_edit)
        il.addLayout(name_row)

        mp_row = QHBoxLayout()
        mp_lbl = QLabel(tr("state_manpower_label"))
        mp_lbl.setStyleSheet(_LABEL_STYLE)
        mp_row.addWidget(mp_lbl)
        self._state_manpower_spin = QSpinBox()
        self._state_manpower_spin.setRange(0, 100000000)
        self._state_manpower_spin.setSingleStep(10000)
        self._state_manpower_spin.setStyleSheet(_SPINBOX_STYLE)
        self._state_manpower_spin.valueChanged.connect(self._on_state_manpower_changed)
        mp_row.addWidget(self._state_manpower_spin)
        il.addLayout(mp_row)

        cat_row = QHBoxLayout()
        cat_lbl = QLabel(tr("state_category_label"))
        cat_lbl.setStyleSheet(_LABEL_STYLE)
        cat_row.addWidget(cat_lbl)
        self._state_category_combo = QComboBox()
        self._state_category_combo.setStyleSheet(_COMBOBOX_STYLE)
        self._state_category_combo.addItems(StateManager.CATEGORIES)
        self._state_category_combo.currentTextChanged.connect(self._on_state_category_changed)
        cat_row.addWidget(self._state_category_combo)
        il.addLayout(cat_row)

        detail_btn = QPushButton(tr("state_detail_btn"))
        detail_btn.clicked.connect(self._on_state_detail_clicked)
        il.addWidget(detail_btn)

        lay.addWidget(info_box)

        lay.addStretch()

    # ── 槽函数 ──
    def _on_auto_states(self) -> None:
        per_state = self._state_per_spin.value()
        self.auto_states_requested.emit(per_state)

    def _on_state_list_clicked(self, row: int) -> None:
        item = self._state_list.item(row)
        if item is not None:
            state_id = item.data(Qt.UserRole)
            if state_id is not None:
                self._current_state_id = int(state_id)
                self.state_selected.emit(state_id)

    def _on_state_name_changed(self) -> None:
        item = self._state_list.currentItem()
        if item is not None:
            state_id = item.data(Qt.UserRole)
            if state_id is not None:
                self.state_property_changed.emit(
                    state_id, "name", self._state_name_edit.text()
                )

    def _on_state_manpower_changed(self, value: int) -> None:
        item = self._state_list.currentItem()
        if item is not None:
            state_id = item.data(Qt.UserRole)
            if state_id is not None:
                self.state_property_changed.emit(state_id, "manpower", value)

    def _on_state_category_changed(self, text: str) -> None:
        item = self._state_list.currentItem()
        if item is not None:
            state_id = item.data(Qt.UserRole)
            if state_id is not None:
                self.state_property_changed.emit(state_id, "category", text)

    def _on_state_detail_clicked(self) -> None:
        if self._current_state_id > 0:
            self.state_detail_requested.emit(self._current_state_id)

    # ── 公共更新方法 ──
    def update_state_list(self, states: list[tuple[int, str, int]]) -> None:
        """刷新 State 列表，items 为 (id, name, province_count)"""
        self._state_list.clear()
        for state_id, name, prov_count in states:
            item = QListWidgetItem(f"[{state_id}] {name} ({prov_count})")
            item.setData(Qt.UserRole, state_id)
            self._state_list.addItem(item)

    def update_state_info(self, name: str, manpower: int, category: str) -> None:
        """填充 State 属性字段"""
        self._state_name_edit.blockSignals(True)
        self._state_name_edit.setText(name)
        self._state_name_edit.blockSignals(False)

        self._state_manpower_spin.blockSignals(True)
        self._state_manpower_spin.setValue(manpower)
        self._state_manpower_spin.blockSignals(False)

        self._state_category_combo.blockSignals(True)
        idx = self._state_category_combo.findText(category)
        if idx >= 0:
            self._state_category_combo.setCurrentIndex(idx)
        self._state_category_combo.blockSignals(False)
