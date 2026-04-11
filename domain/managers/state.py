"""
State 管理器 — State 数据结构、自动分组、手动编辑
"""
import numpy as np
from dataclasses import dataclass, field
from scipy.ndimage import label
from data.constants import MAP_WIDTH, MAP_HEIGHT, TILE_LAND


@dataclass
class StateData:
    """一个 State 的数据"""
    id: int
    name: str = ""
    provinces: list[int] = field(default_factory=list)
    manpower: int = 100000
    category: str = "town"  # wasteland/pastoral/tiny/small/town/large_town/city/large_city/megalopolis
    owner_tag: str = ""
    victory_points: dict[int, int] = field(default_factory=dict)  # {province_id: vp_value}

    # ── 进阶字段 (State modding 规范) ──
    impassable: bool = False  # 不可通行 state, 不能部署单位/建楼
    controller_tag: str = ""  # 初始控制者 (≠ owner 时用于战争开局)
    local_supplies: float = 0.0  # 本地补给加成
    # 资源: oil/aluminium/rubber/tungsten/steel/chromium (值=0 不写)
    resources: dict[str, int] = field(default_factory=dict)
    # state 级建筑: infrastructure/arms_factory/industrial_complex/dockyard/
    # air_base/anti_air_building/radar_station/synthetic_refinery/fuel_silo/
    # nuclear_reactor/rocket_site/mass_transit/supply_node (值=0 不写)
    buildings: dict[str, int] = field(default_factory=dict)
    # 省份级建筑: {province_id: {building_name: level}}
    # 用于 bunker / coastal_bunker / naval_base 按省份写
    province_buildings: dict[int, dict[str, int]] = field(default_factory=dict)
    # 额外 core TAG 列表 (owner_tag 会自动 add_core_of)
    extra_cores: list[str] = field(default_factory=list)
    # 宣称 TAG 列表
    claims: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.name:
            self.name = f"STATE_{self.id}"


