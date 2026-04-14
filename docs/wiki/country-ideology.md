# HOI4 国家与标签规则

> 来源: Paradox Wiki (Country creation / Ideology modding)
> 编译: 只保留格式规范/字段定义/文件路径/约束条件

---

## 1. 国家创建所需文件清单

| # | 文件路径 | 用途 | 必需 |
|---|---------|------|------|
| 1 | `common/country_tags/*.txt` | TAG 注册 | **必需** |
| 2 | `common/countries/<Name>.txt` | 图形文化+颜色 | **必需** |
| 3 | `history/countries/TAG - name.txt` | 初始状态(首都/政治/科技/OOB) | **必需** |
| 4 | `gfx/flags/TAG.tga` + 各意识形态变体 | 国旗(3种尺寸) | **必需** |
| 5 | `localisation/english/*_l_english.yml` | 国名/政党名 | **必需** |
| 6 | `common/characters/TAG*.txt` | 领导人/将领/顾问 | **必需**(至少1个leader) |
| 7 | `history/units/TAG_1936.txt` | OOB(师/海/空) | 可选 |
| 8 | `history/states/*.txt` | 领土归属(add_state_core/transfer_state) | **必需** |
| 9 | `common/names/*.txt` | 随机人名池 | 可选 |
| 10 | `portraits/*.txt` | 通用肖像池 | 可选 |
| 11 | `colors.txt` | UI颜色覆盖 | 可选 |
| 12 | `common/ideologies/*.txt` | 自定义意识形态(用vanilla则不需要) | 可选 |
| 13 | `common/ai_peace/*.txt` | AI和谈行为(每意识形态一个文件) | 可选 |
| 14 | `interface/*.gfx` | sprite定义(肖像/意识形态图标) | 按需 |

---

## 2. TAG 规则

### 格式
```
SCO = "countries/Scotland.txt"
```
- **3个大写字母**，定义在 `common/country_tags/*.txt`
- 值指向 `common/countries/` 下的文件(相对路径)

### 保留TAG (违反后果: 逻辑冲突/崩溃)
| 保留词 | 原因 |
|--------|------|
| `NOT` | 触发器流控 |
| `AND` | 触发器流控 |
| `TAG` | country触发器关键字 |
| `OOB` | OOB参数关键字 |
| `LOG` | 日志effect/trigger |
| `NUM` | 数组计数 |
| `RED` | 地图模式变量 |
| 纯数字(如`123`) | 引擎解析冲突 |

---

## 3. Country 文件格式

**路径**: `common/countries/<Name>.txt`

```
graphical_culture = commonwealth_gfx      # 3D模型组
graphical_culture_2d = commonwealth_2d    # 2D UI组
color = rgb { 2 10 222 }                  # 0-255 或 0-1 (恰好用1表示第二种)
```

**颜色覆盖** (`colors.txt`):
```
SCO = {
    color = rgb { 2 10 222 }        # 地图色
    color_ui = rgb { 255 255 155 }  # UI色
}
```
- 支持 `hsv { H S V }` 格式
- 引擎自动修正: 饱和度 ×0.6, 明度 ×0.8

---

## 4. Country History 文件格式

**路径**: `history/countries/TAG - name.txt`
**约束**: 文件名前3字符**必须**匹配TAG(不区分大小写)，违反后果: 引擎不加载

### 基础字段
```
capital = 121                      # 必须是 state ID，不是 province ID！
                                   # 违反后果: 首都位置错误/无首都

oob = "SCO_1936"                   # OOB文件名(不含.txt)
set_research_slots = 3             # 研究槽数
set_stability = 0.7                # 0-1 (映射0%-100%)
set_war_support = 0.5              # 0-1
```

### 科技
```
set_technology = {
    infantry_weapons = 1
    infantry_weapons1 = 1
    gw_artillery = 1
    basic_train = 1
}
```

### Ideas
```
add_ideas = {
    war_economy
    extensive_conscription
}
```

