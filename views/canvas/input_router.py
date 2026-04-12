"""
输入事件路由 Mixin — 鼠标/键盘事件处理
从 canvas_widget.py 拆分而来
"""
from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QMouseEvent, QWheelEvent

from data.constants import (
    MAP_WIDTH, MAP_HEIGHT,
    TILE_SEA, TILE_LAKE,
    ZOOM_MIN, ZOOM_MAX, ZOOM_STEP,
)
from data.terrain_types import TERRAIN_TYPES, PALETTE_TO_TYPE


class InputMixin:
    """鼠标/键盘事件处理方法。假设 self 拥有 MapCanvas 的全部状态属性。"""

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
                    from data.constants import TILE_SEA
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
        """右键省份 → 弹出上下文菜单（所有模式）"""
        pos = self.mapToScene(event.pos())
        sx, sy = int(pos.x()), int(pos.y())
        if 0 <= sx < MAP_WIDTH and 0 <= sy < MAP_HEIGHT:
            pid = int(self._province_map[sy, sx])
            if pid > 0:
                self.province_right_clicked.emit(pid)
                # 传递屏幕坐标，供弹出菜单定位
                global_pos = self.mapToGlobal(event.pos())
                self.province_right_clicked_at.emit(pid, global_pos.x(), global_pos.y())
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
