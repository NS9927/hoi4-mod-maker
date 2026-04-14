# HOI4 故障排除速查

> 编译自 Paradox Wiki "Troubleshooting" 页面

## 日志文件

路径: `Documents/Paradox Interactive/Hearts of Iron IV/logs/`

| 文件 | 用途 | 重要性 |
|------|------|--------|
| **error.log** | 非致命错误, common/ 下的几乎都要修 | **高** |
| **setup.log** | 加载流程完成标记, 定位崩溃阶段 | **高** |
| **memory.log** | 加载时内存用量, 定位加载崩溃 | **高** |
| **game.log** | 游戏内国家行为, 定位特定操作崩溃 | **高** |
| exceptions.log | 崩溃栈跟踪 | **低(不可信)** |
| text.log | 本地化 key 断言 | 中 |
| time.log | 各步骤耗时 | 中 |

## Crash Data Log

启动项加 `-crash_data_log` → 崩溃时 `crashes/meta.yml` 包含 `LastRead` 字段

```yaml
LastRead: map/supply_nodes.txt (727)   # 文件名 + 最后读取行号
LastRead: client_ping (1)               # 脚本名(非文件)
```

**重要**: LastRead 指向文件最后一行 → 实际崩溃可能在**下一个被读取的文件**

## 崩溃分类速查表

### 主菜单加载

| LastRead | 原因 |
|----------|------|
| `gfx/models/supply/railroad.shader` | **BMP 文件错误**: 尺寸不能被 256 整除 / 超 40MiB / 尺寸不一致 / DIB 头格式错 |
| `common/countries/cosmetic.txt` | replace_path 覆盖了 national_focus/ 或 continuous_focus/ |
| `map/rocketsites.txt` | replace_path 覆盖 history/states/ 或 common/unit_leader/ |
| `common/national_focus/*.txt` (最后一行) | shared_focus 引用不存在的共享焦点 |
| `history/general/*.txt` 等 | VP 引用不存在的省份 |
| savegame 名 / `map/cities.txt` | 定义国家太多 + 动态国家太少(上限约 40-80 个) |

### 选国/加载

| LastRead | 原因 |
|----------|------|
| `set_controller` | 国家 history 文件缺少有效 capital |
| `map/supply_nodes.txt` / `map/railways.txt` | 补给节点/铁路放在无效省份(不在任何 state 中) |
| `tutorial/tutorial.txt` | tutorial 引用无效 state ID / 缺少 `tutorial = { }` |
| `start_game_command` | 地图数据不完整 (coastal no port / buildings 缺失) |

### 游戏中

| LastRead | 原因 |
|----------|------|
| `client_ping` / `hourly_tick` | **AI 相关崩溃**(关 AI 可验证): |
| | - 国家有师模板但无匹配 ai_templates |
| | - **state 无 owner** → AI 评估空袭时崩溃 |
| | - **buildings.txt 不完整** → naval_base 缺定义 → CPU 死循环 |

## error.log 快速分析 (30秒)

```bash
LD="D:/Documents/Paradox Interactive/Hearts of Iron IV/logs"
wc -l "$LD/error.log"
grep -oE "\[[a-z_]+\.cpp:[0-9]+\]" "$LD/error.log" | sort | uniq -c | sort -rn | head
tail -30 "$LD/error.log"
```

## 调试方法

1. 查 `crashes/meta.yml` 的 `LastRead`
2. LastRead 无用 → 批量移除/恢复 mod 文件, **二分查找**
3. `client_ping` → 关 AI (`ai` 命令) 验证是否 AI 相关
4. **replace_path 是崩溃大户** → 两个 .mod 文件都要改
5. 空文件可能被跳过 → 同一崩溃可能显示不同 LastRead

## 常用 console 命令

| 命令 | 用途 |
|------|------|
| `tdebug` | 显示 state/省份 ID |
| `ai` | 开关 AI |
| `reloadfx all` | 重载视觉效果 |
| `reload localization` | 重载本地化 |
| `tag TAG` | 切换国家 |
| `Focus.NoChecks` | 跳过国策条件 |
| `Focus.AutoComplete` | 国策瞬间完成 |
