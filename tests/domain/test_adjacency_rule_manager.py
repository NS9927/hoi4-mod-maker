"""
AdjacencyRuleManager 单元测试.
"""

import pytest

from domain.managers.adjacency_rule import (
    AdjacencyRuleManager, AdjacencyRule, ALL_PASS_TYPES, ALL_RELATIONS,
)


def test_default_rule_friend_passes_neutral_passes():
    r = AdjacencyRule(name="TEST")
    # 默认 friend 和 neutral 全部 yes
    for p in ALL_PASS_TYPES:
        assert r.friend[p] is True
        assert r.neutral[p] is True
        assert r.contested[p] is False
        assert r.enemy[p] is False


def test_to_block_contains_all_relations_and_name():
    r = AdjacencyRule(name="SUEZ_CANAL")
    block = r.to_block()
    assert 'name = "SUEZ_CANAL"' in block
    for rel in ALL_RELATIONS:
        assert f"\t{rel} = {{" in block
    for p in ALL_PASS_TYPES:
        assert p in block


def test_required_provinces_in_block():
    r = AdjacencyRule(name="TEST", required_provinces=[100, 200, 300])
    block = r.to_block()
    assert "required_provinces = { 100 200 300 }" in block


def test_icon_only_when_set():
    r1 = AdjacencyRule(name="A", icon_province=-1)
    assert "icon =" not in r1.to_block()
    r2 = AdjacencyRule(name="B", icon_province=42)
    assert "icon = 42" in r2.to_block()


def test_manager_add_remove():
    m = AdjacencyRuleManager()
    m.add(AdjacencyRule(name="X"))
    m.add(AdjacencyRule(name="Y"))
    assert m.count() == 2
    assert m.remove("X") is True
    assert m.count() == 1
    assert m.get("X") is None
    assert m.get("Y") is not None


def test_add_overwrites_same_name():
    m = AdjacencyRuleManager()
    m.add(AdjacencyRule(name="X", icon_province=10))
    m.add(AdjacencyRule(name="X", icon_province=20))
    assert m.count() == 1
    assert m.get("X").icon_province == 20


def test_drop_provinces_removes_referencing_rules():
    m = AdjacencyRuleManager()
    m.add(AdjacencyRule(name="A", required_provinces=[1, 2, 3]))
    m.add(AdjacencyRule(name="B", required_provinces=[10, 20]))
    m.add(AdjacencyRule(name="C", icon_province=5))
    m.drop_provinces({2, 5})
    assert m.count() == 1  # only B survives
    assert m.get("B") is not None


def test_remap_provinces():
    m = AdjacencyRuleManager()
    m.add(AdjacencyRule(name="A", required_provinces=[1, 2], icon_province=1))
    m.remap_provinces({1: 11, 2: 22})
    rule = m.get("A")
    assert rule.required_provinces == [11, 22]
    assert rule.icon_province == 11


def test_serialize_roundtrip():
    m = AdjacencyRuleManager()
    m.add(AdjacencyRule(
        name="SUEZ", required_provinces=[1, 2, 3], icon_province=5,
    ))
    # 改一些 friend/enemy 设置
    m.get("SUEZ").enemy["army"] = True  # 通常 enemy 全 no, 改一个验证序列化
    data = m.to_dict()

    m2 = AdjacencyRuleManager()
    m2.from_dict(data)
    assert m2.count() == 1
    rule = m2.get("SUEZ")
    assert rule.required_provinces == [1, 2, 3]
    assert rule.icon_province == 5
    assert rule.enemy["army"] is True
