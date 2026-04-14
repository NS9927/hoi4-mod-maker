# HOI4 脚本系统规则

> 来源: Paradox Wiki (Event/Focus/Decision/Idea modding)
> 编译日期: 2026-04-13 | 只保留格式规范/字段定义/文件路径

---

## 1. 事件 (Events)

### 文件路径
- 事件定义: `events/*.txt`
- 本地化: `localisation/english/*_l_english.yml` (UTF-8-BOM)
- 图片精灵: `interface/*.gfx` → 引用 `gfx/event_pictures/*.dds`
- on_actions: `common/on_actions/*.txt`

### 事件类型

| 类型 | ROOT 范围 | 额外范围 | 备注 |
|------|----------|---------|------|
| `country_event` | 接收国 | 无 | 标准事件 |
| `news_event` | 接收国 | 无 | 仅外观不同; 必须 `major = yes`; 可禁弹窗 |
| `state_event` | 接收国 | +state | 需 `trigger_for` 指定接收国 |
| `unit_leader_event` | 接收国 | +unit leader | 特殊外观 |
| `operative_leader_event` | 接收国 | +operative | 特殊外观 |

### 命名空间
```pdx
add_namespace = my_mod    # 必须在事件定义之前, 在任何事件块之外声明
```

### 事件字段 (完整)
```pdx
country_event = {
    id = namespace.123              # 必填, 格式 namespace.整数 (0-99999)
    title = loc_key                 # 或 title = { text = key trigger = { } }
    desc = loc_key                  # 同上, 支持条件分支
    picture = GFX_sprite_name       # 引用 interface/*.gfx 中的 spriteType

    is_triggered_only = yes         # 禁止自动触发, 只能用 effect 触发
    fire_only_once = yes            # 全局只触发一次 (所有国家共享计数)
    hidden = yes                    # 隐藏事件, 无需 title/desc, 自动选第一个 option
    major = yes                     # 所有国家都收到 (news_event 默认行为)
    show_major = { trigger }        # 限制哪些国家看到 major 事件
    fire_for_sender = no            # major 时排除原始接收国
    minor_flavor = yes              # 标记为小彩蛋 (玩家可在 UI 禁用)
    timeout_days = 20               # 玩家不选则自动选第一个, 默认 13 天

    trigger = { }                   # 自动触发条件 (每20天检查一次)
    mean_time_to_happen = {         # 自动触发用, MTTH 块
        days/months/years = X
        modifier = { factor = 0.5 条件 }
    }

    immediate = { effect }          # 触发后立即执行, 在玩家选择前
    after = { effect }              # 玩家选完后执行 (1.16.9+)

    option = {
        name = loc_key
        trigger = { }               # 该选项的可见条件
        ai_chance = { base = 10 modifier = { factor = 0 条件 } }
        original_recipient_only = yes  # major 时仅原接收国可见
        # ... 任意 effect ...
    }
}
```

### 用 effect 触发事件
```pdx
# 简写
country_event = my_mod.1

# 完整写法 (时间可叠加)
country_event = { id = my_mod.1  days = 3  random_days = 2  tooltip = loc_key }

# state_event 必须指定接收国
state_event = { id = my_mod.2  trigger_for = GER }  # 或 controller/owner/occupied
```

### 范围传递规则
- effect 触发: 上层 ROOT → 事件 FROM; 上层 FROM → 事件 FROM.FROM
- on_action 的 `random_events` 块: 不传递, 用 on_action 自身范围
- 不存在的国家可通过 effect 收到事件, 但有延迟时计时器不走

---

## 2. 国策树 (National Focus)

### 文件路径
- 国策定义: `common/national_focus/*.txt`
- 持续国策: `common/continuous_focus/*.txt`
- 内嵌窗口: `common/focus_inlay_windows/*.txt`
- 图标精灵: `gfx/interface/goals/` + `interface/goals.gfx` & `goals_shine.gfx`
- 本地化: `localisation/english/*_l_english.yml`

### focus_tree 顶层结构
```pdx
focus_tree = {
    id = my_tree                    # 必填, 重复会报错
    country = {                     # MTTH 块, 分数最高的树被加载
        factor = 0
        modifier = { add = 10  tag = GER }
    }
    default = no                    # 全局只能有一个 default = yes
    reset_on_civilwar = no
    shared_focus = shared_focus_id  # 引用不存在的 shared_focus 会崩溃!
    continuous_focus_position = { x = 50 y = 1000 }
    initial_show_position = { focus = GER_rhineland }

    focus = { ... }                 # 至少一个
}
```

