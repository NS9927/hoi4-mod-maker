"""country feature 页面 — 独立 QWidget, 不依赖 ToolPanel."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QLineEdit,
    QListWidget, QListWidgetItem,
)
from PyQt5.QtGui import QColor, QBrush

from domain.managers.country import RULING_PARTIES

from ui.i18n import tr
from ui.styles import (
    make_section as _make_section,
    _BORDER, _DIM, _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE,
    _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE, _LINEEDIT_STYLE,
    _COMBOBOX_STYLE, _LIST_STYLE,
)




class CountryPage(QWidget):
    """国家编辑页面."""

    # 输出信号
    create_country_requested = pyqtSignal()
    quick_create_country_requested = pyqtSignal(str, str, str)
    country_selected = pyqtSignal(str)
    country_property_changed = pyqtSignal(str, str, object)
    country_color_change_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._quick_create_color = (100, 100, 200)
        self._init_ui()

    def _init_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)

        # 创建国家按钮
        create_btn = QPushButton(tr("country_create_btn"))
        create_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        create_btn.clicked.connect(self.create_country_requested.emit)
        lay.addWidget(create_btn)

        # 快速创建国家按钮
        quick_btn = QPushButton(tr("country_quick_create_btn"))
        quick_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        quick_btn.setToolTip(tr("country_quick_create_tip"))
        quick_btn.clicked.connect(self._show_quick_create_dialog)
        lay.addWidget(quick_btn)

        # 国家列表
        list_box = _make_section(tr("country_list_section"))
        self._country_list = QListWidget()
        self._country_list.setStyleSheet(_LIST_STYLE)
        self._country_list.setMaximumHeight(200)
        self._country_list.currentRowChanged.connect(self._on_country_list_clicked)
        list_box.layout().addWidget(self._country_list)
        lay.addWidget(list_box)

        # 国家属性面板
        info_box = _make_section(tr("country_props_section"))
        il = info_box.layout()

        # TAG
        tag_row = QHBoxLayout()
        tag_lbl = QLabel("TAG:")
        tag_lbl.setStyleSheet(_LABEL_STYLE)
        tag_row.addWidget(tag_lbl)
        self._country_tag_label = QLabel("—")
        self._country_tag_label.setStyleSheet(_DIM_LABEL_STYLE)
        tag_row.addStretch()
        tag_row.addWidget(self._country_tag_label)
        il.addLayout(tag_row)

        # 名称
        cname_row = QHBoxLayout()
        cname_lbl = QLabel(tr("country_name_label"))
        cname_lbl.setStyleSheet(_LABEL_STYLE)
        cname_row.addWidget(cname_lbl)
        self._country_name_edit = QLineEdit()
        self._country_name_edit.setStyleSheet(_LINEEDIT_STYLE)
        self._country_name_edit.editingFinished.connect(self._on_country_name_changed)
        cname_row.addWidget(self._country_name_edit)
        il.addLayout(cname_row)

        # 执政党
        party_row = QHBoxLayout()
        party_lbl = QLabel(tr("country_party_label"))
        party_lbl.setStyleSheet(_LABEL_STYLE)
        party_row.addWidget(party_lbl)
        self._country_party_combo = QComboBox()
        self._country_party_combo.setStyleSheet(_COMBOBOX_STYLE)
        self._country_party_combo.addItems(RULING_PARTIES)
        self._country_party_combo.currentTextChanged.connect(self._on_country_party_changed)
        party_row.addWidget(self._country_party_combo)
        il.addLayout(party_row)

        # 颜色显示（可点击修改）
        color_row = QHBoxLayout()
        color_lbl = QLabel(tr("country_color_label"))
        color_lbl.setStyleSheet(_LABEL_STYLE)
        color_row.addWidget(color_lbl)
        self._country_color_btn = QPushButton()
        self._country_color_btn.setFixedSize(40, 20)
        self._country_color_btn.setStyleSheet(
            f"background: rgb(100,100,200); border: 1px solid {_BORDER}; border-radius: 3px;"
        )
        self._country_color_btn.setToolTip(tr("country_color_tip"))
        self._country_color_btn.clicked.connect(self._on_country_color_clicked)
        color_row.addStretch()
        color_row.addWidget(self._country_color_btn)
        il.addLayout(color_row)

        # 首都
        cap_row = QHBoxLayout()
        cap_lbl = QLabel(tr("country_capital_label"))
        cap_lbl.setStyleSheet(_LABEL_STYLE)
        cap_row.addWidget(cap_lbl)
        self._country_capital_label = QLabel(tr("country_capital_unset"))
        self._country_capital_label.setStyleSheet(_DIM_LABEL_STYLE)
        cap_row.addStretch()
        cap_row.addWidget(self._country_capital_label)
        il.addLayout(cap_row)

        lay.addWidget(info_box)

        # 提示
        hint = QLabel(tr("country_hint"))
        hint.setStyleSheet(f"color: {_DIM}; font-size: 11px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        lay.addStretch()

    # ── 槽函数 ──
    def _on_country_list_clicked(self, row: int) -> None:
        item = self._country_list.item(row)
        if item is not None:
            tag = item.data(Qt.UserRole)
            if tag is not None:
                self.country_selected.emit(tag)

    def _on_country_name_changed(self) -> None:
        tag = self._country_tag_label.text()
        if tag and tag != "—":
            self.country_property_changed.emit(
                tag, "name", self._country_name_edit.text()
            )

    def _on_country_party_changed(self, text: str) -> None:
        tag = self._country_tag_label.text()
        if tag and tag != "—":
            self.country_property_changed.emit(tag, "ruling_party", text)

    def _on_country_color_clicked(self) -> None:
        tag = self._country_tag_label.text()
        if tag and tag != "—":
            self.country_color_change_requested.emit(tag)

    def _show_quick_create_dialog(self) -> None:
        """弹出快速创建国家对话框"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QColorDialog

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("country_quick_dlg_title"))
        dlg.setMinimumWidth(300)

        form = QFormLayout(dlg)

        tag_edit = QLineEdit()
        tag_edit.setPlaceholderText(tr("country_tag_placeholder"))
        tag_edit.setMaxLength(3)
        tag_edit.setStyleSheet(_LINEEDIT_STYLE)
        form.addRow(tr("country_tag_row"), tag_edit)

        name_edit = QLineEdit()
        name_edit.setPlaceholderText(tr("country_name_placeholder"))
        name_edit.setStyleSheet(_LINEEDIT_STYLE)
        form.addRow(tr("country_name_label"), name_edit)

        party_combo = QComboBox()
        party_combo.setStyleSheet(_COMBOBOX_STYLE)
        party_combo.addItems(RULING_PARTIES)
        party_combo.setCurrentText("neutrality")
        form.addRow(tr("country_party_label"), party_combo)

        color_btn = QPushButton()
        color_btn.setFixedSize(60, 24)
        import random
        _r, _g, _b = random.randint(50, 220), random.randint(50, 220), random.randint(50, 220)
        color_btn.setStyleSheet(
            f"background: rgb({_r},{_g},{_b}); border: 1px solid {_BORDER}; border-radius: 3px;"
        )
        color_btn._color = (_r, _g, _b)

        def _pick_color():
            c = QColorDialog.getColor(QColor(*color_btn._color), dlg, tr("country_pick_color_title"))
            if c.isValid():
                color_btn._color = (c.red(), c.green(), c.blue())
                color_btn.setStyleSheet(
                    f"background: rgb({c.red()},{c.green()},{c.blue()}); "
                    f"border: 1px solid {_BORDER}; border-radius: 3px;"
                )

        color_btn.clicked.connect(_pick_color)
        form.addRow(tr("country_color_label"), color_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)

        if dlg.exec_() == QDialog.DialogCode.Accepted:
            tag = tag_edit.text().strip().upper()
            name = name_edit.text().strip() or tag
            party = party_combo.currentText()
            if len(tag) == 3 and tag.isalpha():
                self._quick_create_color = color_btn._color
                self.quick_create_country_requested.emit(tag, name, party)
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(dlg, tr("dlg_error"), tr("country_tag_invalid"))

    # ── 公共更新方法 ──
    def update_country_list(self, countries: list[tuple[str, str, tuple]]) -> None:
        """刷新国家列表，items 为 (tag, name, color)"""
        self._country_list.clear()
        for tag, name, color in countries:
            item = QListWidgetItem(f"[{tag}] {name}")
            item.setData(Qt.UserRole, tag)
            r, g, b = color
            item.setForeground(QBrush(QColor(r, g, b)))
            self._country_list.addItem(item)

    def update_country_info(
        self, tag: str, name: str, party: str, color: tuple, capital_name: str
    ) -> None:
        """填充国家属性字段"""
        self._country_tag_label.setText(tag)

        self._country_name_edit.blockSignals(True)
        self._country_name_edit.setText(name)
        self._country_name_edit.blockSignals(False)

        self._country_party_combo.blockSignals(True)
        idx = self._country_party_combo.findText(party)
        if idx >= 0:
            self._country_party_combo.setCurrentIndex(idx)
        self._country_party_combo.blockSignals(False)

        r, g, b = color
        self._country_color_btn.setStyleSheet(
            f"background: rgb({r},{g},{b}); border: 1px solid {_BORDER}; border-radius: 3px;"
        )

        self._country_capital_label.setText(capital_name if capital_name else tr("country_capital_unset"))
