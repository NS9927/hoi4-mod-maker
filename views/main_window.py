"""
主窗口 — 薄壳，只做 UI 组装和信号路由。
所有业务逻辑委托给 ApplicationController。

文件操作/对话框拆分在:
  - views/main_window_actions.py (省份生成/验证/国家/河流/地形/大陆/战略区/后勤)
  - views/main_window_file_ops.py (新建/打开/保存/导入/导出)
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QMessageBox,
    QLabel, QApplication, QInputDialog, QSplitter, QStackedWidget,
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QKeySequence

from model.project import Project
from model.events import EventBus
from commands.history import CommandHistory
from controllers.app_controller import ApplicationController

from controllers.land import LandController
from controllers.province import ProvinceController
from controllers.terrain import TerrainController
from controllers.height import HeightController
from controllers.river import RiverController
from controllers.state import StateController
from controllers.country import CountryController
from controllers.continent import ContinentController
from controllers.logistics import LogisticsController
from controllers.strategic_region import StrategicRegionController
from controllers.colormap import ColormapController
from controllers.default_map import DefaultMapController

from views.canvas.widget import MapCanvas
from views.main_window_actions import MainWindowActionsMixin
from views.welcome_page import WelcomePage, save_recent_project
from views.context_menu import ProvinceContextMenu
from views.shortcuts import ShortcutManager, show_shortcut_dialog
from ui.tool_panel import ToolPanel
from ui.i18n import tr
from data.constants import DEFAULT_PROVINCES


class MainWindow(MainWindowActionsMixin, QMainWindow):
    """主窗口 — 纯 UI 壳，逻辑在 ApplicationController。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setMinimumSize(1200, 700)

        # ── 核心对象 ──
        self._event_bus = EventBus()
        self._project = Project(event_bus=self._event_bus)
        self._cmd_history = CommandHistory(event_bus=self._event_bus)

        # 旧版 undo manager（画布 stroke 仍在用，阶段 4 统一后删除）
        from domain.undo_manager import UndoManager
        self._undo_mgr = UndoManager(max_steps=30)

        # ── 12 个 Controller ──
        self._controllers: dict[str, object] = {
            "land": LandController(self._project, self._cmd_history),
            "province": ProvinceController(self._project, self._cmd_history),
            "terrain": TerrainController(self._project, self._cmd_history),
            "height": HeightController(self._project, self._cmd_history),
            "river": RiverController(self._project, self._cmd_history),
            "state": StateController(self._project, self._cmd_history),
            "country": CountryController(self._project, self._cmd_history),
            "continent": ContinentController(self._project, self._cmd_history),
            "logistics": LogisticsController(self._project, self._cmd_history),
            "strategic_region": StrategicRegionController(self._project, self._cmd_history),
            "colormap": ColormapController(self._project, self._cmd_history),
            "default_map": DefaultMapController(self._project, self._cmd_history),
        }

        # ── 快捷键管理器 ──
        self._shortcut_mgr = ShortcutManager()

        # ── UI 组装 ──
        self._init_ui()
        self._init_menu()
        self._init_statusbar()

        # ── ApplicationController（在 UI 组装后创建）──
        self._app = ApplicationController(
            self._project, self._canvas, self._tool_panel,
            self._cmd_history, self._controllers, self._undo_mgr,
        )

        self._connect_signals()
        self._subscribe_events()
        self._init_shortcuts()

        # ── 右键上下文菜单 ──
        self._context_menu = ProvinceContextMenu(
            self._project, self._controllers, self._canvas,
        )

        # 启动时显示欢迎页
        self._show_welcome()

        # 让 canvas 和 project 共享同一个 MapData 实例
        self._canvas.set_map_data(self._project.map_data)

        # 初始模式
        self._on_mode_changed("land")

        QTimer.singleShot(100, self._canvas.fit_in_view)

    # ═══════════════════════ UI 初始化 ═══════════════════════

    def _init_ui(self) -> None:
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # 欢迎页
        self._welcome_page = WelcomePage()
        self._welcome_page.new_project_requested.connect(self._on_welcome_new)
        self._welcome_page.open_project_requested.connect(self._on_open_project)
        self._welcome_page.open_recent_requested.connect(self._on_welcome_open_recent)
        self._welcome_page.import_mod_requested.connect(self._on_welcome_import_mod)
        self._stack.addWidget(self._welcome_page)

        # 编辑器 splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setStyleSheet(
            "QSplitter::handle { background: #3a3a4a; width: 3px; }"
        )

        self._tool_panel = ToolPanel()
        self._splitter.addWidget(self._tool_panel)

        self._canvas = MapCanvas()
        self._splitter.addWidget(self._canvas)

        self._splitter.setSizes([320, 1200])
        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        self._stack.addWidget(self._splitter)

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
        self._add_action(file_menu, "导入MOD地图...", self._on_import_mod_map, "Ctrl+Shift+M")
        self._add_action(file_menu, tr("action_export_mod"), self._on_export_mod, "Ctrl+E")
        self._add_action(file_menu, "测试导出（最小MOD）", self._on_test_export, "Ctrl+T")
        file_menu.addSeparator()
        self._add_action(file_menu, tr("action_exit"), self.close, QKeySequence.StandardKey.Quit)

        # 编辑
        edit_menu = menubar.addMenu(tr("menu_edit"))
        self._undo_action = self._add_action(edit_menu, tr("action_undo"), self._on_undo, "Ctrl+Z")
        self._redo_action = self._add_action(edit_menu, tr("action_redo"), self._on_redo, "Ctrl+Y")

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
        self._add_action(tools_menu, tr("action_generate_provinces"),
                         lambda: self._on_generate_provinces(DEFAULT_PROVINCES), "Ctrl+G")
        self._add_action(tools_menu, tr("action_validate"), self._on_validate, "Ctrl+Shift+V")

        # 设置
        settings_menu = menubar.addMenu(tr("menu_settings"))
        self._add_action(settings_menu, tr("action_language"), self._on_toggle_language)
        self._add_action(settings_menu, "快捷键设置...", self._on_shortcut_settings)

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

    # ═══════════════════════ 信号连接 ═══════════════════════

    def _connect_signals(self) -> None:
        tp = self._tool_panel
        cv = self._canvas

        # 模式切换
        tp.mode_changed.connect(self._on_mode_changed)

        # 工具/画笔 → 画布 (直通)
        tp.tool_changed.connect(cv.set_tool)
        tp.tile_type_changed.connect(cv.set_tile_type)
        tp.brush_size_changed.connect(cv.set_brush_size)
        tp.terrain_index_changed.connect(cv.set_terrain_index)
        tp.terrain_brush_mode_changed.connect(cv.set_terrain_brush_mode)
        tp.height_value_changed.connect(cv.set_height_value)

        # 参考图控件 → 画布
        tp._vanilla_ref_opacity_slider.valueChanged.connect(
            lambda v: cv.set_vanilla_ref_opacity(v / 100.0)
        )
        tp._vanilla_ref_toggle.toggled.connect(
            lambda on: cv.toggle_vanilla_ref(not on)
        )
        tp.ref_opacity_slider.valueChanged.connect(
            lambda v: cv.set_ref_opacity(v / 100.0)
        )
        tp._ref_scale_slider.valueChanged.connect(
            lambda v: cv.set_ref_scale(v / 100.0)
        )
        tp._ref_fit_btn.clicked.connect(cv.fit_ref_to_map)
        tp._ref_toggle.toggled.connect(
            lambda on: cv.toggle_ref_image(not on)
        )

        # 操作按钮 → 本窗口处理（含 UI 交互）
        tp.generate_provinces_requested.connect(self._on_generate_provinces)
        tp.validate_requested.connect(self._on_validate)
        tp.auto_terrain_requested.connect(self._on_auto_terrain)
        tp.auto_height_requested.connect(self._on_auto_height)
        tp.smooth_height_requested.connect(self._on_smooth_height)
        tp.export_requested.connect(self._on_export_mod)

        # Province 信号 → controller
        tp.split_province_requested.connect(self._on_split_province)
        tp.lasso_province_toggled.connect(self._on_lasso_toggled)
        tp.merge_mode_toggled.connect(self._on_merge_toggled)
        tp.regen_mode_toggled.connect(self._on_regen_mode_toggled)
        tp.regen_execute_requested.connect(self._on_regen_execute)

        # State 信号 → controller
        tp.auto_states_requested.connect(
            lambda count: self._controllers["state"].auto_states(count)
        )
        tp.state_selected.connect(
            lambda sid: self._controllers["state"].select_state(sid)
        )
        tp.state_property_changed.connect(
            lambda sid, prop, val: self._controllers["state"].change_property(sid, prop, val)
        )
        tp.state_detail_requested.connect(self._on_state_detail_requested)

        # Country 信号 → controller
        tp.create_country_requested.connect(self._on_create_country)
        tp.quick_create_country_requested.connect(self._on_quick_create_country)
        tp.country_selected.connect(
            lambda tag: self._controllers["country"].select_country(tag)
        )
        tp.country_property_changed.connect(
            lambda tag, prop, val: self._controllers["country"].change_property(tag, prop, val)
        )
        tp.country_color_change_requested.connect(self._on_country_color_change)

        # River 信号
        tp.river_type_changed.connect(cv.set_river_type)
        tp.validate_river_requested.connect(self._on_validate_river)

        # Logistics 信号 → controller
        tp.open_adjacency_dialog_requested.connect(self._open_adjacency_dialog)
        tp.open_railway_list_requested.connect(self._open_railway_dialog)
        tp.logistics_railway_level_changed.connect(
            lambda lv: self._controllers["logistics"].set_railway_level(lv)
        )
        tp.logistics_railway_draw_toggled.connect(
            lambda on: self._controllers["logistics"].toggle_railway_draw(on)
        )
        tp.logistics_supply_pick_toggled.connect(
            lambda on: self._controllers["logistics"].toggle_supply_pick(on)
        )

        # Continent 信号 → controller
        tp.continent_pick_toggled.connect(self._on_continent_pick_toggled)
        tp.continent_add_requested.connect(
            lambda name: self._on_continent_add(name)
        )
        tp.continent_rename_requested.connect(
            lambda idx, name: self._on_continent_rename(idx, name)
        )
        tp.continent_remove_requested.connect(
            lambda idx: self._on_continent_remove(idx)
        )

        # Strategic region 信号 → controller
        tp.strategic_region_auto_requested.connect(
            lambda: self._controllers["strategic_region"].auto_generate()
        )
        tp.strategic_region_pick_toggled.connect(self._on_sr_pick_toggled)
        tp.strategic_region_new_requested.connect(
            lambda: (self._controllers["strategic_region"].create_region(), self._refresh_sr_list())
        )
        tp.strategic_region_delete_requested.connect(self._on_sr_delete)
        tp.strategic_region_name_changed.connect(self._on_sr_name_changed)
        tp.strategic_region_weather_changed.connect(self._on_sr_weather_changed)
        tp.strategic_region_naval_changed.connect(self._on_sr_naval_changed)
        tp.strategic_region_selected.connect(self._on_sr_selected)

        # Colormap 信号 → controller
        tp.colormap_color_changed.connect(
            lambda attr, r, g, b: self._controllers["colormap"].change_color(attr, r, g, b)
        )
        tp.colormap_reset_requested.connect(
            lambda: self._controllers["colormap"].reset()
        )

        # Default map 信号 → controller
        tp.default_map_river_changed.connect(
            lambda lv: self._controllers["default_map"].set_river_level(lv)
        )
        tp.default_map_tree_add_requested.connect(self._on_dm_tree_add)
        tp.default_map_tree_del_requested.connect(self._on_dm_tree_del)
        tp.default_map_tree_reset_requested.connect(self._on_dm_tree_reset)

        # 画布信号
        cv.province_clicked.connect(self._on_province_clicked)
        cv.province_double_clicked.connect(self._on_province_double_clicked)
        cv.province_right_clicked.connect(self._on_province_right_clicked)
        cv.province_right_clicked_at.connect(self._on_province_right_clicked_at)
        cv.provinces_cleared.connect(self._on_provinces_cleared)
        cv.stroke_started.connect(self._app.on_stroke_started)
        cv.stroke_ended.connect(self._app.on_stroke_ended)
        cv.mouse_moved.connect(
            lambda x, y: self._status_pos.setText(tr("status_pos", x, y))
        )
        cv.zoom_changed.connect(
            lambda z: self._status_zoom.setText(tr("status_zoom", z))
        )

    # ═══════════════════════ EventBus 订阅 ═══════════════════

    def _subscribe_events(self) -> None:
        bus = self._event_bus
        # 只订阅纯 UI 更新事件，业务事件由 AppController 处理
        bus.subscribe("status_message", self._on_evt_status)
        bus.subscribe("undo_state_changed", self._on_evt_undo_state)
        bus.subscribe("province_count_changed", self._on_evt_province_count)
        bus.subscribe("vp_dialog_requested", self._on_evt_vp_dialog)
        bus.subscribe("logistics_province_picked", self._on_evt_logistics_picked)

    def _on_evt_status(self, event) -> None:
        self._status_info.setText(event.data.get("text", ""))

    def _on_evt_undo_state(self, event) -> None:
        pass  # TODO: enable/disable undo/redo actions

    def _on_evt_province_count(self, event) -> None:
        count = event.data.get("count", 0)
        self._status_provinces.setText(tr("status_provinces", count))

    def _on_evt_vp_dialog(self, event) -> None:
        """StateController 请求弹 VP 对话框。"""
        pid = event.data.get("pid", 0)
        if pid <= 0:
            return
        value, ok = QInputDialog.getInt(
            self, "设置胜利点",
            f"省份 {pid} 的 VP 分值\n(1=小镇, 5=中等, 10=城市, 20=首都):",
            1, 0, 50, 1,
        )
        if ok:
            ctrl: StateController = self._controllers["state"]
            ctrl.set_vp(pid, value)

    def _on_evt_logistics_picked(self, event) -> None:
        pid = event.data.get("pid", 0)
        target = event.data.get("target", "")
        if target in ("adj_from", "adj_to", "adj_through"):
            if self._adjacency_dialog is not None:
                self._adjacency_dialog.receive_picked_province(pid)
        elif target in ("rule_required", "rule_icon"):
            if self._adjacency_rule_dialog is not None:
                self._adjacency_rule_dialog.receive_picked_province(pid)

    # ═══════════════════════ 模式切换 ═══════════════════════

    def _on_mode_changed(self, mode: str) -> None:
        mode_name = self._app.on_mode_changed(mode)
        self._status_mode.setText(f"模式: {mode_name}")

    # ═══════════════════════ 省份点击路由 ═══════════════════

    def _on_province_clicked(self, pid: int) -> None:
        if pid <= 0:
            return
        # 增量生成选区模式：点击省份加入/移出选区
        ctrl_prov: ProvinceController = self._controllers["province"]
        if ctrl_prov.regen_mode:
            ctrl_prov.toggle_regen_province(pid)
            self._status_info.setText(
                f'已选中 {len(ctrl_prov.regen_selected_pids)} 个省份'
            )
            return
        try:
            info = self._app.on_province_clicked(pid)
            if info:
                self._tool_panel.update_province_info(
                    pid, info["ptype"], info["terrain"],
                    info["pixels"], info["coastal"],
                )
        except Exception as e:
            self._status_info.setText(f"操作异常: {e}")
            import traceback
            traceback.print_exc()

    def _on_province_double_clicked(self, pid: int) -> None:
        self._app.on_province_double_clicked(pid)

    def _on_province_right_clicked(self, pid: int) -> None:
        pass

    def _on_province_right_clicked_at(self, pid: int, screen_x: int, screen_y: int) -> None:
        if pid <= 0:
            return
        self._context_menu.show(pid, QPoint(screen_x, screen_y))

    def _on_provinces_cleared(self) -> None:
        self._update_province_count()
        self._status_info.setText("修改大陆数据，省份已清除（需要重新生成）")

    # ═══════════════════════ 撤销/重做 ═══════════════════════

    def _on_undo(self) -> None:
        msg = self._app.undo()
        self._status_info.setText(msg)
        self._update_province_count()

    def _on_redo(self) -> None:
        msg = self._app.redo()
        self._status_info.setText(msg)
        self._update_province_count()

    # ═══════════════════════ Province 操作 ═══════════════════

    def _on_split_province(self) -> None:
        ctrl: ProvinceController = self._controllers["province"]
        pid = self._canvas._selected_province_id
        ctrl.selected_province_id = pid
        ok = ctrl.split_selected()
        if ok:
            self._update_province_count()

    def _on_merge_toggled(self, on: bool) -> None:
        if on:
            QMessageBox.information(
                self, "合并省份",
                "先点击要保留的省份，再点击要被合并的省份。\n"
                "被合并省份的像素将并入保留省份。",
            )
        self._controllers["province"].set_merge_mode(on)

    def _on_lasso_toggled(self, on: bool) -> None:
        if on:
            QMessageBox.information(
                self, "扩张省份",
                "点击要扩张的省份，然后拖动画笔将周围像素并入该省份。",
            )
            self._controllers["province"].set_merge_mode(False)
            from domain.tools import lasso_province  # noqa: F401
            self._canvas.set_framework_tool(
                "lasso_province",
                undo_mgr=self._undo_mgr,
                state_mgr=self._project.state_mgr,
                country_mgr=self._project.country_mgr,
            )
            self._status_info.setText("扩张模式：点击省份后拖动扩张")
        else:
            self._canvas.set_framework_tool(None)
            self._status_info.setText("回到查看模式")

    def _on_regen_mode_toggled(self, on: bool) -> None:
        ctrl: ProvinceController = self._controllers["province"]
        ctrl.set_regen_mode(on)
        if on:
            self._status_info.setText('增量生成：点击省份选择区域，然后点「重新生成」')
        else:
            self._status_info.setText("回到查看模式")

    def _on_regen_execute(self) -> None:
        ctrl: ProvinceController = self._controllers["province"]
        if not ctrl.regen_selected_pids:
            QMessageBox.warning(self, "增量生成", "请先选择要重新生成的省份区域")
            return
        n = len(ctrl.regen_selected_pids)
        reply = QMessageBox.question(
            self, "增量生成",
            f"将对 {n} 个省份所在区域重新生成省份。\n"
            "该区域内的旧省份将被删除并重新划分。\n\n"
            "继续吗？",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        removed, created = ctrl.execute_regen()
        self._update_province_count()
        QMessageBox.information(
            self, "增量生成完成",
            f"删除 {removed} 个旧省份，新建 {created} 个省份。"
        )

    # ═══════════════════════ State 管理 ═══════════════════════

    def _on_state_detail_requested(self, state_id: int) -> None:
        state = self._project.state_mgr.get_state(state_id)
        if not state:
            return
        from features.map.state.detail_dialog import StateDetailDialog
        tags = list(self._project.country_mgr.countries.keys())
        dlg = StateDetailDialog(state, tags, parent=self)
        if dlg.exec_() == dlg.Accepted:
            self._app._refresh_state_list()
            self._status_info.setText(f"State {state_id} 已更新")

    # ═══════════════════════ 省份计数 ═══════════════════════

    def _update_province_count(self) -> None:
        count = self._app.update_province_count()
        self._status_provinces.setText(tr("status_provinces", count))

    # ═══════════════════════ 欢迎页 ═══════════════════════════

    def _show_welcome(self) -> None:
        self._stack.setCurrentWidget(self._welcome_page)

    def _show_editor(self) -> None:
        self._stack.setCurrentWidget(self._splitter)
        QTimer.singleShot(100, self._canvas.fit_in_view)

    def _on_welcome_new(self, width: int, height: int) -> None:
        self._on_new_project()
        self._show_editor()

    def _on_welcome_open_recent(self, path: str) -> None:
        import os
        if not os.path.exists(path):
            QMessageBox.warning(self, "错误", f"文件不存在:\n{path}")
            return
        self._load_project_file(path)
        save_recent_project(path)
        self._show_editor()

    def _on_welcome_import_mod(self) -> None:
        """欢迎页的导入MOD按钮：直接选文件夹 → 导入 → 进编辑器。"""
        from PyQt5.QtWidgets import QFileDialog, QProgressDialog
        from services.import_service import validate_mod_directory, import_mod_map

        mod_dir = QFileDialog.getExistingDirectory(
            self, "选择 HOI4 MOD 或原版目录",
            "", QFileDialog.Option.ShowDirsOnly,
        )
        if not mod_dir:
            return

        missing = validate_mod_directory(mod_dir)
        if missing:
            QMessageBox.warning(
                self, "导入失败",
                f"目录缺少必需文件:\n" + "\n".join(missing),
            )
            return

        # 显示进度提示
        progress = QProgressDialog("正在读取MOD地图文件...", None, 0, 0, self)
        progress.setWindowTitle("导入MOD")
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()

        try:
            result = import_mod_map(mod_dir)
        except Exception as e:
            progress.close()
            import traceback
            QMessageBox.critical(
                self, "导入失败",
                f"读取MOD文件时出错:\n{e}\n\n{traceback.format_exc()}"
            )
            return

        progress.setLabelText("正在初始化地图...")
        QApplication.processEvents()

        new_w, new_h = result["width"], result["height"]

        from data.constants import set_map_size
        set_map_size(new_w, new_h)

        # 创建项目并填充数据
        self._project.new_project(new_w, new_h)
        md = self._project.map_data
        md.tile_map = result["tile_map"]
        md.province_map = result["province_map"]
        md.terrain_map = result["terrain_map"]
        md.height_map = result["height_map"]
        if result["river_map"] is not None:
            md.river_map = result["river_map"]
        md.provincial_terrain = result.get("provincial_terrain", {})

        self._canvas.set_map_data(md)
        self._canvas._scene.setSceneRect(0, 0, new_w, new_h)

        progress.setLabelText("正在渲染...")
        QApplication.processEvents()

        self._show_editor()
        self._canvas.refresh_display()
        self._update_province_count()
        self._project.mark_dirty()

        progress.close()

        info_text = f"MOD地图已导入 ({new_w}×{new_h}, {result['province_count']} 省份)"
        self._status_info.setText(info_text)

        warnings_text = ""
        if result["warnings"]:
            warnings_text = "\n\n注意:\n" + "\n".join(f"- {w}" for w in result["warnings"])
        QMessageBox.information(self, "导入完成", info_text + warnings_text)

    # ═══════════════════════ 快捷键 ═══════════════════════════

    def _init_shortcuts(self) -> None:
        mgr = self._shortcut_mgr

        mgr.register("undo", self._on_undo)
        mgr.register("redo", self._on_redo)
        mgr.register("save", self._on_save_project)
        mgr.register("open", self._on_open_project)
        mgr.register("new", self._on_new_project)
        mgr.register("export", self._on_export_mod)
        mgr.register("zoom_fit", self._canvas.fit_in_view)

        # 模式切换
        modes = ["land", "province", "terrain", "height",
                 "river", "state", "country", "continent"]
        for mode_name in modes:
            key = f"mode_{mode_name}"
            mgr.register(key, lambda m=mode_name: self._on_mode_changed(m))

        # 工具切换
        tools = ["brush", "eraser", "fill", "transform", "pan"]
        for tool_name in tools:
            key = f"tool_{tool_name}"
            mgr.register(key, lambda t=tool_name: self._canvas.set_tool(t))

        mgr.register("delete", lambda: None)

        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence as KS

        mode_tool_keys = [k for k in mgr.get_all_bindings()
                          if k.startswith("mode_") or k.startswith("tool_")]
        for name in mode_tool_keys:
            key_str = mgr.get_binding(name)
            cb = mgr._callbacks.get(name)
            if cb and key_str:
                sc = QShortcut(KS(key_str), self)
                sc.setContext(Qt.ShortcutContext.WindowShortcut)
                sc.activated.connect(cb)
                mgr._shortcuts.append(sc)

    def _on_shortcut_settings(self) -> None:
        show_shortcut_dialog(self, self._shortcut_mgr)
