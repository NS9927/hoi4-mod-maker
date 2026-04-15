"""
工具面板 — 暗色主题，12 种编辑模式，模式切换标签页

各页面已解耦为独立 QWidget 类, ToolPanel 负责:
1. 实例化各 page 并加入 QStackedWidget
2. 转发 page 信号到自身同名信号 (保持 MainWindow 连接不变)
3. 转发公共更新方法到对应 page
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QButtonGroup,
    QFrame, QStackedWidget, QScrollArea,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal

from data.constants import BRUSH_DEFAULT
from ui.i18n import tr

# 色板 / 样式常量从统一位置 import
from ui.styles import (
    _BG, _INPUT_BG, _BORDER, _TEXT, _ACCENT,
    _SECTION_STYLE, _SUCCESS_BTN_STYLE,
)


# ── 分组折叠模式栏 ─────────────────────────────────────────
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
    """分组折叠模式导航栏."""
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
            header = QPushButton(f"▼  {group_name}")
            header.setStyleSheet(_GROUP_HEADER_STYLE)
            header.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(header)

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

            header.setProperty("group_name", group_name)
            header.setProperty("collapsed", False)
            header.clicked.connect(
                lambda checked=False, h=header, c=container: self._toggle_group(h, c)
            )

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
            header.setText(header.text().replace("▶ ", "▼ "))
            header.setProperty("collapsed", False)
        else:
            container.hide()
            header.setText(header.text().replace("▼ ", "▶ "))
            header.setProperty("collapsed", True)


# ── 主面板 ────────────────────────────────────────────────
class ToolPanel(QWidget):
    """左侧工具面板 — 12 种模式, 信号转发到各 page"""

    # 信号 (保持与 MainWindow 的连接不变)
    mode_changed = pyqtSignal(str)
    tool_changed = pyqtSignal(str)
    tile_type_changed = pyqtSignal(int)
    brush_size_changed = pyqtSignal(int)
    terrain_index_changed = pyqtSignal(int)
    terrain_brush_mode_changed = pyqtSignal(bool)
    height_value_changed = pyqtSignal(int)
    generate_provinces_requested = pyqtSignal(int)
    validate_requested = pyqtSignal()
    quick_init_requested = pyqtSignal()
    auto_terrain_requested = pyqtSignal()
    terrain_brush_size_changed = pyqtSignal(int)
    terrain_soft_edge_changed = pyqtSignal(bool)
    auto_height_requested = pyqtSignal()
    smooth_height_requested = pyqtSignal()
    export_requested = pyqtSignal()
    split_province_requested = pyqtSignal()
    lasso_province_toggled = pyqtSignal(bool)
    merge_mode_toggled = pyqtSignal(bool)
    regen_mode_toggled = pyqtSignal(bool)
    regen_execute_requested = pyqtSignal()

    # State / Country 信号
    auto_states_requested = pyqtSignal(int)
    state_selected = pyqtSignal(int)
    state_property_changed = pyqtSignal(int, str, object)
    state_detail_requested = pyqtSignal(int)
    batch_create_state_toggled = pyqtSignal(bool)
    batch_create_state_confirmed = pyqtSignal()
    create_country_requested = pyqtSignal()
    quick_create_country_requested = pyqtSignal(str, str, str)
    country_selected = pyqtSignal(str)
    country_property_changed = pyqtSignal(str, str, object)
    country_color_change_requested = pyqtSignal(str)

    # 河流信号
    river_type_changed = pyqtSignal(int)
    validate_river_requested = pyqtSignal()

    # 后勤信号
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
    create_from_states_toggled = pyqtSignal(bool)
    create_from_states_confirmed = pyqtSignal()

    # 总览贴图信号
    colormap_color_changed = pyqtSignal(str, int, int, int)
    colormap_reset_requested = pyqtSignal()

    # 地图配置信号
    default_map_river_changed = pyqtSignal(int)
    default_map_tree_add_requested = pyqtSignal()
    default_map_tree_del_requested = pyqtSignal()
    default_map_tree_reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)
        self.setMaximumWidth(520)
        self.setStyleSheet(f"background: {_BG};")
        self._init_ui()

    # ── UI 构建 ───────────────────────────────────────────
    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 分组折叠模式栏
        self._mode_tabs = _GroupedModeBar([
            (tr("group_map_drawing"), [
                ("land", tr("mode_land")),
                ("province", tr("mode_province")),
                ("height", tr("mode_height")),
                ("terrain", tr("mode_terrain")),
                ("river", tr("mode_river_nav")),
            ]),
            (tr("group_region_mgmt"), [
                ("state", tr("mode_state")),
                ("country", tr("mode_country")),
                ("continent", tr("mode_continent")),
                ("strategic_region", tr("mode_strategic_region")),
            ]),
            (tr("group_logistics_config"), [
                ("logistics", tr("mode_logistics")),
                ("colormap", tr("mode_colormap")),
                ("default_map", tr("mode_default_map")),
            ]),
        ])
        self._mode_tabs.mode_changed.connect(self._on_mode_changed)
        root.addWidget(self._mode_tabs)

        # 页面内容滚动区域 (只包裹 stack，mode_tabs 固定在上方)
        self._page_scroll = QScrollArea()
        self._page_scroll.setWidgetResizable(True)
        self._page_scroll.setFrameShape(QFrame.NoFrame)
        self._page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._page_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent; border: none;")
        self._stack.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self._page_scroll.setWidget(self._stack)
        root.addWidget(self._page_scroll, 1)

        # 创建各页面实例并连接信号
        self._create_pages()

        # 底部固定区域
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {_BORDER}; margin: 0;")
        root.addWidget(sep)

        export_btn = QPushButton(tr("panel_export_btn"))
        export_btn.setStyleSheet(_SUCCESS_BTN_STYLE)
        export_btn.clicked.connect(self.export_requested.emit)
        root.addWidget(export_btn)

    def _create_pages(self) -> None:
        """实例化各 page 类, 加入 stack, 连接信号转发."""
        from features.map.land.page import LandPage
        from features.map.province.page import ProvincePage
        from features.map.terrain.page import TerrainPage
        from features.map.height.page import HeightPage
        from features.map.river.page import RiverPage
        from features.map.state.page import StatePage
        from features.map.country.page import CountryPage
        from features.map.continent.page import ContinentPage
        from features.map.strategic_region.page import StrategicRegionPage
        from features.map.logistics.page import LogisticsPage
        from features.map.colormap.page import ColormapPage
        from features.map.default_map.page import DefaultMapPage

        # 创建实例
        self._land_page = LandPage()
        self._province_page = ProvincePage()
        self._terrain_page = TerrainPage()
        self._height_page = HeightPage()
        self._river_page = RiverPage()
        self._state_page = StatePage()
        self._country_page = CountryPage()
        self._continent_page = ContinentPage()
        self._strategic_region_page = StrategicRegionPage()
        self._logistics_page = LogisticsPage()
        self._colormap_page = ColormapPage()
        self._default_map_page = DefaultMapPage()

        # 按 mode_id 顺序加入 stack
        page_list = [
            ("land", self._land_page),
            ("province", self._province_page),
            ("height", self._height_page),
            ("terrain", self._terrain_page),
            ("river", self._river_page),
            ("state", self._state_page),
            ("country", self._country_page),
            ("continent", self._continent_page),
            ("strategic_region", self._strategic_region_page),
            ("logistics", self._logistics_page),
            ("colormap", self._colormap_page),
            ("default_map", self._default_map_page),
        ]
        self._pages: dict[str, QWidget] = {}
        self._mode_index: dict[str, int] = {}
        for i, (mode_id, page) in enumerate(page_list):
            self._stack.addWidget(page)
            self._pages[mode_id] = page
            self._mode_index[mode_id] = i
        self._stack.setCurrentIndex(0)

        # ── 信号转发 ──
        self._connect_land_signals()
        self._connect_province_signals()
        self._connect_terrain_signals()
        self._connect_height_signals()
        self._connect_river_signals()
        self._connect_state_signals()
        self._connect_country_signals()
        self._connect_continent_signals()
        self._connect_strategic_region_signals()
        self._connect_logistics_signals()
        self._connect_colormap_signals()
        self._connect_default_map_signals()

    def _connect_land_signals(self) -> None:
        p = self._land_page
        p.tool_changed.connect(self.tool_changed)
        p.tile_type_changed.connect(self.tile_type_changed)
        p.brush_size_changed.connect(self.brush_size_changed)
        p.generate_provinces_requested.connect(self.generate_provinces_requested)
        p.validate_requested.connect(self.validate_requested)
        p.quick_init_requested.connect(self.quick_init_requested)

    def _connect_province_signals(self) -> None:
        p = self._province_page
        p.split_province_requested.connect(self.split_province_requested)
        p.lasso_province_toggled.connect(self.lasso_province_toggled)
        p.merge_mode_toggled.connect(self.merge_mode_toggled)
        p.regen_mode_toggled.connect(self.regen_mode_toggled)
        p.regen_execute_requested.connect(self.regen_execute_requested)

    def _connect_terrain_signals(self) -> None:
        p = self._terrain_page
        p.terrain_index_changed.connect(self.terrain_index_changed)
        p.terrain_brush_mode_changed.connect(self.terrain_brush_mode_changed)
        p.terrain_brush_size_changed.connect(self.terrain_brush_size_changed)
        p.terrain_soft_edge_changed.connect(self.terrain_soft_edge_changed)
        p.auto_terrain_requested.connect(self.auto_terrain_requested)

    def _connect_height_signals(self) -> None:
        p = self._height_page
        p.height_value_changed.connect(self.height_value_changed)
        p.auto_height_requested.connect(self.auto_height_requested)
        p.smooth_height_requested.connect(self.smooth_height_requested)

    def _connect_river_signals(self) -> None:
        p = self._river_page
        p.tool_changed.connect(self.tool_changed)
        p.brush_size_changed.connect(self.brush_size_changed)
        p.river_type_changed.connect(self.river_type_changed)
        p.validate_river_requested.connect(self.validate_river_requested)

    def _connect_state_signals(self) -> None:
        p = self._state_page
        p.auto_states_requested.connect(self.auto_states_requested)
        p.state_selected.connect(self.state_selected)
        p.state_property_changed.connect(self.state_property_changed)
        p.state_detail_requested.connect(self.state_detail_requested)
        p.batch_create_state_toggled.connect(self.batch_create_state_toggled)
        p.batch_create_state_confirmed.connect(self.batch_create_state_confirmed)

    def _connect_country_signals(self) -> None:
        p = self._country_page
        p.create_country_requested.connect(self.create_country_requested)
        p.quick_create_country_requested.connect(self.quick_create_country_requested)
        p.country_selected.connect(self.country_selected)
        p.country_property_changed.connect(self.country_property_changed)
        p.country_color_change_requested.connect(self.country_color_change_requested)

    def _connect_continent_signals(self) -> None:
        p = self._continent_page
        p.continent_pick_toggled.connect(self.continent_pick_toggled)
        p.continent_add_requested.connect(self.continent_add_requested)
        p.continent_rename_requested.connect(self.continent_rename_requested)
        p.continent_remove_requested.connect(self.continent_remove_requested)

    def _connect_strategic_region_signals(self) -> None:
        p = self._strategic_region_page
        p.strategic_region_auto_requested.connect(self.strategic_region_auto_requested)
        p.strategic_region_selected.connect(self.strategic_region_selected)
        p.strategic_region_new_requested.connect(self.strategic_region_new_requested)
        p.strategic_region_delete_requested.connect(self.strategic_region_delete_requested)
        p.strategic_region_name_changed.connect(self.strategic_region_name_changed)
        p.strategic_region_weather_changed.connect(self.strategic_region_weather_changed)
        p.strategic_region_naval_changed.connect(self.strategic_region_naval_changed)
        p.strategic_region_pick_toggled.connect(self.strategic_region_pick_toggled)
        p.create_from_states_toggled.connect(self.create_from_states_toggled)
        p.create_from_states_confirmed.connect(self.create_from_states_confirmed)

    def _connect_logistics_signals(self) -> None:
        p = self._logistics_page
        p.open_adjacency_dialog_requested.connect(self.open_adjacency_dialog_requested)
        p.open_railway_list_requested.connect(self.open_railway_list_requested)
        p.logistics_railway_level_changed.connect(self.logistics_railway_level_changed)
        p.logistics_railway_draw_toggled.connect(self.logistics_railway_draw_toggled)
        p.logistics_supply_pick_toggled.connect(self.logistics_supply_pick_toggled)

    def _connect_colormap_signals(self) -> None:
        p = self._colormap_page
        p.colormap_color_changed.connect(self.colormap_color_changed)
        p.colormap_reset_requested.connect(self.colormap_reset_requested)

    def _connect_default_map_signals(self) -> None:
        p = self._default_map_page
        p.default_map_river_changed.connect(self.default_map_river_changed)
        p.default_map_tree_add_requested.connect(self.default_map_tree_add_requested)
        p.default_map_tree_del_requested.connect(self.default_map_tree_del_requested)
        p.default_map_tree_reset_requested.connect(self.default_map_tree_reset_requested)

    # ── 属性 (保持与 MainWindow 的兼容) ──────────────────────
    @property
    def ref_opacity_slider(self) -> QSlider:
        return self._land_page._ref_opacity_slider

    @property
    def mode_tabs(self) -> _GroupedModeBar:
        return self._mode_tabs

    # 参考图控件 — 暴露给 MainWindow 直连画布
    @property
    def _vanilla_ref_opacity_slider(self) -> QSlider:
        return self._land_page._vanilla_ref_opacity_slider

    @property
    def _vanilla_ref_toggle(self) -> QPushButton:
        return self._land_page._vanilla_ref_toggle

    @property
    def _ref_scale_slider(self) -> QSlider:
        return self._land_page._ref_scale_slider

    @property
    def _ref_fit_btn(self) -> QPushButton:
        return self._land_page._ref_fit_btn

    @property
    def _ref_toggle(self) -> QPushButton:
        return self._land_page._ref_toggle

    # 快速创建颜色 — 外部读取
    @property
    def _quick_create_color(self) -> tuple:
        return self._country_page._quick_create_color

    # 后勤状态标签 — 外部直接更新
    @property
    def _logi_adj_status(self) -> QLabel:
        return self._logistics_page._logi_adj_status

    @property
    def _logi_rail_status(self) -> QLabel:
        return self._logistics_page._logi_rail_status

    @property
    def _logi_sup_status(self) -> QLabel:
        return self._logistics_page._logi_sup_status

    @property
    def _logi_rail_draw_btn(self) -> QPushButton:
        return self._logistics_page._logi_rail_draw_btn

    @property
    def _logi_sup_toggle_btn(self) -> QPushButton:
        return self._logistics_page._logi_sup_toggle_btn

    @property
    def _logi_rail_level(self):
        return self._logistics_page._logi_rail_level

    # 大陆列表/拾取/状态 — 外部直接访问
    @property
    def _continent_list(self):
        return self._continent_page._continent_list

    @property
    def _continent_pick_btn(self):
        return self._continent_page._continent_pick_btn

    @property
    def _continent_status(self):
        return self._continent_page._continent_status

    # 战略区域 — 外部直接访问
    @property
    def _sr_list(self):
        return self._strategic_region_page._sr_list

    @property
    def _sr_name_edit(self):
        return self._strategic_region_page._sr_name_edit

    @property
    def _sr_weather_combo(self):
        return self._strategic_region_page._sr_weather_combo

    @property
    def _sr_naval_combo(self):
        return self._strategic_region_page._sr_naval_combo

    @property
    def _sr_prov_count(self):
        return self._strategic_region_page._sr_prov_count

    @property
    def _sr_pick_btn(self):
        return self._strategic_region_page._sr_pick_btn

    # Colormap swatches — 外部通过旧名访问
    @property
    def _colormap_land_swatch(self):
        return self._colormap_page._swatches["land"]

    @property
    def _colormap_sea_swatch(self):
        return self._colormap_page._swatches["sea"]

    @property
    def _colormap_lake_swatch(self):
        return self._colormap_page._swatches["lake"]

    # Default map — 外部直接访问
    @property
    def _dm_river_max(self):
        return self._default_map_page._dm_river_max

    @property
    def _dm_tree_list(self):
        return self._default_map_page._dm_tree_list

    # Province 合并/扩张按钮 — 外部访问
    @property
    def _merge_btn(self):
        return self._province_page._merge_btn

    @property
    def _expand_btn(self):
        return self._province_page._expand_btn

    @property
    def _province_hint(self):
        return self._province_page._province_hint

    # ── 槽函数 ────────────────────────────────────────────
    def _on_mode_changed(self, mode: str) -> None:
        idx = self._mode_index.get(mode, 0)
        self._stack.setCurrentIndex(idx)
        # 切换模式时自动设工具为 brush（省份/state/country 模式除外）
        if mode not in ("province", "state", "country"):
            self.tool_changed.emit("brush")
        self.mode_changed.emit(mode)

    # ── 公共方法 (转发到对应 page) ────────────────────────
    def update_province_info(
        self, pid: int, ptype: str, terrain: str, pixels: int, coastal: bool
    ) -> None:
        """更新省份信息面板"""
        self._province_page.update_province_info(pid, ptype, terrain, pixels, coastal)

    def update_state_list(self, states: list[tuple[int, str]]) -> None:
        """刷新 State 列表"""
        self._state_page.update_state_list(states)

    def update_state_info(self, name: str, manpower: int, category: str) -> None:
        """填充 State 属性字段"""
        self._state_page.update_state_info(name, manpower, category)

    def update_country_list(self, countries: list[tuple[str, str, tuple]]) -> None:
        """刷新国家列表"""
        self._country_page.update_country_list(countries)

    def update_country_info(
        self, tag: str, name: str, party: str, color: tuple, capital_name: str
    ) -> None:
        """填充国家属性字段"""
        self._country_page.update_country_info(tag, name, party, color, capital_name)
