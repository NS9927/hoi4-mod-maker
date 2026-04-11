"""
工具面板 — 暗色主题，6 种编辑模式，模式切换标签页
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QSlider, QLabel, QButtonGroup,
    QSpinBox, QFrame, QStackedWidget, QGridLayout,
    QSizePolicy, QListWidget, QListWidgetItem, QComboBox,
    QLineEdit, QColorDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPixmap, QIcon, QBrush

from data.constants import (
    TILE_LAND, TILE_SEA, TILE_LAKE,
    BRUSH_MIN, BRUSH_MAX, BRUSH_DEFAULT,
)
from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX
from domain.managers.state import StateManager
from domain.managers.country import RULING_PARTIES
from domain.managers.river import PAINTABLE_RIVER_TYPES, RIVER_PALETTE


# 色板 / 样式常量 / 辅助函数从统一位置 import
from ui.styles import (
    _BG, _INPUT_BG, _BORDER, _TEXT, _DIM, _ACCENT, _SUCCESS,
    _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE, _SLIDER_STYLE,
    _TOOL_BTN_STYLE, _PRIMARY_BTN_STYLE, _SECONDARY_BTN_STYLE,
    _SUCCESS_BTN_STYLE, _SPINBOX_STYLE, _LINEEDIT_STYLE,
    _COMBOBOX_STYLE, _LIST_STYLE, _color_icon,
)



# ── 分组折叠模式栏 ─────────────────────────────────────────
# groups: [("组名", "emoji", [("mode_id", "icon label"), ...]), ...]

_GROUP_HEADER_STYLE = f"""
    QPushButton {{
        background: {_INPUT_BG};
        border: none;
        border-left: 3px solid {_ACCENT};
        color: {_ACCENT};
        font-size: 13px;
        font-weight: 700;
        text-align: left;
        padding: 10px 12px;
        margin: 0;
    }}
    QPushButton:hover {{
        background: rgba(108, 108, 240, 0.08);
    }}
"""

_MODE_BTN_STYLE = f"""
    QPushButton {{
        background: transparent;
        border: none;
        border-left: 3px solid transparent;
        color: {_TEXT};
        padding: 8px 12px 8px 20px;
        font-size: 13px;
        font-weight: 400;
        text-align: left;
        margin: 0;
    }}
    QPushButton:checked {{
        background: rgba(108, 108, 240, 0.15);
        border-left: 3px solid {_ACCENT};
        color: white;
        font-weight: 600;
    }}
    QPushButton:hover:!checked {{
        background: rgba(108, 108, 240, 0.06);
        color: {_TEXT};
    }}
