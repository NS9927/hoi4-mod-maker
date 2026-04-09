"""
工具面板 — 暗色主题，6 种编辑模式，模式切换标签页
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QSlider, QLabel, QButtonGroup,
    QSpinBox, QFrame, QStackedWidget, QGridLayout,
    QSizePolicy, QListWidget, QListWidgetItem, QComboBox,
    QLineEdit, QColorDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPixmap, QIcon, QBrush

from data.constants import (
    TILE_LAND, TILE_SEA, TILE_LAKE,
    BRUSH_MIN, BRUSH_MAX, BRUSH_DEFAULT,
)
from data.terrain_types import TERRAIN_TYPES, TERRAIN_PALETTE_INDEX
from core.state_manager import StateManager
from core.country_manager import RULING_PARTIES
from core.river_manager import PAINTABLE_RIVER_TYPES, RIVER_PALETTE


# ── 色板常量 ──────────────────────────────────────────────
_BG = "#1a2235"
_INPUT_BG = "#0d1525"
_BORDER = "#2a3a55"
_TEXT = "#e2e8f0"
_DIM = "#8892a8"
_ACCENT = "#3b82f6"
_SUCCESS = "#22c55e"

_SECTION_STYLE = f"""
    QGroupBox {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 6px;
        margin-top: 14px;
        padding-top: 14px;
        color: {_DIM};
        font-size: 11px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
    }}
"""

_LABEL_STYLE = f"color: {_TEXT}; font-size: 12px;"
_DIM_LABEL_STYLE = f"color: {_DIM}; font-size: 11px;"

_SLIDER_STYLE = f"""
    QSlider::groove:horizontal {{
        height: 4px;
        background: {_BORDER};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 14px; height: 14px;
        margin: -5px 0;
        background: {_ACCENT};
        border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{
        background: {_ACCENT};
        border-radius: 2px;
    }}
"""

_TOOL_BTN_STYLE = f"""
    QPushButton {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        color: {_DIM};
        padding: 5px 2px;
        font-size: 11px;
        border-radius: 4px;
    }}
    QPushButton:checked {{
        background: {_ACCENT};
        color: white;
        border-color: {_ACCENT};
    }}
    QPushButton:hover:!checked {{
        background: rgba(255, 255, 255, 0.05);
    }}
"""

_PRIMARY_BTN_STYLE = f"""
    QPushButton {{
        background: {_ACCENT};
        border: none;
        color: white;
        padding: 7px 12px;
        font-size: 12px;
        font-weight: 600;
        border-radius: 5px;
    }}
    QPushButton:hover {{
        background: #2563eb;
    }}
"""

_SECONDARY_BTN_STYLE = f"""
    QPushButton {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        color: {_TEXT};
        padding: 6px 10px;
        font-size: 11px;
        border-radius: 5px;
    }}
    QPushButton:hover {{
        background: rgba(255, 255, 255, 0.06);
    }}
"""

_SUCCESS_BTN_STYLE = f"""
    QPushButton {{
        background: {_SUCCESS};
        border: none;
        color: white;
        padding: 8px 12px;
        font-size: 13px;
        font-weight: 700;
        border-radius: 5px;
    }}
    QPushButton:hover {{
        background: #16a34a;
    }}
"""

_SPINBOX_STYLE = f"""
    QSpinBox {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        color: {_TEXT};
        padding: 3px 6px;
        font-size: 12px;
    }}
"""

_LINEEDIT_STYLE = f"""
    QLineEdit {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        color: {_TEXT};
        padding: 3px 6px;
        font-size: 12px;
    }}
"""

_COMBOBOX_STYLE = f"""
    QComboBox {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        color: {_TEXT};
        padding: 3px 6px;
        font-size: 12px;
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        color: {_TEXT};
        selection-background-color: {_ACCENT};
    }}
"""

_LIST_STYLE = f"""
    QListWidget {{
        background: {_INPUT_BG};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        color: {_TEXT};
        font-size: 11px;
    }}
    QListWidget::item {{
        padding: 4px 6px;
    }}
    QListWidget::item:selected {{
        background: {_ACCENT};
        color: white;
    }}
    QListWidget::item:hover:!selected {{
        background: rgba(255, 255, 255, 0.05);
    }}
