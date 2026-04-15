"""state feature 页面 — 独立 QWidget, 不依赖 ToolPanel."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QSpinBox, QListWidget, QListWidgetItem,
    QComboBox, QLineEdit,
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_state_id = 0
        self._init_ui()

    def _init_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)

        # 自动分组按钮
        auto_btn = QPushButton(tr("state_auto_btn"))
        auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        auto_btn.clicked.connect(self._on_auto_states)
        lay.addWidget(auto_btn)

        # 每State省份数
        spin_row = QHBoxLayout()
        spin_lbl = QLabel(tr("state_per_spin_label"))
        spin_lbl.setStyleSheet(_LABEL_STYLE)
        spin_row.addWidget(spin_lbl)
        self._state_per_spin = QSpinBox()
        self._state_per_spin.setRange(5, 30)
        self._state_per_spin.setValue(15)
        self._state_per_spin.setStyleSheet(_SPINBOX_STYLE)
        spin_row.addWidget(self._state_per_spin)
        lay.addLayout(spin_row)

        # 批量建州
        batch_box = _make_section(tr("state_batch_section"))
        self._batch_btn = QPushButton(tr("state_batch_select_btn"))
        self._batch_btn.setCheckable(True)
        self._batch_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        self._batch_btn.setToolTip(tr("state_batch_select_tip"))
        self._batch_btn.toggled.connect(self.batch_create_state_toggled.emit)
        batch_box.layout().addWidget(self._batch_btn)

        self._batch_confirm_btn = QPushButton(tr("state_batch_confirm_btn"))
        self._batch_confirm_btn.setStyleSheet(
            "QPushButton { background: #22c55e; color: white; padding: 6px;"
            " border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #2ad66a; }"
        )
        self._batch_confirm_btn.clicked.connect(self.batch_create_state_confirmed.emit)
        batch_box.layout().addWidget(self._batch_confirm_btn)
        lay.addWidget(batch_box)

        # State 列表
        list_box = _make_section(tr("state_list_section"))
        self._state_list = QListWidget()
        self._state_list.setStyleSheet(_LIST_STYLE)
        self._state_list.setMaximumHeight(200)
        self._state_list.currentRowChanged.connect(self._on_state_list_clicked)
        list_box.layout().addWidget(self._state_list)
        lay.addWidget(list_box)

        # State 属性面板
        info_box = _make_section(tr("state_props_section"))
        il = info_box.layout()

        # 名称
        name_row = QHBoxLayout()
        name_lbl = QLabel(tr("state_name_label"))
        name_lbl.setStyleSheet(_LABEL_STYLE)
        name_row.addWidget(name_lbl)
        self._state_name_edit = QLineEdit()
        self._state_name_edit.setStyleSheet(_LINEEDIT_STYLE)
        self._state_name_edit.editingFinished.connect(self._on_state_name_changed)
        name_row.addWidget(self._state_name_edit)
        il.addLayout(name_row)

        # 人口
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

        # 类别
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

        lay.addWidget(info_box)

        # 详情按钮
        detail_btn = QPushButton(tr("state_detail_btn"))
        detail_btn.clicked.connect(self._on_state_detail_clicked)
        lay.addWidget(detail_btn)

        # 提示
        hint = QLabel(tr("state_hint"))
        hint.setStyleSheet(f"color: {_DIM}; font-size: 11px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

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
    def update_state_list(self, states: list[tuple[int, str]]) -> None:
        """刷新 State 列表，items 为 (id, name)"""
        self._state_list.clear()
        for state_id, name in states:
            item = QListWidgetItem(f"[{state_id}] {name}")
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
