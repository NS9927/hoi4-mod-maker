"""
叠加层 Mixin — 省份边界/VP标记/变换框/套索/画笔光标
从 canvas_widget.py 拆分而来
"""
import numpy as np
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import (
    QImage, QPixmap, QPainter, QColor, QPen, QPainterPath, QBrush,
)

class OverlayMixin:
    """叠加层相关方法。假设 self 拥有:
    - _province_pixmap_item, _province_map, _selected_province_id
    - _show_provinces, _display_mode
    - _vp_overlay_item, _vp_data, _map_data
    - _transform_border, _transform_handles, _transform_box, _zoom
    - _lasso_path_item, _lasso_overlay, _framework_ctx
    - _brush_cursor, _current_tool, _brush_size
    """

    def _rebuild_border_cache(self) -> None:
        """重建省份边界缓存 + base QPixmap（只在省份数据变化时调用）。"""
        if self._province_map.max() == 0:
            self._border_cache = None
            self._border_base_pixmap = None
            return
        h, w = self._province_map.shape
        borders = np.zeros((h, w), dtype=bool)
        borders[:-1, :] |= self._province_map[:-1, :] != self._province_map[1:, :]
        borders[:, :-1] |= self._province_map[:, :-1] != self._province_map[:, 1:]
        self._border_cache = borders
        # 生成 base pixmap（只做一次，不用每次 copy 46MB）
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        rgba[borders, 3] = 180
        img = QImage(rgba.data, w, h,
                     w * 4, QImage.Format.Format_ARGB32)
        img._ref = rgba
        self._border_base_pixmap = QPixmap.fromImage(img)

    def _render_province_overlay(self) -> None:
        """渲染省份边界叠加层（base pixmap + 高亮用 QPainter 画）"""
        if not self._show_provinces or self._province_map.max() == 0:
            self._province_pixmap_item.setVisible(False)
            return

        if not hasattr(self, '_border_cache') or self._border_cache is None:
            self._rebuild_border_cache()
        if not hasattr(self, '_border_base_pixmap') or self._border_base_pixmap is None:
            self._rebuild_border_cache()

        # 从 base pixmap 复制（QPixmap copy 很快，不涉及 numpy）
        result = QPixmap(self._border_base_pixmap)

        # 高亮选中省份（用 QPainter 画黄色边框，不操作 numpy 数组）
        sel = self._selected_province_id
        if sel > 0:
            ys, xs = np.where(self._province_map == sel)
            if len(ys) > 0:
                y0 = max(0, int(ys.min()) - 1)
                y1 = min(self.map_h, int(ys.max()) + 2)
                x0 = max(0, int(xs.min()) - 1)
                x1 = min(self.map_w, int(xs.max()) + 2)

                # 在小区域内算高亮边界
                sub = self._province_map[y0:y1, x0:x1]
                sel_mask = sub == sel
                sel_border = np.zeros_like(sel_mask)
                sel_border[:-1, :] |= sel_mask[:-1, :] != sel_mask[1:, :]
                sel_border[1:, :]  |= sel_mask[:-1, :] != sel_mask[1:, :]
                sel_border[:, :-1] |= sel_mask[:, :-1] != sel_mask[:, 1:]
                sel_border[:, 1:]  |= sel_mask[:, :-1] != sel_mask[:, 1:]

                # 画黄色高亮到小区域
                h_rgba = np.zeros((y1 - y0, x1 - x0, 4), dtype=np.uint8)
                h_rgba[sel_border] = (0, 230, 255, 255)  # BGRA: yellow
                h_img = QImage(h_rgba.data, x1 - x0, y1 - y0,
                              (x1 - x0) * 4, QImage.Format.Format_ARGB32)
                h_img._ref = h_rgba

                painter = QPainter(result)
                painter.drawImage(x0, y0, h_img)
                painter.end()
        self._province_pixmap_item.setPixmap(result)
        self._province_pixmap_item.setVisible(True)

    def set_vp_data(self, vp_dict: dict[int, int]) -> None:
        """设置 VP 数据 {province_id: vp_value}，在 state/province 模式显示标记"""
        self._vp_data = dict(vp_dict)
        self._vp_cache_dirty = True
        self._update_vp_visibility()

    def _update_vp_visibility(self) -> None:
        """根据当前模式显示/隐藏 VP 叠加层，只在数据变化时重绘"""
        if self._display_mode not in ("state", "province") or not self._vp_data:
            self._vp_overlay_item.setVisible(False)
            return
        if getattr(self, '_vp_cache_dirty', True):
            self._render_vp_overlay()
            self._vp_cache_dirty = False
        self._vp_overlay_item.setVisible(True)

    def _render_vp_overlay(self) -> None:
        """渲染 VP 标记叠加层（仅在 VP 数据变化时调用，结果缓存）"""
        if not self._vp_data:
            return

        # 创建透明画布
        img = QImage(self.map_w, self.map_h, QImage.Format.Format_ARGB32)
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

            radius = max(6, min(14, 4 + vp_val))
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setBrush(QBrush(QColor(220, 30, 30)))
            painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

            from PyQt5.QtGui import QFont
            font = QFont("Arial", max(8, min(12, 6 + vp_val // 2)))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            text_rect = QRectF(cx - 20, cy - 10, 40, 20)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(vp_val))

        painter.end()
        self._vp_overlay_item.setPixmap(QPixmap.fromImage(img))

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
        rgba = np.zeros((self.map_h, self.map_w, 4), dtype=np.uint8)
        rgba[mask] = color
        img = QImage(rgba.data, self.map_w, self.map_h,
                     self.map_w * 4, QImage.Format.Format_ARGB32)
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

    def _update_brush_cursor(self, sx: int, sy: int) -> None:
        """更新画笔预览光标位置和大小。
        省份模式不显示刷子框 — 它是边界编辑工具，不是绘画工具。"""
        if self._current_tool in ("brush", "eraser") and self._display_mode in ("land", "river"):
            r = self._brush_size // 2
            self._brush_cursor.setRect(sx - r, sy - r, self._brush_size, self._brush_size)
            self._brush_cursor.setVisible(True)
        else:
            self._brush_cursor.setVisible(False)
