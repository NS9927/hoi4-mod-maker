"""
地图画布组件 — 基于 QGraphicsView 的大画布
支持六种编辑模式：land / terrain / height / province / state / country
性能优化：脏矩形局部更新，避免每次操作渲染整张地图
"""
import numpy as np
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPoint, QRectF, QRect, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QWheelEvent, QMouseEvent, QPen

from data.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    TILE_UNDEFINED, TILE_LAND, TILE_SEA, TILE_LAKE,
    ZOOM_MIN, ZOOM_MAX, ZOOM_STEP,
    BRUSH_DEFAULT,
)
from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX
from core.river_manager import (
    RIVER_DISPLAY_COLORS, RIVER_SOURCE, RIVER_BG_LAND, RIVER_BG_SEA,
    RIVER_ERASE, VALID_RIVER_VALUES,
)

# 地块类型对应的 BGRA 值（QImage Format_RGB32）
_TILE_BGRA = {
    TILE_UNDEFINED: (30, 20, 20, 255),
    TILE_LAND:      (101, 172, 139, 255),
    TILE_SEA:       (156, 105, 68, 255),
    TILE_LAKE:      (210, 160, 100, 255),
}

# 构建 terrain 索引 → BGRA 颜色查找表
_TERRAIN_INDEX_TO_BGRA = {}
for _name, _idx in TERRAIN_PALETTE_INDEX.items():
    _r, _g, _b = TERRAIN_TYPES[_name].color
    _TERRAIN_INDEX_TO_BGRA[_idx] = (_b, _g, _r, 255)

# 构建 terrain 颜色 LUT (numpy数组, 256 entries, BGRA)
_TERRAIN_COLOR_LUT = np.zeros((256, 4), dtype=np.uint8)
for _idx, _bgra in _TERRAIN_INDEX_TO_BGRA.items():
    _TERRAIN_COLOR_LUT[_idx] = _bgra

# 河流颜色 LUT (索引 → BGRA)
_RIVER_COLOR_LUT = np.zeros((256, 4), dtype=np.uint8)
for _ridx, _rbgra in RIVER_DISPLAY_COLORS.items():
    _RIVER_COLOR_LUT[_ridx] = _rbgra
# 背景色不需要在画布上显示（用底图）

# 省份随机颜色 LUT (确定性, 基于省份ID)
_PROVINCE_COLOR_LUT_SIZE = 65536
_rng = np.random.RandomState(42)
_PROVINCE_COLOR_LUT = np.zeros((_PROVINCE_COLOR_LUT_SIZE, 4), dtype=np.uint8)
_PROVINCE_COLOR_LUT[:, 0] = _rng.randint(40, 220, _PROVINCE_COLOR_LUT_SIZE, dtype=np.uint8)
_PROVINCE_COLOR_LUT[:, 1] = _rng.randint(40, 220, _PROVINCE_COLOR_LUT_SIZE, dtype=np.uint8)
_PROVINCE_COLOR_LUT[:, 2] = _rng.randint(40, 220, _PROVINCE_COLOR_LUT_SIZE, dtype=np.uint8)
_PROVINCE_COLOR_LUT[:, 3] = 255
# ID 0 = 未分配，用深色
_PROVINCE_COLOR_LUT[0] = (30, 20, 20, 255)


