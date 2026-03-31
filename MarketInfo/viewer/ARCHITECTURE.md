# 热点监控面板 - 架构文档

## 一、项目概述

A股热点板块实时监控面板，基于 PySide6 + Matplotlib，支持：
- 热点添加/删除
- 热点历史查询
- 股票分时图实时显示
- MCP 服务调用

## 二、模块划分

```
viewer/
├── topic_monitor.py    # 主界面入口 (~300行)
├── mcp_runner.py        # MCP 异步客户端 (~80行)
├── stock_widget.py     # 自治股票组件 (~130行)
├── mcp_settings.py     # 设置弹窗 (~140行)
├── kline_viewer.py     # K线/分时图组件 (~1350行)
├── screen_three_up.py  # 选股策略（未用）
└── __init__.py
```

## 三、数据流

```
┌──────────────────────────────────────────────────────────────────┐
│                    topic_monitor.py                              │
│                                                                  │
│   TopicMonitorPanel                                              │
│       │                                                          │
│       ├── _init_mcp() ────→ mcp_runner.py (MCPRunner)           │
│       │                      │                                  │
│       │                      └── call_tool()                     │
│       │                                  ↓                     │
│       │                      MCP Server:9876                    │
│       │                            add_topic_history             │
│       │                            get_topic_history             │
│       │                            delete_topic_history          │
│       │                                                          │
│       ├── load_history() ──→ 解析结果                          │
│       │                                                          │
│       └── create_topic_card()                                  │
│               │                                                  │
│               ├── 热点名称 + 利好消息（直接显示）              │
│               │                                                  │
│               └── stock_codes[] → StockWidget (每只股票)        │
│                       │                                          │
│                       └── stock_widget.py                      │
│                               │                                 │
│                               ├── _load_data()                  │
│                               │                                │
│                               └── akshare (直接获取分时)       │
└──────────────────────────────────────────────────────────────────┘
```

## 四、模块职责

### 1. topic_monitor.py（主界面）
**职责**：主界面、UI 组件管理、MCP 调用

| 类/函数 | 职责 |
|--------|------|
| `TopicMonitorPanel` | 主面板，管理热点网格 |
| `NewsDialog` | 利好消息弹窗 |
| `DARK_STYLE` | 深色主题 CSS |

**数据**：`self.topics` - 热点列表

### 2. mcp_runner.py（MCP 客户端）
**职责**：异步调用 MCP 服务

| 类/函数 | 职责 |
|--------|------|
| `MCPRunner` | 独立线程 + asyncio 调用 MCP |

**信号**：
- `result_ready(call_id, tool_name, result)` - 调用结果
- `connected()` - 连接成功
- `error(msg)` - 连接失败

### 3. stock_widget.py（自治股票组件）
**职责**：独立加载股票名称和分时数据

| 类/函数 | 职责 |
|--------|------|
| `StockWidget` | 自治组件，自己加载数据 |
| `normalize_code()` | 代码规范化（600000 → 600000.SH） |
| `_stock_name_cache` | 名称缓存（模块级） |
| `_minute_data_cache` | 分时缓存（模块级） |

**行为**：
1. 创建时显示代码+"加载中..."
2. 延迟 200ms 后开始加载
3. 检查缓存，有则直接显示
4. 无则请求 AKShare 获取分时数据
5. 渲染图表

### 4. mcp_settings.py（设置）
**职责**：MCP 服务地址配置

| 函数 | 职责 |
|------|------|
| `get_mcp_url()` | 获取服务地址 |
| `get_fullscreen()` | 获取是否全屏 |
| `MCPSettingsDialog` | 设置弹窗 |

**配置文件**：`~/.marketinfo/settings.json`

### 5. kline_viewer.py（K线组件）
**职责**：K线/分时图渲染（第三方组件，未修改）

## 五、数据模型

### topic（MCP 返回）
```python
{
    "id": 1,
    "name": "AI概念",
    "news": "政策利好",
    "stock_codes": ["600519.SH", "000001.SZ", ...],
    "created_at": 1774800000000
}
```

### StockWidget 内部
```python
{
    "ts_code": "600519.SH",  # 规范化代码
    "name": "贵州茅台",     # 从缓存获取
    "chart": KLineChart     # 图表对象
}
```

## 六、关键流程

### 1. 启动流程
```
start.bat
    ↓
service_manager.py → 启动 MCP Server
    ↓
topic_monitor.py → TopicMonitorPanel.__init__()
    ↓
_init_mcp() → MCPRunner.start() → 连接 MCP
    ↓
_on_mcp_connected() → load_history()
    ↓
refresh_grid() → 创建话题卡片 + StockWidget
    ↓
每个 StockWidget 延迟加载自己的分时图
```

### 2. 添加热点流程
```
add_topic(name, news)
    ↓
_call_mcp("add_topic_history", {name, news})
    ↓
MCP 返回 success: true
    ↓
load_history() → 刷新热点列表
```

### 3. 分时加载流程
```
StockWidget 创建
    ↓
200ms 后 _start_load()
    ↓
检查 _minute_data_cache
    ↓
有缓存 → _render(df)
    ↓
无缓存 → _fetch_minute() → AKShare API
    ↓
渲染 KLineChart
```

## 七、性能优化

### 1. 自治模式
- **每个 StockWidget 独立加载**，不阻塞主线程
- 延迟 200ms 启动，让 UI 先渲染

### 2. 缓存
- **分时缓存**：5分钟有效
- **名称缓存**：模块级全局缓存

### 3. 渐进显示
- 框架先显示，"加载中..."后过渡到图表

## 八、编码规范

### 模块导入顺序
```python
# 标准库
import sys, os, json

# 第三方
import pandas as pd
from PySide6.QtWidgets import ...

# 本地模块
from viewer.stock_widget import StockWidget
from viewer.mcp_runner import MCPRunner
from viewer.mcp_settings import ...
```

### 类定义顺序
1. 外部模块导入
2. 全局常量/缓存
3. 工具函数
4. 主类（继承 QWidget/QDialog）
5. 主入口

### 信号连接
```python
self._mcp.result_ready.connect(self._on_result)
self._mcp.connected.connect(self._on_connected)
```

## 九、调试日志

```bash
[MCP] 连接成功!
[MCP →] add_topic_history | params: {'name': 'AI概念'}
[MCP ←] add_topic_history | success: True
[AKShare] 获取分时数据失败: ...
```

## 十、相关文件位置

| 用途 | 路径 |
|------|------|
| 启动入口 | `MarketInfo/start.bat` |
| 服务管理 | `MarketInfo/service_manager.py` |
| MCP服务 | `MarketInfo/mcp_server/server.py` |
| 数据库 | `MarketInfo/data/MarketInfo.db` |
| 用户配置 | `~/.marketinfo/settings.json` |