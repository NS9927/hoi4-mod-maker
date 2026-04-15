# HOI4 幻想世界 MOD 制作工具

> Hearts of Iron IV 全转换 MOD 制作工具

一个用 Python + PyQt5 写的桌面应用，从零开始画地图、生成省份、设置 State 和国家，**一键导出**完整可玩的 HOI4 Total Conversion MOD。

**当前版本**：v1.0.1

---

## 功能

### 地图绘制（12 种编辑模式）
- 大陆 / 海洋 / 湖泊画笔，支持画笔/橡皮/填充/变换/平移
- 加载原版地图参考 + 自定义参考底图叠加描图
- 支持 4 种地图尺寸：2048×1024 / 3072×1536 / 4096×2048 / 5632×2048

### 省份系统
- Voronoi + Lloyd 松弛自动生成省份，密度可调（海洋/湖泊独立密度）
- **合并** / **切割** / **套索扩张**工具
- 增量生成（选区域重新生成省份）
- 一键全图诊断：X-crossings / 过小省份 / 不连通 / 沿海检测

### 地形 / 高度 / 河流
- 10 种地形画刷（平原/森林/丘陵/山地/沙漠/沼泽/丛林/城市/海洋/湖泊）
- 智能地形生成（高度分层 + 噪声边界 + 散点斑点）
- 智能高度图生成（海岸距离场 + Perlin 噪声山脉 + 平滑滤镜）
- 河流绘制（12 种类型，严格按 HOI4 调色板）

### State / 国家 / 战略区域
- 自动从省份生成 State，支持归属国家、人口、等级、VP
- 创建国家（TAG / 颜色 / 政党 / 首都）
- 大陆分区 / 战略区域管理
- 后勤系统（邻接 / 铁路 / 补给节点）
- 一键初始化（自动生成州 + 战略区域 + 默认国家）

### 一键导出
- 2000+ HOI4 文件全部生成（provinces.bmp / definition.csv / heightmap / terrain / rivers / states / countries / buildings / supply 等）
- 导出前自动预检 + 自动补全缺失数据
- replace_path 智能生成（清洗 vanilla 冲突）
- 导出完成后可直接启动 HOI4 进游戏

### 工程管理
- 保存 / 加载 `.hoi4proj` 工程文件（zip 格式）
- 撤销 / 重做（Command 模式，30 步历史）
- 中英文双语界面
- 导入已有 MOD 地图

---

## 安装

```bash
git clone https://github.com/AmonStreeling/hoi4-mod-maker.git
cd hoi4-mod-maker
pip install -r requirements.txt
python main.py
```

**系统要求**：
- Python 3.10+
- Windows（主要测试平台）

**依赖**：PyQt5, NumPy, Pillow, SciPy

---

## 项目结构

```
hoi4_map_maker/
├── main.py                         # 入口
├── model/                          # 数据中心 (Project + EventBus)
├── domain/                         # 纯数据层 (MapData + 8个Manager + 生成器/验证器)
├── commands/                       # Command 模式 undo/redo
├── controllers/                    # 13 个业务 Controller
├── views/                          # 主窗口 + 画布
├── ui/                             # 工具面板 + 样式 + 国际化
├── features/                       # 12 个地图编辑模式 + 10 个内容模块(2.0)
├── services/                       # 导出/导入/项目服务
├── export/                         # MOD 导出器 (writers按HOI4目录分组)
├── data/                           # 常量 + 地形定义
├── app/                            # DI容器 + Feature注册
└── tests/                          # pytest 测试
```

架构：MVC + Command + EventBus，224 个 Python 文件，26000 行代码。

---

## 路线图

### v1.0 — 地图工具完全体 ✅
- [x] 大陆 / 省份 / 地形 / 高度 / 河流编辑
- [x] State / 国家 / 大陆 / 战略区域
- [x] 后勤系统（邻接 / 铁路 / 补给）
- [x] 一键导出可玩 MOD
- [x] 导入已有 MOD 地图
- [x] 中英文双语
- [x] 打包 .exe 发布

### v2.0 — 玩法内容
- [ ] 科技树 / 国策树编辑器
- [ ] 顾问 / 将领 / 间谍系统
- [ ] 起始部队 OOB
- [ ] 事件 / 决议编辑器
- [ ] Ideas / Namelist / Portraits

---

## 许可证

本项目采用 **GNU General Public License v3.0** 开源许可。

- ✅ 自由使用、修改、分发
- ✅ 用本工具做的 MOD 不受 GPL 约束
- ❌ 修改本工具代码后必须同样以 GPL 开源
- 详见 [LICENSE](LICENSE) 文件

---

## 贡献

欢迎提 Issue 和 Pull Request。

提交代码请遵循：
- 中文注释
- snake_case 函数名 / CamelCase 类名
- 文件 < 800 行
- NumPy 向量化，不要 Python 循环处理像素