class MapCanvas(QGraphicsView):
    """地图画布，支持缩放/拖动/绘制，脏矩形局部更新"""

    mouse_moved = pyqtSignal(int, int)
    zoom_changed = pyqtSignal(float)
    province_clicked = pyqtSignal(int)
    province_double_clicked = pyqtSignal(int)   # 双击省份（设VP）
    province_right_clicked = pyqtSignal(int)    # 右键省份（设首都）
    provinces_cleared = pyqtSignal()  # 大陆模式修改时自动清除省份
    stroke_started = pyqtSignal()     # 画笔操作开始
    stroke_ended = pyqtSignal()       # 画笔操作结束

    def __init__(self, parent=None):
        super().__init__(parent)

        # 数据层
        self._tile_map = np.full((MAP_HEIGHT, MAP_WIDTH), TILE_SEA, dtype=np.uint8)
        self._province_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.int32)
        self._terrain_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.uint8)
        self._height_map = np.full((MAP_HEIGHT, MAP_WIDTH), 40, dtype=np.uint8)
        self._river_map = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=np.uint8)

        # 河流编辑状态
        self._current_river_type = RIVER_SOURCE

        # 显示缓冲区（BGRA）
        self._display_buffer = np.zeros((MAP_HEIGHT, MAP_WIDTH, 4), dtype=np.uint8)
        self._province_border_buffer = None  # 延迟创建

        # State / Country 颜色缓冲区
        self._state_color_rgb = None   # np.ndarray (H, W, 3) or None
        self._country_color_rgb = None  # np.ndarray (H, W, 3) or None

        # 显示/编辑模式
        self._display_mode = "land"

        # 当前状态
        self._zoom = 1.0
        self._current_tool = "brush"
        self._current_tile_type = TILE_LAND
        self._current_terrain_index = 0
        self._selected_province_id = 0  # 省份模式下选中的省份ID
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

        self._ref_pixmap_item = QGraphicsPixmapItem()
        self._ref_pixmap_item.setOpacity(0.4)
        self._ref_pixmap_item.setZValue(1)
        self._scene.addItem(self._ref_pixmap_item)

        self._province_pixmap_item = QGraphicsPixmapItem()
        self._province_pixmap_item.setOpacity(0.6)
        self._province_pixmap_item.setZValue(2)
        self._scene.addItem(self._province_pixmap_item)

        # 画笔预览光标（半透明圆圈）
        self._brush_cursor = QGraphicsEllipseItem()
        self._brush_cursor.setPen(QPen(QColor(255, 255, 255, 180), 1))
        self._brush_cursor.setBrush(QColor(255, 255, 255, 40))
        self._brush_cursor.setZValue(10)
        self._brush_cursor.setVisible(False)
        self._scene.addItem(self._brush_cursor)

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

    # ========== 数据访问 ==========

    @property
    def tile_map(self) -> np.ndarray:
        return self._tile_map

    @tile_map.setter
    def tile_map(self, data: np.ndarray) -> None:
        self._tile_map = data.astype(np.uint8)
        if self._display_mode == "land":
            self._full_render()

    @property
    def province_map(self) -> np.ndarray:
        return self._province_map

    @province_map.setter
    def province_map(self, data: np.ndarray) -> None:
        self._province_map = data.astype(np.int32)
        self._has_provinces = int(self._province_map.max()) > 0
        if self._display_mode == "province":
            self._full_render()
        self._render_province_overlay()

    @property
    def terrain_map(self) -> np.ndarray:
        return self._terrain_map

    @terrain_map.setter
    def terrain_map(self, data: np.ndarray) -> None:
        self._terrain_map = data.astype(np.uint8)
        if self._display_mode == "terrain":
            self._full_render()

    @property
    def height_map(self) -> np.ndarray:
        return self._height_map

    @height_map.setter
    def height_map(self, data: np.ndarray) -> None:
        self._height_map = data.astype(np.uint8)
        if self._display_mode == "height":
            self._full_render()

    @property
    def river_map(self) -> np.ndarray:
        return self._river_map

    @river_map.setter
    def river_map(self, data: np.ndarray) -> None:
        self._river_map = data.astype(np.uint8)
        if self._display_mode == "river":
            self._full_render()

    def set_river_type(self, river_type: int) -> None:
        self._current_river_type = max(0, min(255, river_type))

    @property
    def display_mode(self) -> str:
        return self._display_mode

    @display_mode.setter
    def display_mode(self, mode: str) -> None:
        if mode not in ("land", "terrain", "height", "province", "state", "country", "river"):
            return
        if mode == self._display_mode:
            return
        self._display_mode = mode
        self._full_render()

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

    # ========== 参考图 ==========

    def load_reference_image(self, file_path: str) -> bool:
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return False
        scaled = pixmap.scaled(MAP_WIDTH, MAP_HEIGHT,
                               Qt.AspectRatioMode.IgnoreAspectRatio,
                               Qt.TransformMode.SmoothTransformation)
        self._ref_pixmap_item.setPixmap(scaled)
        self._ref_pixmap_item.setVisible(self._show_ref_image)
        return True

    def set_ref_opacity(self, opacity: float) -> None:
        self._ref_pixmap_item.setOpacity(max(0.0, min(1.0, opacity)))

    def toggle_ref_image(self, visible: bool) -> None:
        self._show_ref_image = visible
        self._ref_pixmap_item.setVisible(visible)

    # ========== 渲染（性能核心） ==========

    def _full_render(self) -> None:
        """全量渲染整个地图到显示缓冲区（根据当前模式）"""
        renderers = {
            "land": self._render_land_mode,
            "terrain": self._render_terrain_mode,
            "height": self._render_height_mode,
            "province": self._render_province_mode,
            "state": self._render_state_mode,
            "country": self._render_country_mode,
            "river": self._render_river_mode,
        }
        renderers[self._display_mode]()
        self._update_pixmap_from_buffer()

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
        }
        renderers[self._display_mode](x0, y0, x1, y1)
        self._update_pixmap_from_buffer()

    # ---------- land 模式渲染 ----------

    def _render_land_mode(self) -> None:
        """全量渲染 land 模式"""
        for tile_type, (b, g, r, a) in _TILE_BGRA.items():
            mask = self._tile_map == tile_type
            self._display_buffer[mask, 0] = b
            self._display_buffer[mask, 1] = g
            self._display_buffer[mask, 2] = r
            self._display_buffer[mask, 3] = a

    def _partial_render_land(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """局部渲染 land 模式"""
        region = self._tile_map[y0:y1, x0:x1]
        buf = self._display_buffer[y0:y1, x0:x1]
        for tile_type, (b, g, r, a) in _TILE_BGRA.items():
            mask = region == tile_type
            buf[mask, 0] = b
            buf[mask, 1] = g
            buf[mask, 2] = r
            buf[mask, 3] = a

    # ---------- terrain 模式渲染 ----------

    def _render_terrain_mode(self) -> None:
        """全量渲染 terrain 模式"""
        self._display_buffer[:] = _TERRAIN_COLOR_LUT[self._terrain_map]

    def _partial_render_terrain(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """局部渲染 terrain 模式"""
        self._display_buffer[y0:y1, x0:x1] = (
            _TERRAIN_COLOR_LUT[self._terrain_map[y0:y1, x0:x1]]
        )

    # ---------- height 模式渲染 ----------

    def _render_height_mode(self) -> None:
        """全量渲染 height 模式 — 灰度"""
        self._display_buffer[:, :, 0] = self._height_map
        self._display_buffer[:, :, 1] = self._height_map
        self._display_buffer[:, :, 2] = self._height_map
        self._display_buffer[:, :, 3] = 255

    def _partial_render_height(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """局部渲染 height 模式"""
        region = self._height_map[y0:y1, x0:x1]
        buf = self._display_buffer[y0:y1, x0:x1]
        buf[:, :, 0] = region
        buf[:, :, 1] = region
        buf[:, :, 2] = region
        buf[:, :, 3] = 255

    # ---------- province 模式渲染 ----------

    def _render_province_mode(self) -> None:
        """全量渲染 province 模式 — 按省份ID着色"""
        indices = self._province_map % _PROVINCE_COLOR_LUT_SIZE
        self._display_buffer[:] = _PROVINCE_COLOR_LUT[indices]

    def _partial_render_province(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """局部渲染 province 模式"""
        indices = self._province_map[y0:y1, x0:x1] % _PROVINCE_COLOR_LUT_SIZE
        self._display_buffer[y0:y1, x0:x1] = _PROVINCE_COLOR_LUT[indices]

    # ---------- state 模式渲染 ----------

    def _render_state_mode(self) -> None:
        """全量渲染 state 模式 — 使用预计算的 RGB 数组"""
        if self._state_color_rgb is not None:
            # RGB → BGRA
            self._display_buffer[:, :, 0] = self._state_color_rgb[:, :, 2]  # B
            self._display_buffer[:, :, 1] = self._state_color_rgb[:, :, 1]  # G
            self._display_buffer[:, :, 2] = self._state_color_rgb[:, :, 0]  # R
            self._display_buffer[:, :, 3] = 255
        else:
            # 无 State 数据，显示深灰
            self._display_buffer[:, :, 0] = 40
            self._display_buffer[:, :, 1] = 40
            self._display_buffer[:, :, 2] = 40
            self._display_buffer[:, :, 3] = 255

    def _partial_render_state(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """局部渲染 state 模式 — 使用存储的 RGB 数组"""
        buf = self._display_buffer[y0:y1, x0:x1]
        if self._state_color_rgb is not None:
            region = self._state_color_rgb[y0:y1, x0:x1]
            buf[:, :, 0] = region[:, :, 2]
            buf[:, :, 1] = region[:, :, 1]
            buf[:, :, 2] = region[:, :, 0]
            buf[:, :, 3] = 255
        else:
            buf[:, :, :] = [40, 40, 40, 255]

    # ---------- country 模式渲染 ----------

    def _render_country_mode(self) -> None:
        """全量渲染 country 模式 — 使用预计算的 RGB 数组"""
        if self._country_color_rgb is not None:
            self._display_buffer[:, :, 0] = self._country_color_rgb[:, :, 2]
            self._display_buffer[:, :, 1] = self._country_color_rgb[:, :, 1]
            self._display_buffer[:, :, 2] = self._country_color_rgb[:, :, 0]
            self._display_buffer[:, :, 3] = 255
        else:
            self._display_buffer[:, :, 0] = 60
            self._display_buffer[:, :, 1] = 60
            self._display_buffer[:, :, 2] = 60
            self._display_buffer[:, :, 3] = 255

    def _partial_render_country(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """局部渲染 country 模式 — 使用存储的 RGB 数组"""
        buf = self._display_buffer[y0:y1, x0:x1]
        if self._country_color_rgb is not None:
            region = self._country_color_rgb[y0:y1, x0:x1]
            buf[:, :, 0] = region[:, :, 2]
            buf[:, :, 1] = region[:, :, 1]
            buf[:, :, 2] = region[:, :, 0]
            buf[:, :, 3] = 255
        else:
            buf[:, :, :] = [60, 60, 60, 255]

    # ---------- river 模式渲染 ----------

    def _render_river_mode(self) -> None:
        """全量渲染 river 模式 — 陆地底图叠加河流"""
        # 先渲染陆地作为底图
        self._render_land_mode()
        # 叠加河流
        river_mask = self._river_map > 0
        if np.any(river_mask):
            colors = _RIVER_COLOR_LUT[self._river_map]
            self._display_buffer[river_mask] = colors[river_mask]

    def _partial_render_river(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """局部渲染 river 模式"""
        self._partial_render_land(x0, y0, x1, y1)
        region = self._river_map[y0:y1, x0:x1]
        river_mask = region > 0
        if np.any(river_mask):
            buf = self._display_buffer[y0:y1, x0:x1]
            colors = _RIVER_COLOR_LUT[region]
            buf[river_mask] = colors[river_mask]

    # ---------- 通用渲染辅助 ----------

    def _update_pixmap_from_buffer(self) -> None:
        """将显示缓冲区写入 QPixmap"""
        img = QImage(self._display_buffer.data, MAP_WIDTH, MAP_HEIGHT,
                     MAP_WIDTH * 4, QImage.Format.Format_RGB32)
        img._ref = self._display_buffer  # 防止 GC
        self._map_pixmap_item.setPixmap(QPixmap.fromImage(img))

    def _render_province_overlay(self) -> None:
        """渲染省份边界叠加层"""
        if not self._show_provinces or self._province_map.max() == 0:
            self._province_pixmap_item.setVisible(False)
            return

        borders = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)
        borders[:-1, :] |= self._province_map[:-1, :] != self._province_map[1:, :]
        borders[:, :-1] |= self._province_map[:, :-1] != self._province_map[:, 1:]

        rgba = np.zeros((MAP_HEIGHT, MAP_WIDTH, 4), dtype=np.uint8)
        rgba[borders, 3] = 180  # 黑色半透明边界

        img = QImage(rgba.data, MAP_WIDTH, MAP_HEIGHT,
                     MAP_WIDTH * 4, QImage.Format.Format_ARGB32)
        img._ref = rgba
        self._province_pixmap_item.setPixmap(QPixmap.fromImage(img))
        self._province_pixmap_item.setVisible(True)

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
            right_half = mask & (np.arange(MAP_WIDTH)[np.newaxis, :] > mid_x)
        else:
            # 垂直方向更高，沿 y 中线切
            mid_y = (ys.min() + ys.max()) // 2
            right_half = mask & (np.arange(MAP_HEIGHT)[:, np.newaxis] > mid_y)

        if not np.any(right_half):
            return False

        self._province_map[right_half] = new_id
        self._full_render()
        self._render_province_overlay()
        return True

    def merge_provinces(self, pid_keep: int, pid_remove: int) -> bool:
        """合并两个省份：pid_remove 的所有像素归入 pid_keep"""
        if pid_keep <= 0 or pid_remove <= 0 or pid_keep == pid_remove:
            return False
        mask = self._province_map == pid_remove
        if not np.any(mask):
            return False
        self._province_map[mask] = pid_keep
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
        """在单个位置盖一个方形笔刷印章（根据当前模式）"""
        r = self._brush_size // 2
        x0 = max(0, cx - r)
        y0 = max(0, cy - r)
        x1 = min(MAP_WIDTH, cx + r + 1)
        y1 = min(MAP_HEIGHT, cy + r + 1)
        if x0 >= x1 or y0 >= y1:
            return

        mode = self._display_mode

        if mode == "land":
            # 修改大陆时，如果已有省份数据则自动清除（只检查一次）
            if self._has_provinces:
                self._has_provinces = False
                self._province_map[:] = 0
                self._province_pixmap_item.setVisible(False)
                self.provinces_cleared.emit()

            if self._current_tool == "eraser":
                self._tile_map[y0:y1, x0:x1] = TILE_UNDEFINED
            elif self._current_tool == "brush":
                self._tile_map[y0:y1, x0:x1] = self._current_tile_type

        elif mode == "terrain":
            # 地形按省份为单位分配，不是逐像素
            return

        elif mode == "height":
            # 高度也按省份为单位分配
            return

        elif mode == "province":
            # 省份模式：边界拖动（用画笔刷省份ID）
            if self._selected_province_id > 0:
                self._province_map[y0:y1, x0:x1] = self._selected_province_id
            else:
                return

        elif mode == "river":
            if self._current_tool == "eraser":
                self._river_map[y0:y1, x0:x1] = RIVER_NONE
            elif self._current_tool == "brush":
                self._river_map[y0:y1, x0:x1] = self._current_river_type

        self._mark_dirty(x0, y0, x1, y1)

    def _paint_at(self, scene_x: int, scene_y: int) -> None:
        """在指定位置绘制，并与上一个位置做线性插值避免断线"""
        if self._last_draw_pos is not None:
            lx, ly = self._last_draw_pos
            # Bresenham 线性插值
            dx = abs(scene_x - lx)
            dy = abs(scene_y - ly)
            steps = max(dx, dy)
            if steps > 1:
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

    def _flood_fill(self, x: int, y: int) -> None:
        if x < 0 or x >= MAP_WIDTH or y < 0 or y >= MAP_HEIGHT:
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
        visited = np.zeros((MAP_HEIGHT, MAP_WIDTH), dtype=bool)

        while stack:
            cx, cy = stack.pop()
            if cx < 0 or cx >= MAP_WIDTH or cy < 0 or cy >= MAP_HEIGHT:
                continue
            if visited[cy, cx] or data[cy, cx] != target:
                continue

            left = cx
            while left > 0 and data[cy, left - 1] == target and not visited[cy, left - 1]:
                left -= 1
            right = cx
            while right < MAP_WIDTH - 1 and data[cy, right + 1] == target and not visited[cy, right + 1]:
                right += 1

            data[cy, left:right + 1] = fill_val
            visited[cy, left:right + 1] = True

            for nx in range(left, right + 1):
                if cy > 0 and not visited[cy - 1, nx] and data[cy - 1, nx] == target:
                    stack.append((nx, cy - 1))
                if cy < MAP_HEIGHT - 1 and not visited[cy + 1, nx] and data[cy + 1, nx] == target:
                    stack.append((nx, cy + 1))

        # 填充后全量渲染（因为区域不确定）
        self._full_render()

    # ========== 事件处理 ==========

    def _scene_pos(self, event: QMouseEvent) -> tuple[int, int]:
        pos = self.mapToScene(event.pos())
        return int(pos.x()), int(pos.y())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            if self._space_pressed or self._current_tool == "pan":
                self._is_panning = True
                self._pan_start = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return

            # 地形/高度/State/Country 模式：点击省份操作
            if self._display_mode in ("terrain", "height", "state", "country"):
                sx, sy = self._scene_pos(event)
                if 0 <= sx < MAP_WIDTH and 0 <= sy < MAP_HEIGHT:
                    pid = int(self._province_map[sy, sx])
                    if pid > 0:
                        mask = self._province_map == pid
                        # 地形模式：点击省份 → 整个省份填充当前地形
                        if self._display_mode == "terrain":
                            self.stroke_started.emit()
                            self._terrain_map[mask] = self._current_terrain_index
                            self._full_render()
                            self.stroke_ended.emit()
                        # 高度模式：点击省份 → 整个省份设为当前高度值
                        elif self._display_mode == "height":
                            self.stroke_started.emit()
                            self._height_map[mask] = self._current_height_value
                            self._full_render()
                            self.stroke_ended.emit()
                        self.province_clicked.emit(pid)
                event.accept()
                return

            # 省份模式：左键选中省份，拖动可修改边界
            if self._display_mode == "province":
                sx, sy = self._scene_pos(event)
                if 0 <= sx < MAP_WIDTH and 0 <= sy < MAP_HEIGHT:
                    pid = int(self._province_map[sy, sx])
                    if pid > 0:
                        self._selected_province_id = pid
                        self.province_clicked.emit(pid)
                        # 允许画笔模式下拖动修改边界
                        if self._current_tool in ("brush", "eraser"):
                            self._is_drawing = True
                            self.stroke_started.emit()
                            self._paint_at(sx, sy)
                event.accept()
                return

            # 河流模式：画笔绘制
            if self._display_mode == "river":
                if self._current_tool in ("brush", "eraser"):
                    self._is_drawing = True
                    self.stroke_started.emit()
                    sx, sy = self._scene_pos(event)
                    self._paint_at(sx, sy)
                    event.accept()
                    return

            if self._current_tool in ("brush", "eraser"):
                self._is_drawing = True
                self.stroke_started.emit()
                sx, sy = self._scene_pos(event)
                self._paint_at(sx, sy)
                event.accept()
                return

            if self._current_tool == "fill":
                self.stroke_started.emit()
                sx, sy = self._scene_pos(event)
                self._flood_fill(sx, sy)
                self.stroke_ended.emit()
                event.accept()
                return

        super().mousePressEvent(event)

    def _update_brush_cursor(self, sx: int, sy: int) -> None:
        """更新画笔预览光标位置和大小"""
        if self._current_tool in ("brush", "eraser") and self._display_mode in ("land", "terrain", "height", "river", "province"):
            r = self._brush_size // 2
            self._brush_cursor.setRect(sx - r, sy - r, self._brush_size, self._brush_size)
            self._brush_cursor.setVisible(True)
        else:
            self._brush_cursor.setVisible(False)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        sx, sy = self._scene_pos(event)
        if 0 <= sx < MAP_WIDTH and 0 <= sy < MAP_HEIGHT:
            self.mouse_moved.emit(sx, sy)
            self._update_brush_cursor(sx, sy)
        else:
            self._brush_cursor.setVisible(False)

        if self._is_panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        if self._is_drawing and self._current_tool in ("brush", "eraser"):
            self._paint_at(sx, sy)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            if self._is_panning:
                self._is_panning = False
                self.setCursor(Qt.CursorShape.CrossCursor if self._current_tool != "pan"
                              else Qt.CursorShape.OpenHandCursor)
                event.accept()
                return
            if self._is_drawing:
                self._is_drawing = False
                self._last_draw_pos = None  # 清除插值起点
                self._flush_dirty()
                # 省份/河流模式拖动结束后刷新
                if self._display_mode == "province":
                    self._render_province_overlay()
                self.stroke_ended.emit()
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """双击省份 → 设置 VP（所有模式，但不触发画笔）"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 阻止双击触发画笔
            self._is_drawing = False
            self._last_draw_pos = None
            sx, sy = self._scene_pos(event)
            if 0 <= sx < MAP_WIDTH and 0 <= sy < MAP_HEIGHT:
                pid = int(self._province_map[sy, sx])
                if pid > 0:
                    self.province_double_clicked.emit(pid)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:
        """右键省份 → 设首都（仅 state/country 模式）"""
        if self._display_mode not in ("state", "country"):
            super().contextMenuEvent(event)
            return
        pos = self.mapToScene(event.pos())
        sx, sy = int(pos.x()), int(pos.y())
        if 0 <= sx < MAP_WIDTH and 0 <= sy < MAP_HEIGHT:
            pid = int(self._province_map[sy, sx])
            if pid > 0:
                self.province_right_clicked.emit(pid)
                return
        super().contextMenuEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        factor = ZOOM_STEP if event.angleDelta().y() > 0 else 1.0 / ZOOM_STEP
        new_zoom = self._zoom * factor
        if ZOOM_MIN <= new_zoom <= ZOOM_MAX:
            self._zoom = new_zoom
            self.scale(factor, factor)
            self.zoom_changed.emit(self._zoom)
        event.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Space:
            self._space_pressed = True
            if not self._is_drawing:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Space:
            self._space_pressed = False
            if not self._is_panning:
                self.setCursor(Qt.CursorShape.CrossCursor if self._current_tool != "pan"
                              else Qt.CursorShape.OpenHandCursor)
        super().keyReleaseEvent(event)

    def fit_in_view(self) -> None:
        self.fitInView(QRectF(0, 0, MAP_WIDTH, MAP_HEIGHT),
                       Qt.AspectRatioMode.KeepAspectRatio)
        transform = self.transform()
        self._zoom = transform.m11()
        self.zoom_changed.emit(self._zoom)
