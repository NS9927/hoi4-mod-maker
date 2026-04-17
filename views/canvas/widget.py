"""
地图画布组件 — 基于 QGraphicsView 的大画布
支持六种编辑模式：land / terrain / height / province / state / country
性能优化：脏矩形局部更新，避免每次操作渲染整张地图

从 ui/canvas_widget.py 拆分而来，保留核心逻辑:
- __init__: 场景/图层/状态初始化
- 数据属性 (tile_map, province_map 等)
- 渲染分发 (_full_render / _partial_render)
- 绘制操作 (_stamp_brush / _paint_at / _flood_fill)
- 变换操作 (_apply_transform / _cancel_transform / _end_transform)
- 省份操作 (merge / split / cleanup)
- 模式/工具设置
- 导航辅助
"""
import numpy as np
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsRectItem,
)
from PyQt5.QtCore import Qt, QPoint, QRectF, QRect, pyqtSignal, QTimer
from PyQt5.QtGui import (
    QImage, QPixmap, QPainter, QColor, QWheelEvent, QMouseEvent,
    QPen, QPainterPath, QBrush, QKeyEvent,
)

from data.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    TILE_UNDEFINED, TILE_LAND, TILE_SEA, TILE_LAKE,
    ZOOM_MIN, ZOOM_MAX, ZOOM_STEP,
    BRUSH_DEFAULT,
)
from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX, GRAPHICAL_TERRAINS, PALETTE_TO_TYPE
from domain.managers.river import (
    RIVER_DISPLAY_COLORS, RIVER_SOURCE, RIVER_BG_LAND, RIVER_BG_SEA,
    RIVER_ERASE, VALID_RIVER_VALUES,
)

from views.canvas.ref_images import RefImageMixin
from views.canvas.overlays import OverlayMixin
from views.canvas.input_router import InputMixin


