"""
参考图管理 Mixin — 用户参考图 + 原版地图参考层
从 canvas_widget.py 拆分而来
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from data.constants import MAP_WIDTH, MAP_HEIGHT


class RefImageMixin:
    """参考图相关方法。假设 self 拥有:
    - _ref_pixmap_item, _vanilla_ref_item
    - _ref_original_pixmap, _ref_scale
    - _show_ref_image
    """

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
