"""
主窗口文件操作 — 新建/打开/保存/导入/导出。
从 views/main_window_actions.py 拆分，作为 mixin 使用。
"""
from __future__ import annotations

import numpy as np
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QApplication, QInputDialog,
)
from PyQt5.QtGui import QColor

from ui.i18n import tr
from data.constants import (
    TILE_SEA, TILE_LAND,
    DEFAULT_MOD_OUTPUT_PATH,
)


def _populate_imported_data(project, result: dict) -> None:
    """把导入的 states 和 strategic regions 数据填充到 project 的 manager 里。"""
    from domain.managers.state import StateData

    # 填充 states
    for sd in result.get("states", []):
        state = StateData(
            id=sd["id"],
            name=sd.get("name", f"STATE_{sd['id']}"),
            provinces=sd.get("provinces", []),
            manpower=sd.get("manpower", 100000),
            category=sd.get("category", "town"),
            owner_tag=sd.get("owner", ""),
        )
        project.state_mgr.states[sd["id"]] = state
        for pid in state.provinces:
            project.state_mgr._province_to_state[pid] = sd["id"]
    # 更新 _next_id
    if project.state_mgr.states:
        project.state_mgr._next_id = max(project.state_mgr.states.keys()) + 1

    # 填充 strategic regions
    sr_mgr = project.strategic_region_mgr
    for rd in result.get("strategic_regions", []):
        r = sr_mgr.create_region(name=rd.get("name", ""))
        # create_region 自动分配 ID，但我们要用原始 ID
        # 先删掉自动分配的，再用原始 ID 放回
        auto_id = r.id
        sr_mgr._regions.pop(auto_id, None)
        r.id = rd["id"]
        r.province_ids = rd.get("provinces", [])
        sr_mgr._regions[r.id] = r
    if sr_mgr._regions:
        sr_mgr._next_id = max(sr_mgr._regions.keys()) + 1

    # 填充 country（从 states 的 owner 提取）
    owners = set(sd.get("owner", "") for sd in result.get("states", []))
    owners.discard("")
    for tag in sorted(owners):
        if tag not in project.country_mgr.countries:
            project.country_mgr.create_country(tag, name=tag)
        # 分配 state 到国家
        for sd in result.get("states", []):
            if sd.get("owner") == tag:
                project.country_mgr.assign_state(sd["id"], tag)

    # 填充 railways
    for rd in result.get("railways", []):
        try:
            project.railway_mgr.add(rd["level"], rd["province_ids"])
        except (ValueError, KeyError):
            pass  # 跳过格式不合法的铁路

    # 填充 supply_nodes
    for sd in result.get("supply_nodes", []):
        try:
            project.supply_mgr.add(sd["province_id"], sd["level"])
        except (ValueError, KeyError):
            pass

    # 填充 adjacencies
    from domain.managers.adjacency import AdjacencyEntry
    for ad in result.get("adjacencies", []):
        entry = AdjacencyEntry(
            from_id=ad["from_id"],
            to_id=ad["to_id"],
            type=ad.get("type", "sea"),
            through_id=ad.get("through_id", -1),
            start_x=ad.get("start_x", -1),
            start_y=ad.get("start_y", -1),
            stop_x=ad.get("stop_x", -1),
            stop_y=ad.get("stop_y", -1),
            rule_name=ad.get("rule", ""),
            comment=ad.get("comment", ""),
        )
        project.adjacency_mgr.add(entry)


