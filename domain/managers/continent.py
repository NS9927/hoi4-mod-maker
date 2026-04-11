"""
Continent 管理器 — 大陆数据结构、省份指派、导出

HOI4 规则（Map modding §Continents）:
- continent.txt 列出所有大陆名
- definition.csv 最后一列 continent 是整数索引 (1-based)
- 海/湖省份 continent = 0
- 所有陆地省份必须属于某个大陆, 否则报错

默认值: 一个大陆 "default_continent", 所有陆地省份全部归属它.
用户可在 UI 添加/重命名/删除大陆, 并把省份指派到指定大陆.
"""

from __future__ import annotations


class ContinentManager:
    """管理大陆列表 + 省份→大陆映射"""

    DEFAULT_NAME = "default_continent"

    def __init__(self) -> None:
        # 大陆名列表, 索引从 0 开始; HOI4 continent ID = index + 1
        self._names: list[str] = [self.DEFAULT_NAME]
        # 省份 → 大陆索引 (0-based); 未在此 dict 的 land 省份默认指向 0
        self._province_continent: dict[int, int] = {}

    # ───────────── 大陆 CRUD ─────────────

    @property
    def names(self) -> list[str]:
        """返回大陆名列表 (顺序即 HOI4 ID 顺序, 1-based)"""
        return list(self._names)

    def count(self) -> int:
        return len(self._names)

    def get_name(self, index: int) -> str:
        """按 0-based 索引取名, 越界返回默认"""
        if 0 <= index < len(self._names):
            return self._names[index]
        return self.DEFAULT_NAME

    def add_continent(self, name: str) -> int:
        """添加大陆, 返回其 0-based 索引. 重名则返回现有索引."""
        name = name.strip()
        if not name:
            raise ValueError("大陆名不能为空")
        if name in self._names:
            return self._names.index(name)
        self._names.append(name)
        return len(self._names) - 1

    def rename_continent(self, index: int, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            raise ValueError("大陆名不能为空")
        if not (0 <= index < len(self._names)):
            raise IndexError(f"大陆索引越界: {index}")
        if new_name in self._names and self._names.index(new_name) != index:
            raise ValueError(f"大陆名已存在: {new_name}")
        self._names[index] = new_name

    def remove_continent(self, index: int) -> None:
        """删除大陆. 必须至少保留 1 个. 指向该大陆的省份改指向 0."""
        if len(self._names) <= 1:
            raise ValueError("必须至少保留 1 个大陆")
        if not (0 <= index < len(self._names)):
            raise IndexError(f"大陆索引越界: {index}")
        self._names.pop(index)
        # 重新映射省份: 被删的 → 0, 后面的 → 前移 1
        new_map: dict[int, int] = {}
        for pid, ci in self._province_continent.items():
            if ci == index:
                new_map[pid] = 0
            elif ci > index:
                new_map[pid] = ci - 1
            else:
                new_map[pid] = ci
        self._province_continent = new_map

    # ───────────── 省份指派 ─────────────

    def assign_province(self, pid: int, continent_index: int) -> None:
        if not (0 <= continent_index < len(self._names)):
            raise IndexError(f"大陆索引越界: {continent_index}")
        self._province_continent[pid] = continent_index

    def assign_provinces(self, pids: list[int], continent_index: int) -> None:
        for pid in pids:
            self.assign_province(pid, continent_index)

    def get_province_continent(self, pid: int) -> int:
        """返回省份的 0-based 大陆索引, 未指派返回 0"""
        return self._province_continent.get(pid, 0)

    def get_province_continent_hoi4_id(self, pid: int, is_land: bool) -> int:
        """返回 HOI4 continent ID (1-based). 海/湖返回 0."""
        if not is_land:
            return 0
        return self.get_province_continent(pid) + 1

    # ───────────── 数据同步 ─────────────

    def drop_provinces(self, pids: set[int]) -> None:
        """删除一批省份的指派 (供 compact_with_references 调用)"""
        for pid in pids:
            self._province_continent.pop(pid, None)

    def remap_provinces(self, old_to_new: dict[int, int]) -> None:
        """按旧→新 ID 映射重写 (供 ID 压实调用)"""
        new_map: dict[int, int] = {}
        for old_pid, ci in self._province_continent.items():
            new_pid = old_to_new.get(old_pid)
            if new_pid is not None:
                new_map[new_pid] = ci
        self._province_continent = new_map

    def clear(self) -> None:
        self._names = [self.DEFAULT_NAME]
        self._province_continent = {}

    # ───────────── 序列化 ─────────────

    def to_dict(self) -> dict:
        return {
            "names": list(self._names),
            "province_continent": dict(self._province_continent),
        }

    def from_dict(self, data: dict) -> None:
        self._names = list(data.get("names", [self.DEFAULT_NAME]))
        if not self._names:
            self._names = [self.DEFAULT_NAME]
        raw = data.get("province_continent", {})
        # JSON 会把 int key 转成 str, 这里兼容
        self._province_continent = {int(k): int(v) for k, v in raw.items()}