class StateManager:
    """管理所有 State"""

    # State 类别选项
    CATEGORIES = [
        "wasteland", "pastoral", "tiny", "small", "town",
        "large_town", "city", "large_city", "megalopolis",
    ]

    def __init__(self):
        self._states: dict[int, StateData] = {}
        self._province_to_state: dict[int, int] = {}  # pid → state_id
        self._next_id = 1

    @property
    def states(self) -> dict[int, StateData]:
        return self._states

    def get_state(self, state_id: int) -> StateData | None:
        return self._states.get(state_id)

    def get_state_of_province(self, pid: int) -> int:
        """查询省份所属的 State ID，0=未分配"""
        return self._province_to_state.get(pid, 0)

    def create_state(self, provinces: list[int] | None = None) -> StateData:
        """创建新 State"""
        sid = self._next_id
        self._next_id += 1
        state = StateData(id=sid, provinces=provinces or [])
        self._states[sid] = state
        for pid in state.provinces:
            self._province_to_state[pid] = sid
        return state

    def assign_province(self, pid: int, state_id: int) -> None:
        """将省份移动到指定 State"""
        # 从旧 State 移除
        old_sid = self._province_to_state.get(pid, 0)
        if old_sid > 0 and old_sid in self._states:
            provs = self._states[old_sid].provinces
            if pid in provs:
                provs.remove(pid)

        # 加入新 State
        if state_id in self._states:
            if pid not in self._states[state_id].provinces:
                self._states[state_id].provinces.append(pid)
            self._province_to_state[pid] = state_id

    def set_vp(self, province_id: int, value: int, name: str = "") -> None:
        """设置胜利点"""
        sid = self._province_to_state.get(province_id, 0)
        if sid > 0 and sid in self._states:
            self._states[sid].victory_points[province_id] = value

    def remove_vp(self, province_id: int) -> None:
        """移除胜利点"""
        sid = self._province_to_state.get(province_id, 0)
        if sid > 0 and sid in self._states:
            self._states[sid].victory_points.pop(province_id, None)

    def clear(self) -> None:
        """清空所有数据"""
        self._states.clear()
        self._province_to_state.clear()
        self._next_id = 1

    def auto_split(
        self,
        province_map: np.ndarray,
        tile_map: np.ndarray,
        per_state: int = 15,
    ) -> None:
        """
        自动按地理位置把陆地省份分成 State。
        先用连通分量找独立陆块，再在每个陆块内部按坐标分组，
        避免隔海的省份被分到同一个 State。
        """
        self.clear()

        max_pid = int(province_map.max())
        if max_pid == 0:
            return

        # 向量化：一次性计算所有省份的中心和类型
        # 用 bincount 批量统计，避免逐省份全图扫描
        flat_pm = province_map.ravel()
        flat_tm = tile_map.ravel()
        flat_land = (flat_tm == TILE_LAND).astype(np.int32)

        # 每个省份的像素数和陆地像素数
        pid_count = np.bincount(flat_pm, minlength=max_pid + 1)
        pid_land_count = np.bincount(flat_pm, weights=flat_land, minlength=max_pid + 1)

        # 陆地省份：陆地像素 > 总像素的一半
        land_ids = []
        for pid in range(1, max_pid + 1):
            if pid_count[pid] > 0 and pid_land_count[pid] > pid_count[pid] / 2:
                land_ids.append(pid)

        if not land_ids:
            return

        # 向量化计算省份质心
        ys_all, xs_all = np.mgrid[0:MAP_HEIGHT, 0:MAP_WIDTH]
        flat_ys = ys_all.ravel().astype(np.float64)
        flat_xs = xs_all.ravel().astype(np.float64)

        sum_y = np.bincount(flat_pm, weights=flat_ys, minlength=max_pid + 1)
        sum_x = np.bincount(flat_pm, weights=flat_xs, minlength=max_pid + 1)

        centers = {}
        land_set = set(land_ids)
        for pid in land_ids:
            cnt = pid_count[pid]
            if cnt > 0:
                centers[pid] = (sum_y[pid] / cnt, sum_x[pid] / cnt)

        # 用连通分量找独立陆块
        land_binary = (tile_map == TILE_LAND).astype(np.int32)
        labeled_land, num_landmasses = label(land_binary)

        # 每个省份属于哪个陆块（用省份中心像素所在的连通分量）
        pid_to_landmass: dict[int, int] = {}
        for pid in land_ids:
            cy, cx = centers[pid]
            iy, ix = int(cy), int(cx)
            iy = min(max(iy, 0), MAP_HEIGHT - 1)
            ix = min(max(ix, 0), MAP_WIDTH - 1)
            lm = int(labeled_land[iy, ix])
            if lm == 0:
                # 中心点不在陆地上（边缘情况），找该省份任意陆地像素
                mask = (province_map == pid) & (tile_map == TILE_LAND)
                pts = np.where(mask)
                if len(pts[0]) > 0:
                    lm = int(labeled_land[pts[0][0], pts[1][0]])
            pid_to_landmass[pid] = lm

        # 按陆块分组
        landmass_groups: dict[int, list[int]] = {}
        for pid in land_ids:
            lm = pid_to_landmass.get(pid, 0)
            if lm not in landmass_groups:
                landmass_groups[lm] = []
            landmass_groups[lm].append(pid)

        # 在每个陆块内部按坐标排序分组
        for lm_id, group_pids in landmass_groups.items():
            sorted_pids = sorted(
                group_pids,
                key=lambda p: (centers[p][0] // 100, centers[p][1])
            )
            for i in range(0, len(sorted_pids), per_state):
                chunk = sorted_pids[i:i + per_state]
                state = self.create_state(chunk)
                state.manpower = len(chunk) * 50000
                if chunk:
                    state.victory_points[chunk[0]] = 1

    def build_state_color_map(self, province_map: np.ndarray) -> np.ndarray:
        """生成 State 颜色图（用于显示）"""
        # 为每个 State 分配确定性颜色
        rng = np.random.RandomState(123)
        colors = {}
        for sid in self._states:
            colors[sid] = (
                int(rng.randint(60, 220)),
                int(rng.randint(60, 220)),
                int(rng.randint(60, 220)),
            )

        # 构建 LUT: province_id → (R, G, B)
        max_pid = int(province_map.max())
        lut = np.zeros((max_pid + 1, 3), dtype=np.uint8)
        lut[:, :] = 40  # 未分配=深灰

        for pid, sid in self._province_to_state.items():
            if pid <= max_pid and sid in colors:
                lut[pid] = colors[sid]

        # 应用到整张图
        flat = province_map.ravel()
        flat_clipped = np.clip(flat, 0, max_pid)
        rgb = lut[flat_clipped].reshape(province_map.shape[0], province_map.shape[1], 3)
        return rgb