class MainWindowFileOpsMixin:
    """文件/导入/导出/测试导出操作，混入 MainWindow。"""

    # ═══════════════════════ 导出 ═══════════════════════════

    def _on_export_mod(self) -> None:
        from views.export_dialog import ExportDialog
        dlg = ExportDialog(self._project, self._canvas, parent=self)
        dlg.exec_()

    # ═══════════════════════ 新建/打开/保存 ═══════════════

    def _on_new_project(self) -> None:
        reply = QMessageBox.question(
            self, tr("dlg_confirm"),
            "新建项目将清除当前数据，是否继续？",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        from data.constants import MAP_SIZE_PRESETS, set_map_size
        presets = list(MAP_SIZE_PRESETS.keys())
        default_idx = len(presets) - 1
        for i, name in enumerate(presets):
            if "原版" in name:
                default_idx = i
                break

        chosen, ok = QInputDialog.getItem(
            self, "选择地图尺寸", "选择新项目的地图尺寸：",
            presets, default_idx, False,
        )
        if not ok:
            return

        new_w, new_h = MAP_SIZE_PRESETS[chosen]
        set_map_size(new_w, new_h)

        self._canvas.tile_map = np.full((new_h, new_w), TILE_SEA, dtype=np.uint8)
        self._canvas.province_map = np.zeros((new_h, new_w), dtype=np.int32)
        self._canvas.terrain_map = np.zeros((new_h, new_w), dtype=np.uint8)
        self._canvas.height_map = np.full((new_h, new_w), 40, dtype=np.uint8)
        self._canvas.river_map = np.zeros((new_h, new_w), dtype=np.uint8)
        self._project.state_mgr.clear()
        self._project.country_mgr.clear()
        self._cmd_history.clear()
        self._update_province_count()
        self._canvas.refresh_display()
        self._status_info.setText(f"新项目已创建 ({new_w}×{new_h})")
        if hasattr(self, '_show_editor'):
            self._show_editor()

    def _on_save_project(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "保存项目", "", "HOI4 项目 (*.hoi4proj);;All Files (*)"
        )
        if not path:
            return
        try:
            from services.project_service import save_project
            save_project(
                path, self._canvas, self._project.state_mgr,
                self._project.country_mgr, self._project.continent_mgr,
                adjacency_mgr=self._project.adjacency_mgr,
                railway_mgr=self._project.railway_mgr,
                supply_mgr=self._project.supply_mgr,
                adjacency_rule_mgr=self._project.adjacency_rule_mgr,
                strategic_region_mgr=self._project.strategic_region_mgr,
            )
            self._status_info.setText(f"项目已保存: {path}")
            # 记录到最近项目
            from views.welcome_page import save_recent_project
            save_recent_project(path)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def _on_open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "打开项目", "", "HOI4 项目 (*.hoi4proj);;All Files (*)"
        )
        if not path:
            return
        self._load_project_file(path)

    def _load_project_file(self, path: str) -> None:
        """加载指定路径的项目文件。"""
        try:
            from services.project_service import load_project
            load_project(
                path, self._canvas, self._project.state_mgr,
                self._project.country_mgr, self._project.continent_mgr,
                adjacency_mgr=self._project.adjacency_mgr,
                railway_mgr=self._project.railway_mgr,
                supply_mgr=self._project.supply_mgr,
                adjacency_rule_mgr=self._project.adjacency_rule_mgr,
                strategic_region_mgr=self._project.strategic_region_mgr,
            )
            self._update_province_count()
            self._app._refresh_state_list()
            self._app._refresh_country_list()
            self._status_info.setText(f"项目已加载: {path}")
            # 记录到最近项目 + 切换到编辑器
            from views.welcome_page import save_recent_project
            save_recent_project(path)
            if hasattr(self, '_show_editor'):
                self._show_editor()
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))

    # ═══════════════════════ 参考图/导入 ═══════════════════════

    def _on_load_vanilla_ref(self) -> None:
        from data.constants import DEFAULT_HOI4_PATH
        import os
        candidates = [
            os.path.join(DEFAULT_HOI4_PATH, "map", "provinces.bmp"),
            os.path.join(DEFAULT_HOI4_PATH, "map", "terrain",
                         "colormap_rgb_cityemissivemask_a.dds"),
        ]
        for path in candidates:
            if os.path.exists(path):
                if self._canvas.load_vanilla_reference(path):
                    self._status_info.setText(
                        f"原版地图参考已加载: {os.path.basename(path)}"
                    )
                    return
        QMessageBox.warning(
            self, "错误",
            f"未找到原版地图文件\n检查路径: {DEFAULT_HOI4_PATH}",
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
        """从真实地图提取陆海"""
        from PIL import Image

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择陆海源图", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)",
        )
        if not file_path:
            return

        threshold, ok = QInputDialog.getInt(
            self, "陆海阈值",
            "灰度阈值 (0-255)\n>= 阈值为陆地，< 阈值为海洋\n"
            "建议：高度图用 1；卫星图用 90 左右",
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
            from data.constants import MAP_WIDTH, MAP_HEIGHT
            img = img.resize((MAP_WIDTH, MAP_HEIGHT), Image.Resampling.LANCZOS)
            arr = np.array(img, dtype=np.uint8)
            land_mask = (arr < threshold) if invert else (arr >= threshold)
        except Exception as e:
            QMessageBox.warning(self, tr("dlg_error"), f"读取图片失败：{e}")
            return

        # 通过 BrushStrokeCommand 记录快照（统一走 CommandHistory）
        from commands.land.brush_stroke import BrushStrokeCommand
        before = BrushStrokeCommand.snapshot_arrays({"tile_map": self._canvas.tile_map})

        new_tm = np.where(land_mask, TILE_LAND, TILE_SEA).astype(np.uint8)
        self._canvas.tile_map[:] = new_tm
        from domain.generators.province import auto_classify_water
        auto_classify_water(self._canvas.tile_map)

        # 提交撤销命令
        after = BrushStrokeCommand.snapshot_arrays({"tile_map": self._canvas.tile_map})
        cmd = BrushStrokeCommand("从图片提取陆海", before, after)
        cmd.set_target_arrays({"tile_map": self._canvas.tile_map})
        self._cmd_history._undo_stack.append(cmd)
        self._cmd_history._redo_stack.clear()
        self._cmd_history._notify()

        self._canvas.refresh_display()

        from data.constants import MAP_WIDTH, MAP_HEIGHT
        land_n = int(land_mask.sum())
        total = MAP_WIDTH * MAP_HEIGHT
        self._status_info.setText(
            f"陆海导入完成 — 陆地 {land_n/total*100:.1f}%"
            f" / 海洋 {(1-land_n/total)*100:.1f}%"
        )

    def _on_import_mod_map(self) -> None:
        """从 HOI4 mod/vanilla 目录导入地图图层"""
        reply = QMessageBox.question(
            self, tr("dlg_confirm"),
            "导入将替换当前地图数据，是否继续？",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        mod_dir = QFileDialog.getExistingDirectory(
            self, "选择 HOI4 MOD 或原版目录",
            "", QFileDialog.Option.ShowDirsOnly,
        )
        if not mod_dir:
            return

        from services.import_service import validate_mod_directory, import_mod_map

        missing = validate_mod_directory(mod_dir)
        if missing:
            QMessageBox.warning(
                self, tr("dlg_error"),
                f"目录缺少必需文件:\n" + "\n".join(missing),
            )
            return

        try:
            result = import_mod_map(mod_dir)
        except Exception as e:
            QMessageBox.warning(self, tr("dlg_error"), f"导入失败：{e}")
            return

        new_w, new_h = result["width"], result["height"]

        # 更新全局地图尺寸
        from data.constants import set_map_size
        set_map_size(new_w, new_h)

        # 通过 Project 统一更新（保持 canvas 和 project 的 map_data 同步）
        from domain.map_data import MapData
        md = MapData()
        # 直接替换数组引用（尺寸可能不同，不能用 [:] 原地写入）
        md.tile_map = result["tile_map"]
        md.province_map = result["province_map"]
        md.terrain_map = result["terrain_map"]
        md.height_map = result["height_map"]
        if result["river_map"] is not None:
            md.river_map = result["river_map"]
        md.provincial_terrain = result.get("provincial_terrain", {})

        self._project.map_data = md
        self._project.state_mgr.clear()
        self._project.country_mgr.clear()
        self._project.continent_mgr.clear()
        self._project.strategic_region_mgr.clear()
        self._project.railway_mgr.clear()
        self._project.supply_mgr.clear()
        self._project.adjacency_mgr.clear()
        self._cmd_history.clear()

        # 保留导入的美术资产（colormap/world_normal 等），导出时不会覆盖
        imported_assets = result.get("assets", {})
        self._project.assets = dict(imported_assets)
        self._project.dirty_assets = set()

        # 填充 states 数据
        _populate_imported_data(self._project, result)

        # 让 canvas 使用同一个 map_data
        self._canvas.set_map_data(md)
        self._canvas._scene.setSceneRect(0, 0, new_w, new_h)
        self._canvas.refresh_display()
        self._update_province_count()
        # 刷新 State/Country 着色（导入后切模式才能看到颜色）
        self._app._refresh_state_colors()
        self._app._refresh_country_colors()
        self._app._refresh_country_list()
        self._app._refresh_state_list()
        self._project.mark_dirty()

        state_count = len(self._project.state_mgr.states)
        sr_count = self._project.strategic_region_mgr.count()
        asset_count = len(self._project.assets)
        info_text = (f"MOD地图已导入 ({new_w}×{new_h}, {result['province_count']} 省份, "
                     f"{state_count} 州, {sr_count} 战略区域, {asset_count} 美术资产)")
        self._status_info.setText(info_text)

        warnings_text = ""
        if result["warnings"]:
            warnings_text = "\n\n注意:\n" + "\n".join(f"- {w}" for w in result["warnings"])
        QMessageBox.information(
            self, "导入完成", info_text + warnings_text
        )

    # ═══════════════════════ 测试导出 ═══════════════════════

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
        from PyQt5.QtWidgets import (
            QDialog, QVBoxLayout, QRadioButton,
            QDialogButtonBox, QLabel, QGroupBox,
        )

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
            QMessageBox.critical(
                self, "导出失败", f"{e}\n\n{traceback.format_exc()}"
            )
        finally:
            self._status_info.setText(tr("status_ready"))