### 单个 focus 字段
```pdx
focus = {
    id = GER_rhineland              # 建议 TAG_ 前缀避免冲突
    icon = GFX_focus_generic_army   # 需同时有 _shine 精灵
    text_icon = focus_titlebar_style
    dynamic = yes                   # 允许动态标题/图标

    # 位置 (x=96px, y=130px 为一个单位)
    x = 5
    y = 0
    relative_position_id = GER_base_focus   # 相对定位, 必须同树
    offset = { x = 1 y = 0 trigger = { has_dlc = "DLC" } }

    # 前置与互斥
    prerequisite = { focus = A focus = B }   # 任一完成即可 (OR)
    prerequisite = { focus = C }             # 多个 prerequisite 块 = AND
    mutually_exclusive = { focus = X }       # X 完成则本 focus 不可选

    # 可用性
    available = { is_subject = no }          # 持续检查, 不满足则灰色
    allow_branch = { tag = GER }            # 仅加载树时检查一次
    bypass = { has_war = yes }              # 满足则标记完成但不给奖励
    bypass_if_unavailable = yes             # available 为 false 时自动跳过
    bypass_effect = { effect }              # 跳过时执行
    cancel = { trigger }                    # 额外取消条件
    cancelable = no                         # 禁止手动取消
    cancel_if_invalid = yes                 # 默认 yes, available 不满足时取消
    continue_if_invalid = no                # 默认 no
    available_if_capitulated = no           # 默认 no

    # 机制
    cost = 10                               # 默认 1 = 7天 (1点/天)
    will_lead_to_war_with = FRA

    # 执行
    select_effect = { effect }              # 选择时执行 (使 focus 不可取消)
    completion_reward = { effect }          # 完成奖励 (执行时 focus 尚未标记完成)
    complete_tooltip = { effect }           # 仅改 tooltip, 等同 hidden effect

    # AI
    ai_will_do = { factor = 1  modifier = { factor = 10 has_war = yes } }
    historical_ai = { is_historical_focus_on = yes }
    search_filters = { FOCUS_FILTER_POLITICAL FOCUS_FILTER_MANPOWER }
}
```

### shared_focus (共享国策)
```pdx
# 根级定义, 在 focus_tree 外部
shared_focus = {
    id = my_shared
    # ... 同 focus 字段 ...
}
# 在 focus_tree 中引用:
focus_tree = {
    shared_focus = my_shared   # 会连带加载其 prerequisite 链上的所有 shared_focus
}
```

### joint_focus (联合国策)
```pdx
joint_focus = {
    id = joint_something
    joint_trigger = { is_in_faction_with = GER }
    completion_reward = { }                        # 所有满足 joint_trigger 的国家执行
    completion_reward_joint_originator = { }        # 仅完成国执行
    completion_reward_joint_member = { }            # 仅其他成员国执行
}
```

---

## 3. 决议 (Decisions)

### 文件路径
- 分类: `common/decisions/categories/*.txt`
- 决议: `common/decisions/*.txt`
- 本地化: `localisation/english/*_l_english.yml`
- 图标: `interface/decisions.gfx` (自动加前缀 `GFX_decision_`)

### 决议分类 (category)
```pdx
decision_category_name = {
    icon = generic_civil_support         # 自动加 GFX_decision_category_ 前缀
    picture = GFX_decision_cat_picture
    priority = 5                         # 越大越靠上, 默认 1
    allowed = { original_tag = GER }     # 仅游戏启动时检查
    visible = { has_war = yes }          # 持续检查
    visible_when_empty = no
    highlight_states = { state = 50 }
    scripted_gui = my_gui_id
}
```

### 普通决议
```pdx
decision_category_name = {              # 必须与上面分类同名
    my_decision = {
        icon = generic_form_nation       # 自动加 GFX_decision_ 前缀
        allowed = { }                    # 启动时一次性检查
        visible = { }                    # 持续检查, false 则隐藏
        available = { }                  # 持续检查, false 则灰色
        cost = 50                        # 政治点数, 支持变量
        custom_cost_trigger = { }        # 自定义花费条件
        custom_cost_text = loc_key       # 需 _blocked 和 _tooltip 变体

        complete_effect = { }            # 点击时执行
        days_remove = 30                 # 计时天数; -1 = 永不过期
        modifier = { }                   # 计时期间生效的修正
        targeted_modifier = { tag = ENG war_support_factor = -0.1 }
        remove_effect = { }              # 计时结束执行
        cancel_trigger = { }            # 提前取消条件 (不执行 remove_effect)
        cancel_effect = { }             # 取消时执行
        cancel_if_not_visible = yes     # visible 的条件自动加入 cancel

        fire_only_once = yes
        days_re_enable = 60             # 冷却天数, 默认 1
        war_with_on_complete = TAG
        war_with_on_remove = TAG
        fixed_random_seed = no          # 默认 yes; no = 允许动态随机

        ai_will_do = { base = 0  modifier = { add = 10 has_war = yes } }
        ai_hint_pp_cost = 50            # 告诉 AI 预留政治点数
        priority = 10
    }
}
```

