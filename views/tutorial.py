"""
交互式新手教程 — 自动创建小画布，一步步引导用户完成从画地图到导出的全流程。
"""
from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox

from ui.tutorial_overlay import TutorialOverlay
from ui.i18n import tr


class TutorialController:
    """管理交互式教程的步骤推进。"""

    def __init__(self, main_window) -> None:
        self._mw = main_window
        self._overlay = TutorialOverlay(main_window)
        self._overlay.skip_requested.connect(self.stop)
        self._overlay.next_requested.connect(self._on_next)
        self._step = 0
        self._event_bus = main_window._event_bus
        self._subscriptions: list[tuple[str, object]] = []

    def start(self) -> None:
        """启动教程：新建小画布 → 进入编辑器 → 开始第1步。"""
        # 新建小画布 1024×512
        mw = self._mw
        mw._on_new_project()
        mw._show_editor()

        # 调整 overlay 尺寸覆盖主窗口
        self._overlay.setGeometry(mw.centralWidget().rect())
        self._overlay.show()
        self._overlay.raise_()

        self._step = 0
        self._show_current_step()

    def stop(self) -> None:
        """结束教程。"""
        self._unsubscribe_all()
        self._overlay.hide()
        self._step = 0

    # ── 步骤定义 ──────────────────────────────────────────

    _STEPS = [
        # (mode_to_switch, method_name)
        ("land",             "_step_draw_land"),
        ("land",             "_step_generate_provinces"),
        ("height",           "_step_auto_height"),
        ("terrain",          "_step_auto_terrain"),
        ("land",             "_step_quick_init"),
        (None,               "_step_export"),
        (None,               "_step_done"),
    ]

    def _show_current_step(self) -> None:
        if self._step >= len(self._STEPS):
            self.stop()
            return

        mode, method_name = self._STEPS[self._step]

        # 自动切换模式
        if mode:
            tp = self._mw._tool_panel
            tp._mode_tabs._buttons[mode].setChecked(True)
            tp._on_mode_changed(mode)

        # 调用步骤方法
        getattr(self, method_name)()

    def _on_next(self) -> None:
        """用户点了下一步。"""
        self._unsubscribe_all()
        self._step += 1
        self._show_current_step()

    def _advance_auto(self) -> None:
        """自动推进到下一步（带短暂延迟让用户看到效果）。"""
        self._unsubscribe_all()
        self._step += 1
        QTimer.singleShot(800, self._show_current_step)

    # ── 各步骤实现 ────────────────────────────────────────

    def _step_draw_land(self) -> None:
        """第1步：画陆地。"""
        self._overlay.set_next_text(tr("tut_next"))
        self._overlay.show_step(
            tr("tut_step_n", 1, 6),
            tr("tut_step1_msg"),
            target=self._mw._canvas,
            show_next=True,
        )

    def _step_generate_provinces(self) -> None:
        """第2步：生成省份。"""
        # 自动调低省份数量（小画布用 500）
        land_page = self._mw._tool_panel._land_page
        land_page._province_count_spin.setValue(500)

        self._overlay.show_step(
            tr("tut_step_n", 2, 6),
            tr("tut_step2_msg"),
            target=land_page,
            show_next=False,
        )
        self._overlay.set_next_text(tr("tut_next"))

        # 监听省份生成完成
        self._subscribe("province_map_regenerated", lambda *a: self._advance_auto())

    def _step_auto_height(self) -> None:
        """第3步：自动生成高度图。"""
        height_page = self._mw._tool_panel._height_page

        self._overlay.show_step(
            tr("tut_step_n", 3, 6),
            tr("tut_step3_msg"),
            target=height_page,
            show_next=False,
        )

        # 监听 auto_height 信号
        self._mw._tool_panel.auto_height_requested.connect(self._on_height_done)

    def _on_height_done(self) -> None:
        self._mw._tool_panel.auto_height_requested.disconnect(self._on_height_done)
        self._advance_auto()

    def _step_auto_terrain(self) -> None:
        """第4步：自动生成地形。"""
        terrain_page = self._mw._tool_panel._terrain_page

        self._overlay.show_step(
            tr("tut_step_n", 4, 6),
            tr("tut_step4_msg"),
            target=terrain_page,
            show_next=False,
        )

        self._mw._tool_panel.auto_terrain_requested.connect(self._on_terrain_done)

    def _on_terrain_done(self) -> None:
        self._mw._tool_panel.auto_terrain_requested.disconnect(self._on_terrain_done)
        self._advance_auto()

    def _step_quick_init(self) -> None:
        """第5步：一键初始化。"""
        land_page = self._mw._tool_panel._land_page

        self._overlay.show_step(
            tr("tut_step_n", 5, 6),
            tr("tut_step5_msg"),
            target=land_page,
            show_next=False,
        )

        self._mw._tool_panel.quick_init_requested.connect(self._on_init_done)

    def _on_init_done(self) -> None:
        self._mw._tool_panel.quick_init_requested.disconnect(self._on_init_done)
        self._advance_auto()

    def _step_export(self) -> None:
        """第6步：导出。"""
        self._overlay.show_step(
            tr("tut_step_n", 6, 6),
            tr("tut_step6_msg"),
            target=None,
            show_next=True,
        )
        self._overlay.set_next_text(tr("tut_finish"))

    def _step_done(self) -> None:
        """教程完成。"""
        self.stop()
        QMessageBox.information(
            self._mw,
            tr("tut_done_title"),
            tr("tut_done_msg"),
        )

    # ── EventBus 工具方法 ─────────────────────────────────

    def _subscribe(self, event: str, callback) -> None:
        self._event_bus.subscribe(event, callback)
        self._subscriptions.append((event, callback))

    def _unsubscribe_all(self) -> None:
        for event, callback in self._subscriptions:
            try:
                self._event_bus.unsubscribe(event, callback)
            except (ValueError, KeyError):
                pass
        self._subscriptions.clear()
