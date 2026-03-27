# Viewer - GUI 工具集

基于 PyQt5 + Matplotlib 的可视化工具，提供 K线查看、热点监控、选股策略等功能。

---

## 工具列表

| 文件 | 说明 |
|------|------|
| [kline_viewer.py](kline_viewer.py) | K线查看器（**停止维护**） |
| [topic_monitor.py](topic_monitor.py) | 热点监控面板 |
| [screen_three_up.py](screen_three_up.py) | 三连阳筛选工具（**停止维护**） |
| [skills/](skills/) | 选股策略模块 |

---

## 快速启动

```bash
# 启动 K线查看器
python viewer/kline_viewer.py

# 启动热点监控面板
python viewer/topic_monitor.py

# 启动三连阳筛选
python viewer/screen_three_up.py
```

---

## topic_monitor.py - 热点监控面板

### 功能

- **添加热点**：输入热点名称和利好消息，自动关联板块和股票
- **分时图**：每个热点卡片显示关联股票的分时图（最多5只）
- **自动刷新**：每30秒自动刷新所有分时图
- **热点历史**：从数据库加载历史热点记录

### 界面布局

```
顶部控制栏
├── 热点名称输入框
├── 利好消息输入框
├── [添加热点] 按钮
├── [刷新(30秒)] 按钮
└── [清除] 按钮

主体区域（2列网格）
└── 热点卡片
    ├── 热点名称 + 板块名称
    ├── 利好消息（点击弹出详情）
    ├── 股票分时图网格
    └── [删除] 按钮
```

### 热点卡片

每个卡片显示：
- 热点名称（如 `【AI概念】`）
- 关联板块名称（如 `人工智能 / AI大模型`）
- 利好消息（截断显示，点击展开）
- 最多5只股票的分时图（3x2 网格）
- 删除按钮

### 数据关联

用户只需输入热点名称（如 `AI概念`），系统自动：
1. 通过名称模糊匹配 `concept_board` 表 → 获取 `concept_codes` 和 `board_names`
2. 通过 `concept_codes` 查询 `stock_concept` 表 → 获取关联股票列表

### 依赖

```
PyQt5
matplotlib
akshare（获取实时分时数据）
```

---

## kline_viewer.py - K线查看器

功能：查看股票 K线图、分时图，支持选股策略执行。

> **⚠️ 注意**：`kline_viewer.py` 已停止维护，代码不再更新。如需使用请参考 `topic_monitor.py` 的 `KLineChart` 组件，其包含最新的分时图绘制逻辑。

详见文件内嵌文档。

---

## skills/ - 选股策略模块

| 文件 | 说明 |
|------|------|
| [skill_base.py](skills/skill_base.py) | 策略基类 |
| [skill_manager.py](skills/skill_manager.py) | 策略管理器 |
| [skill_template.py](skills/skill_template.py) | 策略模板 |
| [three_consecutive_up_skill.py](skills/three_consecutive_up_skill.py) | 三连阳策略 |
| [冲高回落次日高开_skill.py](skills/冲高回落次日高开_skill.py) | 冲高回落次日高开策略 |

---

## 相关文档

- [DB_TABLES.md](DB_TABLES.md) - `topic_history` 表结构
- [mcp_server/README.md](../mcp_server/README.md) - 热点 MCP 工具
- [CLAUDE.md](../CLAUDE.md) - 项目概览