"""
主窗口动作处理 — 省份生成/验证/国家对话框/河流/地形/大陆/战略区/后勤。
从 views/main_window.py 拆分，作为 mixin 使用。

文件操作 (新建/打开/保存/导入/导出/测试导出) 在 views/main_window_file_ops.py。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from PyQt5.QtWidgets import (
    QMessageBox, QApplication, QInputDialog, QColorDialog,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor

from ui.i18n import tr, set_language, get_language
from views.main_window_file_ops import MainWindowFileOpsMixin

if TYPE_CHECKING:
    from controllers.country import CountryController
    from controllers.default_map import DefaultMapController
    from controllers.logistics import LogisticsController


# ── 后台线程 ──

class _GenerateThread(QThread):
    """后台线程生成省份"""
    finished = pyqtSignal(object, int)
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
    """后台线程验证省份"""
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


class MainWindowActionsMixin(MainWindowFileOpsMixin):
    """省份生成/验证/国家对话框/河流/地形/大陆/战略区/后勤处理。"""

    # ═══════════════════════ 省份生成与验证 ═══════════════════

    def _on_generate_provinces(self, count: int) -> None:
        incremental = False
        has_provinces = int(self._canvas.province_map.max()) > 0

        if has_provinces:
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
        """诊断对话框：可点击的问题列表，双击跳转"""
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
            QLabel, QDialogButtonBox,
        )
        from PyQt5.QtCore import Qt as _Qt

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("validate_title"))
        dlg.resize(520, 520)
        v = QVBoxLayout(dlg)

        province_count = int(self._canvas.province_map.max())
        coastal_count = results.get("coastal_mismatch", 0)
        warn = results.get("count_warning", "")
        info_text = f"省份总数：{province_count}    沿海：{coastal_count}"
        if warn:
            info_text += f"\n⚠ {warn}"
        v.addWidget(QLabel(info_text))

        v.addWidget(QLabel("双击问题项跳转到地图对应位置："))
        list_w = QListWidget()
        v.addWidget(list_w)

        def add_item(text: str, jump_type: str, data) -> None:
            it = QListWidgetItem(text)
            it.setData(_Qt.ItemDataRole.UserRole, (jump_type, data))
            list_w.addItem(it)

        x_positions = results.get("x_crossing_positions", [])
        for i, (y, x) in enumerate(x_positions[:50]):
            add_item(f"X-crossing #{i+1} at ({x}, {y})", "xy", (x, y))
        if len(x_positions) > 50:
            add_item(f"... 还有 {len(x_positions)-50} 个 X-crossing 未列出", "none", None)

        for pid in results.get("too_small_ids", [])[:50]:
            add_item(f"过小省份 ID={pid}（< 8 像素）", "pid", pid)
        for pid in results.get("not_contiguous_ids", [])[:50]:
            add_item(f"不连通省份 ID={pid}（多个碎片）", "pid", pid)
        for pid in results.get("too_large_ids", [])[:50]:
            add_item(f"过大省份 ID={pid}", "pid", pid)
        gaps = results.get("id_gaps", [])
        if gaps:
            add_item(f"省份 ID 不连续：缺失 {len(gaps)} 个（导出时自动修复）", "none", None)
        if list_w.count() == 0:
            list_w.addItem("✓ 没有发现任何问题")

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

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)
        dlg.exec_()

    # ═══════════════════════ Country 对话框 ═══════════════════

    def _on_create_country(self) -> None:
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

        import random
        default_color = QColor(
            random.randint(60, 220), random.randint(60, 220), random.randint(60, 220)
        )
        chosen = QColorDialog.getColor(default_color, self, f"选择 {tag} 的颜色")
        if not chosen.isValid():
            return
        color = (chosen.red(), chosen.green(), chosen.blue())

        ctrl: CountryController = self._controllers["country"]
        if not ctrl.create_country(tag, name or tag, color):
            QMessageBox.warning(self, "错误", "创建国家失败")

    def _on_quick_create_country(self, tag: str, name: str, party: str) -> None:
        color = getattr(self._tool_panel, '_quick_create_color', (100, 100, 200))
        ctrl: CountryController = self._controllers["country"]
        ctrl.create_country(tag, name, color, party)

    def _on_country_color_change(self, tag: str) -> None:
        country = self._project.country_mgr.get_country(tag)
        if not country:
            return
        r, g, b = country.color
        chosen = QColorDialog.getColor(QColor(r, g, b), self, f"修改 {tag} 的颜色")
        if not chosen.isValid():
            return
        ctrl: CountryController = self._controllers["country"]
        ctrl.change_color(tag, (chosen.red(), chosen.green(), chosen.blue()))

    # ═══════════════════════ River / Terrain / Height ═══════

    def _on_validate_river(self) -> None:
        from domain.managers.river import validate_rivers
        warnings = validate_rivers(self._canvas.river_map)
        QMessageBox.information(self, "河流验证", "\n".join(warnings))

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

    # ═══════════════════════ Continent ═══════════════════════

    def _on_continent_pick_toggled(self, on: bool) -> None:
        from controllers.continent import ContinentController
        ctrl: ContinentController = self._controllers["continent"]
        if on:
            item = self._tool_panel._continent_list.currentItem()
            if item is None:
                self._tool_panel._continent_pick_btn.setChecked(False)
                return
            row = self._tool_panel._continent_list.currentRow()
            ctrl.toggle_pick(True, row)
        else:
            ctrl.toggle_pick(False)

    def _on_continent_add(self, name: str) -> None:
        from controllers.continent import ContinentController
        ctrl: ContinentController = self._controllers["continent"]
        if ctrl.add_continent(name):
            self._refresh_continent_list()
        else:
            QMessageBox.warning(self, "错误", "添加大陆失败")

    def _on_continent_rename(self, index: int, name: str) -> None:
        from controllers.continent import ContinentController
        ctrl: ContinentController = self._controllers["continent"]
        if ctrl.rename_continent(index, name):
            self._refresh_continent_list()
        else:
            QMessageBox.warning(self, "错误", "重命名失败")

    def _on_continent_remove(self, index: int) -> None:
        from controllers.continent import ContinentController
        ctrl: ContinentController = self._controllers["continent"]
        if ctrl.remove_continent(index):
            self._refresh_continent_list()
        else:
            QMessageBox.warning(self, "错误", "删除失败")

    def _refresh_continent_list(self) -> None:
        from PyQt5.QtWidgets import QListWidgetItem
        lst = self._tool_panel._continent_list
        lst.clear()
        cm = self._project.continent_mgr
        for i, name in enumerate(cm.names):
            count = sum(1 for ci in cm._province_continent.values() if ci == i)
            lst.addItem(QListWidgetItem(f"{i+1}. {name}  ({count} 省)"))

    # ═══════════════════════ Strategic Region ═══════════════

    def _on_sr_pick_toggled(self, on: bool) -> None:
        ctrl = self._controllers["strategic_region"]
        if on:
            lst = self._tool_panel._sr_list
            item = lst.currentItem()
            if item is None:
                self._tool_panel._sr_pick_btn.setChecked(False)
                return
            rid = int(item.data(Qt.UserRole) or 0)
            ctrl.toggle_pick(True, rid)
        else:
            ctrl.toggle_pick(False)

    def _on_sr_delete(self) -> None:
        lst = self._tool_panel._sr_list
        item = lst.currentItem()
        if item is None:
            return
        rid = int(item.data(Qt.UserRole) or 0)
        self._controllers["strategic_region"].delete_region(rid)
        self._refresh_sr_list()

    def _get_sr_current_rid(self) -> int:
        lst = self._tool_panel._sr_list
        item = lst.currentItem()
        return int(item.data(Qt.UserRole) or 0) if item else 0

    def _on_sr_selected(self, row: int) -> None:
        lst = self._tool_panel._sr_list
        item = lst.item(row)
        if item is None:
            return
        rid = int(item.data(Qt.UserRole) or 0)
        r = self._project.strategic_region_mgr.get(rid)
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
        rid = self._get_sr_current_rid()
        if rid > 0:
            self._controllers["strategic_region"].set_name(rid, name)
            self._refresh_sr_list()

    def _on_sr_weather_changed(self, preset: str) -> None:
        rid = self._get_sr_current_rid()
        if rid > 0:
            self._controllers["strategic_region"].set_weather(rid, preset)

    def _on_sr_naval_changed(self, naval: str) -> None:
        rid = self._get_sr_current_rid()
        if rid > 0:
            self._controllers["strategic_region"].set_naval(rid, naval)

    def _refresh_sr_list(self) -> None:
        from PyQt5.QtWidgets import QListWidgetItem
        from domain.managers.strategic_region import PRESET_LABELS
        lst = self._tool_panel._sr_list
        lst.clear()
        for r in sorted(self._project.strategic_region_mgr.regions.values(), key=lambda x: x.id):
            label = (
                f"#{r.id} {r.name}  ({len(r.province_ids)}省, "
                f"{PRESET_LABELS.get(r.weather_preset, r.weather_preset)})"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, r.id)
            lst.addItem(item)

    # ═══════════════════════ Logistics 对话框 ═══════════════

    _adjacency_dialog = None
    _railway_dialog = None
    _adjacency_rule_dialog = None

    def _open_adjacency_dialog(self) -> None:
        if self._adjacency_dialog is not None:
            self._adjacency_dialog.raise_()
            self._adjacency_dialog.activateWindow()
            return
        from features.map.logistics.adjacency_dialog import AdjacencyDialog
        dlg = AdjacencyDialog(self._project.adjacency_mgr, parent=self)
        dlg.pick_mode_changed.connect(self._on_adjacency_pick_mode)
        dlg.finished.connect(self._on_adjacency_dialog_closed)
        self._adjacency_dialog = dlg
        dlg.show()

    def _on_adjacency_pick_mode(self, on: bool, target: str) -> None:
        ctrl: LogisticsController = self._controllers["logistics"]
        ctrl.set_adjacency_pick(on, target)

    def _on_adjacency_dialog_closed(self, *_args) -> None:
        self._adjacency_dialog = None
        ctrl: LogisticsController = self._controllers["logistics"]
        if ctrl.pick_target and ctrl.pick_target.startswith("adj_"):
            ctrl.pick_target = None

    def _open_railway_dialog(self) -> None:
        if self._railway_dialog is not None:
            self._railway_dialog.raise_()
            self._railway_dialog.activateWindow()
            return
        from features.map.logistics.railway_dialog import RailwayDialog
        dlg = RailwayDialog(self._project.railway_mgr, parent=self)
        dlg.finished.connect(self._on_railway_dialog_closed)
        self._railway_dialog = dlg
        dlg.show()

    def _on_railway_dialog_closed(self, *_args) -> None:
        self._railway_dialog = None

    # ═══════════════════════ Default Map ═══════════════════

    def _on_dm_tree_add(self) -> None:
        v, ok = QInputDialog.getInt(
            self, "添加", "Palette 索引 (1-13):", value=4, min=1, max=13
        )
        if ok:
            ctrl: DefaultMapController = self._controllers["default_map"]
            if ctrl.add_tree_index(v):
                self._refresh_dm_tree_list()

    def _on_dm_tree_del(self) -> None:
        lst = self._tool_panel._dm_tree_list
        row = lst.currentRow()
        ctrl: DefaultMapController = self._controllers["default_map"]
        if ctrl.remove_tree_index(row):
            self._refresh_dm_tree_list()

    def _on_dm_tree_reset(self) -> None:
        ctrl: DefaultMapController = self._controllers["default_map"]
        ctrl.reset_tree_indices()
        self._refresh_dm_tree_list()

    def _refresh_dm_tree_list(self) -> None:
        from PyQt5.QtWidgets import QListWidgetItem
        lst = self._tool_panel._dm_tree_list
        lst.clear()
        for idx in self._project.default_map_settings.tree_palette_indices:
            lst.addItem(QListWidgetItem(str(idx)))

    # ═══════════════════════ 杂项 ═══════════════════════════

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