class MapCanvas(InputMixin, OverlayMixin, RefImageMixin, QGraphicsView):
    """地图画布，支持缩放/拖动/绘制，脏矩形局部更新"""

    mouse_moved = pyqtSignal(int, int)
    zoom_changed = pyqtSignal(float)
    province_clicked = pyqtSignal(int)
    province_double_clicked = pyqtSignal(int)   # 双击省份（设VP）
    province_right_clicked = pyqtSignal(int)    # 右键省份（设首都）
    province_right_clicked_at = pyqtSignal(int, int, int)  # pid, screen_x, screen_y (右键菜单用)
    provinces_cleared = pyqtSignal()  # 大陆模式修改时自动清除省份
    stroke_started = pyqtSignal()     # 画笔操作开始
    stroke_ended = pyqtSignal()       # 画笔操作结束
    ridge_drawn = pyqtSignal(list)    # 山脉画线完成, [(y,x), ...]
    split_line_drawn = pyqtSignal(int, list)  # 切割线完成, (pid, [(y,x), ...])
    province_gaps_detected = pyqtSignal(list)  # 省份 ID 空洞, [gap_id, ...]

    def __init__(self, parent=None):
        super().__init__(parent)

        # 数据层 — 通过 MapData 集中管理
        # 私有字段是 MapData 数组的别名（指向同一个 numpy 对象）
        from domain.map_data import MapData
        self._map_data = MapData()
        self._tile_map = self._map_data.tile_map
        self._province_map = self._map_data.province_map
        self._terrain_map = self._map_data.terrain_map
        self._height_map = self._map_data.height_map
        self._river_map = self._map_data.river_map

        # 河流编辑状态
        self._current_river_type = RIVER_SOURCE

        # 地形画笔模式: False=按省份(默认), True=逐像素画笔
        self._terrain_brush_mode = False

        # 显示缓冲区（BGRA）
        self._display_buffer = np.zeros((MAP_HEIGHT, MAP_WIDTH, 4), dtype=np.uint8)
        self._province_border_buffer = None  # 延迟创建

        # State / Country 颜色缓冲区
        self._state_color_rgb = None   # np.ndarray (H, W, 3) or None
        self._country_color_rgb = None  # np.ndarray (H, W, 3) or None
        # 省份属性地形（gameplay terrain）颜色缓冲区
        self._provincial_terrain_color_rgb = None  # np.ndarray (H, W, 3) or None

        # 显示/编辑模式
        self._display_mode = "land"

        # 框架工具（新规范）：当不为 None 时，鼠标事件转发给它
        self._framework_tool = None     # core.tools.base.Tool 实例
        self._framework_ctx = None       # ToolContext

        # 当前状态
        self._zoom = 1.0
        self._current_tool = "brush"
        self._current_tile_type = TILE_LAND
        self._current_terrain_index = 0
        self._selected_province_id = 0  # 省份模式下选中的省份ID
        self._selected_province_tile = 0  # 选中省份的地块类型（边界编辑时只能影响同类型像素）
        self._has_provinces = False     # 是否有省份数据（避免每笔都扫描整张图）
        self._current_height_value = 120
        self._brush_size = BRUSH_DEFAULT
        self._is_drawing = False
        self._is_panning = False
        self._pan_start = QPoint()
        self._space_pressed = False
        self._last_draw_pos = None  # 上一次绘制位置，用于插值连线
        self._show_ref_image = True
        self._show_provinces = True

        # 框选模式
        self._selection_mode = False
        self._selection_rect = None  # (x0, y0, x1, y1) scene coords
        self._selection_start = None
        self._selection_callback = None  # 框选完成后的回调

        # 变换工具状态
        self._transform_active = False    # 变换框是否激活
        self._transform_selecting = False # 正在框选阶段
        self._transform_box = None       # (x0, y0, x1, y1) 当前变换框
        self._transform_snippet = None   # 剪切出的 tile_map 片段 (numpy)
        self._transform_orig_box = None  # 原始框位置
        self._transform_drag = None      # 当前拖拽类型: "move"/"tl"/"tr"/"bl"/"br"/"rotate"/None
        self._transform_drag_start = None
        self._transform_angle = 0.0      # 旋转角度（度）

        # 脏矩形（需要刷新的区域）
        self._dirty_rect = None  # (x0, y0, x1, y1) 或 None

        # 延迟渲染定时器（合并连续绘制操作）
        self._render_timer = QTimer()
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(16)  # ~60fps
        self._render_timer.timeout.connect(self._flush_dirty)

        # 场景和图层
        self._scene = QGraphicsScene(self)
        self._scene.setSceneRect(0, 0, MAP_WIDTH, MAP_HEIGHT)
        self.setScene(self._scene)

        self._map_pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._map_pixmap_item)

        # 原版地图参考层 (底层)
        self._vanilla_ref_item = QGraphicsPixmapItem()
        self._vanilla_ref_item.setOpacity(0.3)
        self._vanilla_ref_item.setZValue(1)
        self._scene.addItem(self._vanilla_ref_item)

        # 用户自定义参考图层 (上层)
        self._ref_pixmap_item = QGraphicsPixmapItem()
        self._ref_pixmap_item.setOpacity(0.4)
        self._ref_pixmap_item.setZValue(2)
        self._scene.addItem(self._ref_pixmap_item)

        self._province_pixmap_item = QGraphicsPixmapItem()
        self._province_pixmap_item.setOpacity(0.6)
        self._province_pixmap_item.setZValue(2)
        self._scene.addItem(self._province_pixmap_item)

        # 框选矩形（用于框选放大等功能）
        self._selection_rect_item = QGraphicsRectItem()
        self._selection_rect_item.setPen(QPen(QColor(255, 255, 0), 2, Qt.DashLine))
        self._selection_rect_item.setBrush(QBrush(QColor(255, 255, 0, 30)))
        self._selection_rect_item.setZValue(100)
        self._selection_rect_item.setVisible(False)
        self._scene.addItem(self._selection_rect_item)

        # 切割预览线
        from PyQt5.QtWidgets import QGraphicsPathItem
        self._split_line_item = QGraphicsPathItem()
        self._split_line_item.setPen(QPen(QColor(255, 80, 80), 2, Qt.SolidLine))
        self._split_line_item.setZValue(102)
        self._split_line_item.setVisible(False)
        self._scene.addItem(self._split_line_item)

        # 变换框（边框 + 4 个角 handle）
        self._transform_border = QGraphicsRectItem()
        self._transform_border.setPen(QPen(QColor(0, 200, 255), 2))
        self._transform_border.setBrush(QBrush(Qt.NoBrush))
        self._transform_border.setZValue(101)
        self._transform_border.setVisible(False)
        self._scene.addItem(self._transform_border)

        self._transform_handles: dict[str, QGraphicsRectItem] = {}
        for hid in ("tl", "tr", "bl", "br"):
            h = QGraphicsRectItem(-4, -4, 8, 8)
            h.setPen(QPen(QColor(0, 200, 255), 1))
            h.setBrush(QBrush(QColor(255, 255, 255)))
            h.setZValue(102)
            h.setVisible(False)
            self._scene.addItem(h)
            self._transform_handles[hid] = h

        # 画笔预览光标（半透明圆圈）
        self._brush_cursor = QGraphicsEllipseItem()
        self._brush_cursor.setPen(QPen(QColor(255, 255, 255, 180), 1))
        self._brush_cursor.setBrush(QColor(255, 255, 255, 40))
        self._brush_cursor.setZValue(10)
        self._brush_cursor.setVisible(False)
        self._scene.addItem(self._brush_cursor)

        # 密度叠加层
        self._density_overlay_item = QGraphicsPixmapItem()
        self._density_overlay_item.setZValue(5)
        self._density_overlay_item.setVisible(False)
        self._density_overlay_visible = False
        self._scene.addItem(self._density_overlay_item)

        # 套索路径反馈（黄色虚线）
        self._lasso_path_item = QGraphicsPathItem()
        pen = QPen(QColor(255, 230, 0, 230), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setCosmetic(True)  # 不随缩放变粗细
        self._lasso_path_item.setPen(pen)
        self._lasso_path_item.setZValue(11)
        self._lasso_path_item.setVisible(False)
        self._scene.addItem(self._lasso_path_item)

        # 山脉画线路径反馈（红色实线，比套索粗）
        self._ridge_path_item = QGraphicsPathItem()
        ridge_pen = QPen(QColor(230, 60, 60, 240), 3)
        ridge_pen.setStyle(Qt.PenStyle.SolidLine)
        ridge_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        ridge_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        ridge_pen.setCosmetic(True)
        self._ridge_path_item.setPen(ridge_pen)
        self._ridge_path_item.setZValue(12)
        self._ridge_path_item.setVisible(False)
        self._scene.addItem(self._ridge_path_item)

        # 套索 allowed 区域 overlay（半透明黄色填充）
        self._lasso_overlay = QGraphicsPixmapItem()
        self._lasso_overlay.setZValue(9)
        self._lasso_overlay.setVisible(False)
        self._scene.addItem(self._lasso_overlay)

        # VP 标记叠加层 (Feature 10)
        self._vp_overlay_item = QGraphicsPixmapItem()
        self._vp_overlay_item.setZValue(5)
        self._vp_overlay_item.setVisible(False)
        self._scene.addItem(self._vp_overlay_item)
        self._vp_data: dict[int, int] = {}  # {province_id: vp_value}

        # 视图设置
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.setStyleSheet("background: #050a12; border: none;")

        # 初始全量渲染
        self._full_render()

    # ========== 动态地图尺寸 ==========

    @property
    def map_h(self) -> int:
        return self._display_buffer.shape[0]

    @property
    def map_w(self) -> int:
        return self._display_buffer.shape[1]

    # ========== 数据访问 ==========

    def set_map_data(self, map_data) -> None:
        """替换底层 MapData 并重新绑定所有局部别名。

        调用时机：MainWindow 初始化后 / 新建项目 / 加载项目，
        让 canvas 和 project 共享同一个 MapData 实例，
        这样 controller 通过 Command 修改 project.map_data 的数组时，
        canvas 也能立即看到变化。
        """
        self._map_data = map_data
        self._tile_map = map_data.tile_map
        self._province_map = map_data.province_map
        self._terrain_map = map_data.terrain_map
        self._height_map = map_data.height_map
        self._river_map = map_data.river_map
        self._has_provinces = int(self._province_map.max()) > 0
        # 清除所有缓存
        self._border_cache = None
        if hasattr(self, '_border_base_pixmap'):
            self._border_base_pixmap = None
        self._state_color_rgb = None
        self._country_color_rgb = None
        h, w = map_data.tile_map.shape[0], map_data.tile_map.shape[1]
        self._display_buffer = np.zeros((h, w, 4), dtype=np.uint8)
        self._scene.setSceneRect(0, 0, w, h)

    @property
    def map_data(self):
        """暴露 MapData 给外部使用高级查询方法（get_neighbors 等）。"""
        return self._map_data

    def set_framework_tool(self, tool_name: str | None, undo_mgr=None,
                            state_mgr=None, country_mgr=None) -> None:
        """启用/禁用一个框架工具。tool_name=None 关闭。"""
        from domain.tools import get_tool, ToolContext

        if tool_name is None:
            if self._framework_tool is not None and self._framework_ctx is not None:
                self._framework_tool.on_cancel(self._framework_ctx)
            self._framework_tool = None
            self._framework_ctx = None
            self._clear_lasso_visual()
            self._render_province_overlay()
            return

        tool = get_tool(tool_name)
        if tool is None:
            return
        if undo_mgr is None:
            return
        self._framework_tool = tool
        self._framework_ctx = ToolContext(
            map_data=self._map_data,
            undo_mgr=undo_mgr,
            state_mgr=state_mgr,
            country_mgr=country_mgr,
            display_mode=self._display_mode,
            brush_size=self._brush_size,
        )

    def _set_layer(self, attr: str, data: np.ndarray, dtype) -> None:
        """统一的图层替换：写入 MapData，同步本地别名。

        如果形状相同，原地写入以保持引用稳定（controller/command 持有的引用不会失效）。
        形状不同时（地图尺寸变化）才替换整个数组。
        """
        existing = getattr(self._map_data, attr, None)
        if existing is not None and existing.shape == data.shape:
            existing[:] = data.astype(dtype)
            # 别名仍指向同一对象，无需更新
        else:
            new_arr = data.astype(dtype)
            setattr(self._map_data, attr, new_arr)
            setattr(self, "_" + attr, new_arr)
            # 地图尺寸变化时，同步 display_buffer 和 scene rect
            h, w = new_arr.shape[:2]
            if (h, w) != (self._display_buffer.shape[0], self._display_buffer.shape[1]):
                self._display_buffer = np.zeros((h, w, 4), dtype=np.uint8)
                self._scene.setSceneRect(0, 0, w, h)

    def _rebind_aliases(self) -> None:
        """重新绑定局部别名到 MapData 当前属性。

        当 Command 或外部代码替换了 MapData 的某个属性（而非原地修改），
        canvas 的 _tile_map 等局部别名会过期。调用此方法刷新。
        """
        self._tile_map = self._map_data.tile_map
        self._province_map = self._map_data.province_map
        self._terrain_map = self._map_data.terrain_map
        self._height_map = self._map_data.height_map
        self._river_map = self._map_data.river_map

    @property
    def tile_map(self) -> np.ndarray:
        return self._tile_map

    @tile_map.setter
    def tile_map(self, data: np.ndarray) -> None:
        self._set_layer("tile_map", data, np.uint8)
        if self._display_mode == "land":
            self._full_render()

    @property
    def province_map(self) -> np.ndarray:
        return self._province_map

    @province_map.setter
    def province_map(self, data: np.ndarray) -> None:
        self._set_layer("province_map", data, np.int32)
        self._has_provinces = int(self._province_map.max()) > 0
        # 省份数据变了，清除边界缓存以便下次重建
        self._border_cache = None
        if hasattr(self, '_border_base_pixmap'):
            self._border_base_pixmap = None
        if self._display_mode == "province":
            self._full_render()
        self._render_province_overlay()

    @property
    def terrain_map(self) -> np.ndarray:
        return self._terrain_map

    @terrain_map.setter
    def terrain_map(self, data: np.ndarray) -> None:
        self._set_layer("terrain_map", data, np.uint8)
        if self._display_mode == "terrain":
            self._full_render()

    @property
    def height_map(self) -> np.ndarray:
        return self._height_map

    @height_map.setter
    def height_map(self, data: np.ndarray) -> None:
        self._set_layer("height_map", data, np.uint8)
        if self._display_mode == "height":
            self._full_render()

    @property
    def river_map(self) -> np.ndarray:
        return self._river_map

    @river_map.setter
    def river_map(self, data: np.ndarray) -> None:
        self._set_layer("river_map", data, np.uint8)
        if self._display_mode == "river":
            self._full_render()

    def set_river_type(self, river_type: int) -> None:
        self._current_river_type = max(0, min(255, river_type))

    @property
    def display_mode(self) -> str:
        return self._display_mode

    @display_mode.setter
    def display_mode(self, mode: str) -> None:
        _VALID = (
            "land", "terrain", "height", "province",
            "state", "country", "river", "logistics",
            "continent", "strategic_region", "colormap", "default_map",
            "province_terrain",
        )
        if mode not in _VALID:
            return
        if mode == self._display_mode:
            return
        self._display_mode = mode
        self._full_render()
        # 后勤模式：自动显示 supply/railway overlay
        if mode == "logistics":
            self.refresh_logistics_overlay()
        elif self._lasso_overlay.isVisible():
            # 离开后勤模式：清掉后勤 overlay（但套索/批量选择的 overlay 会被别处管理）
            # 只有在不是批量选择等状态时才清
            pass  # 先不动，让 set_batch_selection_pids 等管理

    # ========== 工具设置 ==========

    def set_tool(self, tool: str) -> None:
        self._current_tool = tool
        self.setCursor(Qt.CursorShape.OpenHandCursor if tool == "pan"
                       else Qt.CursorShape.CrossCursor)

    def set_tile_type(self, tile_type: int) -> None:
        self._current_tile_type = tile_type

    def set_brush_size(self, size: int) -> None:
        self._brush_size = max(1, min(100, size))

    def set_terrain_index(self, index: int) -> None:
        self._current_terrain_index = max(0, min(255, index))

    def set_terrain_brush_mode(self, brush_mode: bool) -> None:
        """切换地形编辑模式: True=画笔逐像素, False=按省份(默认)"""
        self._terrain_brush_mode = brush_mode

    def set_height_value(self, value: int) -> None:
        self._current_height_value = max(0, min(255, value))

    # ========== State / Country 颜色设置 ==========

    def set_state_colors(self, rgb: np.ndarray) -> None:
        """存储 State 颜色 RGB 数组并触发渲染"""
        self._state_color_rgb = rgb
        if self._display_mode == "state":
            self._full_render()

    def set_country_colors(self, rgb: np.ndarray) -> None:
        """存储 Country 颜色 RGB 数组并触发渲染"""
        self._country_color_rgb = rgb
        if self._display_mode == "country":
            self._full_render()

    def set_provincial_terrain_colors(self, rgb: np.ndarray) -> None:
        """存储省份属性地形 RGB 数组并触发渲染"""
        self._provincial_terrain_color_rgb = rgb
        if self._display_mode == "province_terrain":
            self._full_render()

    def set_batch_selection_pids(self, pids: list[int]) -> None:
        """高亮显示批量选中的省份（用于创建 state/country 等场景）。

        pids 为空时清除高亮。使用半透明黄色 overlay。
        """
        from PyQt5.QtGui import QImage, QPixmap
        if not pids or self._province_map is None:
            self._lasso_overlay.setVisible(False)
            return
        mask = np.isin(self._province_map, list(pids))
        h, w = self._province_map.shape
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        # 半透明亮黄（选中感），RGB 255,220,0 + alpha 100
        rgba[mask] = (255, 220, 0, 100)
        img = QImage(rgba.data, w, h, w * 4, QImage.Format.Format_ARGB32)
        img._ref = rgba  # 防止内存被释放
        self._lasso_overlay.setPixmap(QPixmap.fromImage(img))
        self._lasso_overlay.setVisible(True)

    def refresh_logistics_overlay(self) -> None:
        """后勤模式下绘制补给节点和铁路 overlay（在 _lasso_overlay 上画）。

        补给节点：小绿圆，半径=3+level
        铁路：彩色线（level 1=细灰 / level 5=粗红），线宽 = 1+level
        """
        from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QPen
        if self._province_map is None:
            self._lasso_overlay.setVisible(False)
            return

        pm = self._province_map
        h, w = pm.shape

        # 拿到 managers（挂在 canvas 实例上）
        supply_mgr = getattr(self, '_supply_mgr', None)
        railway_mgr = getattr(self, '_railway_mgr', None)
        if supply_mgr is None and railway_mgr is None:
            self._lasso_overlay.setVisible(False)
            return

        # 预计算省份质心（用于画节点/线条）
        max_pid = int(pm.max())
        if max_pid <= 0:
            return
        flat = pm.ravel()
        pid_count = np.bincount(flat, minlength=max_pid + 1)
        ys_grid, xs_grid = np.mgrid[0:h, 0:w]
        sum_y = np.bincount(flat, weights=ys_grid.ravel().astype(np.float64), minlength=max_pid + 1)
        sum_x = np.bincount(flat, weights=xs_grid.ravel().astype(np.float64), minlength=max_pid + 1)

        # 用 QPainter 在 transparent QImage 上画
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        img.fill(0)  # 全透明
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 铁路线（级别 1-5 颜色由灰到红，粗细从 2 到 6）
        RAIL_COLORS = {
            1: QColor(120, 120, 140, 200),  # 灰
            2: QColor(100, 160, 100, 210),  # 深绿
            3: QColor(230, 180, 60, 220),   # 金黄
            4: QColor(230, 130, 60, 230),   # 橙
            5: QColor(230, 60, 60, 240),    # 红（最高级）
        }
        if railway_mgr is not None:
            for entry in railway_mgr._entries:
                lvl = entry.level
                color = RAIL_COLORS.get(lvl, RAIL_COLORS[1])
                pen = QPen(color, 1 + lvl)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                # 把 province_ids 按顺序画线
                pts = []
                for pid in entry.province_ids:
                    if 0 < pid <= max_pid and pid_count[pid] > 0:
                        cx = sum_x[pid] / pid_count[pid]
                        cy = sum_y[pid] / pid_count[pid]
                        pts.append((cx, cy))
                for i in range(len(pts) - 1):
                    x1, y1 = pts[i]
                    x2, y2 = pts[i + 1]
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # 海峡/邻接 — 不在后勤 overlay 画（太多会乱），只在邻接对话框里管理
        # 如果需要可在邻接对话框打开时单独渲染

        # 补给节点（绿圆，中心有白心）
        if supply_mgr is not None:
            for pid, node in supply_mgr._nodes.items():
                if 0 < pid <= max_pid and pid_count[pid] > 0:
                    cx = int(sum_x[pid] / pid_count[pid])
                    cy = int(sum_y[pid] / pid_count[pid])
                    r = 5 + node.level  # 半径 6-10
                    # 绿色外圈
                    painter.setPen(QPen(QColor(0, 0, 0, 200), 2))
                    painter.setBrush(QColor(80, 220, 80, 230))
                    painter.drawEllipse(cx - r, cy - r, 2 * r, 2 * r)
                    # 白心
                    painter.setBrush(QColor(255, 255, 255, 255))
                    painter.drawEllipse(cx - 2, cy - 2, 4, 4)

        painter.end()
        self._lasso_overlay.setPixmap(QPixmap.fromImage(img))
        self._lasso_overlay.setVisible(True)

    # ── 变换工具 ──

    def _apply_transform(self) -> None:
        """将变换结果（缩放+旋转）写入 tile_map。"""
        if self._transform_snippet is None or self._transform_box is None:
            return

        from scipy.ndimage import zoom, rotate

        x0, y0, x1, y1 = [int(v) for v in self._transform_box]
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(self.map_w, x1); y1 = min(self.map_h, y1)
        tw, th = x1 - x0, y1 - y0
        if tw < 2 or th < 2:
            return

        # 1. 缩放 snippet 到目标尺寸
        src_h, src_w = self._transform_snippet.shape
        zy = th / src_h
        zx = tw / src_w
        scaled = zoom(self._transform_snippet.astype(np.float32), (zy, zx), order=0)
        scaled = np.round(scaled).astype(np.uint8)

        # 2. 旋转（如果有角度）
        if abs(self._transform_angle) > 0.5:
            # cval=TILE_SEA 填充旋转后的空白区域
            rotated = rotate(scaled.astype(np.float32), -self._transform_angle,
                             reshape=False, order=0, cval=float(TILE_SEA))
            scaled = np.round(rotated).astype(np.uint8)

        # 3. 先清除旧变换区域，再写入
        # 清除整个可能被影响的区域
        ox0, oy0, ox1, oy1 = self._transform_orig_box
        self._tile_map[oy0:oy1, ox0:ox1] = TILE_SEA  # 清原位
        # 也清当前框位置（可能被上次预览污染）
        self._tile_map[y0:y1, x0:x1] = TILE_SEA

        # 写入
        sh, sw = scaled.shape
        ph = min(sh, y1 - y0)
        pw = min(sw, x1 - x0)
        self._tile_map[y0:y0 + ph, x0:x0 + pw] = scaled[:ph, :pw]
        # _tile_map 和 _map_data.tile_map 是同一个数组，无需额外同步
        self._full_render()

    def _cancel_transform(self) -> None:
        """取消变换，恢复原始状态。"""
        if self._transform_snippet is not None and self._transform_orig_box is not None:
            # 恢复原始片段到原始位置
            ox0, oy0, ox1, oy1 = self._transform_orig_box
            self._tile_map[oy0:oy1, ox0:ox1] = self._transform_snippet
            # _tile_map 和 _map_data.tile_map 是同一个数组，无需额外同步
            self._full_render()
        self._end_transform()

    def _end_transform(self) -> None:
        """清理变换状态。"""
        self._transform_active = False
        self._transform_selecting = False
        self._transform_box = None
        self._transform_snippet = None
        self._transform_orig_box = None
        self._transform_drag = None
        self._transform_angle = 0.0
        self._update_transform_visuals()

    # ── 框选模式 ──

    def start_selection_mode(self, callback) -> None:
        """进入框选模式。用户拖拽出矩形后调用 callback(x0, y0, x1, y1)."""
        self._selection_mode = True
        self._selection_callback = callback
        self._selection_rect_item.setVisible(False)
        self.setCursor(Qt.CrossCursor)

    def _finish_selection(self) -> None:
        """框选完成，调用回调。"""
        self._selection_mode = False
        self._selection_rect_item.setVisible(False)
        self.setCursor(Qt.CursorShape.CrossCursor)
        if self._selection_rect and self._selection_callback:
            x0, y0, x1, y1 = self._selection_rect
            if x1 > x0 + 5 and y1 > y0 + 5:  # 最小 5px
                self._selection_callback(x0, y0, x1, y1)
        self._selection_rect = None
        self._selection_callback = None

    # ========== 渲染（性能核心） ==========

    def _full_render(self) -> None:
        """全量渲染整个地图到显示缓冲区（根据当前模式）"""
        # 新 mode 没有专用 renderer 的复用 land
        renderers = {
            "land": self._render_land_mode,
            "terrain": self._render_terrain_mode,
            "height": self._render_height_mode,
            "province": self._render_province_mode,
            "state": self._render_state_mode,
            "country": self._render_country_mode,
            "river": self._render_river_mode,
            "logistics": self._render_logistics_mode,
            "density": self._render_land_mode,
            "continent": self._render_land_mode,
            "strategic_region": self._render_land_mode,
            "colormap": self._render_land_mode,
            "default_map": self._render_land_mode,
            "province_terrain": self._render_province_terrain_mode,
        }
        renderers.get(self._display_mode, self._render_land_mode)()
        self._update_pixmap_from_buffer()
        # VP 叠加层可见性切换（不重绘，用缓存）
        self._update_vp_visibility()
        # 密度叠加层：density 模式自动显示
        self.set_density_overlay_visible(self._display_mode == "density")

    def _partial_render(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """局部渲染指定矩形区域（根据当前模式）"""
        renderers = {
            "land": self._partial_render_land,
            "terrain": self._partial_render_terrain,
            "height": self._partial_render_height,
            "province": self._partial_render_province,
            "state": self._partial_render_state,
            "country": self._partial_render_country,
            "river": self._partial_render_river,
            "logistics": self._partial_render_logistics,
            "density": self._partial_render_land,
            "continent": self._partial_render_land,
            "strategic_region": self._partial_render_land,
            "colormap": self._partial_render_land,
            "default_map": self._partial_render_land,
            "province_terrain": self._partial_render_province_terrain,
        }
        renderers[self._display_mode](x0, y0, x1, y1)
        self._update_pixmap_from_buffer()

    def _render_logistics_mode(self) -> None:
        from features.map.logistics.renderer import render
        render(self)

    def _partial_render_logistics(self, x0: int, y0: int, x1: int, y1: int) -> None:
        from features.map.logistics.renderer import partial_render
        partial_render(self, x0, y0, x1, y1)

    # ---------- land 模式渲染 ----------

    def _render_land_mode(self) -> None:
        from features.map.land.renderer import render
        render(self)

    def _partial_render_land(self, x0: int, y0: int, x1: int, y1: int) -> None:
        from features.map.land.renderer import partial_render
        partial_render(self, x0, y0, x1, y1)

    # ---------- terrain 模式渲染 ----------

    def _render_terrain_mode(self) -> None:
        from features.map.terrain.renderer import render
        render(self)

    def _partial_render_terrain(self, x0: int, y0: int, x1: int, y1: int) -> None:
        from features.map.terrain.renderer import partial_render
        partial_render(self, x0, y0, x1, y1)

    # ---------- height 模式渲染 ----------

    def _render_height_mode(self) -> None:
        from features.map.height.renderer import render
        render(self)

    def _partial_render_height(self, x0: int, y0: int, x1: int, y1: int) -> None:
        from features.map.height.renderer import partial_render
        partial_render(self, x0, y0, x1, y1)

    # ---------- province 模式渲染 ----------

    def _render_province_mode(self) -> None:
        from features.map.province.renderer import render
        render(self)

    def _partial_render_province(self, x0: int, y0: int, x1: int, y1: int) -> None:
        from features.map.province.renderer import partial_render
        partial_render(self, x0, y0, x1, y1)

    # ---------- state 模式渲染 ----------

    def _render_state_mode(self) -> None:
        from features.map.state.renderer import render
        render(self)

    def _partial_render_state(self, x0: int, y0: int, x1: int, y1: int) -> None:
        from features.map.state.renderer import partial_render
        partial_render(self, x0, y0, x1, y1)

    # ---------- province_terrain 模式渲染（gameplay terrain 颜色） ----------

    def _render_province_terrain_mode(self) -> None:
        from features.map.province_terrain.renderer import render
        render(self)

    def _partial_render_province_terrain(self, x0: int, y0: int, x1: int, y1: int) -> None:
        from features.map.province_terrain.renderer import partial_render
        partial_render(self, x0, y0, x1, y1)

    # ---------- country 模式渲染 ----------

    def _render_country_mode(self) -> None:
        from features.map.country.renderer import render
        render(self)

    def _partial_render_country(self, x0: int, y0: int, x1: int, y1: int) -> None:
        from features.map.country.renderer import partial_render
        partial_render(self, x0, y0, x1, y1)

    # ---------- river 模式渲染 ----------

    def _render_river_mode(self) -> None:
        from features.map.river.renderer import render
        render(self)

    def _partial_render_river(self, x0: int, y0: int, x1: int, y1: int) -> None:
        from features.map.river.renderer import partial_render
        partial_render(self, x0, y0, x1, y1)

    # ---------- 通用渲染辅助 ----------

    def _update_pixmap_from_buffer(self) -> None:
        """将显示缓冲区写入 QPixmap"""
        img = QImage(self._display_buffer.data, self.map_w, self.map_h,
                     self.map_w * 4, QImage.Format.Format_RGB32)
        img._ref = self._display_buffer  # 防止 GC
        self._map_pixmap_item.setPixmap(QPixmap.fromImage(img))

    def _cleanup_after_province_edit(self) -> None:
        """边界编辑结束后的安全清理：
        1. 修复可能产生的 X-crossings
        2. 修复可能产生的不连通碎片（边界编辑可能把对方省份切成两半）
        3. 压实 ID（防止某省份被推到 0 像素消失后留下 gap）
        4. 维护选中省份 ID 在压实后仍指向正确省份
        """
        from domain.validators.province import fix_x_crossings
        from domain.generators.province import _fix_non_contiguous_fast, compact_province_ids

        old_sel = self._selected_province_id

        # 1. X-crossings
        for _ in range(5):
            if fix_x_crossings(self._province_map) == 0:
                break

        # 2. 不连通碎片
        _fix_non_contiguous_fast(self._province_map)

        # 3. 压实前先记录 selected 是否还存在
        sel_existed = bool((self._province_map == old_sel).any()) if old_sel > 0 else False

        # 4. 压实 ID（用映射表追踪 selected 的新 ID）
        if old_sel > 0 and sel_existed:
            unique_before = np.unique(self._province_map)
            compact_province_ids(self._province_map)
            unique_after = np.unique(self._province_map)
            # 找出 old_sel 在压实后的新 ID
            old_list = unique_before.tolist()
            new_list = unique_after.tolist()
            if old_sel in old_list:
                idx = old_list.index(old_sel)
                self._selected_province_id = int(new_list[idx])
        else:
            compact_province_ids(self._province_map)
            if not sel_existed:
                # 选中省份被推没了
                self._selected_province_id = 0

    def center_on_pixel(self, x: int, y: int, zoom: float | None = None) -> None:
        """让画布中心对准地图坐标 (x, y)，可选放大到 zoom 倍。
        用于验证对话框跳转到问题位置。"""
        if not (0 <= x < self.map_w and 0 <= y < self.map_h):
            return
        if zoom is not None:
            self.resetTransform()
            self.scale(zoom, zoom)
        self.centerOn(float(x), float(y))

    def center_on_province(self, pid: int) -> None:
        """跳转到指定省份的中心，并选中它"""
        if pid <= 0 or pid > self._province_map.max():
            return
        ys, xs = np.where(self._province_map == pid)
        if len(ys) == 0:
            return
        cx = int(xs.mean())
        cy = int(ys.mean())
        self._selected_province_id = pid
        self._selected_province_tile = int(self._tile_map[cy, cx])
        self._render_province_overlay()
        self.center_on_pixel(cx, cy, zoom=2.0)

    def split_province(self, pid: int) -> bool:
        """切割省份：沿中线把一个省份分成两半，新半用新ID"""
        if pid <= 0:
            return False
        mask = self._province_map == pid
        ys, xs = np.where(mask)
        if len(ys) < 2:
            return False

        # 沿较长轴的中线切割
        y_range = ys.max() - ys.min()
        x_range = xs.max() - xs.min()
        new_id = int(self._province_map.max()) + 1

        if x_range >= y_range:
            # 水平方向更宽，沿 x 中线切
            mid_x = (xs.min() + xs.max()) // 2
            right_half = mask & (np.arange(self.map_w)[np.newaxis, :] > mid_x)
        else:
            # 垂直方向更高，沿 y 中线切
            mid_y = (ys.min() + ys.max()) // 2
            right_half = mask & (np.arange(self.map_h)[:, np.newaxis] > mid_y)

        if not np.any(right_half):
            return False

        self._province_map[right_half] = new_id
        self._full_render()
        self._render_province_overlay()
        return True

    def merge_provinces(self, pid_keep: int, pid_remove: int,
                         state_mgr=None, country_mgr=None) -> bool:
        """合并两个省份：pid_remove 的所有像素归入 pid_keep。
        合并后立即压实 ID 并同步 state/country 引用，避免 ID gap。"""
        if pid_keep <= 0 or pid_remove <= 0 or pid_keep == pid_remove:
            return False
        mask = self._province_map == pid_remove
        if not np.any(mask):
            return False
        self._province_map[mask] = pid_keep
        # 压实 + 同步引用
        mapping = self._map_data.compact_with_references(
            state_mgr=state_mgr, country_mgr=country_mgr,
        )
        # 更新 canvas 持有的选中省份 id
        if self._selected_province_id in mapping:
            self._selected_province_id = mapping[self._selected_province_id]
        self._border_cache = None  # 省份变了，清缓存
        if hasattr(self, '_border_base_pixmap'):
            self._border_base_pixmap = None
        self._full_render()
        self._render_province_overlay()
        return True

    def refresh_display(self) -> None:
        self._full_render()
        self._render_province_overlay()

    # ========== 脏矩形系统 ==========

    def _mark_dirty(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """标记脏区域，合并多次绘制"""
        if self._dirty_rect is None:
            self._dirty_rect = (x0, y0, x1, y1)
        else:
            dx0, dy0, dx1, dy1 = self._dirty_rect
            self._dirty_rect = (min(dx0, x0), min(dy0, y0), max(dx1, x1), max(dy1, y1))
        if not self._render_timer.isActive():
            self._render_timer.start()

    def _flush_dirty(self) -> None:
        """刷新脏区域"""
        if self._dirty_rect is None:
            return
        x0, y0, x1, y1 = self._dirty_rect
        self._dirty_rect = None
        self._partial_render(x0, y0, x1, y1)

    # ========== 绘制操作 ==========

    def _stamp_brush(self, cx: int, cy: int) -> None:
        """在单个位置盖一个圆形笔刷印章（根据当前模式）"""
        import numpy as np

        # 省份模式：固定 1 像素，不依赖刷子大小（边界编辑要精确）
        if self._display_mode == "province":
            r = 0
        else:
            r = self._brush_size // 2
        x0 = max(0, cx - r)
        y0 = max(0, cy - r)
        x1 = min(self.map_w, cx + r + 1)
        y1 = min(self.map_h, cy + r + 1)
        if x0 >= x1 or y0 >= y1:
            return

        # 构建圆形 mask（r >= 2 时用圆，小笔刷不需要）
        if r >= 2:
            yy, xx = np.ogrid[y0:y1, x0:x1]
            circle = (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r
        else:
            circle = None  # 小笔刷直接全覆盖

        mode = self._display_mode

        if mode in ("land", "density"):
            # 密度画笔模式
            if self._display_mode == "density":
                dm = getattr(self._map_data, 'density_map', None) if self._map_data else None
                if dm is not None:
                    # 用密度专属画笔大小
                    dr = getattr(self, '_density_brush_size', 30) // 2
                    dy0, dy1 = max(0, cy - dr), min(self.map_h, cy + dr + 1)
                    dx0, dx1 = max(0, cx - dr), min(self.map_w, cx + dr + 1)
                    yy_d, xx_d = np.ogrid[dy0:dy1, dx0:dx1]
                    dist_sq = (yy_d - cy) ** 2 + (xx_d - cx) ** 2
                    r_sq = dr * dr
                    d_circle = dist_sq <= r_sq
                    dv = getattr(self, '_density_paint_value', 0.8)
                    soft = getattr(self, '_density_soft_edge', 0.5)
                    if soft > 0.01:
                        dist_norm = np.sqrt(dist_sq[d_circle].astype(np.float32)) / max(dr, 1)
                        falloff = np.exp(-dist_norm * dist_norm / (2 * soft * soft))
                        old_vals = dm[dy0:dy1, dx0:dx1][d_circle]
                        dm[dy0:dy1, dx0:dx1][d_circle] = old_vals + (dv - old_vals) * falloff
                    else:
                        dm[dy0:dy1, dx0:dx1][d_circle] = dv
                return

            # 修改大陆时，如果已有省份数据则自动清除（只检查一次）
            if self._has_provinces:
                self._has_provinces = False
                self._province_map[:] = 0
                self._province_pixmap_item.setVisible(False)
                self.provinces_cleared.emit()

            if self._current_tool == "eraser":
                if circle is not None:
                    self._tile_map[y0:y1, x0:x1][circle] = TILE_SEA
                else:
                    self._tile_map[y0:y1, x0:x1] = TILE_SEA
            elif self._current_tool == "brush":
                if circle is not None:
                    self._tile_map[y0:y1, x0:x1][circle] = self._current_tile_type
                else:
                    self._tile_map[y0:y1, x0:x1] = self._current_tile_type

        elif mode == "terrain":
            if not self._terrain_brush_mode:
                return
            if self._current_tool == "eraser":
                if circle is not None:
                    self._terrain_map[y0:y1, x0:x1][circle] = 0
                else:
                    self._terrain_map[y0:y1, x0:x1] = 0
            elif self._current_tool == "brush":
                if circle is not None:
                    self._terrain_map[y0:y1, x0:x1][circle] = self._current_terrain_index
                else:
                    self._terrain_map[y0:y1, x0:x1] = self._current_terrain_index

        elif mode == "height":
            return

        elif mode == "province":
            if self._selected_province_id <= 0:
                return
            sub_pm = self._province_map[y0:y1, x0:x1]
            sub_tm = self._tile_map[y0:y1, x0:x1]
            mask = (
                (sub_tm == self._selected_province_tile)
                & (sub_pm != 0)
                & (sub_pm != self._selected_province_id)
            )
            sub_pm[mask] = self._selected_province_id

        elif mode == "river":
            if self._current_tool == "eraser":
                if circle is not None:
                    self._river_map[y0:y1, x0:x1][circle] = RIVER_ERASE
                else:
                    self._river_map[y0:y1, x0:x1] = RIVER_ERASE
            elif self._current_tool == "brush":
                if circle is not None:
                    self._river_map[y0:y1, x0:x1][circle] = self._current_river_type
                else:
                    self._river_map[y0:y1, x0:x1] = self._current_river_type

        self._mark_dirty(x0, y0, x1, y1)

    def _paint_at(self, scene_x: int, scene_y: int) -> None:
        """在指定位置绘制，并与上一个位置做插值避免断线。

        河流模式用**阶梯式正交路径**（先水平后垂直），符合 HOI4 规则
        （pixels do not connect diagonally — Paradox wiki《Map modding》）。
        其它模式用 Bresenham 斜线（更平滑）。
        """
        if self._last_draw_pos is not None:
            lx, ly = self._last_draw_pos
            dx = abs(scene_x - lx)
            dy = abs(scene_y - ly)
            steps = max(dx, dy)
            if self._display_mode == "river":
                # 河流：永远走阶梯（哪怕只是 1 像素的对角移动也要走正交）
                # 慢速拖鼠标每次只报 1px，dx=dy=1 时 steps=1，
                # 走直接 stamp 会产生一串对角像素 → 不合法
                if dx > 0 or dy > 0:
                    self._stamp_orthogonal(lx, ly, scene_x, scene_y)
            elif steps > 1:
                # 其它模式：Bresenham 斜线插值（平滑）
                for i in range(1, steps + 1):
                    t = i / steps
                    ix = int(lx + (scene_x - lx) * t)
                    iy = int(ly + (scene_y - ly) * t)
                    self._stamp_brush(ix, iy)
            else:
                self._stamp_brush(scene_x, scene_y)
        else:
            self._stamp_brush(scene_x, scene_y)

        self._last_draw_pos = (scene_x, scene_y)

    def _stamp_orthogonal(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """正交阶梯画线：先沿 x 方向走一格一格，再沿 y 方向。
        保证相邻两像素必然上下左右相贴，不产生对角连接。
        用于河流模式 — HOI4 规定河流只能正交连接。
        """
        # 水平段
        x = x0
        step_x = 1 if x1 > x0 else -1 if x1 < x0 else 0
        while x != x1:
            x += step_x
            self._stamp_brush(x, y0)
        # 垂直段
        y = y0
        step_y = 1 if y1 > y0 else -1 if y1 < y0 else 0
        while y != y1:
            y += step_y
            self._stamp_brush(x1, y)

    def _flood_fill(self, x: int, y: int) -> None:
        if x < 0 or x >= self.map_w or y < 0 or y >= self.map_h:
            return

        mode = self._display_mode

        if mode in ("province", "state", "country", "river"):
            return  # 这些模式不支持填充

        # 确定填充目标数组和填充值
        if mode == "land":
            data = self._tile_map
            fill_val = self._current_tile_type
        elif mode == "terrain":
            data = self._terrain_map
            fill_val = self._current_terrain_index
        elif mode == "height":
            data = self._height_map
            fill_val = self._current_height_value
        else:
            return

        target = data[y, x]
        if target == fill_val:
            return

        stack = [(x, y)]
        visited = np.zeros((self.map_h, self.map_w), dtype=bool)

        while stack:
            cx, cy = stack.pop()
            if cx < 0 or cx >= self.map_w or cy < 0 or cy >= self.map_h:
                continue
            if visited[cy, cx] or data[cy, cx] != target:
                continue

            left = cx
            while left > 0 and data[cy, left - 1] == target and not visited[cy, left - 1]:
                left -= 1
            right = cx
            while right < self.map_w - 1 and data[cy, right + 1] == target and not visited[cy, right + 1]:
                right += 1

            data[cy, left:right + 1] = fill_val
            visited[cy, left:right + 1] = True

            for nx in range(left, right + 1):
                if cy > 0 and not visited[cy - 1, nx] and data[cy - 1, nx] == target:
                    stack.append((nx, cy - 1))
                if cy < self.map_h - 1 and not visited[cy + 1, nx] and data[cy + 1, nx] == target:
                    stack.append((nx, cy + 1))

        # 填充后全量渲染（因为区域不确定）
        self._full_render()

    # ========== 事件辅助 ==========

    def _scene_pos(self, event: QMouseEvent) -> tuple[int, int]:
        pos = self.mapToScene(event.pos())
        return int(pos.x()), int(pos.y())

    def _scene_pos_clamped(self, event: QMouseEvent) -> tuple[int, int]:
        """返回限制在地图边界内的场景坐标"""
        sx, sy = self._scene_pos(event)
        return max(0, min(self.map_w - 1, sx)), max(0, min(self.map_h - 1, sy))

    def _is_in_bounds(self, sx: int, sy: int) -> bool:
        """检查坐标是否在地图边界内"""
        return 0 <= sx < self.map_w and 0 <= sy < self.map_h

    def cleanup_mode_state(self) -> None:
        """清理所有临时模式状态。模式切换时调用，防止状态残留导致异常。"""
        # 变换工具状态
        if self._transform_active:
            self._end_transform()
        self._transform_selecting = False
        self._transform_box = None
        self._transform_snippet = None
        self._transform_orig_box = None
        self._transform_drag = None
        self._transform_drag_start = None
        self._transform_angle = 0.0

        # 框选状态
        self._selection_mode = False
        self._selection_rect = None
        self._selection_start = None
        self._selection_rect_item.setVisible(False)

        # 绘制状态
        self._is_drawing = False
        self._last_draw_pos = None

        # 框架工具
        self._framework_tool = None

        # 省份选中
        self._selected_province_id = 0

        # lasso / overlay 清理
        self._clear_lasso_visual()

        # 光标重置
        self.setCursor(Qt.CursorShape.CrossCursor)

    def fit_in_view(self) -> None:
        self.fitInView(QRectF(0, 0, self.map_w, self.map_h),
                       Qt.AspectRatioMode.KeepAspectRatio)
        transform = self.transform()
        self._zoom = transform.m11()
        self.zoom_changed.emit(self._zoom)