### 外交
```
create_faction = "faction_loc_key"
add_to_faction = IRE
```

### 傀儡关系
```
# 必须写在附庸国的history文件中，且在set_politics之前
# 违反后果: 政治设置被重置
ENG = {
    if = {
        limit = { has_dlc = "Together for Victory" }
        set_autonomy = {
            target = SCO
            autonomous_state = autonomy_integrated_puppet
        }
        else = {
            puppet = SCO
        }
    }
}
```

### 日期条件块
```
1939.1.1 = {
    oob = "SCO_1939"
    set_technology = { nukes = 1 }
}
```
- 仅在**严格晚于**该日期的开局才生效

### OOB加载(DLC分支)
```
if = {
    limit = { has_dlc = "Man the Guns" }
    set_naval_oob = "SCO_1936_naval_mtg"
}
if = {
    limit = { NOT = { has_dlc = "Man the Guns" } }
    set_naval_oob = "SCO_1936_naval_legacy"
}
```

---

## 5. 政治/政党/意识形态设置

### set_politics (执行顺序关键!)
```
set_politics = {
    ruling_party = neutrality       # 必须是已定义的ideology group名
    last_election = "1932.11.8"     # 日期字符串
    election_frequency = 48         # 月数
    elections_allowed = yes          # yes/no
}
```

### set_popularities
```
set_popularities = {
    democratic = 80
    communism = 10
    fascism = 10
}
```
- **必须加到100**，违反后果: 意识形态系统崩坏，所有支持率显示异常

### 领导人招募顺序
```
recruit_character = SCO_ronald_mcdonald   # 必须在 set_politics 之前!
```
- **违反后果**: set_politics 会用默认leader覆盖你recruit的leader

---

## 6. Ideology 定义格式

**路径**: `common/ideologies/*.txt`

```
ideologies = {
    anarchist = {                          # ideology group 名
        types = {
            anarcho_syndicalism = {        # sub-ideology 名
                can_be_randomly_selected = no
                color = { 169 42 42 }      # RGB 0-255
            }
        }
        dynamic_faction_names = {
            "FACTION_NAME_ANARCHIST_1"     # 本地化key
        }
        color = { 169 42 42 }             # group 颜色
        rules = {
            can_create_collaboration_government = yes/no
            can_declare_war_on_same_ideology = yes/no
            can_force_government = yes/no
            can_send_volunteers = yes/no
            can_puppet = yes/no
            can_lower_tension = yes/no
            can_only_justify_war_on_threat_country = yes/no
            can_guarantee_other_ideologies = yes/no
        }
        can_host_government_in_exile = no
        war_impact_on_world_tension = 0.2       # -1 到 1
        faction_impact_on_world_tension = 0.3   # -1 到 1
        modifiers = {
            generate_wargoal_tension = 0.5      # 0-1
            join_faction_tension = 0.5          # 0-1
            lend_lease_tension = 0.5            # 0-1
            send_volunteers_tension = 0.5       # 0-1
            guarantee_tension = 0.5             # 0-1
            take_states_cost_factor = 0         # -1 到 1
            annex_cost_factor = 0               # -1 到 1
            justify_war_goal_when_in_major_war_time = 0  # 0-1
            drift_defence_factor = 0            # -1 到 1
            puppet_cost_factor = 0              # -1 到 1
        }
        can_be_boosted = no                # 能否被顾问boost
        can_collaborate = yes              # 能否建合作政府
        faction_modifiers = {
            faction_trade_opinion_factor = 0.50
        }
        ai_anarchist = yes                 # ai_<ideology名> = yes
    }
}
```

