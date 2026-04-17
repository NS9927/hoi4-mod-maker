"""
国家管理器 — 创建/编辑国家、分配领土、设首都
"""
import numpy as np
from dataclasses import dataclass, field


@dataclass
class NationalSpirit:
    """民族精神 / 国家 idea"""
    id: str                       # idea ID（建议 TAG_xxx 格式）
    name: str                     # 显示名（本地化）
    desc: str = ""                # 描述（本地化）
    modifiers: dict[str, float] = field(default_factory=dict)  # {modifier_key: value}
    picture: str = "generic_pp_unaligned"


@dataclass
class CountryData:
    """一个国家的数据"""
    tag: str                     # 3字母代码，如 KAR
    name: str = ""               # 显示名称
    color: tuple[int, int, int] = (100, 100, 200)  # RGB 颜色
    capital: int = 0             # 首都省份 ID
    ruling_party: str = "neutrality"  # neutrality/democratic/fascism/communism
    popularities: dict[str, int] = field(default_factory=lambda: {
        "democratic": 10,
        "fascism": 5,
        "communism": 5,
        "neutrality": 80,
    })
    national_spirits: list[NationalSpirit] = field(default_factory=list)

    def __post_init__(self):
        if not self.name:
            self.name = self.tag


RULING_PARTIES = ["neutrality", "democratic", "fascism", "communism"]


class CountryManager:
    """管理所有国家"""

    def __init__(self):
        self._countries: dict[str, CountryData] = {}
        self._state_owner: dict[int, str] = {}  # state_id → tag

    @property
    def countries(self) -> dict[str, CountryData]:
        return self._countries

    def get_country(self, tag: str) -> CountryData | None:
        return self._countries.get(tag)

    def get_owner_of_state(self, state_id: int) -> str:
        """获取 State 的所有者 TAG，空字符串=未分配"""
        return self._state_owner.get(state_id, "")

    def create_country(
        self, tag: str, name: str = "", color: tuple[int, int, int] = (100, 100, 200),
    ) -> CountryData:
        """创建国家"""
        tag = tag.upper()[:3]
        if len(tag) != 3:
            raise ValueError("TAG 必须是 3 个字符")
        if not tag.isalnum():
            raise ValueError("TAG 只能包含字母和数字")
        country = CountryData(tag=tag, name=name or tag, color=color)
        self._countries[tag] = country
        return country

    def remove_country(self, tag: str) -> None:
        """删除国家"""
        self._countries.pop(tag, None)
        # 清除该国家的领土
        to_remove = [sid for sid, t in self._state_owner.items() if t == tag]
        for sid in to_remove:
            del self._state_owner[sid]

    def assign_state(self, state_id: int, tag: str) -> None:
        """将 State 分配给国家"""
        if tag and tag in self._countries:
            self._state_owner[state_id] = tag
        elif not tag:
            self._state_owner.pop(state_id, None)

    def set_capital(self, tag: str, province_id: int) -> None:
        """设置首都"""
        if tag in self._countries:
            self._countries[tag].capital = province_id

    def set_ruling_party(self, tag: str, party: str) -> None:
        """设置执政党"""
        if tag in self._countries and party in RULING_PARTIES:
            self._countries[tag].ruling_party = party

    def set_popularity(self, tag: str, party: str, value: int) -> None:
        """设置某政党支持率"""
        if tag in self._countries:
            self._countries[tag].popularities[party] = max(0, min(100, value))

    def get_states_of_country(self, tag: str) -> list[int]:
        """获取某国家的所有 State ID"""
        return [sid for sid, t in self._state_owner.items() if t == tag]

    def clear(self) -> None:
        """清空所有数据"""
        self._countries.clear()
        self._state_owner.clear()

    def build_country_color_map(
        self,
        province_map: np.ndarray,
        state_manager,  # StateManager 实例
    ) -> np.ndarray:
        """生成国家颜色图（用于显示）"""
        max_pid = int(province_map.max())
        lut = np.full((max_pid + 1, 3), 60, dtype=np.uint8)  # 未分配=深灰

        # 遍历每个 State，用所有者国家颜色填省份
        for sid, state in state_manager.states.items():
            tag = self._state_owner.get(sid, "")
            if tag and tag in self._countries:
                color = self._countries[tag].color
                for pid in state.provinces:
                    if pid <= max_pid:
                        lut[pid] = color

        flat = province_map.ravel()
        flat_clipped = np.clip(flat, 0, max_pid)
        rgb = lut[flat_clipped].reshape(province_map.shape[0], province_map.shape[1], 3)
        return rgb

    def get_country_list(self) -> list[tuple[str, str, tuple[int, int, int]]]:
        """返回 [(tag, name, color), ...] 用于 UI 列表"""
        return [(c.tag, c.name, c.color) for c in self._countries.values()]
