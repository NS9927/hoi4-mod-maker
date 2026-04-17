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

    def __init__(self, tile_map, count, province_map=None, incremental=False,
                 sea_scale=0.15, lake_scale=0.3, density_map=None,
                 skip_mismatch_clear=False):
        super().__init__()
        self._tile_map = tile_map.copy()
        self._count = count
        self._province_map = province_map.copy() if province_map is not None else None
        self._incremental = incremental
        self._sea_scale = sea_scale
        self._lake_scale = lake_scale
        self._density_map = density_map.copy() if density_map is not None else None
        self._skip_mismatch_clear = skip_mismatch_clear

    def run(self):
        try:
            if self._incremental and self._province_map is not None:
                from domain.generators.province import generate_provinces_incremental
                pm, cnt = generate_provinces_incremental(
                    self._tile_map, self._province_map,
                    skip_mismatch_clear=self._skip_mismatch_clear,
                )
            else:
                from domain.generators.province import generate_provinces
                pm, cnt = generate_provinces(
                    self._tile_map, self._count,
                    sea_scale=self._sea_scale,
                    density_map=self._density_map,
                )
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

    # ═══════════════════════ 新大陆 ═══════════════════

    def _on_new_land_generate(self) -> None:
        """新大陆页面的生成按钮：用 mask 清零 → 增量生成 → 清空 mask。"""
        import numpy as np

        mask = self._canvas.new_land_mask
        n = int(mask.sum())
        if n == 0:
            self._status_info.setText("没有画新陆地，先用画笔画。")
            return

        self._status_info.setText(f"正在为 {n} 像素新陆地生成省份...")
        QApplication.processEvents()

        # 保存 mask 副本，立刻清空原 mask（用户可以马上画下一批）
        mask_copy = mask.copy()
        self._new_land_mask_copy = mask_copy  # 给 _on_generate_done 用于 terrain 同步
        self._canvas.new_land_mask[:] = False
        if hasattr(self._tool_panel, '_new_land_page'):
            self._tool_panel._new_land_page.update_pixel_count(0)

        # 清零 mask 像素的 province_map
        pm_copy = self._canvas.province_map.copy()
        pm_copy[mask_copy] = 0

        # 读取省份数量参数
        count = 12000
        if hasattr(self._tool_panel, '_land_page') and self._tool_panel._land_page is not None:
            params = self._tool_panel._land_page.get_generation_params()
            count = params.get("target_count", 12000)

        self._gen_thread = _GenerateThread(
            self._canvas.tile_map, count,
            province_map=pm_copy,
            incremental=True,
            skip_mismatch_clear=True,
        )
        self._gen_thread.finished.connect(self._on_generate_done)
        self._gen_thread.error.connect(self._on_generate_error)
        self._gen_thread.start()

    def _on_new_land_clear(self) -> None:
        """清空新大陆画笔的 mask。"""
        self._canvas.new_land_mask[:] = False
        self._status_info.setText("新大陆画笔已清空。")
        # 更新页面像素计数
        if hasattr(self._tool_panel, '_new_land_page'):
            self._tool_panel._new_land_page.update_pixel_count(0)

    # ═══════════════════════ 州自动分组 ═══════════════════

    def _on_auto_states_with_confirm(self, per_state: int) -> None:
        """自动分组前确认（会清空现有州数据）。"""
        existing = len(self._project.state_mgr.states)
        if existing > 0:
            reply = QMessageBox.question(
                self, "确认自动分组",
                f"当前已有 {existing} 个州。\n"
                f"自动分组将清空所有现有州数据，重新按每州 {per_state} 个省份分组。\n\n"
                f"是否继续？",
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._controllers["state"].auto_states(per_state)

    # ═══════════════════════ 战略区域自动生成 ═══════════════════

    def _on_auto_sr_with_confirm(self) -> None:
        """自动生成战略区域前确认。"""
        existing = self._project.strategic_region_mgr.count()
        if existing > 0:
            reply = QMessageBox.question(
                self, "确认自动生成",
                f"当前已有 {existing} 个战略区域。\n"
                f"自动生成将清空所有现有战略区域数据。\n\n是否继续？",
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._controllers["strategic_region"].auto_generate()

    # ═══════════════════════ 省份生成与验证 ═══════════════════

    def _on_generate_provinces(self, count: int) -> None:
        incremental = False
        has_provinces = int(self._canvas.province_map.max()) > 0

        if has_provinces:
            reply = QMessageBox.question(
                self, tr("dlg_gen_mode_title"),
                tr("dlg_gen_mode_body"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            incremental = (reply == QMessageBox.StandardButton.Yes)

        self._status_info.setText(tr("status_generating_bg"))
        QApplication.processEvents()

        # 从 Land 页面读取密度参数
        sea_scale = 0.15
        lake_scale = 0.3
        density_map = self._project.map_data.density_map
        if hasattr(self._tool_panel, '_land_page') and self._tool_panel._land_page is not None:
            params = self._tool_panel._land_page.get_generation_params()
            sea_scale = params.get("sea_scale", 0.15)
            lake_scale = params.get("lake_scale", 0.3)

        # 增量模式：用新大陆画笔的 mask 预清除像素
        province_map_for_thread = None
        if incremental:
            province_map_for_thread = self._canvas.province_map.copy()
            mask = self._canvas.new_land_mask
            if mask.any():
                province_map_for_thread[mask] = 0

        has_new_land_mask = incremental and self._canvas.new_land_mask.any()
        self._gen_thread = _GenerateThread(
            self._canvas.tile_map, count,
            province_map=province_map_for_thread,
            incremental=incremental,
            sea_scale=sea_scale,
            lake_scale=lake_scale,
            density_map=density_map,
            skip_mismatch_clear=has_new_land_mask,
        )
        self._gen_thread.finished.connect(self._on_generate_done)
        self._gen_thread.error.connect(self._on_generate_error)
        self._gen_thread.start()

    def _on_generate_done(self, province_map, count: int) -> None:
        was_incremental = getattr(self._gen_thread, '_incremental', False)
        self._canvas.province_map = province_map
        self._project.mark_dirty()
        self._update_province_count()

        # 发事件，级联清理由各 controller 自动处理
        self._event_bus.emit(
            "province_map_regenerated", incremental=was_incremental,
        )

        # 强制刷新画布（增量模式不切模式，保持新大陆画笔工具状态）
        self._canvas.refresh_display()

        # 增量生成后：同步 terrain + 清理被吞省份 + 自动分配 + 清空画笔 mask
        if was_incremental:
            import numpy as np
            from data.constants import TILE_LAND, TILE_SEA, TILE_LAKE
            from data.terrain_types import TERRAIN_PALETTE_INDEX, DEFAULT_TERRAIN_FOR_TILE

            # 同步 terrain_map（用保存的 mask 副本，不依赖 canvas.new_land_mask）
            saved_mask = getattr(self, '_new_land_mask_copy', None)
            if saved_mask is not None and saved_mask.any():
                tm = self._canvas.tile_map
                terrain_map = self._project.map_data.terrain_map
                for tile_type in (TILE_LAND, TILE_SEA, TILE_LAKE):
                    t_name = DEFAULT_TERRAIN_FOR_TILE.get(tile_type)
                    if t_name and t_name in TERRAIN_PALETTE_INDEX:
                        t_mask = saved_mask & (tm == tile_type)
                        if np.any(t_mask):
                            terrain_map[t_mask] = TERRAIN_PALETTE_INDEX[t_name]
                self._new_land_mask_copy = None

            consumed = self._cleanup_consumed_provinces(province_map)
            assigned = self._auto_assign_new_provinces(province_map)
            msg = tr("status_gen_done").format(count=count)
            msg += f" ({assigned} 个新省份已自动分配)"
            if consumed:
                ids_str = ", ".join(str(i) for i in sorted(consumed)[:10])
                if len(consumed) > 10:
                    ids_str += f" ... 共 {len(consumed)} 个"
                msg += f"\n⚠ 被完全吞并的省份: {ids_str}"
            self._status_info.setText(msg)
        else:
            self._status_info.setText(tr("status_gen_done").format(count=count))

    def _cleanup_consumed_provinces(self, province_map) -> set[int]:
        """清理被完全吞并的省份：从 state/country/战略区中移除不存在的省份引用。"""
        import numpy as np

        existing_pids = set(np.unique(province_map).tolist())
        existing_pids.discard(0)
        consumed: set[int] = set()

        state_mgr = self._project.state_mgr
        sr_mgr = self._project.strategic_region_mgr
        country_mgr = self._project.country_mgr

        # 清理 state 引用
        for sid, state in list(state_mgr.states.items()):
            old_provinces = state.provinces
            new_provinces = [p for p in old_provinces if p in existing_pids]
            removed = set(old_provinces) - set(new_provinces)
            if removed:
                consumed.update(removed)
                state.provinces = new_provinces
                if not new_provinces:
                    state_mgr.states.pop(sid, None)

        # 重建 province_to_state 索引
        if consumed and hasattr(state_mgr, '_province_to_state'):
            state_mgr._province_to_state = {
                pid: sid for sid, s in state_mgr.states.items()
                for pid in s.provinces
            }

        # 清理战略区引用
        if sr_mgr:
            for r in sr_mgr.regions.values():
                r.province_ids = [p for p in r.province_ids if p in existing_pids]

        # 清理国家首都引用
        if country_mgr:
            for tag, country in country_mgr.countries.items():
                if country.capital > 0 and country.capital not in existing_pids:
                    consumed.add(country.capital)
                    # 找该国其他省份作为新首都
                    new_cap = 0
                    owned_states = country_mgr.get_states_of_country(tag)
                    if state_mgr and owned_states:
                        for osid in owned_states:
                            s = state_mgr.get_state(osid)
                            if s and s.provinces:
                                new_cap = s.provinces[0]
                                break
                    country.capital = new_cap

        return consumed

    def _auto_assign_new_provinces(self, province_map) -> int:
        """增量生成后，把没有 state 的陆地省份分配到相邻最近的 state/战略区。"""
        import numpy as np
        from data.constants import TILE_LAND

        state_mgr = self._project.state_mgr
        sr_mgr = self._project.strategic_region_mgr
        tile_map = self._canvas.tile_map
        pm = province_map

        # 找未分配 state 的陆地省份
        max_pid = int(pm.max())
        if max_pid == 0:
            return 0

        assigned_count = 0
        # 预计算质心
        flat = pm.ravel()
        n = max_pid + 1
        pid_count = np.bincount(flat, minlength=n)
        ys, xs = np.mgrid[0:pm.shape[0], 0:pm.shape[1]]
        sum_y = np.bincount(flat, weights=ys.ravel().astype(np.float64), minlength=n)
        sum_x = np.bincount(flat, weights=xs.ravel().astype(np.float64), minlength=n)

        # 已有 state 的省份 → 质心
        state_centers: dict[int, tuple[float, float]] = {}  # state_id → (cy, cx)
        for sid, state in state_mgr.states.items():
            total_y, total_x, cnt = 0.0, 0.0, 0
            for p in state.provinces:
                if 0 < p < n and pid_count[p] > 0:
                    total_y += sum_y[p] / pid_count[p]
                    total_x += sum_x[p] / pid_count[p]
                    cnt += 1
            if cnt > 0:
                state_centers[sid] = (total_y / cnt, total_x / cnt)

        # 对每个未分配的陆地省份，找最近 state
        for pid in range(1, max_pid + 1):
            if pid_count[pid] == 0:
                continue
            # 检查是否陆地
            cy = int(sum_y[pid] / pid_count[pid])
            cx = int(sum_x[pid] / pid_count[pid])
            cy = min(cy, pm.shape[0] - 1)
            cx = min(cx, pm.shape[1] - 1)
            if int(tile_map[cy, cx]) != TILE_LAND:
                continue
            # 已有 state → 跳过
            if state_mgr.get_state_of_province(pid) > 0:
                continue

            # 找最近 state
            best_sid, best_dist = 0, float('inf')
            py = sum_y[pid] / pid_count[pid]
            px = sum_x[pid] / pid_count[pid]
            for sid, (sy, sx) in state_centers.items():
                d = (py - sy) ** 2 + (px - sx) ** 2
                if d < best_dist:
                    best_dist = d
                    best_sid = sid
            if best_sid > 0:
                state = state_mgr.get_state(best_sid)
                if state:
                    state.provinces.append(pid)
                    state_mgr._province_to_state[pid] = best_sid
                    assigned_count += 1

            # 战略区域也一样
            if sr_mgr.get_region_of_province(pid) == 0:
                # 找最近的战略区
                best_rid, best_dist = 0, float('inf')
                for rid, region in sr_mgr._regions.items():
                    if not region.province_ids:
                        continue
                    # 用第一个有像素的省份算距离
                    for rp in region.province_ids[:5]:
                        if 0 < rp < n and pid_count[rp] > 0:
                            ry = sum_y[rp] / pid_count[rp]
                            rx = sum_x[rp] / pid_count[rp]
                            d = (py - ry) ** 2 + (px - rx) ** 2
                            if d < best_dist:
                                best_dist = d
                                best_rid = rid
                            break
                if best_rid > 0:
                    sr_mgr._regions[best_rid].province_ids.append(pid)

        return assigned_count

    def _on_generate_error(self, msg: str) -> None:
        QMessageBox.critical(self, tr("dlg_error"), msg)
        self._status_info.setText(tr("status_ready"))

    def _on_smooth_coast(self) -> None:
        """平滑海岸线。有选区时只平滑选区内，否则全图。"""
        from domain.generators.coastline import smooth_coastline
        map_data = self._project.map_data

        # 检查画布是否有选区（变换工具框选的区域）
        sel = getattr(self._canvas, '_selection_rect', None)
        if sel:
            x0, y0, x1, y1 = sel
            # 转换为整数像素坐标 (region 参数是 y0, x0, y1, x1)
            region = (int(y0), int(x0), int(y1), int(x1))
        else:
            region = None

        new_tile = smooth_coastline(map_data.tile_map, region=region)
        map_data.tile_map[:] = new_tile
        self._canvas.tile_map = map_data.tile_map
        self._canvas._full_render()
        self._project.mark_dirty()
        if region:
            self._status_info.setText(tr("status_coast_smoothed_region"))
        else:
            self._status_info.setText(tr("status_coast_smoothed"))

    def _on_density_clear(self) -> None:
        """清除密度图，恢复均匀。"""
        self._project.map_data.density_map = None
        self._tool_panel._land_page._density_map = None
        self._canvas.set_density_overlay_visible(self._canvas._display_mode == "density")
        self._status_info.setText(tr("status_density_cleared"))

    def _on_quick_init(self) -> None:
        """一键初始化：自动生成州 + 战略区域 + 默认国家。"""
        pm = self._canvas.province_map
        if int(pm.max()) == 0:
            QMessageBox.warning(self, tr("dlg_quick_init_title"), tr("dlg_quick_init_no_provinces"))
            return

        reply = QMessageBox.question(
            self, tr("dlg_quick_init_title"),
            tr("dlg_quick_init_body"),
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._status_info.setText(tr("status_initializing"))
        QApplication.processEvents()

        try:
            from views.export_dialog import auto_complete_project

            class _FakeCanvas:
                def __init__(self, md):
                    self.map_data = md
                    self.province_map = md.province_map
                    self.tile_map = md.tile_map
                    self.terrain_map = md.terrain_map
                    self.height_map = md.height_map
                    self.river_map = md.river_map

            fc = _FakeCanvas(self._project.map_data)
            log = auto_complete_project(self._project, fc)

            self._canvas.refresh_display()
            msg = tr("dlg_quick_init_done") + "\n".join(f"- {l}" for l in log)
            self._status_info.setText(tr("status_init_done"))
            QMessageBox.information(self, tr("dlg_quick_init_title"), msg)
        except Exception as e:
            import traceback
            QMessageBox.critical(self, tr("dlg_init_failed"), f"{e}\n\n{traceback.format_exc()}")

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
        info_text = tr("validate_info").format(total=province_count, coastal=coastal_count)
        if warn:
            info_text += f"\n⚠ {warn}"
        v.addWidget(QLabel(info_text))

        v.addWidget(QLabel(tr("validate_double_click_hint")))
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
            add_item(tr("validate_more_xcrossing").format(n=len(x_positions)-50), "none", None)

        for pid in results.get("too_small_ids", [])[:50]:
            add_item(tr("validate_too_small_item").format(pid=pid), "pid", pid)
        for pid in results.get("not_contiguous_ids", [])[:50]:
            add_item(tr("validate_not_contiguous_item").format(pid=pid), "pid", pid)
        for pid in results.get("too_large_ids", [])[:50]:
            add_item(tr("validate_too_large_item").format(pid=pid), "pid", pid)
        gaps = results.get("id_gaps", [])
        if gaps:
            add_item(tr("validate_id_gaps").format(n=len(gaps)), "none", None)
        if list_w.count() == 0:
            list_w.addItem(tr("validate_no_issues"))

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
        tag, ok = QInputDialog.getText(self, tr("country_create_btn"), tr("dlg_country_tag_prompt"))
        if not ok or not tag:
            return
        tag = tag.upper().strip()[:3]
        if len(tag) != 3 or not tag.isalpha():
            QMessageBox.warning(self, tr("dlg_error"), tr("country_tag_invalid"))
            return

        name, ok = QInputDialog.getText(self, tr("country_create_btn"), tr("dlg_country_name_prompt").format(tag=tag))
        if not ok:
            return

        import random
        default_color = QColor(
            random.randint(60, 220), random.randint(60, 220), random.randint(60, 220)
        )
        chosen = QColorDialog.getColor(default_color, self, tr("dlg_country_pick_color").format(tag=tag))
        if not chosen.isValid():
            return
        color = (chosen.red(), chosen.green(), chosen.blue())

        ctrl: CountryController = self._controllers["country"]
        if not ctrl.create_country(tag, name or tag, color):
            QMessageBox.warning(self, tr("dlg_error"), tr("dlg_country_create_failed"))

    def _on_quick_create_country(self, tag: str, name: str, party: str) -> None:
        color = getattr(self._tool_panel, '_quick_create_color', (100, 100, 200))
        ctrl: CountryController = self._controllers["country"]
        ctrl.create_country(tag, name, color, party)

    def _on_country_color_change(self, tag: str) -> None:
        country = self._project.country_mgr.get_country(tag)
        if not country:
            return
        r, g, b = country.color
        chosen = QColorDialog.getColor(QColor(r, g, b), self, tr("dlg_country_change_color").format(tag=tag))
        if not chosen.isValid():
            return
        ctrl: CountryController = self._controllers["country"]
        ctrl.change_color(tag, (chosen.red(), chosen.green(), chosen.blue()))

    # ═══════════════════════ River / Terrain / Height ═══════

    def _on_validate_river(self) -> None:
        from domain.managers.river import validate_rivers
        warnings = validate_rivers(self._canvas.river_map)
        QMessageBox.information(self, tr("dlg_river_validate_title"), "\n".join(warnings))

    def _on_auto_terrain(self) -> None:
        from services.terrain_service import (
            smart_auto_terrain, TerrainGenConfig,
            compute_provincial_terrain_from_bmp,
        )
        from commands.map.generate_terrain import GenerateTerrainCommand
        self._status_info.setText(tr("status_auto_terrain"))
        self.repaint()
        map_data = self._project.map_data
        # 从 terrain page 获取配置 (如果有)
        config = None
        terrain_page = self._tool_panel._terrain_page
        if hasattr(terrain_page, 'get_gen_config'):
            config = terrain_page.get_gen_config()
        new_terrain = smart_auto_terrain(
            map_data.height_map, map_data.tile_map, config
        )
        cmd = GenerateTerrainCommand(map_data, new_terrain)
        self._cmd_history.execute(cmd)
        # 单向同步：视觉 terrain.bmp → 属性 provincial_terrain dict
        # 每个 land province 按多数地形自动推断属性，用户后续可在"地形(属性)"tab 微调
        new_dict = compute_provincial_terrain_from_bmp(
            map_data.terrain_map, map_data.province_map, map_data.tile_map
        )
        map_data.provincial_terrain.clear()
        map_data.provincial_terrain.update(new_dict)
        self._project.mark_dirty()
        # 自动生成地形 → colormap 要重生
        self._project.mark_assets_dirty(
            "map/terrain/colormap_rgb_cityemissivemask_a.dds",
        )
        # 通知 canvas 地形数据已变 (触发重新渲染)
        self._canvas.terrain_map = map_data.terrain_map
        self._status_info.setText(
            tr("status_auto_terrain_done") + tr("status_auto_terrain_synced", len(new_dict))
        )

    def _on_auto_height(self) -> None:
        from services.terrain_service import smart_auto_height
        self._status_info.setText(tr("status_auto_height"))
        self.repaint()
        config = None
        height_page = self._tool_panel._height_page
        if hasattr(height_page, 'get_height_config'):
            config = height_page.get_height_config()
        map_data = self._project.map_data
        new_height = smart_auto_height(map_data.tile_map, config)
        # 同时更新 map_data 和 canvas (两边共享同一个数组)
        map_data.height_map[:] = new_height
        self._canvas.height_map = map_data.height_map
        self._project.mark_dirty()
        # 自动生成高度 → world_normal / colormap 要重生
        self._project.mark_assets_dirty(
            "map/world_normal.bmp",
            "map/terrain/colormap_rgb_cityemissivemask_a.dds",
        )
        self._status_info.setText(tr("status_auto_height_done"))

    def _on_smooth_height(self) -> None:
        from services.terrain_service import smooth_height
        self._canvas.height_map = smooth_height(self._canvas.height_map)
        self._status_info.setText(tr("status_height_smoothed"))

    # ── 山脉画线 ──

    def _on_ridge_mode(self, enabled: bool) -> None:
        """切换山脉画线模式 — 同步到 canvas。"""
        self._ridge_mode = enabled
        self._canvas._ridge_mode = enabled
        if enabled:
            self._status_info.setText(tr("status_ridge_mode_on"))
        else:
            # 退出模式时取消预览
            if hasattr(self, '_ridge_backup'):
                self._on_ridge_cancel()
            self._status_info.setText(tr("status_ridge_mode_off"))

    def _on_ridge_drawn(self, points: list) -> None:
        """canvas 画线完成 → 进入预览模式（不立即应用）。"""
        if len(points) < 2:
            return
        # 间隔采样
        if len(points) > 100:
            step = len(points) // 100
            points = points[::step] + [points[-1]]

        # 保存原始高度图 + 画线路径
        self._ridge_backup = self._project.map_data.height_map.copy()
        self._ridge_points = points

        # 显示确认/取消按钮
        self._tool_panel._height_page.show_ridge_confirm()

        # 立即生成预览
        self._apply_ridge_preview()
        self._status_info.setText(tr("status_ridge_preview"))

    def _apply_ridge_preview(self) -> None:
        """用当前参数生成山脉预览（不修改 backup）。"""
        if not hasattr(self, '_ridge_backup') or self._ridge_backup is None:
            return
        from services.terrain_service import apply_mountain_ridge
        map_data = self._project.map_data
        peak = getattr(self, '_ridge_peak', 220)
        falloff = getattr(self, '_ridge_falloff', 80)

        preview = apply_mountain_ridge(
            self._ridge_backup, map_data.tile_map,
            self._ridge_points, peak_height=peak, falloff_distance=float(falloff),
        )
        map_data.height_map[:] = preview
        self._canvas.height_map = map_data.height_map
        self._canvas._full_render()

    def _on_ridge_preview(self) -> None:
        """滑块变化 → 刷新预览。"""
        self._apply_ridge_preview()

    def _on_ridge_confirm(self) -> None:
        """确认山脉 → 应用到高度图，清理预览状态。"""
        self._ridge_backup = None
        self._ridge_points = None
        self._tool_panel._height_page.hide_ridge_confirm()
        # 线已经画在 canvas 上，隐藏它
        self._canvas._split_line_item.setVisible(False)
        self._project.mark_dirty()
        self._status_info.setText(tr("status_ridge_applied"))

    def _on_ridge_cancel(self) -> None:
        """取消山脉 → 恢复原始高度图。"""
        if hasattr(self, '_ridge_backup') and self._ridge_backup is not None:
            self._project.map_data.height_map[:] = self._ridge_backup
            self._canvas.height_map = self._project.map_data.height_map
            self._canvas._full_render()
        self._ridge_backup = None
        self._ridge_points = None
        self._tool_panel._height_page.hide_ridge_confirm()
        self._canvas._split_line_item.setVisible(False)
        self._status_info.setText(tr("status_ridge_mode_on"))

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
            QMessageBox.warning(self, tr("dlg_error"), tr("dlg_continent_add_failed"))

    def _on_continent_rename(self, index: int, name: str) -> None:
        from controllers.continent import ContinentController
        ctrl: ContinentController = self._controllers["continent"]
        if ctrl.rename_continent(index, name):
            self._refresh_continent_list()
        else:
            QMessageBox.warning(self, tr("dlg_error"), tr("dlg_continent_rename_failed"))

    def _on_continent_remove(self, index: int) -> None:
        from controllers.continent import ContinentController
        ctrl: ContinentController = self._controllers["continent"]
        if ctrl.remove_continent(index):
            self._refresh_continent_list()
        else:
            QMessageBox.warning(self, tr("dlg_error"), tr("dlg_continent_delete_failed"))

    def _refresh_continent_list(self) -> None:
        from PyQt5.QtWidgets import QListWidgetItem
        lst = self._tool_panel._continent_list
        lst.clear()
        cm = self._project.continent_mgr
        for i, name in enumerate(cm.names):
            count = sum(1 for ci in cm._province_continent.values() if ci == i)
            lst.addItem(QListWidgetItem(f"{i+1}. {name}  ({count} {tr('unit_provinces')})"))

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
        self._tool_panel._sr_prov_count.setText(tr("sr_prov_count").format(len(r.province_ids)))

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
                f"#{r.id} {r.name}  ({len(r.province_ids)}{tr('unit_provinces')}, "
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
        dlg = AdjacencyDialog(
            self._project.adjacency_mgr, parent=self,
            province_map=self._canvas.province_map,
            tile_map=self._canvas.tile_map,
        )
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
            self, tr("defmap_add_btn"), tr("dlg_defmap_palette_prompt"), value=4, min=1, max=13
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
        # 保存语言设置
        import json, os
        config_path = os.path.join(os.path.expanduser("~"), ".hoi4_map_maker.json")
        config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
            except Exception:
                pass
        config["language"] = new_lang
        with open(config_path, "w") as f:
            json.dump(config, f)

        reply = QMessageBox.question(
            self,
            "Language / 语言",
            "Language changed. Restart to apply.\n语言已切换，重启软件生效。\n\nRestart now? / 现在重启？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            import sys
            from PyQt5.QtWidgets import QApplication
            QApplication.quit()
            os.execl(sys.executable, sys.executable, *sys.argv)

    def _on_about(self) -> None:
        QMessageBox.about(
            self, tr("action_about"),
            tr("dlg_about_body"),
        )
