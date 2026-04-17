"""战略区域 page — 独立 QWidget, 不依赖 ToolPanel.

功能: region 列表 + 自动生成 + 编辑 (名字/weather/naval_terrain).
选中列表中的区域后，直接点击地图省份即可分配。
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QComboBox, QScrollArea, QCheckBox,
)

from domain.managers.strategic_region import PRESET_LABELS

from ui.i18n import tr
from ui.styles import (
    _DIM_LABEL_STYLE, _PRIMARY_BTN_STYLE,
    _LIST_STYLE, _COMBOBOX_STYLE, _LINEEDIT_STYLE,
)


class StrategicRegionPage(QWidget):
    """战略区域页面."""

    # 输出信号
    strategic_region_auto_requested = pyqtSignal()
    auto_weather_requested = pyqtSignal()
    strategic_region_selected = pyqtSignal(int)
    strategic_region_new_requested = pyqtSignal()
    strategic_region_delete_requested = pyqtSignal()
    strategic_region_name_changed = pyqtSignal(str)
    strategic_region_weather_changed = pyqtSignal(str)
    strategic_region_naval_changed = pyqtSignal(str)
    strategic_region_pick_toggled = pyqtSignal(bool)
    sr_assign_mode_changed = pyqtSignal(bool)
    create_from_states_toggled = pyqtSignal(bool)
    create_from_states_confirmed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        # 提示
        tip = QLabel("在列表选中一个区域，然后点击地图省份分配。\n白色边界线 = State 边界。")
        tip.setWordWrap(True)
        tip.setStyleSheet(_DIM_LABEL_STYLE)
        lay.addWidget(tip)

        # 自动生成
        auto_btn = QPushButton(tr("sr_auto_btn"))
        auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        auto_btn.clicked.connect(lambda: self.strategic_region_auto_requested.emit())
        lay.addWidget(auto_btn)

        auto_weather_btn = QPushButton(tr("sr_auto_weather_btn"))
        auto_weather_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        auto_weather_btn.clicked.connect(lambda: self.auto_weather_requested.emit())
        lay.addWidget(auto_weather_btn)

        # 从州创建
        self._from_states_btn = QPushButton(tr("sr_from_states_btn"))
        self._from_states_btn.setCheckable(True)
        self._from_states_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        self._from_states_btn.setToolTip(tr("sr_from_states_tip"))
        self._from_states_btn.toggled.connect(self.create_from_states_toggled.emit)
        lay.addWidget(self._from_states_btn)

        self._from_states_confirm_btn = QPushButton(tr("sr_from_states_confirm_btn"))
        self._from_states_confirm_btn.setStyleSheet(
            "QPushButton { background: #22c55e; color: white; padding: 6px;"
            " border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #2ad66a; }"
        )
        self._from_states_confirm_btn.clicked.connect(self.create_from_states_confirmed.emit)
        lay.addWidget(self._from_states_confirm_btn)

        # 分配模式开关
        self._assign_chk = QCheckBox("分配模式（点省份加入选中区域）")
        self._assign_chk.setChecked(False)
        self._assign_chk.setStyleSheet(
            "QCheckBox { color: #f0f0ff; font-size: 13px; font-weight: 600; padding: 6px; }"
            "QCheckBox:checked { color: #86efac; }"
        )
        self._assign_chk.toggled.connect(self.sr_assign_mode_changed.emit)
        lay.addWidget(self._assign_chk)

        # Region 列表（加大高度）
        self._sr_list = QListWidget()
        self._sr_list.setStyleSheet(_LIST_STYLE)
        self._sr_list.setMinimumHeight(180)
        self._sr_list.currentRowChanged.connect(
            lambda row: self.strategic_region_selected.emit(row)
        )
        lay.addWidget(self._sr_list)

        btn_row = QHBoxLayout()
        new_btn = QPushButton(tr("sr_new_btn"))
        new_btn.clicked.connect(lambda: self.strategic_region_new_requested.emit())
        del_btn = QPushButton(tr("sr_delete_btn"))
        del_btn.clicked.connect(lambda: self.strategic_region_delete_requested.emit())
        btn_row.addWidget(new_btn)
        btn_row.addWidget(del_btn)
        lay.addLayout(btn_row)

        # 编辑字段
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel(tr("sr_name_label")))
        self._sr_name_edit = QLineEdit()
        self._sr_name_edit.setStyleSheet(_LINEEDIT_STYLE)
        self._sr_name_edit.editingFinished.connect(
            lambda: self.strategic_region_name_changed.emit(self._sr_name_edit.text())
        )
        name_row.addWidget(self._sr_name_edit)
        lay.addLayout(name_row)

        weather_row = QHBoxLayout()
        weather_row.addWidget(QLabel(tr("sr_weather_label")))
        self._sr_weather_combo = QComboBox()
        self._sr_weather_combo.setStyleSheet(_COMBOBOX_STYLE)
        for key, label in PRESET_LABELS.items():
            self._sr_weather_combo.addItem(label, key)
        self._sr_weather_combo.currentIndexChanged.connect(
            lambda idx: self.strategic_region_weather_changed.emit(
                self._sr_weather_combo.currentData() or "temperate"
            )
        )
        weather_row.addWidget(self._sr_weather_combo)
        lay.addLayout(weather_row)

        naval_row = QHBoxLayout()
        naval_row.addWidget(QLabel(tr("sr_naval_label")))
        self._sr_naval_combo = QComboBox()
        self._sr_naval_combo.setStyleSheet(_COMBOBOX_STYLE)
        self._sr_naval_combo.addItem(tr("sr_naval_none"), "")
        for nt in ("ocean", "deep_ocean", "shallow_sea"):
            self._sr_naval_combo.addItem(nt, nt)
        self._sr_naval_combo.currentIndexChanged.connect(
            lambda idx: self.strategic_region_naval_changed.emit(
                self._sr_naval_combo.currentData() or ""
            )
        )
        naval_row.addWidget(self._sr_naval_combo)
        lay.addLayout(naval_row)

        self._sr_prov_count = QLabel(tr("sr_prov_count", 0))
        self._sr_prov_count.setStyleSheet(_DIM_LABEL_STYLE)
        lay.addWidget(self._sr_prov_count)

        # 保留 pick 按钮引用（兼容 main_window_actions 对 _sr_pick_btn 的访问）
        self._sr_pick_btn = QPushButton()
        self._sr_pick_btn.setVisible(False)

        lay.addStretch(1)
        scroll.setWidget(page)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)
