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

    def __init__(self, tile_map, count):
        super().__init__()
        self._tile_map = tile_map.copy()
        self._count = count

    def run(self):
        try:
            from core.province_generator import generate_provinces
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
            from core.province_validator import validate_provinces
            results = validate_provinces(self._tile_map, self._province_map)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


from ui.canvas_widget import MapCanvas
from ui.tool_panel import ToolPanel
from ui.styles import DARK_STYLESHEET
from ui.i18n import tr, set_language, get_language
from data.constants import (
    MAP_WIDTH, MAP_HEIGHT, DEFAULT_PROVINCES,
    TILE_SEA, TILE_LAND, TILE_LAKE,
    OCEAN_HEIGHT, LAND_BASE_HEIGHT, SEA_LEVEL,
    DEFAULT_MOD_OUTPUT_PATH,
)
from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX, DEFAULT_TERRAIN_FOR_TILE
from core.state_manager import StateManager
from core.country_manager import CountryManager
from core.undo_manager import UndoManager


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setMinimumSize(1200, 700)
        self.setStyleSheet(DARK_STYLESHEET)

        # State / Country 管理器
        self._state_mgr = StateManager()
        self._country_mgr = CountryManager()
        self._undo_mgr = UndoManager(max_steps=30)

        # 当前选中的 State / Country
        self._selected_state_id = 0
        self._selected_country_tag = ""
        self._merge_first_pid = 0  # 省份合并：第一次点击记录的省份ID

        self._init_ui()
        self._init_menu()
        self._init_statusbar()
        self._connect_signals()

        QTimer.singleShot(100, self._canvas.fit_in_view)

    # ────────────────────── UI 初始化 ──────────────────────

    def _init_ui(self) -> None:
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tool_panel = ToolPanel()
        layout.addWidget(self._tool_panel)

        self._canvas = MapCanvas()
        layout.addWidget(self._canvas, stretch=1)

        self.setCentralWidget(central)

    def _init_menu(self) -> None:
        menubar = self.menuBar()

        # 文件
        file_menu = menubar.addMenu(tr("menu_file"))
        self._add_action(file_menu, tr("action_new"), self._on_new_project, QKeySequence.StandardKey.New)
        self._add_action(file_menu, "打开项目", self._on_open_project, "Ctrl+O")
        self._add_action(file_menu, "保存项目", self._on_save_project, "Ctrl+S")
        file_menu.addSeparator()
        self._add_action(file_menu, tr("action_import_image"), self._on_import_image, "Ctrl+I")
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
        self._add_action(tools_menu, tr("action_generate_provinces"), lambda: self._on_generate_provinces(DEFAULT_PROVINCES), "Ctrl+G")
        self._add_action(tools_menu, tr("action_validate"), self._on_validate, "Ctrl+Shift+V")

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
        tp.height_value_changed.connect(cv.set_height_value)

        # 参考图透明度
        tp.ref_opacity_slider.valueChanged.connect(
            lambda v: cv.set_ref_opacity(v / 100.0)
        )

        # 操作按钮
        tp.generate_provinces_requested.connect(self._on_generate_provinces)
        tp.validate_requested.connect(self._on_validate)
        tp.auto_terrain_requested.connect(self._on_auto_terrain)
        tp.auto_height_requested.connect(self._on_auto_height)
        tp.smooth_height_requested.connect(self._on_smooth_height)
        tp.export_requested.connect(self._on_export_mod)
        tp.split_province_requested.connect(self._on_split_province)

        # State / Country 信号
        tp.auto_states_requested.connect(self._on_auto_states)
        tp.state_selected.connect(self._on_state_selected)
        tp.state_property_changed.connect(self._on_state_property_changed)
        tp.create_country_requested.connect(self._on_create_country)
        tp.country_selected.connect(self._on_country_selected)
        tp.country_property_changed.connect(self._on_country_property_changed)
        tp.country_color_change_requested.connect(self._on_country_color_change)

        # 河流信号
        tp.river_type_changed.connect(cv.set_river_type)

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
        self._status_info.setText("正在生成省份...（后台运行中，请稍候）")
        QApplication.processEvents()

        self._gen_thread = _GenerateThread(self._canvas.tile_map, count)
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
        errors = []
        info = []

        # 真正的错误（会导致崩溃）
        if results["x_crossings"] > 0:
            errors.append(tr("validate_x_crossing", results["x_crossings"]))
        if results["too_small"] > 0:
            errors.append(tr("validate_too_small", results["too_small"]))
        if results["not_contiguous"] > 0:
            errors.append(tr("validate_not_contiguous", results["not_contiguous"]))

        # 统计信息（不是错误）
        coastal_count = results.get("coastal_mismatch", 0)
        province_count = int(self._canvas.province_map.max())
        info.append(f"省份总数: {province_count}")
        info.append(f"沿海省份: {coastal_count} 个（自动标记，无需处理）")

        if errors:
            msg = "发现问题:\n" + "\n".join(errors) + "\n\n" + "\n".join(info)
            QMessageBox.warning(self, tr("validate_title"), msg)
        else:
            msg = "验证通过，无问题\n\n" + "\n".join(info)
            QMessageBox.information(self, tr("validate_title"), msg)

    # ────────────────────── 省份点击 ──────────────────────

    def _on_province_clicked(self, pid: int) -> None:
        if pid <= 0:
            return

        mode = self._canvas.display_mode

        # Province 模式：第一次点击选中，第二次点击合并
        if mode == "province":
            if self._merge_first_pid == 0:
                # 第一次点击：选中
                self._merge_first_pid = pid
                self._status_info.setText(
                    f"已选中省份 {pid}，点击相邻省份合并，或再次点击自身取消"
                )
            elif self._merge_first_pid == pid:
                # 点击自身：取消选择
                self._merge_first_pid = 0
                self._status_info.setText("取消选择")
            else:
                # 第二次点击：合并
                ok = self._canvas.merge_provinces(self._merge_first_pid, pid)
                if ok:
                    self._update_province_count()
                    self._status_info.setText(
                        f"省份 {pid} 已合并到 {self._merge_first_pid}"
                    )
                else:
                    self._status_info.setText("合并失败")
                self._merge_first_pid = 0
            return

        # State 模式：将点击的省份分配给当前选中的 State
        if mode == "state":
            if self._selected_state_id > 0:
                self._state_mgr.assign_province(pid, self._selected_state_id)
                self._refresh_state_colors()
                # 更新列表中的信息
                state = self._state_mgr.get_state(self._selected_state_id)
                if state:
                    self._tool_panel.update_state_info(
                        state.name, state.manpower, state.category
                    )
                self._status_info.setText(
                    f"省份 {pid} 已分配到 State {self._selected_state_id}"
                )
            return

        # Country 模式：将省份所属的 State 分配给当前选中的国家
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

        # Province 模式：显示省份信息
        pm = self._canvas.province_map
        tm = self._canvas.tile_map

        mask = pm == pid
        pixels = int(np.sum(mask))

        # 判断类型
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

        # 判断沿海
        from core.province_validator import get_coastal_provinces
        coastal = pid in get_coastal_provinces(tm, pm)

        # 地形（取众数）
        terrain_data = self._canvas.terrain_map[mask]
        if len(terrain_data) > 0:
            terrain_idx = int(np.bincount(terrain_data).argmax())
            # 反查地形名
            terrain_name = "未知"
            for name, idx in TERRAIN_PALETTE_INDEX.items():
                if idx == terrain_idx:
                    terrain_name = TERRAIN_TYPES[name].name_cn
                    break
        else:
            terrain_name = "未知"

        self._tool_panel.update_province_info(pid, ptype, terrain_name, pixels, coastal)

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

    # ────────────────────── 省份切割 ──────────────────

    def _on_split_province(self) -> None:
        """切割当前选中的省份"""
        pid = self._merge_first_pid or self._canvas._selected_province_id
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

    # ────────────────────── 项目保存/加载 ──────────────────

    def _on_save_project(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "保存项目", "", "HOI4 项目 (*.hoi4proj);;All Files (*)"
        )
        if not path:
            return
        try:
            from core.project_io import save_project
            save_project(
                path,
                self._canvas.tile_map,
                self._canvas.province_map,
                self._canvas.terrain_map,
                self._canvas.height_map,
                self._state_mgr,
                self._country_mgr,
                self._canvas.river_map,
            )
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
            from core.project_io import load_project
            tm, pm, terrain, hm, rm = load_project(
                path, self._state_mgr, self._country_mgr
            )
            self._canvas.tile_map = tm
            self._canvas.province_map = pm
            self._canvas.terrain_map = terrain
            self._canvas.height_map = hm
            if rm is not None:
                self._canvas.river_map = rm
            self._update_province_count()
            self._refresh_state_list()
            self._refresh_country_list()
            self._status_info.setText(f"项目已加载: {path}")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))

    # ────────────────────── 地形自动生成 ──────────────────

    def _on_auto_terrain(self) -> None:
        """从陆地/海洋数据自动生成地形图"""
        self._status_info.setText("正在生成地形...")
        self.repaint()

        tm = self._canvas.tile_map
        terrain = np.zeros_like(tm, dtype=np.uint8)
        for tile_type, terrain_name in DEFAULT_TERRAIN_FOR_TILE.items():
            mask = tm == tile_type
            terrain[mask] = TERRAIN_PALETTE_INDEX[terrain_name]

        self._canvas.terrain_map = terrain
        self._status_info.setText("地形生成完成")

    # ────────────────────── 高度图自动生成 ────────────────

    def _on_auto_height(self) -> None:
        """从地块类型自动生成高度图"""
        self._status_info.setText("正在生成高度图...")
        self.repaint()

        from scipy.ndimage import gaussian_filter

        tm = self._canvas.tile_map
        hm = np.full((MAP_HEIGHT, MAP_WIDTH), OCEAN_HEIGHT, dtype=np.float32)

        land_mask = tm == TILE_LAND
        lake_mask = tm == TILE_LAKE
        sea_mask = tm == TILE_SEA

        hm[land_mask] = LAND_BASE_HEIGHT
        hm[lake_mask] = SEA_LEVEL - 5

        hm = gaussian_filter(hm, sigma=8)

        # 确保陆海分明
        hm[sea_mask] = np.minimum(hm[sea_mask], SEA_LEVEL - 1)
        hm[land_mask] = np.maximum(hm[land_mask], SEA_LEVEL + 1)

        hm = np.clip(hm, 0, 255).astype(np.uint8)
        self._canvas.height_map = hm
        self._status_info.setText("高度图生成完成")

    def _on_smooth_height(self) -> None:
        """平滑高度图"""
        from scipy.ndimage import gaussian_filter
        hm = self._canvas.height_map.astype(np.float32)
        hm = gaussian_filter(hm, sigma=4)
        self._canvas.height_map = np.clip(hm, 0, 255).astype(np.uint8)
        self._status_info.setText("高度图已平滑")

    # ────────────────────── 导出 ──────────────────────────

    def _on_export_mod(self) -> None:
        # 导出前验证
        warnings = self._validate_before_export()
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
            from export.mod_exporter import export_full_mod
            export_full_mod(
                self._canvas.tile_map,
                self._canvas.province_map,
                output_dir,
                state_mgr=self._state_mgr,
                country_mgr=self._country_mgr,
                river_map=self._canvas.river_map,
                terrain_map=self._canvas.terrain_map,
                height_map=self._canvas.height_map,
            )
            QMessageBox.information(
                self, tr("export_title"),
                tr("export_success", output_dir),
            )
        except Exception as e:
            QMessageBox.critical(self, tr("dlg_error"), tr("export_failed", str(e)))

    def _validate_before_export(self) -> list[str]:
        """导出前验证，返回警告列表"""
        warnings = []
        pm = self._canvas.province_map
        if int(pm.max()) == 0:
            warnings.append("没有省份数据，请先生成省份")
            return warnings

        if not self._state_mgr.states:
            warnings.append("没有 State，请先自动分组或手动创建")

        if not self._country_mgr.countries:
            warnings.append("没有国家，请先创建至少一个国家")

        # 检查有没有 State 没分配 owner
        unowned = []
        for sid, state in self._state_mgr.states.items():
            owner = self._country_mgr.get_owner_of_state(sid)
            if not owner:
                unowned.append(str(sid))
        if unowned:
            warnings.append(f"{len(unowned)} 个 State 未分配国家: {', '.join(unowned[:5])}...")

        # 检查国家有没有首都
        for tag, country in self._country_mgr.countries.items():
            if country.capital <= 0:
                warnings.append(f"国家 {tag} 没有设首都")

        return warnings

    # ────────────────────── 其他菜单动作 ──────────────────

    def _on_new_project(self) -> None:
        reply = QMessageBox.question(
            self, tr("dlg_confirm"),
            "新建项目将清除当前数据，是否继续？",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._canvas.tile_map = np.full((MAP_HEIGHT, MAP_WIDTH), TILE_SEA, dtype=np.uint8)
            self._canvas.province_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.int32)
            self._canvas.terrain_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.uint8)
            self._canvas.height_map = np.full((MAP_HEIGHT, MAP_WIDTH), 40, dtype=np.uint8)
            self._canvas.river_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.uint8)
            self._state_mgr.clear()
            self._country_mgr.clear()
            self._undo_mgr.clear()
            self._selected_state_id = 0
            self._selected_country_tag = ""
            self._update_province_count()
            self._status_info.setText(tr("status_ready"))

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
            "Version 0.2\n"
            "Map size: 5632 × 2048"
        )

    def _update_province_count(self) -> None:
        count = int(self._canvas.province_map.max())
        self._status_provinces.setText(tr("status_provinces", count))

    # ────────────────────── 测试导出 ──────────────────────

    def _on_test_export(self) -> None:
        """一键生成最小完整MOD并导出，用于测试游戏是否能正常加载"""
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择测试导出目录",
            DEFAULT_MOD_OUTPUT_PATH,
        )
        if not output_dir:
            return

        self._status_info.setText("正在生成测试MOD...")
        QApplication.processEvents()

        try:
            self._generate_test_mod(output_dir)
            QMessageBox.information(
                self, "测试导出",
                f"测试MOD已导出到:\n{output_dir}\n\n"
                "包含: 2块大陆, 200省份, 地形, 河流, 2个国家\n"
                "启动游戏测试是否正常加载。"
            )
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))
        finally:
            self._status_info.setText(tr("status_ready"))

    def _generate_test_mod(self, output_dir: str) -> None:
        """生成最小但完整的测试MOD"""
        from core.province_generator import generate_provinces
        from core.state_manager import StateManager
        from core.country_manager import CountryManager
        from core.river_manager import RIVER_SOURCE, RIVER_WIDTH_3, RIVER_MOUTH
        from export.mod_exporter import export_full_mod

        # 1. 创建地图 — 两块分开的大陆 + 湖泊
        tile_map = np.full((MAP_HEIGHT, MAP_WIDTH), TILE_SEA, dtype=np.uint8)
        # 大陆1: 左侧
        tile_map[400:1200, 300:2200] = TILE_LAND
        # 大陆2: 右侧（隔着海洋）
        tile_map[600:1600, 3200:5000] = TILE_LAND
        # 小岛
        tile_map[200:350, 2500:2800] = TILE_LAND
        # 湖泊（在大陆1内部）
        tile_map[700:800, 1000:1200] = TILE_LAKE

        # 2. 生成省份（少量，快速）
        province_map, count = generate_provinces(tile_map, 200)

        # 3. 地形 — 多种地形测试
        from data.terrain_types import TERRAIN_PALETTE_INDEX, DEFAULT_TERRAIN_FOR_TILE
        terrain_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.uint8)
        for tile_type, terrain_name in DEFAULT_TERRAIN_FOR_TILE.items():
            terrain_map[tile_map == tile_type] = TERRAIN_PALETTE_INDEX[terrain_name]
        # 大陆1北部设为森林
        forest_idx = TERRAIN_PALETTE_INDEX["forest"]
        terrain_map[400:700, 300:2200] = np.where(
            tile_map[400:700, 300:2200] == TILE_LAND, forest_idx,
            terrain_map[400:700, 300:2200]
        )
        # 大陆2南部设为沙漠
        desert_idx = TERRAIN_PALETTE_INDEX["desert"]
        terrain_map[1200:1600, 3200:5000] = np.where(
            tile_map[1200:1600, 3200:5000] == TILE_LAND, desert_idx,
            terrain_map[1200:1600, 3200:5000]
        )
        # 小岛设为丘陵
        hills_idx = TERRAIN_PALETTE_INDEX["hills"]
        terrain_map[200:350, 2500:2800] = np.where(
            tile_map[200:350, 2500:2800] == TILE_LAND, hills_idx,
            terrain_map[200:350, 2500:2800]
        )

        # 4. 高度图
        from scipy.ndimage import gaussian_filter
        height_map = np.full((MAP_HEIGHT, MAP_WIDTH), OCEAN_HEIGHT, dtype=np.float32)
        height_map[tile_map == TILE_LAND] = LAND_BASE_HEIGHT
        height_map[tile_map == TILE_LAKE] = SEA_LEVEL - 5
        # 大陆2中部加山脉
        height_map[900:1100, 3800:4500] = 200
        height_map = gaussian_filter(height_map, sigma=6)
        height_map[tile_map == TILE_SEA] = np.minimum(height_map[tile_map == TILE_SEA], SEA_LEVEL - 1)
        height_map[tile_map == TILE_LAND] = np.maximum(height_map[tile_map == TILE_LAND], SEA_LEVEL + 1)
        height_map = np.clip(height_map, 0, 255).astype(np.uint8)

        # 5. 河流 — 一条简单的河
        river_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.uint8)
        # 源头在山区
        river_map[950, 4200] = RIVER_SOURCE
        # 河道向西流
        river_map[950, 3900:4200] = RIVER_WIDTH_3
        # 入海口
        river_map[950, 3200] = RIVER_MOUTH
        river_map[950, 3201:3900] = RIVER_WIDTH_3

        # 6. State — 自动分组（会按陆块分开）
        sm = StateManager()
        sm.auto_split(province_map, tile_map, per_state=10)

        # 7. 国家 — 两个国家，分别占两块大陆
        cm = CountryManager()
        cm.create_country("AAA", "测试帝国", (200, 80, 80))
        cm.create_country("BBB", "测试共和", (80, 80, 200))

        # 按陆块分配国家
        from scipy.ndimage import label as ndlabel
        land_labeled, num_lm = ndlabel((tile_map == TILE_LAND).astype(np.int32))

        for sid, state in sm.states.items():
            if not state.provinces:
                continue
            # 找这个State的第一个省份在哪个陆块
            pid = state.provinces[0]
            ys, xs = np.where(province_map == pid)
            if len(ys) == 0:
                cm.assign_state(sid, "AAA")
                continue
            cy, cx = int(np.mean(ys)), int(np.mean(xs))
            lm = land_labeled[cy, cx] if 0 <= cy < MAP_HEIGHT and 0 <= cx < MAP_WIDTH else 0
            # 陆块1 → AAA, 其他 → BBB
            if cx < 2600:
                cm.assign_state(sid, "AAA")
            else:
                cm.assign_state(sid, "BBB")

        # 设首都（每个国家第一个State的第一个省份）
        for tag in ["AAA", "BBB"]:
            states_of = cm.get_states_of_country(tag)
            if states_of:
                first_state = sm.get_state(states_of[0])
                if first_state and first_state.provinces:
                    cm.set_capital(tag, first_state.provinces[0])

        # 8. 导出
        export_full_mod(
            tile_map, province_map, output_dir,
            mod_name="TestMOD",
            state_mgr=sm,
            country_mgr=cm,
            river_map=river_map,
            terrain_map=terrain_map,
            height_map=height_map,
        )
