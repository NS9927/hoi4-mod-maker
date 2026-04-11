"""
地图画布组件 — 基于 QGraphicsView 的大画布
支持六种编辑模式：land / terrain / height / province / state / country
性能优化：脏矩形局部更新，避免每次操作渲染整张地图
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

# 地块类型对应的 BGRA 值（QImage Format_RGB32）
_TILE_BGRA = {
    TILE_UNDEFINED: (30, 20, 20, 255),
    TILE_LAND:      (101, 172, 139, 255),
    TILE_SEA:       (156, 105, 68, 255),
    TILE_LAKE:      (210, 160, 100, 255),
}

# 构建 terrain 索引 → BGRA 颜色查找表 (覆盖全部 graphical terrain)
# 每个变体用独立的高饱和色，确保 canvas 上一眼能分辨
_TERRAIN_COLOR_LUT = np.zeros((256, 4), dtype=np.uint8)
_TERRAIN_DISPLAY_COLORS: dict[int, tuple[int, int, int]] = {
    # plains 组: 绿色系
    0:  (120, 180, 60),   # 平原
    5:  (100, 160, 40),   # 平原(变体)
    19: (180, 200, 220),  # 雪原 (偏白蓝)
    # forest 组: 深绿
    1:  (30, 130, 30),    # 森林
    4:  (50, 150, 70),    # 森林(变体)
    # hills 组: 黄橙
    2:  (210, 180, 80),   # 沙漠丘陵
    17: (230, 200, 60),   # 丘陵
    # mountain 组: 灰棕分明
    6:  (140, 130, 120),  # 山地
    10: (160, 140, 100),  # 山地(变体)
    11: (180, 150, 100),  # 沙漠山地
    16: (200, 210, 230),  # 雪山 (偏白蓝)
    18: (190, 170, 110),  # 沙色山地
    20: (130, 150, 100),  # 草地山地
    27: (80, 120, 70),    # 丛林山地
    31: (110, 90, 60),    # 沙漠山顶 (深褐)
    # desert 组: 黄沙系
    3:  (220, 190, 100),  # 沙漠
    7:  (200, 170, 80),   # 沙漠(变体)
    8:  (210, 160, 90),   # 沙漠丘陵
    12: (230, 210, 130),  # 沙漠(岩地)
    # marsh: 暗青绿
    9:  (70, 120, 90),    # 沼泽
    # urban: 紫灰
    13: (160, 130, 170),  # 城市
    # jungle: 黄绿
    21: (60, 140, 20),    # 丛林
    22: (80, 160, 40),    # 丛林(变体)
    # water (不可画但需要显示)
    14: (60, 130, 200),   # 湖泊
    15: (30, 80, 180),    # 海洋
}
for _idx, (_r, _g, _b) in _TERRAIN_DISPLAY_COLORS.items():
    _TERRAIN_COLOR_LUT[_idx] = (_b, _g, _r, 255)  # BGRA

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

        # 套索路径反馈（黄色虚线）
        self._lasso_path_item = QGraphicsPathItem()
        pen = QPen(QColor(255, 230, 0, 230), 2)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setCosmetic(True)  # 不随缩放变粗细
        self._lasso_path_item.setPen(pen)
        self._lasso_path_item.setZValue(11)
        self._lasso_path_item.setVisible(False)
        self._scene.addItem(self._lasso_path_item)

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

    # ========== 数据访问 ==========

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
        """统一的图层替换：写入 MapData，同步本地别名。"""
        new_arr = data.astype(dtype)
        setattr(self._map_data, attr, new_arr)
        setattr(self, "_" + attr, new_arr)

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
        )
        if mode not in _VALID:
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

    def set_terrain_brush_mode(self, brush_mode: bool) -> None:
        """切换地形编辑模式: True=画笔逐像素, False=按省份(默认)"""
        self._terrain_brush_mode = brush_mode

    def set_height_value(self, value: int) -> None:
        self._current_height_value = max(0, min(255, value))

    # ========== State / Country 颜色设置 ==========

    def set_vp_data(self, vp_dict: dict[int, int]) -> None:
        """设置 VP 数据 {province_id: vp_value}，在 state/province 模式显示标记"""
        self._vp_data = dict(vp_dict)
        self._render_vp_overlay()

    def _render_vp_overlay(self) -> None:
        """渲染 VP 标记叠加层：红色圆圈 + 白色 VP 数值"""
        if self._display_mode not in ("state", "province") or not self._vp_data:
            self._vp_overlay_item.setVisible(False)
            return

        # 创建透明画布绘制 VP 标记
        img = QImage(MAP_WIDTH, MAP_HEIGHT, QImage.Format.Format_ARGB32)
        img.fill(QColor(0, 0, 0, 0))
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        for pid, vp_val in self._vp_data.items():
            if vp_val <= 0:
                continue
            centroid = self._map_data.get_province_centroid(pid)
            if centroid is None:
                continue
            cx, cy = centroid

            # 红色填充圆
            radius = max(6, min(14, 4 + vp_val))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setBrush(QBrush(QColor(220, 30, 30)))
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

            # 白色 VP 数值文字
            from PyQt5.QtGui import QFont
            font = QFont("Arial", max(8, min(12, 6 + vp_val // 2)))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            text_rect = QRectF(cx - 20, cy - 10, 40, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(vp_val))

        painter.end()
        self._vp_overlay_item.setPixmap(QPixmap.fromImage(img))
        self._vp_overlay_item.setVisible(True)

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
        self._ref_original_pixmap = pixmap
        self._ref_scale = 1.0
        self._ref_pixmap_item.setPixmap(pixmap)
        self._ref_pixmap_item.setVisible(self._show_ref_image)
        # 默认居中
        self._ref_pixmap_item.setPos(
            (MAP_WIDTH - pixmap.width()) / 2,
            (MAP_HEIGHT - pixmap.height()) / 2,
        )
        return True

    def load_vanilla_reference(self, file_path: str) -> bool:
        """加载原版地图参考（独立于用户参考图，不互相覆盖）。"""
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return False
        scaled = pixmap.scaled(MAP_WIDTH, MAP_HEIGHT,
                               Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self._vanilla_ref_item.setPixmap(scaled)
        self._vanilla_ref_item.setPos(0, 0)
        self._vanilla_ref_item.setVisible(True)
        return True

    def set_vanilla_ref_opacity(self, opacity: float) -> None:
        self._vanilla_ref_item.setOpacity(max(0.0, min(1.0, opacity)))

    def toggle_vanilla_ref(self, visible: bool) -> None:
        self._vanilla_ref_item.setVisible(visible)

    def set_ref_opacity(self, opacity: float) -> None:
        self._ref_pixmap_item.setOpacity(max(0.0, min(1.0, opacity)))

    def set_ref_scale(self, scale: float) -> None:
        """缩放参考图片 (1.0 = 原始大小)."""
        scale = max(0.1, min(10.0, scale))
        self._ref_scale = scale
        if hasattr(self, '_ref_original_pixmap') and not self._ref_original_pixmap.isNull():
            new_w = int(self._ref_original_pixmap.width() * scale)
            new_h = int(self._ref_original_pixmap.height() * scale)
            scaled = self._ref_original_pixmap.scaled(
                new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._ref_pixmap_item.setPixmap(scaled)

    def fit_ref_to_map(self) -> None:
        """让参考图片铺满地图。"""
        if hasattr(self, '_ref_original_pixmap') and not self._ref_original_pixmap.isNull():
            scaled = self._ref_original_pixmap.scaled(
                MAP_WIDTH, MAP_HEIGHT, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self._ref_pixmap_item.setPixmap(scaled)
            self._ref_pixmap_item.setPos(0, 0)
            self._ref_scale = MAP_WIDTH / self._ref_original_pixmap.width()

    def move_ref_image(self, dx: int, dy: int) -> None:
        """移动参考图片位置。"""
        pos = self._ref_pixmap_item.pos()
        self._ref_pixmap_item.setPos(pos.x() + dx, pos.y() + dy)

    def toggle_ref_image(self, visible: bool) -> None:
        self._show_ref_image = visible
        self._ref_pixmap_item.setVisible(visible)

    # ── 变换工具 ──

    def _update_transform_visuals(self) -> None:
        """根据 _transform_box 更新变换框和 handle 位置。"""
        if not self._transform_box:
            self._transform_border.setVisible(False)
            for h in self._transform_handles.values():
                h.setVisible(False)
            return

        x0, y0, x1, y1 = self._transform_box
        self._transform_border.setRect(QRectF(x0, y0, x1 - x0, y1 - y0))
        self._transform_border.setVisible(True)

        positions = {"tl": (x0, y0), "tr": (x1, y0), "bl": (x0, y1), "br": (x1, y1)}
        for hid, (hx, hy) in positions.items():
            self._transform_handles[hid].setPos(hx, hy)
            self._transform_handles[hid].setVisible(True)

    def _hit_test_transform(self, sx: float, sy: float) -> str | None:
        """判断点击位置在变换框的哪个部分。返回 "move"/"tl"/"tr"/"bl"/"br"/None."""
        if not self._transform_box:
            return None
        x0, y0, x1, y1 = self._transform_box
        handle_r = 10 / self._zoom  # handle 热区半径（屏幕像素转场景像素）

        # 检查 4 个角 handle
        for hid, (hx, hy) in [("tl", (x0, y0)), ("tr", (x1, y0)),
                               ("bl", (x0, y1)), ("br", (x1, y1))]:
            if abs(sx - hx) < handle_r and abs(sy - hy) < handle_r:
                return hid

        # 检查是否在框内（移动）
        if x0 <= sx <= x1 and y0 <= sy <= y1:
            return "move"

        # 框外附近 = 旋转（距离框边 < 30px）
        margin = 30 / self._zoom
        if (x0 - margin <= sx <= x1 + margin and y0 - margin <= sy <= y1 + margin):
            return "rotate"
        return None

    def _apply_transform(self) -> None:
        """将变换结果（缩放+旋转）写入 tile_map。"""
        if self._transform_snippet is None or self._transform_box is None:
            return

        from scipy.ndimage import zoom, rotate

        x0, y0, x1, y1 = [int(v) for v in self._transform_box]
        x0 = max(0, x0); y0 = max(0, y0)
        x1 = min(MAP_WIDTH, x1); y1 = min(MAP_HEIGHT, y1)
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
        self._map_data.tile_map = self._tile_map.copy()
        self._full_render()

    def _cancel_transform(self) -> None:
        """取消变换，恢复原始状态。"""
        if self._transform_snippet is not None and self._transform_orig_box is not None:
            # 恢复原始片段到原始位置
            ox0, oy0, ox1, oy1 = self._transform_orig_box
            self._tile_map[oy0:oy1, ox0:ox1] = self._transform_snippet
            self._map_data.tile_map = self._tile_map.copy()
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
            "continent": self._render_land_mode,
            "strategic_region": self._render_land_mode,
            "colormap": self._render_land_mode,
            "default_map": self._render_land_mode,
        }
        renderers.get(self._display_mode, self._render_land_mode)()
        self._update_pixmap_from_buffer()
        # VP 标记叠加 (Feature 10)
        self._render_vp_overlay()

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
            "continent": self._partial_render_land,
            "strategic_region": self._partial_render_land,
            "colormap": self._partial_render_land,
            "default_map": self._partial_render_land,
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

        # 高亮选中省份：用黄色描边它的边界
        sel = self._selected_province_id
        if sel > 0:
            sel_mask = self._province_map == sel
            sel_border = np.zeros_like(borders)
            sel_border[:-1, :] |= sel_mask[:-1, :] != sel_mask[1:, :]
            sel_border[1:, :]  |= sel_mask[:-1, :] != sel_mask[1:, :]
            sel_border[:, :-1] |= sel_mask[:, :-1] != sel_mask[:, 1:]
            sel_border[:, 1:]  |= sel_mask[:, :-1] != sel_mask[:, 1:]
            rgba[sel_border] = (255, 230, 0, 255)  # 不透明黄色

        img = QImage(rgba.data, MAP_WIDTH, MAP_HEIGHT,
                     MAP_WIDTH * 4, QImage.Format.Format_ARGB32)
        img._ref = rgba
        self._province_pixmap_item.setPixmap(QPixmap.fromImage(img))
        self._province_pixmap_item.setVisible(True)

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

    # ────── 扩张工具可视反馈 ──────

    def _show_expand_overlay(self) -> None:
        """显示选中省份的 allowed 区域（半透明黄色）+ 进入扩张时变成绿色。"""
        if self._framework_ctx is None:
            return
        mask = self._framework_ctx.state.get("allowed_mask")
        if mask is None:
            return
        active = self._framework_ctx.state.get("active", False)
        # active 状态用绿色（提示"现在能画了"），未 active 用黄色（提示"再点一次进入"）
        color = (50, 220, 80, 70) if active else (255, 230, 0, 60)
        rgba = np.zeros((MAP_HEIGHT, MAP_WIDTH, 4), dtype=np.uint8)
        rgba[mask] = color
        img = QImage(rgba.data, MAP_WIDTH, MAP_HEIGHT,
                     MAP_WIDTH * 4, QImage.Format.Format_ARGB32)
        img._ref = rgba
        self._lasso_overlay.setPixmap(QPixmap.fromImage(img))
        self._lasso_overlay.setVisible(True)
        # 不显示路径线
        self._lasso_path_item.setVisible(False)

    def _clear_lasso_visual(self) -> None:
        """清除所有套索反馈元素。"""
        self._lasso_path_item.setPath(QPainterPath())
        self._lasso_path_item.setVisible(False)
        self._lasso_overlay.setVisible(False)

    def center_on_pixel(self, x: int, y: int, zoom: float | None = None) -> None:
        """让画布中心对准地图坐标 (x, y)，可选放大到 zoom 倍。
        用于验证对话框跳转到问题位置。"""
        if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
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
        # 省份模式：固定 1 像素，不依赖刷子大小（边界编辑要精确）
        if self._display_mode == "province":
            r = 0
        else:
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
            if not self._terrain_brush_mode:
                # 按省份为单位分配，不走画笔
                return
            # 画笔模式：逐像素绘制 graphical terrain (不影响 provincial_terrain)
            if self._current_tool == "eraser":
                self._terrain_map[y0:y1, x0:x1] = 0
            elif self._current_tool == "brush":
                self._terrain_map[y0:y1, x0:x1] = self._current_terrain_index

        elif mode == "height":
            # 高度也按省份为单位分配
            return

        elif mode == "province":
            # 省份模式：边界拖动 — 只能把"同类型地块的相邻省份像素"转给选中省份
            # 例如：选中一个 land 省份，画笔只影响 land 像素，不会把海或湖变成陆地
            if self._selected_province_id <= 0:
                return
            sub_pm = self._province_map[y0:y1, x0:x1]
            sub_tm = self._tile_map[y0:y1, x0:x1]
            # 条件：地块类型匹配 AND 不是背景 AND 不是已经属于选中省份
            mask = (
                (sub_tm == self._selected_province_tile)
                & (sub_pm != 0)
                & (sub_pm != self._selected_province_id)
            )
            sub_pm[mask] = self._selected_province_id

        elif mode == "river":
            if self._current_tool == "eraser":
                self._river_map[y0:y1, x0:x1] = RIVER_ERASE
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

    def _scene_pos_clamped(self, event: QMouseEvent) -> tuple[int, int]:
        """返回限制在地图边界内的场景坐标"""
        sx, sy = self._scene_pos(event)
        return max(0, min(MAP_WIDTH - 1, sx)), max(0, min(MAP_HEIGHT - 1, sy))

    def _is_in_bounds(self, sx: int, sy: int) -> bool:
        """检查坐标是否在地图边界内"""
        return 0 <= sx < MAP_WIDTH and 0 <= sy < MAP_HEIGHT

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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        # 框选模式拦截
        if self._selection_mode and event.button() == Qt.MouseButton.LeftButton:
            sx, sy = self._scene_pos(event)
            self._selection_start = (int(sx), int(sy))
            self._selection_rect_item.setRect(QRectF(sx, sy, 0, 0))
            self._selection_rect_item.setVisible(True)
            event.accept()
            return

        # Ctrl+左键：拖拽移动参考图
        if (event.button() == Qt.MouseButton.LeftButton
                and event.modifiers() & Qt.ControlModifier):
            self._ref_dragging = True
            self._ref_drag_start = event.pos()
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            event.accept()
            return

        # 框架工具分发（新规范）
        if (event.button() == Qt.MouseButton.LeftButton
                and self._framework_tool is not None
                and not self._space_pressed):
            sx, sy = self._scene_pos(event)
            if 0 <= sx < MAP_WIDTH and 0 <= sy < MAP_HEIGHT:
                self._framework_ctx.dirty_bbox = None
                self._framework_tool.begin_undo(self._framework_ctx)
                self._framework_tool.on_press(self._framework_ctx, sx, sy)
                self._is_drawing = True

                # 扩张工具可视反馈：选中省份后显示 allowed 区域 overlay
                if self._framework_ctx.state.get("pid"):
                    self._show_expand_overlay()

                self.stroke_started.emit()
                self._render_province_overlay()
                event.accept()
                return

        if event.button() == Qt.MouseButton.LeftButton:
            if self._space_pressed or self._current_tool == "pan":
                self._is_panning = True
                self._pan_start = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return

            # 变换工具
            if self._current_tool == "transform" and self._display_mode == "land":
                sx, sy = self._scene_pos(event)

                if self._transform_active:
                    # 已有变换框 — 判断点击位置
                    hit = self._hit_test_transform(sx, sy)
                    if hit:
                        self._transform_drag = hit
                        self._transform_drag_start = (sx, sy)
                        self._transform_box_start = tuple(self._transform_box)
                        self._transform_angle_start = self._transform_angle
                        if hit == "move":
                            self.setCursor(Qt.CursorShape.SizeAllCursor)
                        elif hit == "rotate":
                            self.setCursor(Qt.CursorShape.CrossCursor)
                        else:
                            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                        event.accept()
                        return
                    else:
                        # 点击远处框外 = 确认变换
                        self._apply_transform()
                        self.stroke_ended.emit()
                        self._end_transform()
                        event.accept()
                        return

                # 没有变换框 — 开始框选
                self._transform_selecting = True
                self._selection_start = (int(sx), int(sy))
                self._selection_rect_item.setRect(QRectF(sx, sy, 0, 0))
                self._selection_rect_item.setVisible(True)
                self.stroke_started.emit()
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
                            # 画笔模式：逐像素绘制，不按省份
                            if self._terrain_brush_mode:
                                # 进入画笔绘制流程（和 land 模式类似）
                                self._is_drawing = True
                                self.stroke_started.emit()
                                self._paint_at(sx, sy)
                                event.accept()
                                return
                            # 海洋/湖泊省份不可改地形
                            tile_val = self._tile_map[sy, sx]
                            if tile_val in (TILE_SEA, TILE_LAKE):
                                event.accept()
                                return
                            self.stroke_started.emit()
                            self._terrain_map[mask] = self._current_terrain_index
                            # 同步省份级地形 (Feature A)
                            ptype = PALETTE_TO_TYPE.get(self._current_terrain_index)
                            if ptype:
                                self._map_data.provincial_terrain[pid] = ptype
                            # 联动高度：根据 graphical terrain 的 type 查 height_base
                            if ptype and ptype in TERRAIN_TYPES:
                                self._height_map[mask] = TERRAIN_TYPES[ptype].height_base
                            # 自动平滑高度过渡
                            from services.terrain_service import smooth_height
                            self._height_map = smooth_height(self._height_map, sigma=3.0)
                            self._map_data.height_map = self._height_map
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

            # 省份模式：左键只做选中 (扩张需走 lasso 框架工具, 不允许直接拖动改边界)
            if self._display_mode == "province":
                sx, sy = self._scene_pos(event)
                if 0 <= sx < MAP_WIDTH and 0 <= sy < MAP_HEIGHT:
                    pid = int(self._province_map[sy, sx])
                    if pid > 0:
                        self._selected_province_id = pid
                        self._selected_province_tile = int(self._tile_map[sy, sx])
                        self.province_clicked.emit(pid)
                        self._render_province_overlay()
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
        """更新画笔预览光标位置和大小。
        省份模式不显示刷子框 — 它是边界编辑工具，不是绘画工具。"""
        if self._current_tool in ("brush", "eraser") and self._display_mode in ("land", "river"):
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

        # 变换工具框选拖拽
        if self._transform_selecting and self._selection_start:
            x0, y0 = self._selection_start
            x1 = max(0, min(MAP_WIDTH, int(sx)))
            y1 = max(0, min(MAP_HEIGHT, int(sy)))
            rx0, ry0 = min(x0, x1), min(y0, y1)
            rx1, ry1 = max(x0, x1), max(y0, y1)
            self._selection_rect = (rx0, ry0, rx1, ry1)
            self._selection_rect_item.setRect(QRectF(rx0, ry0, rx1 - rx0, ry1 - ry0))
            event.accept()
            return

        # 变换工具拖拽（移动/缩放）
        if self._transform_drag and self._transform_box:
            dx = sx - self._transform_drag_start[0]
            dy = sy - self._transform_drag_start[1]
            bx0, by0, bx1, by1 = self._transform_box_start

            if self._transform_drag == "move":
                self._transform_box = (bx0 + dx, by0 + dy, bx1 + dx, by1 + dy)
            elif self._transform_drag == "rotate":
                # 以框中心为原点，计算起始角和当前角的差
                import math
                cx = (bx0 + bx1) / 2
                cy = (by0 + by1) / 2
                start_angle = math.atan2(
                    self._transform_drag_start[1] - cy,
                    self._transform_drag_start[0] - cx,
                )
                cur_angle = math.atan2(sy - cy, sx - cx)
                delta_deg = math.degrees(cur_angle - start_angle)
                self._transform_angle = self._transform_angle_start + delta_deg
            elif self._transform_drag == "tl":
                self._transform_box = (bx0 + dx, by0 + dy, bx1, by1)
            elif self._transform_drag == "tr":
                self._transform_box = (bx0, by0 + dy, bx1 + dx, by1)
            elif self._transform_drag == "bl":
                self._transform_box = (bx0 + dx, by0, bx1, by1 + dy)
            elif self._transform_drag == "br":
                self._transform_box = (bx0, by0, bx1 + dx, by1 + dy)

            self._update_transform_visuals()

            # 实时预览
            self._apply_transform()

            event.accept()
            return

        # 框选模式拖拽
        if self._selection_mode and self._selection_start:
            x0, y0 = self._selection_start
            x1, y1 = max(0, min(MAP_WIDTH, int(sx))), max(0, min(MAP_HEIGHT, int(sy)))
            rx0, ry0 = min(x0, x1), min(y0, y1)
            rx1, ry1 = max(x0, x1), max(y0, y1)
            self._selection_rect = (rx0, ry0, rx1, ry1)
            self._selection_rect_item.setRect(QRectF(rx0, ry0, rx1 - rx0, ry1 - ry0))
            event.accept()
            return

        # Ctrl+拖拽：移动参考图
        if getattr(self, '_ref_dragging', False):
            delta = event.pos() - self._ref_drag_start
            self._ref_drag_start = event.pos()
            # 屏幕像素转场景像素（考虑缩放）
            scene_dx = delta.x() / self._zoom
            scene_dy = delta.y() / self._zoom
            self.move_ref_image(scene_dx, scene_dy)
            event.accept()
            return

        if self._is_panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        # 框架工具分发
        if self._is_drawing and self._framework_tool is not None:
            if 0 <= sx < MAP_WIDTH and 0 <= sy < MAP_HEIGHT:
                self._framework_tool.on_drag(self._framework_ctx, sx, sy)
                # 拖动期间持续刷新画布，让用户看到扩张效果
                if self._framework_ctx.state.get("painting"):
                    self._mark_dirty(
                        max(0, sx - 10), max(0, sy - 10),
                        min(MAP_WIDTH, sx + 11), min(MAP_HEIGHT, sy + 11),
                    )
                    self._flush_dirty()
                    self._render_province_overlay()
                event.accept()
                return

        if self._is_drawing and self._current_tool in ("brush", "eraser"):
            self._paint_at(sx, sy)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        # 变换工具框选完成 — 激活变换框
        if self._transform_selecting and self._selection_start:
            self._transform_selecting = False
            self._selection_start = None
            self._selection_rect_item.setVisible(False)
            if self._selection_rect:
                x0, y0, x1, y1 = self._selection_rect
                if x1 - x0 > 5 and y1 - y0 > 5:
                    # 剪切选区内容
                    self._transform_snippet = self._tile_map[y0:y1, x0:x1].copy()
                    self._transform_orig_box = (x0, y0, x1, y1)
                    self._transform_box = (float(x0), float(y0), float(x1), float(y1))
                    # 清除原位置
                    self._tile_map[y0:y1, x0:x1] = TILE_SEA
                    self._full_render()
                    self._transform_active = True
                    self._update_transform_visuals()
            self._selection_rect = None
            event.accept()
            return

        # 变换工具拖拽释放
        if self._transform_drag:
            self._transform_drag = None
            self.setCursor(Qt.CursorShape.CrossCursor)
            event.accept()
            return

        # 框选完成
        if self._selection_mode and self._selection_start:
            self._selection_start = None
            self._finish_selection()
            event.accept()
            return

        # 结束参考图拖拽
        if getattr(self, '_ref_dragging', False):
            self._ref_dragging = False
            self.setCursor(Qt.CursorShape.CrossCursor)
            event.accept()
            return

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

                # 框架工具：先 release，再清理，再 end_undo，最后刷新
                if self._framework_tool is not None:
                    sx, sy = self._scene_pos(event)
                    self._framework_tool.on_release(self._framework_ctx, sx, sy)
                    self._framework_tool.run_cleanup(self._framework_ctx)
                    self._framework_tool.end_undo(self._framework_ctx)
                    # 同步选中状态到 canvas
                    self._selected_province_id = self._framework_ctx.selected_province_id
                    # overlay 跟随：还有 pid 就保留显示，否则清掉
                    if self._framework_ctx.state.get("pid"):
                        self._show_expand_overlay()
                    else:
                        self._clear_lasso_visual()
                    self._mark_dirty(0, 0, MAP_WIDTH, MAP_HEIGHT)
                    self._flush_dirty()
                    if self._display_mode == "province":
                        self._render_province_overlay()
                    self.stroke_ended.emit()
                    event.accept()
                    return

                self._flush_dirty()
                # 省份模式拖动结束后：只刷新边界，不做重清理
                # （重清理移到导出时跑，避免每次松鼠标卡住）
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
        # Ctrl+滚轮：缩放参考图
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            scale_step = 0.1 if delta > 0 else -0.1
            new_scale = getattr(self, '_ref_scale', 1.0) + scale_step
            self.set_ref_scale(new_scale)
            event.accept()
            return

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
        # ESC：取消正在进行的套索/框架工具操作
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Enter 确认变换
            if self._transform_active:
                self._apply_transform()
                self.stroke_ended.emit()
                self._end_transform()
                return
        elif event.key() == Qt.Key.Key_Escape:
            # ESC 取消变换
            if self._transform_active:
                self._cancel_transform()
                self.stroke_ended.emit()
                return
            if self._is_drawing and self._framework_tool is not None:
                self._framework_tool.on_cancel(self._framework_ctx)
                self._is_drawing = False
                self._clear_lasso_visual()
                # 不入撤销栈（因为是取消，pending 直接丢弃）
                self._framework_ctx.undo_mgr._pending = None
                self.stroke_ended.emit()
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