### 任务 (Mission) — 加 `days_mission_timeout` 即变任务
```pdx
my_mission = {
    activation = { has_war = yes }       # 每日检查, 满足则自动出现 (必填)
    days_mission_timeout = 90            # 超时天数 (标志性字段)
    available = { }                      # 满足则任务成功, 执行 complete_effect
    selectable_mission = yes             # yes = 需玩家点击; no = 自动执行
    is_good = yes                        # yes = 反转 tooltip 语义
    timeout_effect = { }                 # 超时执行
    complete_effect = { }
    # visible 在 mission 中无效!
}
```

### 目标决议 (Targeted Decision) — 加 targets/target_trigger
```pdx
my_targeted = {
    targets = { ENG FRA }               # 固定目标列表
    # 或
    target_array = enemies              # 引用数组
    # 或
    target_trigger = { FROM = { is_neighbor_of = ROOT } }  # ROOT=己方, FROM=目标
    target_root_trigger = { has_war = yes }  # 仅检查 ROOT, 性能优化
    targets_dynamic = yes               # 包含内战变体
    target_non_existing = yes           # 允许不存在的国家

    fire_only_once = yes                # 每个目标独立计数
    war_with_target_on_complete = yes   # = war_with_on_complete = FROM
}
```

### 州目标决议 (State Targeted) — 加 `state_target`
```pdx
my_state_decision = {
    state_target = any_owned_state      # yes/any/any_owned_state/any_controlled_state/大陆key
    target_trigger = { FROM = { infrastructure > 3 } }  # FROM = state
    on_map_mode = map_and_decisions_view  # map_only / decision_view_only / map_and_decisions_view
}
```

---

## 4. Ideas / 国家精神

### 文件路径
- 定义: `common/ideas/*.txt`
- 分类: `common/idea_tags/*.txt`
- 本地化: `localisation/english/*_l_english.yml`
- 历史初始: `history/countries/TAG.txt` (用 `add_ideas = idea_id`)
- GUI: `interface/countrypoliticsview.gui`

### 加载顺序注意
文件按 Unicode 排序: 大写 < 下划线 < 小写。含 `modifier` 影响法律价格的 idea 如果文件名大写开头, 会因法律未加载而报错。解决: 用小写/`00_` 前缀。

### 分类定义
```pdx
# common/idea_tags/*.txt
idea_categories = {
    my_slot = {
        slot = slot_name
        character_slot = char_slot_name  # 角色顾问槽位
        cost = 150                       # 默认政治点
        removal_cost = 10
        ledger = hidden                  # hidden|civilian|army|air|navy|military
        hidden = no
        politics_tab = yes
        law = yes                        # 标记为法律类
        designer = yes                   # 标记为设计师类
        use_list_view = yes
    }
}
```

### Idea 字段
```pdx
ideas = {
    country = {                          # 国家精神槽
        my_spirit = {
            picture = my_pic             # 自动加 GFX_idea_ 前缀
            name = alt_loc_key           # 可选, 重定向本地化 key
            modifier = { stability_factor = 0.1 }
            targeted_modifier = { tag = ENG  attack_bonus_against = 0.1 }
            research_bonus = { electronics_tech = 0.1 }
            equipment_bonus = {
                infantry_equipment = { build_cost_ic = -0.1  instant = yes }
            }
            rule = { can_join_factions = no }

            on_add = { effect }          # 仅游戏开局后添加时执行
            on_remove = { effect }
            do_effect = { trigger }      # false 时 modifier 不生效
            cancel = { trigger }         # 持续检查, 满足则自动移除

            allowed = { }               # 启动检查 (可选 idea 用)
            allowed_civil_war = { }     # 内战时哪方保留, 默认 false (都不保留)
            allowed_to_remove = { }     # 能否移除 (持续检查)
            visible = { }              # GUI 可见性 (持续检查)
            available = { }            # 能否选择 (灰色) (持续检查)
            cost = 150                 # 选择花费
            removal_cost = -1          # -1 = 不可移除
            level = 2                  # 阶梯定价
            traits = { trait_id }      # 引用 common/country_leader/ 中的 trait
        }
    }

    hidden_ideas = {                   # 隐藏精神 (不在 GUI 显示)
        my_hidden = { modifier = { } }
    }
}
```