"""


# ── 辅助函数 ──────────────────────────────────────────────
def _color_icon(r: int, g: int, b: int, size: int = 12) -> QIcon:
    px = QPixmap(size, size)
    px.fill(QColor(r, g, b))
    return QIcon(px)


# ── 模式标签栏 ────────────────────────────────────────────
class _ModeTabBar(QWidget):
    """模式切换标签栏"""
    mode_changed = pyqtSignal(str)

    def __init__(self, modes: list[tuple[str, str]], parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        self.setStyleSheet(f"""
            _ModeTabBar {{ background: {_INPUT_BG}; border-radius: 6px; }}
        """)

        self._buttons: dict[str, QPushButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for mode_id, label in modes:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("mode_id", mode_id)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {_DIM};
                    padding: 6px 4px;
                    font-size: 11px;
                    font-weight: 500;
                    border-radius: 4px;
                }}
                QPushButton:checked {{
                    background: {_ACCENT};
                    color: white;
                }}
                QPushButton:hover:!checked {{
                    background: rgba(255, 255, 255, 0.05);
                }}
            """)
            self._group.addButton(btn)
            self._buttons[mode_id] = btn
            layout.addWidget(btn)

        self._group.buttonClicked.connect(
            lambda btn: self.mode_changed.emit(btn.property("mode_id"))
        )

        first_btn = list(self._buttons.values())[0]
        first_btn.setChecked(True)


