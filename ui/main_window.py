"""
主窗口 — 暗色主题，串联工具面板、画布、菜单栏、状态栏
支持6种编辑模式：大陆/省份/地形/高度/State/国家
"""
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QMessageBox,
    QHBoxLayout, QWidget, QLabel, QApplication,
    QInputDialog, QColorDialog,
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QKeySequence, QColor


class _GenerateThread(QThread):
    """后台线程生成省份，避免阻塞 UI"""
    finished = pyqtSignal(object, int)  # (province_map, count)
    error = pyqtSignal(str)

    def __init__(self, tile_map, count, province_map=None, incremental=False):
        super().__init__()
        self._tile_map = tile_map.copy()
        self._count = count
        self._province_map = province_map.copy() if province_map is not None else None
        self._incremental = incremental

    def run(self):
        try:
            if self._incremental and self._province_map is not None:
                from domain.generators.province import generate_provinces_incremental
                pm, cnt = generate_provinces_incremental(
                    self._tile_map, self._province_map
                )
            else:
                from domain.generators.province import generate_provinces
                pm, cnt = generate_provinces(self._tile_map, self._count)
            self.finished.emit(pm, cnt)
        except Exception as e:
            self.error.emit(str(e))

class _ValidateThread(QThread):
    """后台线程验证省份，避免阻塞 UI"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, tile_map, province_map):
        super().__init__()
        self._tile_map = tile_map.copy()
        self._province_map = province_map.copy()

    def run(self):
        try:
            from domain.validators.province import validate_provinces
            results = validate_provinces(self._tile_map, self._province_map)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


from ui.canvas_widget import MapCanvas
from ui.tool_panel import ToolPanel
# DARK_STYLESHEET 不再使用, 全局主题由 main.py 的 qdarktheme 接管
from ui.i18n import tr, set_language, get_language
from data.constants import (
    MAP_WIDTH, MAP_HEIGHT, DEFAULT_PROVINCES,
    TILE_SEA, TILE_LAND, TILE_LAKE,
    OCEAN_HEIGHT, LAND_BASE_HEIGHT, SEA_LEVEL,
    DEFAULT_MOD_OUTPUT_PATH,
)
from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX, DEFAULT_TERRAIN_FOR_TILE
from domain.managers.state import StateManager
from domain.managers.country import CountryManager
from domain.managers.continent import ContinentManager
from domain.undo_manager import UndoManager


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setMinimumSize(1200, 700)
        # 全局主题由 main.py 的 qdarktheme 接管, 不再设 setStyleSheet

        # State / Country / Continent 管理器
        self._state_mgr = StateManager()
        self._country_mgr = CountryManager()
        self._continent_mgr = ContinentManager()
        self._undo_mgr = UndoManager(max_steps=30)

        # 后勤管理器 (Phase 1 + A6 adjacency_rules)
        from domain.managers.adjacency import AdjacencyManager
        from domain.managers.railway import RailwayManager
        from domain.managers.supply_node import SupplyNodeManager
        from domain.managers.adjacency_rule import AdjacencyRuleManager
        from domain.managers.strategic_region import StrategicRegionManager
        self._adjacency_mgr = AdjacencyManager()
        self._railway_mgr = RailwayManager()
        self._supply_mgr = SupplyNodeManager()
        self._adjacency_rule_mgr = AdjacencyRuleManager()
        self._strategic_region_mgr = StrategicRegionManager()

        # 战略总览贴图设置 (A2)
        from domain.managers.colormap_settings import ColormapSettings
        self._colormap_settings = ColormapSettings.default()

        # default.map 配置 (A3)
        from domain.managers.default_map_settings import DefaultMapSettings
        self._default_map_settings = DefaultMapSettings.default()

        # 当前选中的 State / Country
        self._selected_state_id = 0
        self._selected_country_tag = ""
        self._merge_first_pid = 0  # 省份合并：第一次点击记录的省份ID
        self._province_merge_mode = False  # 合并模式开关

        # 大陆编辑器状态
        self._continent_dialog = None
        self._continent_pick_on = False
        self._continent_pick_index = -1

        # 后勤编辑器状态
        self._adjacency_dialog = None
        self._railway_dialog = None
        self._adjacency_rule_dialog = None
        self._strategic_region_dialog = None
        self._strategic_region_pick_on = False
        self._strategic_region_pick_rid = 0
        self._logistics_pick_target: str | None = None  # 'adj_from'/'adj_to'/'adj_through'/'supply'/'rule_required'/'rule_icon'
        self._logistics_railway_draw_on = False
        self._logistics_railway_level = 3
        self._logistics_railway_draft: list[int] = []

        self._init_ui()
        self._init_menu()
        self._init_statusbar()
        self._connect_signals()

        QTimer.singleShot(100, self._canvas.fit_in_view)

    # ────────────────────── UI 初始化 ──────────────────────

    def _init_ui(self) -> None:
        from PyQt5.QtWidgets import QSplitter

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(
            "QSplitter::handle { background: #3a3a4a; width: 3px; }"
        )

        self._tool_panel = ToolPanel()
        splitter.addWidget(self._tool_panel)

        self._canvas = MapCanvas()
        splitter.addWidget(self._canvas)

        # 初始比例: 侧边栏 320, 画布占剩余
        splitter.setSizes([320, 1200])
        splitter.setStretchFactor(0, 0)  # 侧边栏不自动拉伸
        splitter.setStretchFactor(1, 1)  # 画布自动拉伸

        self.setCentralWidget(splitter)

    def _init_menu(self) -> None:
        menubar = self.menuBar()

        # 文件
        file_menu = menubar.addMenu(tr("menu_file"))
        self._add_action(file_menu, tr("action_new"), self._on_new_project, QKeySequence.StandardKey.New)
        self._add_action(file_menu, "打开项目", self._on_open_project, "Ctrl+O")
        self._add_action(file_menu, "保存项目", self._on_save_project, "Ctrl+S")
        file_menu.addSeparator()
        self._add_action(file_menu, tr("action_import_image"), self._on_import_image, "Ctrl+I")
        self._add_action(file_menu, "加载原版地图参考", self._on_load_vanilla_ref)
        self._add_action(file_menu, "从图片提取陆海...", self._on_import_landmask, "Ctrl+Shift+I")
        self._add_action(file_menu, tr("action_export_mod"), self._on_export_mod, "Ctrl+E")
        self._add_action(file_menu, "测试导出（最小MOD）", self._on_test_export, "Ctrl+T")
        file_menu.addSeparator()
        self._add_action(file_menu, tr("action_exit"), self.close, QKeySequence.StandardKey.Quit)

        # 编辑
        edit_menu = menubar.addMenu(tr("menu_edit"))
        self._undo_action = self._add_action(edit_menu, tr("action_undo"), self._on_undo, "Ctrl+Z")
        self._redo_action = self._add_action(edit_menu, tr("action_redo"), self._on_redo, "Ctrl+Y")
        # 框选放大已合并到 Land 模式的"变换"工具

        # 视图
        view_menu = menubar.addMenu(tr("menu_view"))
        self._add_action(view_menu, tr("action_zoom_fit"), self._canvas.fit_in_view, "Ctrl+0")
        act_ref = QAction(tr("action_show_ref"), self)
        act_ref.setCheckable(True)
        act_ref.setChecked(True)
        act_ref.triggered.connect(self._canvas.toggle_ref_image)
        view_menu.addAction(act_ref)

        # 工具
        tools_menu = menubar.addMenu(tr("menu_tools"))
        self._add_action(tools_menu, tr("action_generate_provinces"), lambda: self._on_generate_provinces(DEFAULT_PROVINCES), "Ctrl+G")
        self._add_action(tools_menu, tr("action_validate"), self._on_validate, "Ctrl+Shift+V")
        # 大陆/总览贴图/地图配置/adjacency rules/战略区 已迁到侧边栏 page, 不再菜单弹窗

        # 设置
        settings_menu = menubar.addMenu(tr("menu_settings"))
        self._add_action(settings_menu, tr("action_language"), self._on_toggle_language)

        # 帮助
        help_menu = menubar.addMenu(tr("menu_help"))
        self._add_action(help_menu, tr("action_about"), self._on_about)

    def _add_action(self, menu, text, slot, shortcut=None):
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut) if isinstance(shortcut, str) else shortcut)
        act.triggered.connect(slot)
        menu.addAction(act)
        return act

    def _init_statusbar(self) -> None:
        self._status_pos = QLabel(tr("status_pos", 0, 0))
        self._status_zoom = QLabel(tr("status_zoom", 1.0))
        self._status_provinces = QLabel(tr("status_provinces", 0))
        self._status_mode = QLabel("模式: 大陆")
        self._status_info = QLabel(tr("status_ready"))

        sb = self.statusBar()
        sb.addWidget(self._status_info, stretch=1)
        sb.addPermanentWidget(self._status_mode)
        sb.addPermanentWidget(self._status_provinces)
        sb.addPermanentWidget(self._status_pos)
        sb.addPermanentWidget(self._status_zoom)

    # ────────────────────── 信号连接 ──────────────────────

    def _connect_signals(self) -> None:
        tp = self._tool_panel
        cv = self._canvas

        # 模式切换
        tp.mode_changed.connect(self._on_mode_changed)

        # 工具/画笔
        tp.tool_changed.connect(cv.set_tool)
        tp.tile_type_changed.connect(cv.set_tile_type)
        tp.brush_size_changed.connect(cv.set_brush_size)
        tp.terrain_index_changed.connect(cv.set_terrain_index)
        tp.terrain_brush_mode_changed.connect(cv.set_terrain_brush_mode)
        tp.height_value_changed.connect(cv.set_height_value)

        # 原版地图参考透明度 + 显示/隐藏
        tp._vanilla_ref_opacity_slider.valueChanged.connect(
            lambda v: cv.set_vanilla_ref_opacity(v / 100.0)
        )
        tp._vanilla_ref_toggle.toggled.connect(
            lambda on: cv.toggle_vanilla_ref(not on)
        )
        # 自定义参考图透明度
        tp.ref_opacity_slider.valueChanged.connect(
            lambda v: cv.set_ref_opacity(v / 100.0)
        )
        # 参考图缩放
        tp._ref_scale_slider.valueChanged.connect(
            lambda v: cv.set_ref_scale(v / 100.0)
        )
        # 参考图铺满 + 显示/隐藏
        tp._ref_fit_btn.clicked.connect(cv.fit_ref_to_map)
        tp._ref_toggle.toggled.connect(
            lambda on: cv.toggle_ref_image(not on)
        )

        # 操作按钮
        tp.generate_provinces_requested.connect(self._on_generate_provinces)
        tp.validate_requested.connect(self._on_validate)
        tp.auto_terrain_requested.connect(self._on_auto_terrain)
        tp.auto_height_requested.connect(self._on_auto_height)
        tp.smooth_height_requested.connect(self._on_smooth_height)
        tp.export_requested.connect(self._on_export_mod)
        tp.split_province_requested.connect(self._on_split_province)
        tp.lasso_province_toggled.connect(self._on_lasso_toggled)
        tp.merge_mode_toggled.connect(self._on_merge_mode_toggled)

        # State / Country 信号
        tp.auto_states_requested.connect(self._on_auto_states)
        tp.state_selected.connect(self._on_state_selected)
        tp.state_property_changed.connect(self._on_state_property_changed)
        tp.state_detail_requested.connect(self._on_state_detail_requested)
        tp.create_country_requested.connect(self._on_create_country)
        tp.quick_create_country_requested.connect(self._on_quick_create_country)
        tp.country_selected.connect(self._on_country_selected)
        tp.country_property_changed.connect(self._on_country_property_changed)
        tp.country_color_change_requested.connect(self._on_country_color_change)

        # 河流信号
        tp.river_type_changed.connect(cv.set_river_type)
        tp.validate_river_requested.connect(self._on_validate_river)

        # 后勤信号 (Phase 1)
        tp.open_adjacency_dialog_requested.connect(self._open_adjacency_dialog)
        tp.open_railway_list_requested.connect(self._open_railway_dialog)
        tp.logistics_railway_level_changed.connect(
            self._on_logistics_railway_level_changed
        )
        tp.logistics_railway_draw_toggled.connect(
            self._on_logistics_railway_draw_toggled
        )
        tp.logistics_supply_pick_toggled.connect(
            self._on_logistics_supply_pick_toggled
        )

        # 大陆分区信号 (从菜单弹窗迁到侧边栏)
        tp.continent_pick_toggled.connect(self._on_continent_pick_toggled)
        tp.continent_add_requested.connect(self._on_continent_add)
        tp.continent_rename_requested.connect(self._on_continent_rename)
        tp.continent_remove_requested.connect(self._on_continent_remove)

        # 战略区域信号
        tp.strategic_region_auto_requested.connect(self._on_sr_auto_generate)
        tp.strategic_region_pick_toggled.connect(self._on_sr_pick_toggled)
        tp.strategic_region_new_requested.connect(self._on_sr_new)
        tp.strategic_region_delete_requested.connect(self._on_sr_delete)
        tp.strategic_region_name_changed.connect(self._on_sr_name_changed)
        tp.strategic_region_weather_changed.connect(self._on_sr_weather_changed)
        tp.strategic_region_naval_changed.connect(self._on_sr_naval_changed)
        tp.strategic_region_selected.connect(self._on_sr_selected)

        # 总览贴图信号
        tp.colormap_color_changed.connect(self._on_colormap_color_changed)
        tp.colormap_reset_requested.connect(self._on_colormap_reset)

        # 地图配置信号
        tp.default_map_river_changed.connect(self._on_dm_river_changed)
        tp.default_map_tree_add_requested.connect(self._on_dm_tree_add)
        tp.default_map_tree_del_requested.connect(self._on_dm_tree_del)
        tp.default_map_tree_reset_requested.connect(self._on_dm_tree_reset)

        # 双击/右键省份
        cv.province_double_clicked.connect(self._on_province_double_clicked)
        cv.province_right_clicked.connect(self._on_province_right_clicked)

        # 画布 → 状态栏
        cv.mouse_moved.connect(
            lambda x, y: self._status_pos.setText(tr("status_pos", x, y))
        )
        cv.zoom_changed.connect(
            lambda z: self._status_zoom.setText(tr("status_zoom", z))
        )

        # 省份点击
        cv.province_clicked.connect(self._on_province_clicked)

        # 大陆模式修改时自动清除省份
        cv.provinces_cleared.connect(self._on_provinces_cleared)

        # 撤销/重做：画笔操作的 begin/end
        cv.stroke_started.connect(self._on_stroke_started)
        cv.stroke_ended.connect(self._on_stroke_ended)

    # ────────────────────── 模式切换 ──────────────────────

    def _on_provinces_cleared(self) -> None:
        self._update_province_count()
        self._status_info.setText("修改大陆数据，省份已清除（需要重新生成）")

    def _on_mode_changed(self, mode: str) -> None:
        # 清理旧模式的所有临时状态（防止残留导致崩溃）
        self._canvas.cleanup_mode_state()
        self._province_merge_mode = False
        self._merge_first_pid = 0

        self._canvas.display_mode = mode
        mode_names = {
            "land": "大陆", "province": "省份", "terrain": "地形",
            "height": "高度", "state": "State", "country": "国家",
            "river": "河流",
        }
        self._status_mode.setText(f"模式: {mode_names.get(mode, mode)}")

        # 切换到 state/country 模式时刷新颜色图
        if mode == "state":
            self._refresh_state_colors()
        elif mode == "country":
            self._refresh_country_colors()

    # ────────────────────── 撤销/重做 ──────────────────────

    def _get_undo_arrays(self) -> dict[str, np.ndarray]:
        """获取当前模式需要跟踪的数组"""
        mode = self._canvas.display_mode
        if mode == "land":
            return {"tile_map": self._canvas.tile_map}
        elif mode == "terrain":
            return {"terrain_map": self._canvas.terrain_map}
        elif mode == "height":
            return {"height_map": self._canvas.height_map}
        elif mode == "province":
            return {"province_map": self._canvas.province_map}
        elif mode == "river":
            return {"river_map": self._canvas.river_map}
        return {}

    def _on_stroke_started(self) -> None:
        """画笔操作开始，记录快照"""
        mode = self._canvas.display_mode
        desc = f"{mode} 绘制"
        self._undo_mgr.begin_stroke(desc, self._get_undo_arrays())

    def _on_stroke_ended(self) -> None:
        """画笔操作结束，保存差异"""
        self._undo_mgr.end_stroke(self._get_undo_arrays())

    def _on_undo(self) -> None:
        """执行撤销"""
        # 如果正在画笔操作中，先结束当前笔画
        if self._undo_mgr._pending is not None:
            self._undo_mgr.end_stroke(self._get_undo_arrays())
        arrays = {
            "tile_map": self._canvas.tile_map,
            "province_map": self._canvas.province_map,
            "terrain_map": self._canvas.terrain_map,
            "height_map": self._canvas.height_map,
            "river_map": self._canvas.river_map,
        }
        result = self._undo_mgr.undo(arrays)
        if result is None:
            self._status_info.setText("没有可撤销的操作")
            return
        self._apply_undo_result(result)
        self._status_info.setText("已撤销")

    def _on_redo(self) -> None:
        """执行重做"""
        if self._undo_mgr._pending is not None:
            self._undo_mgr.end_stroke(self._get_undo_arrays())
        arrays = {
            "tile_map": self._canvas.tile_map,
            "province_map": self._canvas.province_map,
            "terrain_map": self._canvas.terrain_map,
            "height_map": self._canvas.height_map,
            "river_map": self._canvas.river_map,
        }
        result = self._undo_mgr.redo(arrays)
        if result is None:
            self._status_info.setText("没有可重做的操作")
            return
        self._apply_undo_result(result)
        self._status_info.setText("已重做")

    def _apply_undo_result(self, result: dict[str, np.ndarray]) -> None:
        """应用撤销/重做结果"""
        if "tile_map" in result:
            self._canvas.tile_map = result["tile_map"]
        if "province_map" in result:
            self._canvas.province_map = result["province_map"]
        if "terrain_map" in result:
            self._canvas.terrain_map = result["terrain_map"]
        if "height_map" in result:
            self._canvas.height_map = result["height_map"]
        if "river_map" in result:
            self._canvas.river_map = result["river_map"]
        self._canvas.refresh_display()
        self._update_province_count()

    # ────────────────────── 省份生成与验证 ──────────────────

    def _on_generate_provinces(self, count: int) -> None:
        incremental = False
        has_provinces = int(self._canvas.province_map.max()) > 0

        if has_provinces:
            # 已有省份，让用户选择
            reply = QMessageBox.question(
                self, "省份生成模式",
                "当前地图已有省份。\n\n"
                "点击 Yes = 只生成新区域的省份（保留已有）\n"
                "点击 No = 重新生成全部省份",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            incremental = (reply == QMessageBox.StandardButton.Yes)

        self._status_info.setText("正在生成省份...（后台运行中，请稍候）")
        QApplication.processEvents()

        self._gen_thread = _GenerateThread(
            self._canvas.tile_map, count,
            province_map=self._canvas.province_map if incremental else None,
            incremental=incremental,
        )
        self._gen_thread.finished.connect(self._on_generate_done)
        self._gen_thread.error.connect(self._on_generate_error)
        self._gen_thread.start()

    def _on_generate_done(self, province_map, count: int) -> None:
        self._canvas.province_map = province_map
        self._update_province_count()
        self._status_info.setText(f"省份生成完成: {count} 个")

    def _on_generate_error(self, msg: str) -> None:
        QMessageBox.critical(self, tr("dlg_error"), msg)
        self._status_info.setText(tr("status_ready"))

    def _on_validate(self) -> None:
        self._status_info.setText(tr("status_validating"))
        QApplication.processEvents()

        # 在后台线程运行验证，避免卡死UI
        self._validate_thread = _ValidateThread(
            self._canvas.tile_map, self._canvas.province_map
        )
        self._validate_thread.finished.connect(self._on_validate_done)
        self._validate_thread.error.connect(self._on_validate_error)
        self._validate_thread.start()

    def _on_validate_done(self, results: dict) -> None:
        self._show_validation_results(results)
        self._status_info.setText(tr("status_ready"))

    def _on_validate_error(self, msg: str) -> None:
        QMessageBox.critical(self, tr("dlg_error"), msg)
        self._status_info.setText(tr("status_ready"))

    def _show_validation_results(self, results: dict) -> None:
        """诊断对话框：可点击的问题列表，双击跳转到画布对应位置"""
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
            QLabel, QDialogButtonBox,
        )
        from PyQt5.QtCore import Qt as _Qt

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("validate_title"))
        dlg.resize(520, 520)
        v = QVBoxLayout(dlg)

        # 顶部统计
        province_count = int(self._canvas.province_map.max())
        coastal_count = results.get("coastal_mismatch", 0)
        warn = results.get("count_warning", "")
        info_text = f"省份总数：{province_count}    沿海：{coastal_count}"
        if warn:
            info_text += f"\n⚠ {warn}"
        v.addWidget(QLabel(info_text))

        # 问题列表
        v.addWidget(QLabel("双击问题项跳转到地图对应位置："))
        list_w = QListWidget()
        v.addWidget(list_w)

        # 每个 item 存 (跳转类型, 数据)：("xy", (x,y)) 或 ("pid", pid)
        def add_item(text: str, jump_type: str, data) -> None:
            it = QListWidgetItem(text)
            it.setData(_Qt.ItemDataRole.UserRole, (jump_type, data))
            list_w.addItem(it)

        # X-crossings：每个位置一项（最多前 50 个，避免列表爆炸）
        x_positions = results.get("x_crossing_positions", [])
        for i, (y, x) in enumerate(x_positions[:50]):
            add_item(f"X-crossing #{i+1} at ({x}, {y})", "xy", (x, y))
        if len(x_positions) > 50:
            add_item(f"... 还有 {len(x_positions)-50} 个 X-crossing 未列出", "none", None)

        # 过小省份
        for pid in results.get("too_small_ids", [])[:50]:
            add_item(f"过小省份 ID={pid}（< 8 像素）", "pid", pid)

        # 不连通省份
        for pid in results.get("not_contiguous_ids", [])[:50]:
            add_item(f"不连通省份 ID={pid}（多个碎片，占用边界配额）", "pid", pid)

        # 过大省份
        for pid in results.get("too_large_ids", [])[:50]:
            add_item(f"过大省份 ID={pid}（TOO LARGE BOX, > 地图 1/8）", "pid", pid)

        # ID gap
        gaps = results.get("id_gaps", [])
        if gaps:
            add_item(f"省份 ID 不连续：缺失 {len(gaps)} 个（导出时自动修复）", "none", None)

        if list_w.count() == 0:
            list_w.addItem("✓ 没有发现任何问题")

        # 双击跳转
        def on_double(item: QListWidgetItem) -> None:
            payload = item.data(_Qt.ItemDataRole.UserRole)
            if not payload:
                return
            jump_type, data = payload
            if jump_type == "xy":
                self._canvas.center_on_pixel(data[0], data[1], zoom=4.0)
            elif jump_type == "pid":
                self._canvas.center_on_province(data)

        list_w.itemDoubleClicked.connect(on_double)

        # 关闭按钮
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        btns.accepted.connect(dlg.accept)
        v.addWidget(btns)
        dlg.exec_()

    # ────────────────────── 省份点击 ──────────────────────

    def _on_province_clicked(self, pid: int) -> None:
        if pid <= 0:
            return
        try:
            self._handle_province_clicked(pid)
        except Exception as e:
            self._status_info.setText(f"操作异常: {e}")
            import traceback
            traceback.print_exc()

    def _handle_province_clicked(self, pid: int) -> None:
        """省份点击的实际处理逻辑，由 _on_province_clicked 包裹 try/except"""
        # 后勤拾取模式优先拦截
        if self._logistics_pick_target is not None:
            self._handle_logistics_pick(pid)
            return
        # 铁路画笔进行中: 追加到草稿
        if self._logistics_railway_draw_on:
            if pid not in self._logistics_railway_draft:
                self._logistics_railway_draft.append(pid)
                self._status_info.setText(
                    f"铁路草稿 ({len(self._logistics_railway_draft)} 省): "
                    f"{' → '.join(str(p) for p in self._logistics_railway_draft[-5:])}"
                )
            return

        # 战略区域拾取模式
        if getattr(self, "_strategic_region_pick_on", False):
            rid = self._strategic_region_pick_rid
            if rid > 0:
                self._strategic_region_mgr.assign_province(pid, rid)
                if self._strategic_region_dialog is not None:
                    self._strategic_region_dialog.notify_assigned(pid)
            return

        # 大陆指派模式优先拦截
        if getattr(self, "_continent_pick_on", False):
            ci = self._continent_pick_index
            if ci >= 0:
                # 只允许陆地省份: 取省份内任意像素的 tile_map 值
                import numpy as _np
                from data.constants import TILE_LAND as _TL
                ys, xs = _np.where(self._canvas.province_map == pid)
                if len(ys) > 0 and int(self._canvas.tile_map[ys[0], xs[0]]) == _TL:
                    self._continent_mgr.assign_province(pid, ci)
                    if self._continent_dialog is not None:
                        self._continent_dialog.notify_assigned(pid)
                else:
                    self._status_info.setText(f"省份 {pid} 不是陆地，跳过")
                return

        # ── 所有模式都先更新省份信息面板 ──
        pm = self._canvas.province_map
        tm = self._canvas.tile_map
        mask = pm == pid
        pixels = int(np.sum(mask))

        tiles = tm[mask]
        land_n = int(np.sum(tiles == TILE_LAND))
        sea_n = int(np.sum(tiles == TILE_SEA))
        lake_n = int(np.sum(tiles == TILE_LAKE))
        if sea_n >= land_n and sea_n >= lake_n:
            ptype = "海洋"
        elif lake_n >= land_n:
            ptype = "湖泊"
        else:
            ptype = "陆地"

        from domain.validators.province import get_coastal_provinces
        coastal = pid in get_coastal_provinces(tm, pm)

        from data.terrain_types import GRAPHICAL_TERRAIN_BY_INDEX
        terrain_data = self._canvas.terrain_map[mask]
        if len(terrain_data) > 0:
            terrain_idx = int(np.bincount(terrain_data).argmax())
            gt = GRAPHICAL_TERRAIN_BY_INDEX.get(terrain_idx)
            terrain_name = gt.name_cn if gt else "未知"
        else:
            terrain_name = "未知"

        self._tool_panel.update_province_info(pid, ptype, terrain_name, pixels, coastal)

        # ── 然后各模式做自己的事 ──
        mode = self._canvas.display_mode

        if mode == "province":
            if self._province_merge_mode:
                if self._merge_first_pid == 0:
                    self._merge_first_pid = pid
                    self._status_info.setText(
                        f"已选中省份 {pid}，点击要合并的目标省份"
                    )
                elif self._merge_first_pid == pid:
                    self._merge_first_pid = 0
                    self._status_info.setText("取消选择，仍在合并模式")
                else:
                    ok = self._canvas.merge_provinces(
                        self._merge_first_pid, pid,
                        state_mgr=self._state_mgr,
                        country_mgr=self._country_mgr,
                    )
                    if ok:
                        self._update_province_count()
                        self._status_info.setText(
                            f"省份 {pid} 已合并到 {self._merge_first_pid}"
                        )
                    else:
                        self._status_info.setText("合并失败")
                    self._merge_first_pid = 0
                    self._province_merge_mode = False
                    self._tool_panel._merge_btn.setChecked(False)
            return

        if mode == "state":
            if self._selected_state_id > 0:
                self._state_mgr.assign_province(pid, self._selected_state_id)
                self._refresh_state_colors()
                state = self._state_mgr.get_state(self._selected_state_id)
                if state:
                    self._tool_panel.update_state_info(
                        state.name, state.manpower, state.category
                    )
                self._status_info.setText(
                    f"省份 {pid} 已分配到 State {self._selected_state_id}"
                )
            return

        if mode == "country":
            if self._selected_country_tag:
                state_id = self._state_mgr.get_state_of_province(pid)
                if state_id > 0:
                    self._country_mgr.assign_state(state_id, self._selected_country_tag)
                    self._refresh_country_colors()
                    self._status_info.setText(
                        f"State {state_id} 已分配给 {self._selected_country_tag}"
                    )
                else:
                    self._status_info.setText("该省份未分配到任何 State")
            return

    # ────────────────────── State 管理 ──────────────────────

    def _on_auto_states(self, per_state: int) -> None:
        """自动分组省份为 State"""
        self._status_info.setText("正在自动分组 State...")
        QApplication.processEvents()

        self._state_mgr.auto_split(
            self._canvas.province_map,
            self._canvas.tile_map,
            per_state,
        )

        self._refresh_state_list()
        self._refresh_state_colors()
        count = len(self._state_mgr.states)
        self._status_info.setText(f"State 分组完成: {count} 个")

    def _on_state_selected(self, state_id: int) -> None:
        """选中某个 State"""
        self._selected_state_id = state_id
        state = self._state_mgr.get_state(state_id)
        if state:
            self._tool_panel.update_state_info(
                state.name, state.manpower, state.category
            )

    def _on_state_property_changed(self, state_id: int, prop: str, value) -> None:
        """State 属性被编辑"""
        state = self._state_mgr.get_state(state_id)
        if not state:
            return
        if prop == "name":
            state.name = str(value)
            self._refresh_state_list()
        elif prop == "manpower":
            state.manpower = int(value)
        elif prop == "category":
            state.category = str(value)

    def _on_state_detail_requested(self, state_id: int) -> None:
        """打开 State 详情对话框 (资源/建筑/核心/宣称)."""
        state = self._state_mgr.get_state(state_id)
        if not state:
            return
        from features.map.state.detail_dialog import StateDetailDialog
        tags = list(self._country_mgr.countries.keys()) if self._country_mgr else []
        dlg = StateDetailDialog(state, tags, parent=self)
        if dlg.exec_() == dlg.Accepted:
            self._refresh_state_list()
            self._status_info.setText(f"State {state_id} 已更新")

    def _refresh_state_list(self) -> None:
        """刷新工具面板中的 State 列表"""
        items = [(sid, s.name) for sid, s in self._state_mgr.states.items()]
        self._tool_panel.update_state_list(items)

    def _refresh_state_colors(self) -> None:
        """重新生成 State 颜色图并设置到画布"""
        if int(self._canvas.province_map.max()) == 0:
            return
        rgb = self._state_mgr.build_state_color_map(self._canvas.province_map)
        self._canvas.set_state_colors(rgb)
        self._refresh_vp_data()

    def _refresh_vp_data(self) -> None:
        """收集所有 State 的 VP 数据并传给画布 (Feature 10)"""
        vp_dict: dict[int, int] = {}
        for state in self._state_mgr.states.values():
            for pid, vp_val in state.victory_points.items():
                if vp_val > 0:
                    vp_dict[pid] = vp_val
        self._canvas.set_vp_data(vp_dict)

    # ────────────────────── Country 管理 ──────────────────

    def _on_create_country(self) -> None:
        """创建新国家"""
        tag, ok = QInputDialog.getText(self, "创建国家", "输入国家 TAG (3个字母):")
        if not ok or not tag:
            return
        tag = tag.upper().strip()[:3]
        if len(tag) != 3 or not tag.isalpha():
            QMessageBox.warning(self, "错误", "TAG 必须是 3 个英文字母")
            return

        name, ok = QInputDialog.getText(self, "创建国家", f"输入国家名称 (TAG: {tag}):")
        if not ok:
            return

        # 弹出颜色选择器
        import random
        default_color = QColor(random.randint(60, 220), random.randint(60, 220), random.randint(60, 220))
        chosen = QColorDialog.getColor(default_color, self, f"选择 {tag} 的颜色")
        if not chosen.isValid():
            return
        color = (chosen.red(), chosen.green(), chosen.blue())

        try:
            self._country_mgr.create_country(tag, name or tag, color)
            self._refresh_country_list()
            self._status_info.setText(f"国家 {tag} 已创建")
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))

    def _on_quick_create_country(self, tag: str, name: str, party: str) -> None:
        """快速创建国家并自动选中，进入领土分配模式"""
        color = getattr(self._tool_panel, '_quick_create_color', (100, 100, 200))
        try:
            country = self._country_mgr.create_country(tag, name, color)
            country.ruling_party = party
            self._refresh_country_list()
            # 自动选中新创建的国家
            self._selected_country_tag = tag
            capital_name = ""
            self._tool_panel.update_country_info(
                tag, name, party, color, capital_name,
            )
            self._status_info.setText(
                f"国家 {tag} ({name}) 已创建，点击 State 分配领土"
            )
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))

    def _on_country_color_change(self, tag: str) -> None:
        """修改国家颜色"""
        country = self._country_mgr.get_country(tag)
        if not country:
            return
        r, g, b = country.color
        current = QColor(r, g, b)
        chosen = QColorDialog.getColor(current, self, f"修改 {tag} 的颜色")
        if not chosen.isValid():
            return
        country.color = (chosen.red(), chosen.green(), chosen.blue())
        self._refresh_country_list()
        self._refresh_country_colors()
        # 更新信息面板
        capital_name = f"省份 {country.capital}" if country.capital > 0 else ""
        self._tool_panel.update_country_info(
            country.tag, country.name, country.ruling_party,
            country.color, capital_name,
        )
        self._status_info.setText(f"{tag} 颜色已修改")

    def _on_country_selected(self, tag: str) -> None:
        """选中某个国家"""
        self._selected_country_tag = tag
        country = self._country_mgr.get_country(tag)
        if country:
            capital_name = f"省份 {country.capital}" if country.capital > 0 else ""
            self._tool_panel.update_country_info(
                country.tag, country.name, country.ruling_party,
                country.color, capital_name,
            )

    def _on_country_property_changed(self, tag: str, prop: str, value) -> None:
        """国家属性被编辑"""
        country = self._country_mgr.get_country(tag)
        if not country:
            return
        if prop == "name":
            country.name = str(value)
            self._refresh_country_list()
        elif prop == "ruling_party":
            self._country_mgr.set_ruling_party(tag, str(value))

    def _refresh_country_list(self) -> None:
        """刷新工具面板中的国家列表"""
        self._tool_panel.update_country_list(self._country_mgr.get_country_list())

    def _refresh_country_colors(self) -> None:
        """重新生成国家颜色图并设置到画布"""
        if int(self._canvas.province_map.max()) == 0:
            return
        rgb = self._country_mgr.build_country_color_map(
            self._canvas.province_map, self._state_mgr
        )
        self._canvas.set_country_colors(rgb)

    # ────────────────────── 扩张工具 ──────────────────

    def _on_merge_mode_toggled(self, on: bool) -> None:
        """开关合并模式。"""
        self._province_merge_mode = on
        self._merge_first_pid = 0
        if on:
            self._status_info.setText("合并模式：点第一个省份，再点第二个")
        else:
            self._status_info.setText("回到查看模式")

    def _on_lasso_toggled(self, on: bool) -> None:
        """启用/禁用扩张工具。"""
        if on:
            self._province_merge_mode = False
            self._merge_first_pid = 0
            from domain.tools import lasso_province  # noqa: F401
            self._canvas.set_framework_tool(
                "lasso_province",
                undo_mgr=self._undo_mgr,
                state_mgr=self._state_mgr,
                country_mgr=self._country_mgr,
            )
            self._status_info.setText(
                "扩张模式：点击省份后拖动扩张"
            )
        else:
            self._canvas.set_framework_tool(None)
            self._status_info.setText("回到查看模式")

    # ────────────────────── 省份切割 ──────────────────

    def _on_split_province(self) -> None:
        """切割当前选中的省份"""
        pid = self._canvas._selected_province_id
        if pid <= 0:
            self._status_info.setText("请先点击选中一个省份")
            return
        ok = self._canvas.split_province(pid)
        if ok:
            self._update_province_count()
            new_id = int(self._canvas.province_map.max())
            self._status_info.setText(f"省份 {pid} 已切割，新省份 ID: {new_id}")
            self._merge_first_pid = 0
        else:
            self._status_info.setText("切割失败（省份太小）")

    # ────────────────────── VP 和首都 ──────────────────

    def _on_province_double_clicked(self, pid: int) -> None:
        """双击省份 → 设置 VP"""
        if pid <= 0:
            return
        sid = self._state_mgr.get_state_of_province(pid)
        if sid == 0:
            QMessageBox.warning(self, "提示", "该省份未分配到任何 State，请先分组")
            return

        value, ok = QInputDialog.getInt(
            self, "设置胜利点",
            f"省份 {pid} 的 VP 分值\n(1=小镇, 5=中等, 10=城市, 20=首都):",
            1, 0, 50, 1,
        )
        if ok:
            if value > 0:
                self._state_mgr.set_vp(pid, value)
                self._status_info.setText(f"省份 {pid} 设为 {value} 分 VP")
            else:
                self._state_mgr.remove_vp(pid)
                self._status_info.setText(f"省份 {pid} VP 已移除")
            self._refresh_vp_data()

    def _on_province_right_clicked(self, pid: int) -> None:
        """右键省份 → 设为当前国家的首都"""
        if pid <= 0 or not self._selected_country_tag:
            if not self._selected_country_tag:
                self._status_info.setText("请先在国家模式下选中一个国家")
            return

        tag = self._selected_country_tag
        self._country_mgr.set_capital(tag, pid)
        country = self._country_mgr.get_country(tag)
        if country:
            capital_name = f"省份 {pid}"
            self._tool_panel.update_country_info(
                country.tag, country.name, country.ruling_party,
                country.color, capital_name,
            )
        self._status_info.setText(f"{tag} 的首都已设为省份 {pid}")

    # ────────────────────── 河流验证 ──────────────────

    def _on_validate_river(self) -> None:
        """验证河流数据并显示结果"""
        from domain.managers.river import validate_rivers
        warnings = validate_rivers(self._canvas.river_map)
        msg = "\n".join(warnings)
        QMessageBox.information(self, "河流验证", msg)

    # ────────────────────── 项目保存/加载 ──────────────────

    def _on_save_project(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "保存项目", "", "HOI4 项目 (*.hoi4proj);;All Files (*)"
        )
        if not path:
            return
        try:
            from services.project_service import save_project
            save_project(path, self._canvas, self._state_mgr,
                         self._country_mgr, self._continent_mgr,
                         adjacency_mgr=self._adjacency_mgr,
                         railway_mgr=self._railway_mgr,
                         supply_mgr=self._supply_mgr,
                         adjacency_rule_mgr=self._adjacency_rule_mgr,
                         strategic_region_mgr=self._strategic_region_mgr)
            self._status_info.setText(f"项目已保存: {path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def _on_open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "打开项目", "", "HOI4 项目 (*.hoi4proj);;All Files (*)"
        )
        if not path:
            return
        try:
            from services.project_service import load_project
            load_project(path, self._canvas, self._state_mgr,
                         self._country_mgr, self._continent_mgr,
                         adjacency_mgr=self._adjacency_mgr,
                         railway_mgr=self._railway_mgr,
                         supply_mgr=self._supply_mgr,
                         adjacency_rule_mgr=self._adjacency_rule_mgr,
                         strategic_region_mgr=self._strategic_region_mgr)
            self._update_province_count()
            self._refresh_state_list()
            self._refresh_country_list()
            self._status_info.setText(f"项目已加载: {path}")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))

    # ────────────────────── 地形自动生成 ──────────────────

    def _on_auto_terrain(self) -> None:
        from services.terrain_service import auto_terrain
        self._status_info.setText("正在生成地形...")
        self.repaint()
        self._canvas.terrain_map = auto_terrain(self._canvas.tile_map)
        self._status_info.setText("地形生成完成")

    def _on_auto_height(self) -> None:
        from services.terrain_service import auto_height
        self._status_info.setText("正在生成高度图...")
        self.repaint()
        self._canvas.height_map = auto_height(self._canvas.tile_map)
        self._status_info.setText("高度图生成完成")

    def _on_smooth_height(self) -> None:
        from services.terrain_service import smooth_height
        self._canvas.height_map = smooth_height(self._canvas.height_map)
        self._status_info.setText("高度图已平滑")

    # ────────────────────── 导出 ──────────────────────────

    def _on_export_mod(self) -> None:
        from services.export_service import validate_before_export, export_mod
        warnings = validate_before_export(
            self._canvas, self._state_mgr, self._country_mgr
        )
        if warnings:
            msg = "发现以下问题:\n\n" + "\n".join(warnings) + "\n\n仍然导出吗？"
            reply = QMessageBox.question(self, "导出验证", msg)
            if reply != QMessageBox.StandardButton.Yes:
                return

        output_dir = QFileDialog.getExistingDirectory(self, tr("export_title"), "")
        if not output_dir:
            return

        self._status_info.setText(tr("status_exporting"))
        self.repaint()

        try:
            report = export_mod(
                output_dir, self._canvas, self._state_mgr,
                self._country_mgr, self._continent_mgr,
                adjacency_mgr=self._adjacency_mgr,
                railway_mgr=self._railway_mgr,
                supply_mgr=self._supply_mgr,
                colormap_settings=self._colormap_settings,
                default_map_settings=self._default_map_settings,
                adjacency_rule_mgr=self._adjacency_rule_mgr,
                strategic_region_mgr=self._strategic_region_mgr,
            )
            # 构建导出报告
            lines = [f"MOD 导出成功！\n路径: {output_dir}\n"]
            if report.stats:
                lines.append("── 统计 ──")
                stat_labels = {
                    "provinces": "省份", "states": "State",
                    "countries": "国家", "files": "文件",
                }
                for k, v in report.stats.items():
                    label = stat_labels.get(k, k)
                    lines.append(f"  {label}: {v}")
            if report.fixed:
                lines.append("\n── 自动修复 ──")
                for f in report.fixed:
                    lines.append(f"  [已修复] {f}")
            if report.warnings:
                lines.append("\n── 警告 ──")
                for w in report.warnings:
                    lines.append(f"  [警告] {w}")
            QMessageBox.information(
                self, tr("export_title"), "\n".join(lines),
            )
        except Exception as e:
            QMessageBox.critical(self, tr("dlg_error"), tr("export_failed", str(e)))

    # ────────────────────── 其他菜单动作 ──────────────────

    def _on_new_project(self) -> None:
        reply = QMessageBox.question(
            self, tr("dlg_confirm"),
            "新建项目将清除当前数据，是否继续？",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # 让用户选择地图尺寸
        from data.constants import MAP_SIZE_PRESETS, set_map_size
        presets = list(MAP_SIZE_PRESETS.keys())
        # 默认选中"原版"
        default_idx = len(presets) - 1
        for i, name in enumerate(presets):
            if "原版" in name:
                default_idx = i
                break

        chosen, ok = QInputDialog.getItem(
            self, "选择地图尺寸",
            "选择新项目的地图尺寸：",
            presets, default_idx, False,
        )
        if not ok:
            return

        new_w, new_h = MAP_SIZE_PRESETS[chosen]
        set_map_size(new_w, new_h)

        # 重新导入更新后的值
        from data.constants import MAP_WIDTH as W, MAP_HEIGHT as H

        self._canvas.tile_map = np.full((new_h, new_w), TILE_SEA, dtype=np.uint8)
        self._canvas.province_map = np.zeros((new_h, new_w), dtype=np.int32)
        self._canvas.terrain_map = np.zeros((new_h, new_w), dtype=np.uint8)
        self._canvas.height_map = np.full((new_h, new_w), 40, dtype=np.uint8)
        self._canvas.river_map = np.zeros((new_h, new_w), dtype=np.uint8)
        self._state_mgr.clear()
        self._country_mgr.clear()
        self._undo_mgr.clear()
        self._selected_state_id = 0
        self._selected_country_tag = ""
        self._update_province_count()
        self._canvas.refresh_display()
        self._status_info.setText(f"新项目已创建 ({new_w}×{new_h})")

    def _on_load_vanilla_ref(self) -> None:
        """加载原版地图作为参考底图（不影响自定义导入的参考图）。"""
        from data.constants import DEFAULT_HOI4_PATH
        import os
        # 优先用 provinces.bmp（跟我们地图同尺寸），其次用 colormap
        candidates = [
            os.path.join(DEFAULT_HOI4_PATH, "map", "provinces.bmp"),
            os.path.join(DEFAULT_HOI4_PATH, "map", "terrain",
                         "colormap_rgb_cityemissivemask_a.dds"),
        ]
        for path in candidates:
            if os.path.exists(path):
                if self._canvas.load_vanilla_reference(path):
                    self._status_info.setText(f"原版地图参考已加载: {os.path.basename(path)}")
                    return
        QMessageBox.warning(self, "错误",
                            f"未找到原版地图文件\n检查路径: {DEFAULT_HOI4_PATH}")

    def _on_scale_selection(self) -> None:
        """框选放大：用户拖拽选区，输入倍数，放大后居中。"""
        self._status_info.setText("拖拽框选要放大的区域...")
        self._canvas.start_selection_mode(self._apply_scale_selection)

    def _apply_scale_selection(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """框选完成后的回调。"""
        import numpy as np
        from scipy.ndimage import zoom
        from data.constants import MAP_WIDTH, MAP_HEIGHT, TILE_SEA

        sel_w, sel_h = x1 - x0, y1 - y0
        max_scale_x = MAP_WIDTH / sel_w
        max_scale_y = MAP_HEIGHT / sel_h
        max_scale = min(max_scale_x, max_scale_y, 20.0)

        from PyQt5.QtWidgets import QInputDialog
        scale, ok = QInputDialog.getDouble(
            self, "框选放大",
            f"选区: {sel_w}×{sel_h} 像素\n"
            f"最大可放大: {max_scale:.1f}x\n\n"
            f"输入放大倍数:",
            value=min(2.0, max_scale), min=1.1, max=max_scale, decimals=1,
        )
        if not ok:
            return

        tile_map = self._canvas.tile_map
        sub = tile_map[y0:y1, x0:x1].copy()

        # 放大（最近邻插值）
        zoomed = zoom(sub.astype(np.float32), scale, order=0)
        zoomed = np.round(zoomed).astype(np.uint8)
        zh, zw = zoomed.shape

        # 原地替换：清除旧选区，把放大结果居中放回原位置
        new_tile = tile_map.copy()
        # 清除原选区
        new_tile[y0:y1, x0:x1] = TILE_SEA

        # 放大后居中于原选区中心
        cy = (y0 + y1) // 2
        cx = (x0 + x1) // 2
        py0 = max(0, cy - zh // 2)
        px0 = max(0, cx - zw // 2)
        py1 = min(MAP_HEIGHT, py0 + zh)
        px1 = min(MAP_WIDTH, px0 + zw)
        zy0 = 0 if py0 > 0 else (zh // 2 - cy)
        zx0 = 0 if px0 > 0 else (zw // 2 - cx)
        new_tile[py0:py1, px0:px1] = zoomed[zy0:zy0 + (py1 - py0), zx0:zx0 + (px1 - px0)]

        # 应用
        self._canvas.stroke_started.emit()
        self._canvas._tile_map[:] = new_tile
        self._canvas._map_data.tile_map = new_tile
        self._canvas._province_map[:] = 0
        self._canvas._map_data.province_map[:] = 0
        self._canvas._full_render()
        self._canvas.stroke_ended.emit()

        self._status_info.setText(
            f"选区已放大 {scale:.1f}x ({sel_w}×{sel_h} → {zw}×{zh})，请重新生成省份"
        )

    def _on_import_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("action_import_image"), "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tga);;All Files (*)",
        )
        if file_path:
            if self._canvas.load_reference_image(file_path):
                self._status_info.setText(f"参考图已加载: {file_path}")
            else:
                QMessageBox.warning(self, tr("dlg_error"), "无法加载图片")

    def _on_import_landmask(self) -> None:
        """从真实地图（高度图/卫星图/掩膜图）提取陆海，写入 tile_map。

        逻辑：读图 → 灰度 → 缩放到 5632×2048 → 阈值化 → 亮=陆/暗=海。
        """
        from PyQt5.QtWidgets import QInputDialog
        from PIL import Image

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择陆海源图",
            "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)",
        )
        if not file_path:
            return

        threshold, ok = QInputDialog.getInt(
            self, "陆海阈值",
            "灰度阈值 (0-255)\n>= 阈值为陆地，< 阈值为海洋\n"
            "建议：高度图用 1（任何非黑像素都是陆地）；卫星图用 90 左右",
            value=1, min=0, max=255,
        )
        if not ok:
            return

        invert_reply = QMessageBox.question(
            self, "反转?", "勾选 Yes 表示：暗色为陆地、亮色为海洋（默认 No）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        invert = (invert_reply == QMessageBox.StandardButton.Yes)

        try:
            img = Image.open(file_path).convert("L")
            img = img.resize((MAP_WIDTH, MAP_HEIGHT), Image.Resampling.LANCZOS)
            arr = np.array(img, dtype=np.uint8)
            land_mask = (arr < threshold) if invert else (arr >= threshold)
        except Exception as e:
            QMessageBox.warning(self, tr("dlg_error"), f"读取图片失败：{e}")
            return

        # 撤销快照
        self._undo_mgr.push_snapshot("从图片提取陆海", {"tile_map": self._canvas.tile_map.copy()})

        new_tm = np.where(land_mask, TILE_LAND, TILE_SEA).astype(np.uint8)
        self._canvas.tile_map[:] = new_tm
        # 自动把被陆地包围的 sea 转为 lake
        from domain.generators.province import auto_classify_water
        lakes_converted = auto_classify_water(self._canvas.tile_map)
        self._canvas.refresh_display()

        land_n = int(land_mask.sum())
        total = MAP_WIDTH * MAP_HEIGHT
        self._status_info.setText(
            f"陆海导入完成 — 陆地 {land_n/total*100:.1f}% / 海洋 {(1-land_n/total)*100:.1f}%"
        )

    def _open_continent_dialog(self) -> None:
        """打开大陆编辑器对话框 (非模态)."""
        if self._continent_dialog is not None:
            self._continent_dialog.raise_()
            self._continent_dialog.activateWindow()
            return
        from features.map.continent.dialog import ContinentDialog
        dlg = ContinentDialog(self._continent_mgr, parent=self)
        dlg.pick_mode_changed.connect(self._on_continent_pick_mode)
        dlg.finished.connect(self._on_continent_dialog_closed)
        self._continent_dialog = dlg
        dlg.show()

    def _on_continent_pick_mode(self, on: bool, index: int) -> None:
        self._continent_pick_on = on
        self._continent_pick_index = index
        if on:
            self._status_info.setText(
                f"大陆指派模式：点击陆地省份 → 归入大陆 #{index + 1}"
            )
        else:
            self._status_info.setText("大陆指派模式已关闭")

    def _on_continent_dialog_closed(self, *_args) -> None:
        self._continent_dialog = None
        self._continent_pick_on = False
        self._continent_pick_index = -1

    def _open_colormap_dialog(self) -> None:
        """打开战略总览贴图颜色对话框 (模态)."""
        from PyQt5.QtWidgets import QDialog
        from features.map.colormap.dialog import ColormapDialog
        dlg = ColormapDialog(self._colormap_settings, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._status_info.setText("总览贴图颜色已更新, 下次导出生效")

    def _open_default_map_dialog(self) -> None:
        """打开 default.map 配置对话框 (模态)."""
        from PyQt5.QtWidgets import QDialog
        from features.map.default_map.dialog import DefaultMapDialog
        pcount = int(self._canvas.province_map.max())
        dlg = DefaultMapDialog(self._default_map_settings, pcount, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._status_info.setText("地图配置已更新, 下次导出生效")

    def _open_adjacency_rule_dialog(self) -> None:
        """打开 adjacency_rules 编辑器 (非模态, 支持画布拾取)."""
        if self._adjacency_rule_dialog is not None:
            self._adjacency_rule_dialog.raise_()
            self._adjacency_rule_dialog.activateWindow()
            return
        from features.map.logistics.rule_dialog import AdjacencyRuleDialog
        dlg = AdjacencyRuleDialog(self._adjacency_rule_mgr, parent=self)
        dlg.pick_mode_changed.connect(self._on_adjacency_rule_pick_mode)
        dlg.finished.connect(self._on_adjacency_rule_dialog_closed)
        self._adjacency_rule_dialog = dlg
        dlg.show()

    def _on_adjacency_rule_pick_mode(self, on: bool, target: str) -> None:
        """rule 对话框进入/退出拾取模式. target='rule_required' 或 'rule_icon'."""
        if on and target:
            self._logistics_pick_target = target
            self._status_info.setText(f"点击画布省份 → 加入 {target}")
        else:
            self._logistics_pick_target = None
            self._status_info.setText("拾取模式关闭")

    def _on_adjacency_rule_dialog_closed(self, *_args) -> None:
        self._adjacency_rule_dialog = None
        if self._logistics_pick_target and self._logistics_pick_target.startswith("rule_"):
            self._logistics_pick_target = None

    def _open_strategic_region_dialog(self) -> None:
        if self._strategic_region_dialog is not None:
            self._strategic_region_dialog.raise_()
            self._strategic_region_dialog.activateWindow()
            return
        from features.map.strategic_region.dialog import StrategicRegionDialog
        dlg = StrategicRegionDialog(
            self._strategic_region_mgr,
            state_mgr=self._state_mgr,
            province_map=self._canvas.province_map,
            tile_map=self._canvas.tile_map,
            parent=self,
        )
        dlg.pick_mode_changed.connect(self._on_strategic_region_pick_mode)
        dlg.finished.connect(self._on_strategic_region_dialog_closed)
        self._strategic_region_dialog = dlg
        dlg.show()

    def _on_strategic_region_pick_mode(self, on: bool, rid: int) -> None:
        self._strategic_region_pick_on = on
        self._strategic_region_pick_rid = rid
        if on:
            self._status_info.setText(f"战略区域拾取: 点击省份 → 加入 Region #{rid}")
        else:
            self._status_info.setText("战略区域拾取关闭")

    def _on_strategic_region_dialog_closed(self, *_args) -> None:
        self._strategic_region_dialog = None
        self._strategic_region_pick_on = False
        self._strategic_region_pick_rid = 0

    # ────────── 后勤 (Logistics) 对话框和拾取 ──────────

    def _open_adjacency_dialog(self) -> None:
        if self._adjacency_dialog is not None:
            self._adjacency_dialog.raise_()
            self._adjacency_dialog.activateWindow()
            return
        from features.map.logistics.adjacency_dialog import AdjacencyDialog
        dlg = AdjacencyDialog(self._adjacency_mgr, parent=self)
        dlg.pick_mode_changed.connect(self._on_adjacency_pick_mode)
        dlg.finished.connect(self._on_adjacency_dialog_closed)
        self._adjacency_dialog = dlg
        dlg.show()

    def _on_adjacency_pick_mode(self, on: bool, target: str) -> None:
        """adjacency 对话框进入/退出拾取模式."""
        if on and target:
            self._logistics_pick_target = f"adj_{target}"
            self._status_info.setText(f"点击画布省份填入 adjacency {target}")
        else:
            self._logistics_pick_target = None
            self._status_info.setText("拾取模式关闭")

    def _on_adjacency_dialog_closed(self, *_args) -> None:
        self._adjacency_dialog = None
        if self._logistics_pick_target and self._logistics_pick_target.startswith("adj_"):
            self._logistics_pick_target = None

    def _open_railway_dialog(self) -> None:
        if self._railway_dialog is not None:
            self._railway_dialog.raise_()
            self._railway_dialog.activateWindow()
            return
        from features.map.logistics.railway_dialog import RailwayDialog
        dlg = RailwayDialog(self._railway_mgr, parent=self)
        dlg.finished.connect(self._on_railway_dialog_closed)
        self._railway_dialog = dlg
        dlg.show()

    def _on_railway_dialog_closed(self, *_args) -> None:
        self._railway_dialog = None

    def _on_logistics_railway_level_changed(self, level: int) -> None:
        self._logistics_railway_level = level

    def _on_logistics_railway_draw_toggled(self, on: bool) -> None:
        """开始/结束铁路画笔. 结束时把草稿变成一条 railway entry."""
        if on:
            self._logistics_railway_draw_on = True
            self._logistics_railway_draft = []
            self._status_info.setText(
                f"铁路画笔已启用 (等级 {self._logistics_railway_level}): 依次点击省份, "
                "再次点击按钮结束"
            )
        else:
            self._logistics_railway_draw_on = False
            draft = self._logistics_railway_draft
            self._logistics_railway_draft = []
            if len(draft) >= 2:
                try:
                    self._railway_mgr.add(
                        level=self._logistics_railway_level,
                        province_ids=draft,
                    )
                    self._status_info.setText(
                        f"铁路已保存: level {self._logistics_railway_level}, "
                        f"{len(draft)} 省"
                    )
                    # 刷新状态
                    if hasattr(self._tool_panel, "_logi_rail_status"):
                        self._tool_panel._logi_rail_status.setText(
                            f"{self._railway_mgr.count()} 条"
                        )
                except ValueError as e:
                    self._status_info.setText(f"铁路保存失败: {e}")
            else:
                self._status_info.setText(
                    "铁路画笔已取消 (至少需要 2 个省份)"
                )

    def _on_logistics_supply_pick_toggled(self, on: bool) -> None:
        if on:
            self._logistics_pick_target = "supply"
            self._status_info.setText("点击陆地省份切换补给节点")
        else:
            if self._logistics_pick_target == "supply":
                self._logistics_pick_target = None
            self._status_info.setText("补给拾取已关闭")

    def _handle_logistics_pick(self, pid: int) -> None:
        """统一的后勤拾取分发."""
        target = self._logistics_pick_target
        if target == "supply":
            # 只允许陆地
            import numpy as _np
            from data.constants import TILE_LAND as _TL
            ys, xs = _np.where(self._canvas.province_map == pid)
            if len(ys) > 0 and int(self._canvas.tile_map[ys[0], xs[0]]) == _TL:
                added = self._supply_mgr.toggle(pid)
                self._status_info.setText(
                    f"补给节点 {'已添加' if added else '已删除'}: 省份 {pid}"
                )
                if hasattr(self._tool_panel, "_logi_sup_status"):
                    self._tool_panel._logi_sup_status.setText(
                        f"{self._supply_mgr.count()} 个"
                    )
            else:
                self._status_info.setText(f"省份 {pid} 不是陆地, 跳过")
            # supply 模式是持续的, 不重置 target
        elif target in ("adj_from", "adj_to", "adj_through"):
            # 把省份 ID 回填给 adjacency 对话框
            field = target.removeprefix("adj_")
            if self._adjacency_dialog is not None:
                self._adjacency_dialog.receive_picked_province(pid)
            self._logistics_pick_target = None
        elif target in ("rule_required", "rule_icon"):
            # 回填给 adjacency_rule 对话框
            if self._adjacency_rule_dialog is not None:
                self._adjacency_rule_dialog.receive_picked_province(pid)
            self._logistics_pick_target = None
        else:
            self._logistics_pick_target = None

    # ────────── 大陆分区 (侧边栏 page) ──────────

    def _on_continent_pick_toggled(self, on: bool) -> None:
        if on:
            item = self._tool_panel._continent_list.currentItem()
            if item is None:
                self._tool_panel._continent_pick_btn.setChecked(False)
                return
            row = self._tool_panel._continent_list.currentRow()
            self._continent_pick_on = True
            self._continent_pick_index = row
            self._status_info.setText(f"大洲指派: 点击陆地省份")
        else:
            self._continent_pick_on = False
            self._continent_pick_index = -1
            self._status_info.setText("大洲指派关闭")

    def _on_continent_add(self, name: str) -> None:
        try:
            self._continent_mgr.add_continent(name)
        except ValueError as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", str(e))
            return
        self._refresh_continent_list()

    def _on_continent_rename(self, index: int, name: str) -> None:
        try:
            self._continent_mgr.rename_continent(index, name)
        except (ValueError, IndexError) as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", str(e))
            return
        self._refresh_continent_list()

    def _on_continent_remove(self, index: int) -> None:
        try:
            self._continent_mgr.remove_continent(index)
        except (ValueError, IndexError) as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "错误", str(e))
            return
        self._refresh_continent_list()

    def _refresh_continent_list(self) -> None:
        from PyQt5.QtWidgets import QListWidgetItem
        lst = self._tool_panel._continent_list
        lst.clear()
        for i, name in enumerate(self._continent_mgr.names):
            count = sum(1 for ci in self._continent_mgr._province_continent.values() if ci == i)
            lst.addItem(QListWidgetItem(f"{i+1}. {name}  ({count} 省)"))

    # ────────── 战略区域 (侧边栏 page) ──────────

    def _on_sr_auto_generate(self) -> None:
        pm = self._canvas.province_map
        tm = self._canvas.tile_map
        if int(pm.max()) == 0:
            self._status_info.setText("请先生成省份")
            return
        self._strategic_region_mgr.auto_generate(pm, tm, state_mgr=self._state_mgr)
        self._refresh_sr_list()
        self._status_info.setText(f"已生成 {self._strategic_region_mgr.count()} 个战略区域")

    def _on_sr_pick_toggled(self, on: bool) -> None:
        self._strategic_region_pick_on = on
        if on:
            # 用列表当前选中的 region
            lst = self._tool_panel._sr_list
            item = lst.currentItem()
            if item is None:
                self._tool_panel._sr_pick_btn.setChecked(False)
                return
            from PyQt5.QtCore import Qt
            rid = item.data(Qt.UserRole)
            self._strategic_region_pick_rid = int(rid) if rid else 0
            self._status_info.setText(f"战略区拾取: 点击省份 → 加入 Region #{self._strategic_region_pick_rid}")
        else:
            self._strategic_region_pick_rid = 0
            self._status_info.setText("战略区拾取关闭")

    def _on_sr_new(self) -> None:
        self._strategic_region_mgr.create_region()
        self._refresh_sr_list()

    def _on_sr_delete(self) -> None:
        lst = self._tool_panel._sr_list
        item = lst.currentItem()
        if item is None:
            return
        from PyQt5.QtCore import Qt
        rid = int(item.data(Qt.UserRole) or 0)
        if rid > 0:
            self._strategic_region_mgr.remove_region(rid)
            self._refresh_sr_list()

    def _on_sr_selected(self, row: int) -> None:
        lst = self._tool_panel._sr_list
        item = lst.item(row)
        if item is None:
            return
        from PyQt5.QtCore import Qt
        rid = int(item.data(Qt.UserRole) or 0)
        r = self._strategic_region_mgr.get(rid)
        if r is None:
            return
        self._tool_panel._sr_name_edit.blockSignals(True)
        self._tool_panel._sr_name_edit.setText(r.name)
        self._tool_panel._sr_name_edit.blockSignals(False)
        idx = self._tool_panel._sr_weather_combo.findData(r.weather_preset)
        if idx >= 0:
            self._tool_panel._sr_weather_combo.blockSignals(True)
            self._tool_panel._sr_weather_combo.setCurrentIndex(idx)
            self._tool_panel._sr_weather_combo.blockSignals(False)
        nidx = self._tool_panel._sr_naval_combo.findData(r.naval_terrain or "")
        if nidx >= 0:
            self._tool_panel._sr_naval_combo.blockSignals(True)
            self._tool_panel._sr_naval_combo.setCurrentIndex(nidx)
            self._tool_panel._sr_naval_combo.blockSignals(False)
        self._tool_panel._sr_prov_count.setText(f"省份: {len(r.province_ids)}")

    def _on_sr_name_changed(self, name: str) -> None:
        lst = self._tool_panel._sr_list
        item = lst.currentItem()
        if item is None:
            return
        from PyQt5.QtCore import Qt
        rid = int(item.data(Qt.UserRole) or 0)
        r = self._strategic_region_mgr.get(rid)
        if r:
            r.name = name.strip() or f"STRATEGICREGION_{rid}"
            self._refresh_sr_list()

    def _on_sr_weather_changed(self, preset: str) -> None:
        lst = self._tool_panel._sr_list
        item = lst.currentItem()
        if item is None:
            return
        from PyQt5.QtCore import Qt
        rid = int(item.data(Qt.UserRole) or 0)
        r = self._strategic_region_mgr.get(rid)
        if r:
            r.weather_preset = preset

    def _on_sr_naval_changed(self, naval: str) -> None:
        lst = self._tool_panel._sr_list
        item = lst.currentItem()
        if item is None:
            return
        from PyQt5.QtCore import Qt
        rid = int(item.data(Qt.UserRole) or 0)
        r = self._strategic_region_mgr.get(rid)
        if r:
            r.naval_terrain = naval

    def _refresh_sr_list(self) -> None:
        from PyQt5.QtWidgets import QListWidgetItem
        from PyQt5.QtCore import Qt
        from domain.managers.strategic_region import PRESET_LABELS
        lst = self._tool_panel._sr_list
        lst.clear()
        for r in sorted(self._strategic_region_mgr.regions.values(), key=lambda x: x.id):
            label = f"#{r.id} {r.name}  ({len(r.province_ids)}省, {PRESET_LABELS.get(r.weather_preset, r.weather_preset)})"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, r.id)
            lst.addItem(item)

    # ────────── 总览贴图 (侧边栏 page) ──────────

    def _on_colormap_color_changed(self, attr: str, r: int, g: int, b: int) -> None:
        from domain.managers.colormap_settings import ColormapColor
        color = ColormapColor(r, g, b)
        setattr(self._colormap_settings, attr, color)
        self._status_info.setText(f"总览贴图 {attr} 颜色已更新 ({r},{g},{b})")

    def _on_colormap_reset(self) -> None:
        from domain.managers.colormap_settings import ColormapSettings
        self._colormap_settings = ColormapSettings.default()
        self._status_info.setText("总览贴图颜色已恢复默认")

    # ────────── 地图配置 (侧边栏 page) ──────────

    def _on_dm_river_changed(self, level: int) -> None:
        self._default_map_settings.river_max_level = level

    def _on_dm_tree_add(self) -> None:
        from PyQt5.QtWidgets import QInputDialog
        v, ok = QInputDialog.getInt(self, "添加", "Palette 索引 (1-13):", value=4, min=1, max=13)
        if ok and v not in self._default_map_settings.tree_palette_indices:
            self._default_map_settings.tree_palette_indices.append(v)
            self._default_map_settings.tree_palette_indices.sort()
            self._refresh_dm_tree_list()

    def _on_dm_tree_del(self) -> None:
        lst = self._tool_panel._dm_tree_list
        row = lst.currentRow()
        if 0 <= row < len(self._default_map_settings.tree_palette_indices):
            self._default_map_settings.tree_palette_indices.pop(row)
            self._refresh_dm_tree_list()

    def _on_dm_tree_reset(self) -> None:
        self._default_map_settings.tree_palette_indices = [3, 4, 7, 10]
        self._refresh_dm_tree_list()

    def _refresh_dm_tree_list(self) -> None:
        from PyQt5.QtWidgets import QListWidgetItem
        lst = self._tool_panel._dm_tree_list
        lst.clear()
        for idx in self._default_map_settings.tree_palette_indices:
            lst.addItem(QListWidgetItem(str(idx)))

    def _on_toggle_language(self) -> None:
        new_lang = "en" if get_language() == "zh" else "zh"
        set_language(new_lang)
        self.setWindowTitle(tr("app_title"))
        self._status_info.setText(tr("status_ready"))
        self._update_province_count()
        QMessageBox.information(
            self, "Language / 语言",
            "语言已切换，部分界面需要重启生效。\n"
            "Language switched. Some UI elements require restart."
        )

    def _on_about(self) -> None:
        QMessageBox.about(
            self, tr("action_about"),
            "HOI4 Fantasy World MOD Maker\n"
            "HOI4 幻想世界 MOD 制作工具\n\n"
            "Version 0.15\n"
            "Map size: 5632 × 2048"
        )

    def _update_province_count(self) -> None:
        count = int(self._canvas.province_map.max())
        self._status_provinces.setText(tr("status_provinces", count))

    # ────────────────────── 渐进式测试导出 ──────────────────────

    # 测试级别描述
    TEST_LEVELS = [
        ("Lv1: 最小完整MOD（1国家）",
         "地图 + State + 1国家(AAA) + 补给 + 战略区域 + replace_path\n"
         "最小可运行配置，测试基础文件格式是否正确"),
        ("Lv2: +2个国家 +bookmark",
         "在Lv1基础上加: 第2个国家(BBB) + bookmark选择界面\n"
         "测试多国家和bookmark"),
        ("Lv3: +意识形态 +State类别",
         "在Lv2基础上加: ideologies, state_category 定义文件\n"
         "测试自定义意识形态/State类别"),
        ("Lv4: +更多replace_path",
         "在Lv3基础上加: 更多replace_path（清空原版国策/事件等）\n"
         "完整TC MOD"),
    ]

    def _on_test_export(self) -> None:
        """渐进式测试导出 — 选择测试级别"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox, QLabel, QGroupBox

        dlg = QDialog(self)
        dlg.setWindowTitle("渐进式测试导出")
        dlg.setMinimumWidth(500)
        layout = QVBoxLayout(dlg)

        layout.addWidget(QLabel("选择测试级别（从低到高，逐级排查崩溃原因）:"))

        group = QGroupBox()
        group_layout = QVBoxLayout(group)
        radios = []
        for i, (title, desc) in enumerate(self.TEST_LEVELS):
            rb = QRadioButton(f"{title}\n    {desc}")
            rb.setStyleSheet("QRadioButton { padding: 6px 0; }")
            if i == 0:
                rb.setChecked(True)
            radios.append(rb)
            group_layout.addWidget(rb)
        layout.addWidget(group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        level = 1
        for i, rb in enumerate(radios):
            if rb.isChecked():
                level = i + 1
                break

        output_dir = QFileDialog.getExistingDirectory(
            self, "选择测试导出目录", DEFAULT_MOD_OUTPUT_PATH,
        )
        if not output_dir:
            return

        self._status_info.setText(f"正在生成 Lv{level} 测试MOD...")
        QApplication.processEvents()

        try:
            from export.test_exporter import export_test_mod
            export_test_mod(output_dir, level)
            QMessageBox.information(
                self, "测试导出",
                f"Lv{level} 测试MOD已导出到:\n{output_dir}\n\n"
                f"{self.TEST_LEVELS[level-1][0]}\n\n"
                "启动游戏测试是否正常加载。\n"
                "如果崩溃，降低级别重试；如果能进，升高级别继续。"
            )
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "导出失败", f"{e}\n\n{traceback.format_exc()}")
        finally:
            self._status_info.setText(tr("status_ready"))
