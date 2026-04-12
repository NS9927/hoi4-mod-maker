"""
CreateCountryCommand — 创建/删除国家。
"""

from __future__ import annotations

from commands.base import Command


class CreateCountryCommand(Command):
    """创建国家，undo 时删除。"""

    label = "创建国家"

    def __init__(
        self,
        country_mgr,
        tag: str,
        name: str = "",
        color: tuple[int, int, int] = (100, 100, 200),
        ruling_party: str = "neutrality",
    ) -> None:
        """
        参数:
            country_mgr: CountryManager 实例
            tag: 3 字母国家代码
            name: 国家显示名
            color: RGB 颜色
            ruling_party: 执政党
        """
        self._country_mgr = country_mgr
        self._tag = tag.upper()[:3]
        self._name = name or self._tag
        self._color = color
        self._ruling_party = ruling_party

    def execute(self) -> None:
        """创建国家。"""
        country = self._country_mgr.create_country(
            self._tag, self._name, self._color
        )
        if self._ruling_party != "neutrality":
            self._country_mgr.set_ruling_party(self._tag, self._ruling_party)

    def undo(self) -> None:
        """删除国家。"""
        self._country_mgr.remove_country(self._tag)
