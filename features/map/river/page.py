"""river feature 页面 — 独立 QWidget, 不依赖 ToolPanel."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QSlider, QLabel, QButtonGroup, QGridLayout,
)

from domain.managers.river import (
    RIVER_MARKER_TYPES, RIVER_WIDTH_TYPES, RIVER_PALETTE,
)

from ui.styles import (
    make_section as _make_section,
    _DIM, _SECTION_STYLE, _LABEL_STYLE, _DIM_LABEL_STYLE, _SLIDER_STYLE,
    _TOOL_BTN_STYLE, _SECONDARY_BTN_STYLE,
)
from ui.i18n import tr




class RiverPage(QWidget):
    """河流编辑页面."""

    # 输出信号
    tool_changed = pyqtSignal(str)
    brush_size_changed = pyqtSignal(int)
    river_type_changed = pyqtSignal(int)
    validate_river_requested = pyqtSignal()
    auto_river_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)

        # 提示
        hint = QLabel(tr("river_hint"))
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # 工具按钮
        tools_box = _make_section(tr("river_section_tools"))
        tl = QHBoxLayout()
        self._river_tool_group = QButtonGroup(self)
        self._river_tool_group.setExclusive(True)
        for tid, label in [("brush", tr("river_tool_brush")), ("eraser", tr("river_tool_eraser")), ("pan", tr("river_tool_pan"))]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("tool_id", tid)
            btn.setStyleSheet(_TOOL_BTN_STYLE)
            btn.setMinimumWidth(48)
            self._river_tool_group.addButton(btn)
            tl.addWidget(btn)
            if tid == "brush":
                btn.setChecked(True)
        self._river_tool_group.buttonClicked.connect(
            lambda b: self.tool_changed.emit(b.property("tool_id"))
        )
        tools_box.layout().addLayout(tl)
        lay.addWidget(tools_box)

        # 画笔大小
        brush_box = _make_section(tr("river_section_brush_size"))
        self._river_brush_label = QLabel("3px")
        self._river_brush_label.setStyleSheet(_DIM_LABEL_STYLE)
        row = QHBoxLayout()
        lbl = QLabel(tr("river_label_size"))
        lbl.setStyleSheet(_LABEL_STYLE)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(self._river_brush_label)
        brush_box.layout().addLayout(row)

        self._river_brush_slider = QSlider(Qt.Orientation.Horizontal)
        self._river_brush_slider.setRange(1, 20)
        self._river_brush_slider.setValue(3)
        self._river_brush_slider.setStyleSheet(_SLIDER_STYLE)
        self._river_brush_slider.valueChanged.connect(self._on_river_brush)
        brush_box.layout().addWidget(self._river_brush_slider)
        lay.addWidget(brush_box)

        # 标记类型 (单像素)
        marker_box = _make_section(tr("river_section_markers"))
        mgrid = QGridLayout()
        mgrid.setSpacing(4)

        for i, (idx, name) in enumerate(RIVER_MARKER_TYPES):
            r, g, b = RIVER_PALETTE[idx]
            btn = _make_river_btn(name, r, g, b)
            btn.clicked.connect(lambda _, ix=idx: self.river_type_changed.emit(ix))
            mgrid.addWidget(btn, 0, i)

        marker_box.layout().addLayout(mgrid)
        lay.addWidget(marker_box)

        # 河流宽度画笔
        width_box = _make_section(tr("river_section_width"))
        wgrid = QGridLayout()
        wgrid.setSpacing(4)

        for i, (idx, name) in enumerate(RIVER_WIDTH_TYPES):
            r, g, b = RIVER_PALETTE[idx]
            btn = _make_river_btn(name, r, g, b)
            btn.clicked.connect(lambda _, ix=idx: self.river_type_changed.emit(ix))
            wgrid.addWidget(btn, i // 3, i % 3)

        width_box.layout().addLayout(wgrid)
        lay.addWidget(width_box)

        # 自动生成
        from ui.styles import _PRIMARY_BTN_STYLE
        auto_btn = QPushButton(tr("river_btn_auto"))
        auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        auto_btn.setToolTip(tr("river_btn_auto_tip"))
        auto_btn.clicked.connect(self.auto_river_requested.emit)
        lay.addWidget(auto_btn)

        # 验证按钮
        validate_btn = QPushButton(tr("river_btn_validate"))
        validate_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        validate_btn.clicked.connect(self.validate_river_requested.emit)
        lay.addWidget(validate_btn)

        lay.addStretch()

    # ── 槽函数 ──
    def _on_river_brush(self, size: int) -> None:
        self._river_brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)


def _make_river_btn(name: str, r: int, g: int, b: int) -> QPushButton:
    """创建河流类型按钮."""
    btn = QPushButton(name)
    brightness = r * 0.299 + g * 0.587 + b * 0.114
    fg = "#000000" if brightness > 140 else "#ffffff"
    btn.setStyleSheet(f"""
        QPushButton {{
            background: rgb({r},{g},{b});
            border: 2px solid transparent;
            color: {fg};
            padding: 6px 2px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
            min-width: 55px;
        }}
        QPushButton:hover {{
            border-color: white;
        }}
    """)
    return btn