# ── 主面板 ────────────────────────────────────────────────
class ToolPanel(QWidget):
    """左侧工具面板 — 支持 land / province / terrain / height / state / country 六种模式"""

    # 信号
    mode_changed = pyqtSignal(str)
    tool_changed = pyqtSignal(str)
    tile_type_changed = pyqtSignal(int)
    brush_size_changed = pyqtSignal(int)
    terrain_index_changed = pyqtSignal(int)
    height_value_changed = pyqtSignal(int)
    generate_provinces_requested = pyqtSignal(int)
    validate_requested = pyqtSignal()
    auto_terrain_requested = pyqtSignal()
    auto_height_requested = pyqtSignal()
    smooth_height_requested = pyqtSignal()
    export_requested = pyqtSignal()
    split_province_requested = pyqtSignal()  # 切割选中省份
    lasso_province_toggled = pyqtSignal(bool)  # 套索工具开关

    # State / Country 信号
    auto_states_requested = pyqtSignal(int)       # per_state count
    state_selected = pyqtSignal(int)              # state_id
    state_property_changed = pyqtSignal(int, str, object)  # (state_id, prop_name, value)
    create_country_requested = pyqtSignal()
    country_selected = pyqtSignal(str)            # tag
    country_property_changed = pyqtSignal(str, str, object)  # (tag, prop_name, value)
    country_color_change_requested = pyqtSignal(str)  # tag — 请求更改国家颜色

    # 河流信号
    river_type_changed = pyqtSignal(int)          # 河流类型索引

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self.setStyleSheet(
            f"background: {_BG}; border-right: 1px solid {_BORDER};"
        )
        self._init_ui()

    # ── UI 构建 ───────────────────────────────────────────
    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # 模式标签
        self._mode_tabs = _ModeTabBar([
            ("land", "大陆"),
            ("province", "省份"),
            ("terrain", "地形"),
            ("height", "高度"),
            ("state", "State"),
            ("country", "国家"),
            ("river", "河流"),
        ])
        self._mode_tabs.mode_changed.connect(self._on_mode_changed)
        root.addWidget(self._mode_tabs)

        # 堆叠容器
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent; border: none;")
        root.addWidget(self._stack, 1)

        self._land_page = self._build_land_page()
        self._province_page = self._build_province_page()
        self._terrain_page = self._build_terrain_page()
        self._height_page = self._build_height_page()
        self._state_page = self._build_state_page()
        self._country_page = self._build_country_page()
        self._river_page = self._build_river_page()

        self._stack.addWidget(self._land_page)
        self._stack.addWidget(self._province_page)
        self._stack.addWidget(self._terrain_page)
        self._stack.addWidget(self._height_page)
        self._stack.addWidget(self._state_page)
        self._stack.addWidget(self._country_page)
        self._stack.addWidget(self._river_page)

        self._mode_index = {
            "land": 0, "province": 1, "terrain": 2, "height": 3,
            "state": 4, "country": 5, "river": 6,
        }
        self._stack.setCurrentIndex(0)

        # 底部固定区域
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {_BORDER};")
        root.addWidget(sep)

        export_btn = QPushButton("导出 MOD")
        export_btn.setStyleSheet(_SUCCESS_BTN_STYLE)
        export_btn.clicked.connect(self.export_requested.emit)
        root.addWidget(export_btn)

    # ── Land 页 ───────────────────────────────────────────
    def _build_land_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # 工具按钮
        tools_box = self._make_section("工具")
        tl = QHBoxLayout()
        self._land_tool_group = QButtonGroup(self)
        self._land_tool_group.setExclusive(True)
        for tid, label in [("brush", "画笔"), ("eraser", "橡皮"),
                           ("fill", "填充"), ("pan", "平移")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("tool_id", tid)
            btn.setStyleSheet(_TOOL_BTN_STYLE)
            btn.setMinimumWidth(48)
            self._land_tool_group.addButton(btn)
            tl.addWidget(btn)
            if tid == "brush":
                btn.setChecked(True)
        self._land_tool_group.buttonClicked.connect(
            lambda b: self.tool_changed.emit(b.property("tool_id"))
        )
        tools_box.layout().addLayout(tl)
        lay.addWidget(tools_box)

        # 画笔大小
        brush_box = self._make_section("画笔大小")
        self._land_brush_label = QLabel(f"{BRUSH_DEFAULT}px")
        self._land_brush_label.setStyleSheet(_DIM_LABEL_STYLE)
        row = QHBoxLayout()
        lbl = QLabel("大小:")
        lbl.setStyleSheet(_LABEL_STYLE)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(self._land_brush_label)
        brush_box.layout().addLayout(row)

        self._land_brush_slider = QSlider(Qt.Orientation.Horizontal)
        self._land_brush_slider.setRange(BRUSH_MIN, BRUSH_MAX)
        self._land_brush_slider.setValue(BRUSH_DEFAULT)
        self._land_brush_slider.setStyleSheet(_SLIDER_STYLE)
        self._land_brush_slider.valueChanged.connect(self._on_land_brush)
        brush_box.layout().addWidget(self._land_brush_slider)
        lay.addWidget(brush_box)

        # 地块类型
        tile_box = self._make_section("大陆绘制")
        for tile_id, label, color in [
            (TILE_LAND, "画陆地", (139, 172, 101)),
            (TILE_SEA,  "画海洋", (68, 105, 156)),
            (TILE_LAKE, "画湖泊", (100, 160, 210)),
        ]:
            btn = QPushButton(f"  {label}")
            btn.setIcon(_color_icon(*color))
            btn.setStyleSheet(_SECONDARY_BTN_STYLE)
            btn.clicked.connect(lambda _, t=tile_id: self._on_tile_click(t))
            tile_box.layout().addWidget(btn)
        lay.addWidget(tile_box)

        # 生成省份
        gen_box = self._make_section("省份生成")
        gen_btn = QPushButton("生成省份")
        gen_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        gen_btn.clicked.connect(self._on_generate_provinces)
        gen_box.layout().addWidget(gen_btn)

        spin_row = QHBoxLayout()
        spin_lbl = QLabel("省份数量:")
        spin_lbl.setStyleSheet(_LABEL_STYLE)
        spin_row.addWidget(spin_lbl)
        self._province_count_spin = QSpinBox()
        self._province_count_spin.setRange(1000, 15000)
        self._province_count_spin.setValue(5000)
        self._province_count_spin.setStyleSheet(_SPINBOX_STYLE)
        spin_row.addWidget(self._province_count_spin)
        gen_box.layout().addLayout(spin_row)

        validate_btn = QPushButton("验证省份")
        validate_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        validate_btn.clicked.connect(self.validate_requested.emit)
        gen_box.layout().addWidget(validate_btn)
        lay.addWidget(gen_box)

        # 参考底图透明度
        ref_box = self._make_section("参考底图")
        opacity_row = QHBoxLayout()
        olbl = QLabel("透明度:")
        olbl.setStyleSheet(_LABEL_STYLE)
        opacity_row.addWidget(olbl)
        self._ref_opacity_label = QLabel("40%")
        self._ref_opacity_label.setStyleSheet(_DIM_LABEL_STYLE)
        opacity_row.addStretch()
        opacity_row.addWidget(self._ref_opacity_label)
        ref_box.layout().addLayout(opacity_row)

        self._ref_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._ref_opacity_slider.setRange(0, 100)
        self._ref_opacity_slider.setValue(40)
        self._ref_opacity_slider.setStyleSheet(_SLIDER_STYLE)
        self._ref_opacity_slider.valueChanged.connect(
            lambda v: self._ref_opacity_label.setText(f"{v}%")
        )
        ref_box.layout().addWidget(self._ref_opacity_slider)
        lay.addWidget(ref_box)

        lay.addStretch()
        return page

    # ── Terrain 页 ────────────────────────────────────────
    def _build_terrain_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # 提示
        hint = QLabel("选择地形类型，然后点击省份分配")
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # 地形调色板
        palette_box = self._make_section("地形类型")
        grid = QGridLayout()
        grid.setSpacing(4)

        # 仅显示可绘制的陆地地形（排除 ocean / lakes）
        paintable = [
            "plains", "forest", "hills", "mountain",
            "desert", "marsh", "jungle", "urban",
        ]
        for i, key in enumerate(paintable):
            tt = TERRAIN_TYPES[key]
            idx = TERRAIN_PALETTE_INDEX[key]
            btn = QPushButton(tt.name_cn)
            r, g, b = tt.color
            # 根据亮度决定文字颜色
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
                    min-width: 60px;
                }}
                QPushButton:hover {{
                    border-color: white;
                }}
            """)
            btn.clicked.connect(
                lambda _, ix=idx: self.terrain_index_changed.emit(ix)
            )
            grid.addWidget(btn, i // 3, i % 3)

        palette_box.layout().addLayout(grid)
        lay.addWidget(palette_box)

        # 自动生成
        auto_btn = QPushButton("从陆地自动生成")
        auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        auto_btn.clicked.connect(self.auto_terrain_requested.emit)
        lay.addWidget(auto_btn)

        lay.addStretch()
        return page

    # ── Height 页 ─────────────────────────────────────────
    def _build_height_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # 提示
        hint = QLabel("调整高度值，然后点击省份分配高度")
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # 高度值
        height_box = self._make_section("高度值")
        val_row = QHBoxLayout()
        vlbl = QLabel("高度:")
        vlbl.setStyleSheet(_LABEL_STYLE)
        val_row.addWidget(vlbl)
        self._height_value_label = QLabel("120")
        self._height_value_label.setStyleSheet(_DIM_LABEL_STYLE)
        val_row.addStretch()
        val_row.addWidget(self._height_value_label)
        height_box.layout().addLayout(val_row)

        self._height_slider = QSlider(Qt.Orientation.Horizontal)
        self._height_slider.setRange(0, 255)
        self._height_slider.setValue(120)
        self._height_slider.setStyleSheet(_SLIDER_STYLE)
        self._height_slider.valueChanged.connect(self._on_height_value)
        height_box.layout().addWidget(self._height_slider)
        lay.addWidget(height_box)

        # 预设按钮
        preset_box = self._make_section("预设")
        preset_grid = QGridLayout()
        preset_grid.setSpacing(4)
        presets = [
            ("海底", 40), ("海平面", 95), ("平地", 120),
            ("丘陵", 160), ("山地", 220),
        ]
        for i, (name, val) in enumerate(presets):
            btn = QPushButton(f"{name}({val})")
            btn.setStyleSheet(_SECONDARY_BTN_STYLE)
            btn.clicked.connect(lambda _, v=val: self._apply_height_preset(v))
            preset_grid.addWidget(btn, i // 3, i % 3)
        preset_box.layout().addLayout(preset_grid)
        lay.addWidget(preset_box)

        # 操作按钮
        auto_btn = QPushButton("从地形自动生成")
        auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        auto_btn.clicked.connect(self.auto_height_requested.emit)
        lay.addWidget(auto_btn)

        smooth_btn = QPushButton("平滑")
        smooth_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        smooth_btn.clicked.connect(self.smooth_height_requested.emit)
        lay.addWidget(smooth_btn)

        lay.addStretch()
        return page

    # ── Province 页 ───────────────────────────────────────
    def _build_province_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # 提示
        hint = QLabel("合并：点第一个省份，再点第二个\n切割：点击省份后点切割按钮")
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # 操作按钮
        ops_box = self._make_section("省份操作")
        split_btn = QPushButton("切割选中省份")
        split_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        ops_box.layout().addWidget(split_btn)
        self._split_btn = split_btn
        split_btn.clicked.connect(self.split_province_requested.emit)

        # 扩张工具切换按钮（默认关闭，避免和合并冲突）
        expand_btn = QPushButton("🖌 启用扩张工具")
        expand_btn.setCheckable(True)
        expand_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        expand_btn.setToolTip(
            "启用后：点击选中省份 → 再点击同一省份激活 → 拖动扩张边界\n"
            "注意：启用扩张时点击合并功能将不可用，关闭后恢复"
        )
        expand_btn.toggled.connect(
            lambda on: self.lasso_province_toggled.emit(on)
        )
        ops_box.layout().addWidget(expand_btn)
        self._expand_btn = expand_btn

        lay.addWidget(ops_box)

        # 省份信息
        info_box = self._make_section("省份信息")
        il = info_box.layout()

        self._prov_labels: dict[str, QLabel] = {}
        for key, display in [
            ("id", "省份 ID"),
            ("type", "类型"),
            ("terrain", "地形"),
            ("pixels", "像素数"),
            ("coastal", "沿海"),
        ]:
            row = QHBoxLayout()
            name_lbl = QLabel(f"{display}:")
            name_lbl.setStyleSheet(_LABEL_STYLE)
            val_lbl = QLabel("—")
            val_lbl.setStyleSheet(_DIM_LABEL_STYLE)
            val_lbl.setAlignment(Qt.AlignRight)
            row.addWidget(name_lbl)
            row.addStretch()
            row.addWidget(val_lbl)
            il.addLayout(row)
            self._prov_labels[key] = val_lbl

        lay.addWidget(info_box)

        # 操作按钮
        merge_btn = QPushButton("合并到相邻省份")
        merge_btn.setStyleSheet(_SECONDARY_BTN_STYLE)
        lay.addWidget(merge_btn)
        self._merge_btn = merge_btn

        delete_btn = QPushButton("删除省份")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: #dc2626;
                border: none;
                color: white;
                padding: 6px 10px;
                font-size: 11px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background: #b91c1c;
            }}
        """)
        lay.addWidget(delete_btn)
        self._delete_btn = delete_btn

        lay.addStretch()
        return page

    # ── State 页 ──────────────────────────────────────────
    def _build_state_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # 自动分组按钮
        auto_btn = QPushButton("自动分组")
        auto_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        auto_btn.clicked.connect(self._on_auto_states)
        lay.addWidget(auto_btn)

        # 每State省份数
        spin_row = QHBoxLayout()
        spin_lbl = QLabel("每State省份数:")
        spin_lbl.setStyleSheet(_LABEL_STYLE)
        spin_row.addWidget(spin_lbl)
        self._state_per_spin = QSpinBox()
        self._state_per_spin.setRange(5, 30)
        self._state_per_spin.setValue(15)
        self._state_per_spin.setStyleSheet(_SPINBOX_STYLE)
        spin_row.addWidget(self._state_per_spin)
        lay.addLayout(spin_row)

        # State 列表
        list_box = self._make_section("State 列表")
        self._state_list = QListWidget()
        self._state_list.setStyleSheet(_LIST_STYLE)
        self._state_list.setMaximumHeight(200)
        self._state_list.currentRowChanged.connect(self._on_state_list_clicked)
        list_box.layout().addWidget(self._state_list)
        lay.addWidget(list_box)

        # State 属性面板
        info_box = self._make_section("State 属性")
        il = info_box.layout()

        # 名称
        name_row = QHBoxLayout()
        name_lbl = QLabel("名称:")
        name_lbl.setStyleSheet(_LABEL_STYLE)
        name_row.addWidget(name_lbl)
        self._state_name_edit = QLineEdit()
        self._state_name_edit.setStyleSheet(_LINEEDIT_STYLE)
        self._state_name_edit.editingFinished.connect(self._on_state_name_changed)
        name_row.addWidget(self._state_name_edit)
        il.addLayout(name_row)

        # 人口
        mp_row = QHBoxLayout()
        mp_lbl = QLabel("人口:")
        mp_lbl.setStyleSheet(_LABEL_STYLE)
        mp_row.addWidget(mp_lbl)
        self._state_manpower_spin = QSpinBox()
        self._state_manpower_spin.setRange(0, 100000000)
        self._state_manpower_spin.setSingleStep(10000)
        self._state_manpower_spin.setStyleSheet(_SPINBOX_STYLE)
        self._state_manpower_spin.valueChanged.connect(self._on_state_manpower_changed)
        mp_row.addWidget(self._state_manpower_spin)
        il.addLayout(mp_row)

        # 类别
        cat_row = QHBoxLayout()
        cat_lbl = QLabel("类别:")
        cat_lbl.setStyleSheet(_LABEL_STYLE)
        cat_row.addWidget(cat_lbl)
        self._state_category_combo = QComboBox()
        self._state_category_combo.setStyleSheet(_COMBOBOX_STYLE)
        self._state_category_combo.addItems(StateManager.CATEGORIES)
        self._state_category_combo.currentTextChanged.connect(self._on_state_category_changed)
        cat_row.addWidget(self._state_category_combo)
        il.addLayout(cat_row)

        lay.addWidget(info_box)

        # 提示
        hint = QLabel("选中State后，点击省份可移入该State")
        hint.setStyleSheet(f"color: {_DIM}; font-size: 11px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        lay.addStretch()
        return page

    # ── Country 页 ────────────────────────────────────────
    def _build_country_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # 创建国家按钮
        create_btn = QPushButton("创建国家")
        create_btn.setStyleSheet(_PRIMARY_BTN_STYLE)
        create_btn.clicked.connect(self.create_country_requested.emit)
        lay.addWidget(create_btn)

        # 国家列表
        list_box = self._make_section("国家列表")
        self._country_list = QListWidget()
        self._country_list.setStyleSheet(_LIST_STYLE)
        self._country_list.setMaximumHeight(200)
        self._country_list.currentRowChanged.connect(self._on_country_list_clicked)
        list_box.layout().addWidget(self._country_list)
        lay.addWidget(list_box)

        # 国家属性面板
        info_box = self._make_section("国家属性")
        il = info_box.layout()

        # TAG
        tag_row = QHBoxLayout()
        tag_lbl = QLabel("TAG:")
        tag_lbl.setStyleSheet(_LABEL_STYLE)
        tag_row.addWidget(tag_lbl)
        self._country_tag_label = QLabel("—")
        self._country_tag_label.setStyleSheet(_DIM_LABEL_STYLE)
        tag_row.addStretch()
        tag_row.addWidget(self._country_tag_label)
        il.addLayout(tag_row)

        # 名称
        cname_row = QHBoxLayout()
        cname_lbl = QLabel("名称:")
        cname_lbl.setStyleSheet(_LABEL_STYLE)
        cname_row.addWidget(cname_lbl)
        self._country_name_edit = QLineEdit()
        self._country_name_edit.setStyleSheet(_LINEEDIT_STYLE)
        self._country_name_edit.editingFinished.connect(self._on_country_name_changed)
        cname_row.addWidget(self._country_name_edit)
        il.addLayout(cname_row)

        # 执政党
        party_row = QHBoxLayout()
        party_lbl = QLabel("执政党:")
        party_lbl.setStyleSheet(_LABEL_STYLE)
        party_row.addWidget(party_lbl)
        self._country_party_combo = QComboBox()
        self._country_party_combo.setStyleSheet(_COMBOBOX_STYLE)
        self._country_party_combo.addItems(RULING_PARTIES)
        self._country_party_combo.currentTextChanged.connect(self._on_country_party_changed)
        party_row.addWidget(self._country_party_combo)
        il.addLayout(party_row)

        # 颜色显示（可点击修改）
        color_row = QHBoxLayout()
        color_lbl = QLabel("颜色:")
        color_lbl.setStyleSheet(_LABEL_STYLE)
        color_row.addWidget(color_lbl)
        self._country_color_btn = QPushButton()
        self._country_color_btn.setFixedSize(40, 20)
        self._country_color_btn.setStyleSheet(
            f"background: rgb(100,100,200); border: 1px solid {_BORDER}; border-radius: 3px;"
        )
        self._country_color_btn.setToolTip("点击修改颜色")
        self._country_color_btn.clicked.connect(self._on_country_color_clicked)
        color_row.addStretch()
        color_row.addWidget(self._country_color_btn)
        il.addLayout(color_row)

        # 首都
        cap_row = QHBoxLayout()
        cap_lbl = QLabel("首都:")
        cap_lbl.setStyleSheet(_LABEL_STYLE)
        cap_row.addWidget(cap_lbl)
        self._country_capital_label = QLabel("未设置")
        self._country_capital_label.setStyleSheet(_DIM_LABEL_STYLE)
        cap_row.addStretch()
        cap_row.addWidget(self._country_capital_label)
        il.addLayout(cap_row)

        lay.addWidget(info_box)

        # 提示
        hint = QLabel("选中国家后，点击State可分配领土")
        hint.setStyleSheet(f"color: {_DIM}; font-size: 11px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        lay.addStretch()
        return page

    # ── River 页 ────────────────────────────────────────
    def _build_river_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # 提示
        hint = QLabel("选择河流类型，用画笔绘制河流\n橡皮擦可清除河流")
        hint.setStyleSheet(f"color: {_DIM}; font-size: 12px; padding: 8px;")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        # 工具按钮
        tools_box = self._make_section("工具")
        tl = QHBoxLayout()
        self._river_tool_group = QButtonGroup(self)
        self._river_tool_group.setExclusive(True)
        for tid, label in [("brush", "画笔"), ("eraser", "橡皮"), ("pan", "平移")]:
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
        brush_box = self._make_section("画笔大小")
        self._river_brush_label = QLabel("3px")
        self._river_brush_label.setStyleSheet(_DIM_LABEL_STYLE)
        row = QHBoxLayout()
        lbl = QLabel("大小:")
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

        # 河流类型选择
        palette_box = self._make_section("河流类型")
        grid = QGridLayout()
        grid.setSpacing(4)

        for i, (idx, name) in enumerate(PAINTABLE_RIVER_TYPES):
            r, g, b = RIVER_PALETTE[idx]
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
            btn.clicked.connect(lambda _, ix=idx: self.river_type_changed.emit(ix))
            grid.addWidget(btn, i // 3, i % 3)

        palette_box.layout().addLayout(grid)
        lay.addWidget(palette_box)

        lay.addStretch()
        return page

    # ── 辅助：创建分组 ───────────────────────────────────
    def _make_section(self, title: str) -> QGroupBox:
        box = QGroupBox(title)
        box.setLayout(QVBoxLayout())
        box.layout().setContentsMargins(8, 8, 8, 8)
        box.layout().setSpacing(4)
        box.setStyleSheet(_SECTION_STYLE)
        return box

    # ── 属性 ──────────────────────────────────────────────
    @property
    def ref_opacity_slider(self) -> QSlider:
        return self._ref_opacity_slider

    @property
    def mode_tabs(self) -> _ModeTabBar:
        return self._mode_tabs

    # ── 槽函数 ────────────────────────────────────────────
    def _on_mode_changed(self, mode: str) -> None:
        idx = self._mode_index.get(mode, 0)
        self._stack.setCurrentIndex(idx)
        # 切换模式时自动设工具为 brush（省份/state/country 模式除外）
        if mode not in ("province", "state", "country"):
            self.tool_changed.emit("brush")
        self.mode_changed.emit(mode)

    def _on_river_brush(self, size: int) -> None:
        self._river_brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def _on_country_color_clicked(self) -> None:
        """点击颜色块弹出颜色选择器"""
        tag = self._country_tag_label.text()
        if tag and tag != "—":
            self.country_color_change_requested.emit(tag)

    def _on_land_brush(self, size: int) -> None:
        self._land_brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def _on_terrain_brush(self, size: int) -> None:
        self._terrain_brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def _on_height_brush(self, size: int) -> None:
        self._height_brush_label.setText(f"{size}px")
        self.brush_size_changed.emit(size)

    def _on_height_value(self, value: int) -> None:
        self._height_value_label.setText(str(value))
        self.height_value_changed.emit(value)

    def _apply_height_preset(self, value: int) -> None:
        self._height_slider.setValue(value)

    def _on_tile_click(self, tile_type: int) -> None:
        self.tile_type_changed.emit(tile_type)
        # 自动切换到画笔工具
        for btn in self._land_tool_group.buttons():
            if btn.property("tool_id") == "brush":
                btn.setChecked(True)
                self.tool_changed.emit("brush")
                break

    def _on_generate_provinces(self) -> None:
        count = self._province_count_spin.value()
        self.generate_provinces_requested.emit(count)

    # ── State 槽函数 ──────────────────────────────────────
    def _on_auto_states(self) -> None:
        per_state = self._state_per_spin.value()
        self.auto_states_requested.emit(per_state)

    def _on_state_list_clicked(self, row: int) -> None:
        item = self._state_list.item(row)
        if item is not None:
            state_id = item.data(Qt.UserRole)
            if state_id is not None:
                self.state_selected.emit(state_id)

    def _on_state_name_changed(self) -> None:
        item = self._state_list.currentItem()
        if item is not None:
            state_id = item.data(Qt.UserRole)
            if state_id is not None:
                self.state_property_changed.emit(
                    state_id, "name", self._state_name_edit.text()
                )

    def _on_state_manpower_changed(self, value: int) -> None:
        item = self._state_list.currentItem()
        if item is not None:
            state_id = item.data(Qt.UserRole)
            if state_id is not None:
                self.state_property_changed.emit(state_id, "manpower", value)

    def _on_state_category_changed(self, text: str) -> None:
        item = self._state_list.currentItem()
        if item is not None:
            state_id = item.data(Qt.UserRole)
            if state_id is not None:
                self.state_property_changed.emit(state_id, "category", text)

    # ── Country 槽函数 ────────────────────────────────────
    def _on_country_list_clicked(self, row: int) -> None:
        item = self._country_list.item(row)
        if item is not None:
            tag = item.data(Qt.UserRole)
            if tag is not None:
                self.country_selected.emit(tag)

    def _on_country_name_changed(self) -> None:
        tag = self._country_tag_label.text()
        if tag and tag != "—":
            self.country_property_changed.emit(
                tag, "name", self._country_name_edit.text()
            )

    def _on_country_party_changed(self, text: str) -> None:
        tag = self._country_tag_label.text()
        if tag and tag != "—":
            self.country_property_changed.emit(tag, "ruling_party", text)

    # ── 公共方法 ──────────────────────────────────────────
    def update_province_info(
        self, pid: int, ptype: str, terrain: str, pixels: int, coastal: bool
    ) -> None:
        """更新省份信息面板"""
        self._prov_labels["id"].setText(str(pid))
        self._prov_labels["type"].setText(ptype)
        self._prov_labels["terrain"].setText(terrain)
        self._prov_labels["pixels"].setText(str(pixels))
        self._prov_labels["coastal"].setText("是" if coastal else "否")

    def update_state_list(self, states: list[tuple[int, str]]) -> None:
        """刷新 State 列表，items 为 (id, name)"""
        self._state_list.clear()
        for state_id, name in states:
            item = QListWidgetItem(f"[{state_id}] {name}")
            item.setData(Qt.UserRole, state_id)
            self._state_list.addItem(item)

    def update_country_list(self, countries: list[tuple[str, str, tuple]]) -> None:
        """刷新国家列表，items 为 (tag, name, color)"""
        self._country_list.clear()
        for tag, name, color in countries:
            item = QListWidgetItem(f"[{tag}] {name}")
            item.setData(Qt.UserRole, tag)
            r, g, b = color
            item.setForeground(QBrush(QColor(r, g, b)))
            self._country_list.addItem(item)

    def update_state_info(self, name: str, manpower: int, category: str) -> None:
        """填充 State 属性字段"""
        self._state_name_edit.blockSignals(True)
        self._state_name_edit.setText(name)
        self._state_name_edit.blockSignals(False)

        self._state_manpower_spin.blockSignals(True)
        self._state_manpower_spin.setValue(manpower)
        self._state_manpower_spin.blockSignals(False)

        self._state_category_combo.blockSignals(True)
        idx = self._state_category_combo.findText(category)
        if idx >= 0:
            self._state_category_combo.setCurrentIndex(idx)
        self._state_category_combo.blockSignals(False)

    def update_country_info(
        self, tag: str, name: str, party: str, color: tuple, capital_name: str
    ) -> None:
        """填充国家属性字段"""
        self._country_tag_label.setText(tag)

        self._country_name_edit.blockSignals(True)
        self._country_name_edit.setText(name)
        self._country_name_edit.blockSignals(False)

        self._country_party_combo.blockSignals(True)
        idx = self._country_party_combo.findText(party)
        if idx >= 0:
            self._country_party_combo.setCurrentIndex(idx)
        self._country_party_combo.blockSignals(False)

        r, g, b = color
        self._country_color_btn.setStyleSheet(
            f"background: rgb({r},{g},{b}); border: 1px solid {_BORDER}; border-radius: 3px;"
        )

        self._country_capital_label.setText(capital_name if capital_name else "未设置")