### Ideology 本地化
```
# ideology group
anarchist:0 "Anarchist"               # 形容词
anarchist_noun:0 "Anarchism"           # 名词 (_noun 后缀)
anarchist_desc:0 "描述文本"            # 描述 (_desc 后缀)
anarchist_drift:0 "Daily Anarchist Support"  # 漂移显示

# sub-ideology
anarcho_syndicalism:0 "Anarcho-Syndicalism"
anarcho_syndicalism_desc:0 "描述文本"

# 国家特定覆盖
TAG_anarchist:0 "无政府国名"
TAG_anarchist_ADJ:0 "形容词"
TAG_anarchist_DEF:0 "the 定冠词形式"
POL_anarcho_syndicalism_desc:0 "波兰专属描述"
```

### Ideology GFX Sprite
```
spriteTypes = {
    spriteType = {
        name = GFX_ideology_anarchist_group     # group 图标
        texturefile = gfx/interface/ideologies/anarchist.dds
    }
    spriteType = {
        name = GFX_ideology_anarcho_syndicalism  # sub-ideology 图标
        texturefile = gfx/interface/ideologies/anarcho_syndicalism.dds
    }
    spriteType = {
        name = GFX_ideology_SCO_anarchist_group  # 国家特定覆盖
        texturefile = gfx/interface/ideologies/SCO_anarchist.dds
    }
}
```
- 支持格式: `.dds`, `.tga`, `.png`
- 路径分隔符用 `/`

---

## 7. 国旗格式

**路径**: `gfx/flags/`

| 尺寸 | 像素 | 子目录 | 文件大小参考 |
|------|------|--------|-------------|
| 标准 | 82×52 | `gfx/flags/` | ~16-17 KiB |
| 中等 | 41×26 | `gfx/flags/medium/` | ~4-5 KiB |
| 小 | 10×7 | `gfx/flags/small/` | ~324-819 B |

### TGA格式要求
- **32-bit ARGB**, 未压缩
- **Origin: bottom-left** (不是top-left!)，违反后果: 国旗上下颠倒
- **无RLE编码**

### 命名规则
- 默认: `TAG.tga`
- 意识形态变体: `TAG_ideology.tga` (如 `SCO_democratic.tga`)
- 每个意识形态group都需要一个变体，缺失则fallback到 `TAG.tga`

### 中小国旗注意
- 中等国旗需要约10个dynamic tag才会显示
- 小国旗需要约20个dynamic tag
- 不满足条件 → 国旗透明

---

## 8. 角色(Character)定义

**路径**: `common/characters/TAG*.txt`

```
characters = {
    SCO_ronald_mcdonald = {
        name = SCO_ronald_mcdonald           # 本地化key
        portraits = {
            civilian = {
                large = GFX_SCO_ronald_mcdonald
            }
        }
        country_leader = {
            ideology = socialism              # 必须是 sub-ideology 名
            traits = { scary_clown }
        }
    }
}
```

### 角色sprite
```
spriteTypes = {
    spriteType = {
        name = GFX_SCO_ronald_mcdonald
        texturefile = gfx/leaders/SCO/ronald_mcdonald.dds
    }
}
```

### 角色本地化
```
SCO_ronald_mcdonald:0 "Ronald McDonald"
SCO_ronald_mcdonald_desc:0 "描述"
```

### History中招募
```
recruit_character = SCO_ronald_mcdonald
```

---

## 9. OOB (Order of Battle) 格式

**路径**: `history/units/TAG_1936.txt`

### 师模板
```
division_template = {
    name = "Blueskirt Division"     # 本地化key或直接字符串
    regiments = {                   # 5列×5行
        infantry = { x = 0 y = 0 }
        infantry = { x = 0 y = 1 }
        artillery_brigade = { x = 1 y = 0 }
    }
    support = {                     # 1列×5行
        artillery = { x = 0 y = 0 }
    }
    division_names_group = USA_INF_01  # 可选
}
```

### 师部署
```
units = {
    division = {
        name = "1st Blueskirt Division"
        location = 9392                    # **province ID** (不是state!)
        division_template = "Blueskirt Division"
        start_experience_factor = 0.2      # 0-1, 默认0
        start_equipment_factor = 0.3       # 0-1, 默认1
        start_manpower_factor = 0.3        # 0-1
    }
}
```