"""


class _GroupedModeBar(QWidget):
    """分组折叠模式导航栏. 竖列大按钮, 每组有标题 + 组内 mode 一个占一行."""
    mode_changed = pyqtSignal(str)

    def __init__(
        self,
        groups: list[tuple[str, list[tuple[str, str]]]],
        parent=None,
    ):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._buttons: dict[str, QPushButton] = {}
        self._group_widgets: dict[str, QWidget] = {}
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        for group_name, modes in groups:
            # 组标题
            header = QPushButton(f"▼  {group_name}")
            header.setStyleSheet(_GROUP_HEADER_STYLE)
            header.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(header)

            # 组内按钮容器: 竖列, 每个 mode 一行
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0, 0, 0, 4)
            vbox.setSpacing(0)

            for mid, label in modes:
                btn = QPushButton(label)
                btn.setCheckable(True)
                btn.setProperty("mode_id", mid)
                btn.setStyleSheet(_MODE_BTN_STYLE)
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self._btn_group.addButton(btn)
                self._buttons[mid] = btn
                vbox.addWidget(btn)

            layout.addWidget(container)
            self._group_widgets[group_name] = container

            # 折叠功能
            header.setProperty("group_name", group_name)
            header.setProperty("collapsed", False)
            header.clicked.connect(
                lambda checked=False, h=header, c=container: self._toggle_group(h, c)
            )

        layout.addStretch(1)  # 底部弹性空间

        self._btn_group.buttonClicked.connect(
            lambda btn: self.mode_changed.emit(btn.property("mode_id"))
        )

        if self._buttons:
            first = list(self._buttons.values())[0]
            first.setChecked(True)

    def _toggle_group(self, header: QPushButton, container: QWidget) -> None:
        collapsed = header.property("collapsed")
        if collapsed:
            container.show()
            text = header.text().replace("▶ ", "▼ ")
            header.setText(text)
            header.setProperty("collapsed", False)
        else:
            container.hide()
            text = header.text().replace("▼ ", "▶ ")
            header.setText(text)
            header.setProperty("collapsed", True)


# ── 主面板 ────────────────────────────────────────────────
class ToolPanel(QWidget):
    """左侧工具面板 — 支持 land / province / terrain / height / state / country 六种模式"""

    # 信号
    mode_changed = pyqtSignal(str)
    tool_changed = pyqtSignal(str)
    tile_type_changed = pyqtSignal(int)
    brush_size_changed = pyqtSignal(int)
    terrain_index_changed = pyqtSignal(int)
    terrain_brush_mode_changed = pyqtSignal(bool)  # True=画笔模式, False=按省份
    height_value_changed = pyqtSignal(int)
    generate_provinces_requested = pyqtSignal(int)
    validate_requested = pyqtSignal()
    auto_terrain_requested = pyqtSignal()
    auto_height_requested = pyqtSignal()
    smooth_height_requested = pyqtSignal()
    export_requested = pyqtSignal()
    split_province_requested = pyqtSignal()  # 切割选中省份
    lasso_province_toggled = pyqtSignal(bool)  # 扩张工具开关
    merge_mode_toggled = pyqtSignal(bool)      # 合并模式开关

    # State / Country 信号
    auto_states_requested = pyqtSignal(int)       # per_state count
    state_selected = pyqtSignal(int)              # state_id
    state_property_changed = pyqtSignal(int, str, object)  # (state_id, prop_name, value)
    state_detail_requested = pyqtSignal(int)      # state_id — 打开详情对话框
    create_country_requested = pyqtSignal()
    quick_create_country_requested = pyqtSignal(str, str, str)  # (tag, name, party)
    country_selected = pyqtSignal(str)            # tag
    country_property_changed = pyqtSignal(str, str, object)  # (tag, prop_name, value)
    country_color_change_requested = pyqtSignal(str)  # tag — 请求更改国家颜色

    # 河流信号
    river_type_changed = pyqtSignal(int)          # 河流类型索引
    validate_river_requested = pyqtSignal()       # 验证河流

    # 后勤信号 (Phase 1)
    open_adjacency_dialog_requested = pyqtSignal()
    open_railway_list_requested = pyqtSignal()
    logistics_railway_level_changed = pyqtSignal(int)
    logistics_railway_draw_toggled = pyqtSignal(bool)
    logistics_supply_pick_toggled = pyqtSignal(bool)

    # 大陆分区信号
    continent_pick_toggled = pyqtSignal(bool)
    continent_add_requested = pyqtSignal(str)
    continent_rename_requested = pyqtSignal(int, str)
    continent_remove_requested = pyqtSignal(int)

    # 战略区域信号
    strategic_region_auto_requested = pyqtSignal()
    strategic_region_selected = pyqtSignal(int)
    strategic_region_new_requested = pyqtSignal()
    strategic_region_delete_requested = pyqtSignal()
    strategic_region_name_changed = pyqtSignal(str)
    strategic_region_weather_changed = pyqtSignal(str)
    strategic_region_naval_changed = pyqtSignal(str)
    strategic_region_pick_toggled = pyqtSignal(bool)

    # 总览贴图信号
    colormap_color_changed = pyqtSignal(str, int, int, int)  # (attr, r, g, b)
    colormap_reset_requested = pyqtSignal()

    # 地图配置信号
    default_map_river_changed = pyqtSignal(int)
    default_map_tree_add_requested = pyqtSignal()
    default_map_tree_del_requested = pyqtSignal()
    default_map_tree_reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self.setMaximumWidth(500)
        self.resize(320, self.height())
        self.setStyleSheet(f"background: {_BG};")
        self._init_ui()

    # ── UI 构建 ───────────────────────────────────────────
    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 分组折叠模式栏 (竖列大按钮, 无 emoji)
        self._mode_tabs = _GroupedModeBar([
            ("地图绘制", [
                ("land", "陆地与海洋"),
                ("province", "省份"),
                ("terrain", "地形"),
                ("height", "高度"),
                ("river", "河流"),
            ]),
            ("区域管理", [
                ("state", "州"),
                ("country", "国家"),
                ("continent", "大洲"),
                ("strategic_region", "战略区"),
            ]),
            ("后勤与配置", [
                ("logistics", "后勤系统"),
                ("colormap", "总览贴图"),
                ("default_map", "地图配置"),
            ]),
        ])
        self._mode_tabs.mode_changed.connect(self._on_mode_changed)
        root.addWidget(self._mode_tabs)

        # 堆叠容器
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent; border: none;")
        root.addWidget(self._stack, 1)

        # 按 mode_id 顺序加 page
        self._pages: dict[str, QWidget] = {}
        _page_builders = [
            ("land", self._build_land_page),
            ("province", self._build_province_page),
            ("terrain", self._build_terrain_page),
            ("height", self._build_height_page),
            ("river", self._build_river_page),
            ("state", self._build_state_page),
            ("country", self._build_country_page),
            ("continent", self._build_continent_page),
            ("strategic_region", self._build_strategic_region_page),
            ("logistics", self._build_logistics_page),
            ("colormap", self._build_colormap_page),
            ("default_map", self._build_default_map_page),
        ]
        self._mode_index: dict[str, int] = {}
        for i, (mode_id, builder) in enumerate(_page_builders):
            page = builder()
            self._stack.addWidget(page)
            self._pages[mode_id] = page
            self._mode_index[mode_id] = i
        self._stack.setCurrentIndex(0)

        # 底部固定区域
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {_BORDER}; margin: 0;")
        root.addWidget(sep)

        export_btn = QPushButton("导出 MOD")
        export_btn.setStyleSheet(_SUCCESS_BTN_STYLE)
        export_btn.clicked.connect(self.export_requested.emit)
        root.addWidget(export_btn)

    # ── Land 页 ───────────────────────────────────────────
    def _build_land_page(self) -> QWidget:
        from features.map.land.page import build_page
        return build_page(self)

    # ── Logistics 页 (Phase 1) ────────────────────────────
    def _build_logistics_page(self) -> QWidget:
        from features.map.logistics.page import build_page
        return build_page(self)

    # ── Continent 页 (从菜单弹窗迁来) ────────────────────
    def _build_continent_page(self) -> QWidget:
        from features.map.continent.page import build_page
        return build_page(self)

    # ── Strategic Region 页 (从菜单弹窗迁来) ─────────────
    def _build_strategic_region_page(self) -> QWidget:
        from features.map.strategic_region.page import build_page
        return build_page(self)

    # ── Colormap 页 (从菜单弹窗迁来) ─────────────────────
    def _build_colormap_page(self) -> QWidget:
        from features.map.colormap.page import build_page
        return build_page(self)

    # ── Default Map 页 (从菜单弹窗迁来) ──────────────────
    def _build_default_map_page(self) -> QWidget:
        from features.map.default_map.page import build_page
        return build_page(self)


    # ── Terrain 页 ────────────────────────────────────────
    def _build_terrain_page(self) -> QWidget:
        from features.map.terrain.page import build_page
        return build_page(self)


    # ── Height 页 ─────────────────────────────────────────
    def _build_height_page(self) -> QWidget:
        from features.map.height.page import build_page
        return build_page(self)


    # ── Province 页 ───────────────────────────────────────
    def _build_province_page(self) -> QWidget:
        from features.map.province.page import build_page
        return build_page(self)


    # ── State 页 ──────────────────────────────────────────
    def _build_state_page(self) -> QWidget:
        from features.map.state.page import build_page
        return build_page(self)


    def _on_state_detail_clicked(self) -> None:
        """请求打开当前选中 state 的详情对话框."""
        sid = getattr(self, "_current_state_id", 0)
        if sid > 0:
            self.state_detail_requested.emit(sid)

    # ── Country 页 ────────────────────────────────────────
    def _build_country_page(self) -> QWidget:
        from features.map.country.page import build_page
        return build_page(self)


    # ── River 页 ────────────────────────────────────────
    def _build_river_page(self) -> QWidget:
        from features.map.river.page import build_page
        return build_page(self)


    # ── 辅助：创建分组 ───────────────────────────────────
    def _make_section(self, title: str) -> QGroupBox:
        box = QGroupBox(title)
        box.setLayout(QVBoxLayout())
        box.layout().setContentsMargins(8, 8, 8, 8)
        box.layout().setSpacing(4)
        box.setStyleSheet(_SECTION_STYLE)
        return box

    # ── 属性 ──────────────────────────────────────────────
    @property
    def ref_opacity_slider(self) -> QSlider:
        return self._ref_opacity_slider

    @property
    def mode_tabs(self) -> _GroupedModeBar:
        return self._mode_tabs

    # ── 槽函数 ────────────────────────────────────────────
    def _on_mode_changed(self, mode: str) -> None:
        idx = self._mode_index.get(mode, 0)
        self._stack.setCurrentIndex(idx)
        # 切换模式时自动设工具为 brush（省份/state/country 模式除外）
        if mode not in ("province", "state", "country"):
            self.tool_changed.emit("brush")
        self.mode_changed.emit(mode)

    def _on_river_brush(self, size: int) -> None:
        self._river_brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def _on_country_color_clicked(self) -> None:
        """点击颜色块弹出颜色选择器"""
        tag = self._country_tag_label.text()
        if tag and tag != "—":
            self.country_color_change_requested.emit(tag)

    def _on_land_brush(self, size: int) -> None:
        self._land_brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def _on_terrain_brush(self, size: int) -> None:
        self._terrain_brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def _on_height_brush(self, size: int) -> None:
        self._height_brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def _on_height_value(self, value: int) -> None:
        self._height_value_label.setText(str(value))
        self.height_value_changed.emit(value)

    def _apply_height_preset(self, value: int) -> None:
        self._height_slider.setValue(value)

    def _on_tile_click(self, tile_type: int) -> None:
        self.tile_type_changed.emit(tile_type)
        # 自动切换到画笔工具
        for btn in self._land_tool_group.buttons():
            if btn.property("tool_id") == "brush":
                btn.setChecked(True)
                self.tool_changed.emit("brush")
                break

    def _on_generate_provinces(self) -> None:
        count = self._province_count_spin.value()
        self.generate_provinces_requested.emit(count)

    # ── State 槽函数 ──────────────────────────────────────
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

    # ── Country 槽函数 ────────────────────────────────────
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

    # ── 公共方法 ──────────────────────────────────────────
    def update_province_info(
        self, pid: int, ptype: str, terrain: str, pixels: int, coastal: bool
    ) -> None:
        """更新省份信息面板"""
        self._prov_labels["id"].setText(str(pid))
        self._prov_labels["type"].setText(ptype)
        self._prov_labels["terrain"].setText(terrain)
        self._prov_labels["pixels"].setText(str(pixels))
        self._prov_labels["coastal"].setText("是" if coastal else "否")

    def update_state_list(self, states: list[tuple[int, str]]) -> None:
        """刷新 State 列表，items 为 (id, name)"""
        self._state_list.clear()
        for state_id, name in states:
            item = QListWidgetItem(f"[{state_id}] {name}")
            item.setData(Qt.UserRole, state_id)
            self._state_list.addItem(item)

    def update_country_list(self, countries: list[tuple[str, str, tuple]]) -> None:
        """刷新国家列表，items 为 (tag, name, color)"""
        self._country_list.clear()
        for tag, name, color in countries:
            item = QListWidgetItem(f"[{tag}] {name}")
            item.setData(Qt.UserRole, tag)
            r, g, b = color
            item.setForeground(QBrush(QColor(r, g, b)))
            self._country_list.addItem(item)

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

        self._country_capital_label.setText(capital_name if capital_name else "未设置")