### 法律示例
```pdx
ideas = {
    economy = {                         # 对应 idea_tags 中定义的 slot
        law = yes
        civilian_economy = {
            cost = 150
            removal_cost = 150
            modifier = { consumer_goods_factor = 0.35 }
            cancel_if_invalid = no
        }
    }
}
```

### 角色顾问/设计师
角色槽 (`character_slot`) 作为并行 idea 槽。idea 可定义到角色槽中, 在 GUI 中像普通 idea 显示。角色 idea 加载晚于普通 idea, 如有交叉引用需在 `common/ideas/` 中放占位。

---

## 5. on_actions 钩子

### 文件路径: `common/on_actions/*.txt`

### 常用钩子列表

| 钩子名 | 触发时机 | ROOT | FROM |
|--------|---------|------|------|
| `on_startup` | 游戏启动/加载 | — | — |
| `on_daily` | 每日 | 每个国家 | — |
| `on_weekly` | 每周 | 每个国家 | — |
| `on_monthly` | 每月 | 每个国家 | — |
| `on_declare_war` | 宣战 | 宣战国 | 被宣战国 |
| `on_peace` | 和平 | 主导国 | — |
| `on_annex` | 吞并 | 吞并国 | 被吞并国 |
| `on_puppet` | 傀儡化 | 宗主国 | 傀儡国 |
| `on_release_as_free` | 释放独立 | 释放国 | 被释放国 |
| `on_state_control_changed` | 州控制权变更 | 新控制国 | FROM.FROM=州 |
| `on_capitulation` | 投降 | 投降国 | 对手 |
| `on_civil_war_end` | 内战结束 | 胜方 | 败方 |
| `on_government_change` | 政体变更 | 变更国 | — |
| `on_coup_succeeded` | 政变成功 | 新政府 | 旧政府 |
| `on_justifying_wargoal_pulse` | 正当化宣战理由脉冲 | 正当化国 | 目标国 |
| `on_join_faction` | 加入阵营 | 加入国 | 阵营领袖 |
| `on_leave_faction` | 离开阵营 | 离开国 | 阵营领袖 |
| `on_nuke_drop` | 投核弹 | 投弹国 | 目标州 |
| `on_unit_leader_created` | 将领创建 | 国家 | 将领 |
| `on_operative_captured` | 特工被捕 | 被捕特工国 | 抓捕国 |
| `on_border_war_won` | 边境冲突胜利 | 胜方 | 败方 |

### on_action 结构
```pdx
on_annex = {
    effect = { ... }                    # 直接执行
    random_events = {                   # 加权随机事件
        100 = my_event.1
        50 = my_event.2
        10 = 0                          # 0 = 什么都不发生
    }
}
```

---

## 6. 常见崩溃/报错原因

### 事件
- **命名空间未声明**: `add_namespace` 必须在事件块外面、事件定义之前
- **ID 非整数或 >= 100000**: 导致 duplicate internal ID
- **MTTH <= 1天** 且无 `fire_only_once`/`is_triggered_only`: 日志刷警告
- **引用不存在的精灵**: picture 字段的 GFX 名必须在 .gfx 中定义

### 国策
- **shared_focus 引用不存在的 ID → 直接崩溃**
- **focus ID 跨树重复**: 导致 prerequisite 连线断裂
- **图标缺 `_shine` 精灵**: 同时需要 `GFX_name` 和 `GFX_name_shine`
- **relative_position_id 递归或跨树**: 可能崩溃
- **completion_reward 中检查自身完成状态**: 执行时 focus 尚未标记完成

### 决议
- **mission 中用 `visible`**: 无效, 不报错但不工作
- **`activation` 块缺失**: mission 永远不出现
- **targeted decision 的 target_trigger 性能**: 每日对所有 ROOT*FROM 组合求值, 国家多会卡

### Ideas
- **文件名大写开头 + modifier 引用法律**: 加载顺序错误导致报错
- **`removal_cost = -1`** 不是禁止移除的唯一方式, 还需确认 `allowed_to_remove`
- **`on_add`/`on_remove` 在开局 history 添加时不执行**: 仅运行时生效
- **角色 idea 加载晚于普通 idea**: 交叉引用需占位 idea

### 通用
- **本地化文件编码必须 UTF-8-BOM**, 否则不显示或乱码
- **花括号不匹配**: 最常见的解析失败原因
- **分号/等号混用**: PDX 脚本用 `=` 不用 `:` 或 `;` (definition.csv 除外)
