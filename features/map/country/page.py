"""country feature 页面 (从 tool_panel 提取).

原始代码是 ToolPanel._build_country_page, 为了按 feature 组织
UI 搬到这里. panel 参数就是原来的 panel, 需要访问 panel._xxx 内部状态.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QSlider, QLabel, QButtonGroup,
    QSpinBox, QFrame, QStackedWidget, QGridLayout,
    QSizePolicy, QListWidget, QListWidgetItem, QComboBox,
    QLineEdit, QColorDialog,
)
from PyQt5.QtGui import QColor, QPixmap, QIcon, QBrush

from data.constants import (
    TILE_LAND, TILE_SEA, TILE_LAKE,
    BRUSH_MIN, BRUSH_MAX, BRUSH_DEFAULT,
)
from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX
from domain.managers.state import StateManager
from domain.managers.country import RULING_PARTIES
from domain.managers.river import PAINTABLE_RIVER_TYPES, RIVER_PALETTE

from ui.styles import (
    _BG, _INPUT_BG, _BORDER, _TEXT, _DIM, _ACCENT, _SUCCESS,
    _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE, _SLIDER_STYLE,
    _TOOL_BTN_STYLE, _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
    _SUCCESS_BTN_STYLE, _SPINBOX_STYLE, _LINEEDIT_STYLE,
    _COMBOBOX_STYLE, _LIST_STYLE, _color_icon,
)


def build_page(panel) -> QWidget:
    """构建 country 页. panel 是 ToolPanel 实例."""
    page = QWidget()
    lay = QVBoxLayout(page)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)

    # 创建国家按钮
    create_btn = QPushButton("创建国家")
    create_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
    create_btn.clicked.connect(panel.create_country_requested.emit)
    lay.addWidget(create_btn)

    # 快速创建国家按钮
    quick_btn = QPushButton("快速创建国家")
    quick_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
    quick_btn.setToolTip("输入 TAG/名称/执政党，一键创建并进入领土分配模式")
    quick_btn.clicked.connect(lambda: _show_quick_create_dialog(panel))
    lay.addWidget(quick_btn)

    # 国家列表
    list_box = panel._make_section("国家列表")
    panel._country_list = QListWidget()
    panel._country_list.setStyleSheet(_LIST_STYLE)
    panel._country_list.setMaximumHeight(200)
    panel._country_list.currentRowChanged.connect(panel._on_country_list_clicked)
    list_box.layout().addWidget(panel._country_list)
    lay.addWidget(list_box)

    # 国家属性面板
    info_box = panel._make_section("国家属性")
    il = info_box.layout()

    # TAG
    tag_row = QHBoxLayout()
    tag_lbl = QLabel("TAG:")
    tag_lbl.setStyleSheet(_LABEL_STYLE)
    tag_row.addWidget(tag_lbl)
    panel._country_tag_label = QLabel("—")
    panel._country_tag_label.setStyleSheet(_DIM_LABEL_STYLE)
    tag_row.addStretch()
    tag_row.addWidget(panel._country_tag_label)
    il.addLayout(tag_row)

    # 名称
    cname_row = QHBoxLayout()
    cname_lbl = QLabel("名称:")
    cname_lbl.setStyleSheet(_LABEL_STYLE)
    cname_row.addWidget(cname_lbl)
    panel._country_name_edit = QLineEdit()
    panel._country_name_edit.setStyleSheet(_LINEEDIT_STYLE)
    panel._country_name_edit.editingFinished.connect(panel._on_country_name_changed)
    cname_row.addWidget(panel._country_name_edit)
    il.addLayout(cname_row)

    # 执政党
    party_row = QHBoxLayout()
    party_lbl = QLabel("执政党:")
    party_lbl.setStyleSheet(_LABEL_STYLE)
    party_row.addWidget(party_lbl)
    panel._country_party_combo = QComboBox()
    panel._country_party_combo.setStyleSheet(_COMBOBOX_STYLE)
    panel._country_party_combo.addItems(RULING_PARTIES)
    panel._country_party_combo.currentTextChanged.connect(panel._on_country_party_changed)
    party_row.addWidget(panel._country_party_combo)
    il.addLayout(party_row)

    # 颜色显示（可点击修改）
    color_row = QHBoxLayout()
    color_lbl = QLabel("颜色:")
    color_lbl.setStyleSheet(_LABEL_STYLE)
    color_row.addWidget(color_lbl)
    panel._country_color_btn = QPushButton()
    panel._country_color_btn.setFixedSize(40, 20)
    panel._country_color_btn.setStyleSheet(
        f"background: rgb(100,100,200); border: 1px solid {_BORDER}; border-radius: 3px;"
    )
    panel._country_color_btn.setToolTip("点击修改颜色")
    panel._country_color_btn.clicked.connect(panel._on_country_color_clicked)
    color_row.addStretch()
    color_row.addWidget(panel._country_color_btn)
    il.addLayout(color_row)

    # 首都
    cap_row = QHBoxLayout()
    cap_lbl = QLabel("首都:")
    cap_lbl.setStyleSheet(_LABEL_STYLE)
    cap_row.addWidget(cap_lbl)
    panel._country_capital_label = QLabel("未设置")
    panel._country_capital_label.setStyleSheet(_DIM_LABEL_STYLE)
    cap_row.addStretch()
    cap_row.addWidget(panel._country_capital_label)
    il.addLayout(cap_row)

    lay.addWidget(info_box)

    # 提示
    hint = QLabel("选中国家后，点击State可分配领土\n快速创建: 创建后自动进入领土分配模式")
    hint.setStyleSheet(f"color: {_DIM}; font-size: 11px; padding: 8px;")
    hint.setWordWrap(True)
    lay.addWidget(hint)

    lay.addStretch()
    return page


def _show_quick_create_dialog(panel) -> None:
    """弹出快速创建国家对话框"""
    from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox

    dlg = QDialog(panel)
    dlg.setWindowTitle("快速创建国家")
    dlg.setMinimumWidth(300)

    form = QFormLayout(dlg)

    tag_edit = QLineEdit()
    tag_edit.setPlaceholderText("如 KAR (3个大写字母)")
    tag_edit.setMaxLength(3)
    tag_edit.setStyleSheet(_LINEEDIT_STYLE)
    form.addRow("TAG:", tag_edit)

    name_edit = QLineEdit()
    name_edit.setPlaceholderText("国家名称")
    name_edit.setStyleSheet(_LINEEDIT_STYLE)
    form.addRow("名称:", name_edit)

    party_combo = QComboBox()
    party_combo.setStyleSheet(_COMBOBOX_STYLE)
    party_combo.addItems(RULING_PARTIES)
    party_combo.setCurrentText("neutrality")
    form.addRow("执政党:", party_combo)

    color_btn = QPushButton()
    color_btn.setFixedSize(60, 24)
    import random
    _r, _g, _b = random.randint(50, 220), random.randint(50, 220), random.randint(50, 220)
    color_btn.setStyleSheet(
        f"background: rgb({_r},{_g},{_b}); border: 1px solid {_BORDER}; border-radius: 3px;"
    )
    color_btn._color = (_r, _g, _b)

    def _pick_color():
        c = QColorDialog.getColor(QColor(*color_btn._color), dlg, "选择国家颜色")
        if c.isValid():
            color_btn._color = (c.red(), c.green(), c.blue())
            color_btn.setStyleSheet(
                f"background: rgb({c.red()},{c.green()},{c.blue()}); "
                f"border: 1px solid {_BORDER}; border-radius: 3px;"
            )

    color_btn.clicked.connect(_pick_color)
    form.addRow("颜色:", color_btn)

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
            # 发射信号，附带颜色信息
            panel._quick_create_color = color_btn._color
            panel.quick_create_country_requested.emit(tag, name, party)
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(dlg, "错误", "TAG 必须是 3 个字母")