经验等级阈值: `{ 0.1=精锐, 0.3=老兵, 0.75=正规, 0.9=新兵 }`

### 装备生产队列
```
instant_effect = {
    add_equipment_production = {
        equipment = {
            type = infantry_equipment_0
            creator = "TAG"
        }
        requested_factories = 1
        progress = 0.19
        efficiency = 100
    }
}
```

---

## 10. 本地化格式

**路径**: `localisation/english/*_l_english.yml`
**编码**: **UTF-8-BOM**, 违反后果: 引擎不读取

### 必需条目
```
l_english:
 SCO:0 "Scotland"                        # 主名称(地图显示)
 SCO_DEF:0 "Scotland"                    # 定冠词形式 (TAG.GetNameDef) **必需**
 SCO_ADJ:0 "Scottish"                    # 形容词 (TAG.GetAdjective)
```

### 意识形态变体
```
 SCO_democratic:0 "Republic of Scotland"
 SCO_democratic_DEF:0 "the Republic of Scotland"
 SCO_democratic_ADJ:0 "Scottish"
 SCO_liberalism:0 "Federal Republic of Scotland"  # sub-ideology级别
```

### 附庸名称
```
 SCO_subject:0 "$OVERLORDADJ$ Scotland"           # 通用附庸
 SCO_IRE_subject:0 "Alba"                         # 特定宗主国
 SCO_autonomy_dominion:0 "Dominion of Scotland"   # 特定自治等级
```

可用变量: `$NONIDEOLOGY$`, `$NONIDEOLOGYADJ$`, `$OVERLORD$`, `$OVERLORDADJ$`, `$OVERLORDNAMEDEF$`

### 优先级 (高→低)
1. 特定宗主国+特定自治等级
2. 通用自治等级
3. 特定宗主国附庸
4. 通用附庸
5. sub-ideology
6. ideology group
7. TAG
8. COUNTRY

### 政党名
```
 SCO_communism_party:0 "SCP"                      # 简称
 SCO_communism_party_long:0 "Scottish Communist Party"  # 全称
```

### 装备名
```
 SCO_artillery_equipment:0 "Armata 75mm wz. 31 St."
 SCO_artillery_equipment_short:0 "75mm wz. 31"
```

---

## 11. 常见崩溃原因

| 问题 | 后果 | 原因 |
|------|------|------|
| TAG 使用保留词(NOT/AND/TAG等) | 逻辑解析冲突，可能崩溃 | 引擎将TAG当作触发器关键字 |
| `capital` 用了province ID而非state ID | 首都丢失/行为异常 | 引擎期望state ID |
| `set_popularities` 总和≠100 | 意识形态系统崩坏 | 引擎不做自动归一化 |
| `recruit_character` 在 `set_politics` 之后 | leader被默认覆盖 | set_politics重置ruling_party的leader |
| 傀儡设置在宗主国文件而非附庸国文件 | 政治设置被重置 | history加载顺序:先附庸后宗主 |
| history文件名前3字符不匹配TAG | 文件不被加载 | 引擎按文件名前缀匹配TAG |
| 国旗TGA用RLE压缩或top-left origin | 国旗不显示/颠倒 | 引擎只支持未压缩+bottom-left |
| 本地化文件缺UTF-8-BOM | 整个文件被忽略 | 引擎不读取无BOM的yml |
| `_DEF` 本地化key缺失 | UI显示空白 | TAG.GetNameDef 找不到 |
| dynamic tag数量不足 | 中小国旗透明/map/cities.txt崩溃 | 引擎预分配dynamic tag池 |
| ideology的 `ai_<name> = yes` 缺失 | AI不使用该意识形态 | AI行为表无法关联 |
| sub-ideology的color未定义 | 引擎fallback到group色或崩溃 | 部分UI取sub-ideology色 |
| OOB文件引用不存在的division_template | 加载时silent fail | 师不会被生成 |
| `location` 用了无效province ID | 师不会被部署 | 引擎找不到部署位置 |
