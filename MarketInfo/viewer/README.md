# Viewer - GUI 工具集

基于 PySide6 + Matplotlib 的可视化工具，提供 K线查看、热点监控、选股策略等功能。

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
python viewer/kline_viewer.py（**停止维护**） 

# 启动热点监控面板
python viewer/topic_monitor.py

# 启动三连阳筛选
python viewer/screen_three_up.py（**停止维护**） 
```

---

## topic_monitor.py - 热点监控面板

### 架构原则

**数据访问必须走 MCP，不得直接引用 QueryDB 或 core 模块。**

所有数据（热点增删改查）通过 MCP 服务器访问，UI 层通过 `_call_mcp()` 调用远程工具。
分时数据来源是AKShare，不得访问MCP获取。

### 功能

- **添加热点**：输入热点名称和利好消息，通过 `add_topic_history` MCP 工具写入
- **分时图**：每个热点卡片显示关联股票的分时图（最多6只）
- **自动刷新**：每30秒自动刷新所有分时图
- **热点历史**：通过 `get_topic_history` MCP 工具加载
- **设置**：MCP 服务地址保存到 `~/.marketinfo/settings.json`，可在界面配置

### 界面布局

```
顶部控制栏
├── 热点名称输入框
├── 利好消息输入框
├── [添加热点] 按钮
├── [刷新] 按钮
├── [清除] 按钮
└── [设置] 按钮（MCP 服务地址）

主体区域（3x2 网格，固定6格）
└── 热点卡片
    ├── 热点名称 + 板块名称
    ├── 利好消息（点击弹出详情）
    ├── 股票分时图网格（2列 x 3行）
    └── [×] 删除按钮
```

### MCP 工具映射

| 操作 | MCP 工具 |
|------|---------|
| 添加热点 | `add_topic_history` |
| 查询热点 | `get_topic_history` |
| 删除热点 | `delete_topic_history` |
| 清空热点 | `clear_all_topic_history` |

### 依赖

```
PySide6
matplotlib
akshare（分时数据，仅回退使用）
mcp（Python SDK）
fastmcp
```

> **⚠️ 注意**：`viewer` 下面所有程序都是独立运行的程序，不依赖 `core/` 模块下的 QueryDB。所有数据访问必须走 MCP 工具。

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