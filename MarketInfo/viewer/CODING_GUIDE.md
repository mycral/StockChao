# topic_monitor.py 编码指南

## 一、项目概述

热点监控面板，用于实时监控股票热点板块及其成分股分时走势。

## 二、架构分层

```
viewer/
├── topic_monitor.py    # 主界面入口
├── mcp_runner.py     # MCP 客户端
├── stock_widget.py  # 自治股票组件
├── mcp_settings.py # 设置弹窗
└── kline_viewer.py # K线组件
```

## 三、核心数据结构

### 股票缓存（模块级）
```python
# stock_widget.py
_stock_name_cache = {}        # {ts_code: name}
_minute_data_cache = {}       # {ts_code: (df, timestamp)}
```

### 热点数据（MCP返回）
```python
topic = {
    'name': str,           # 热点名称，如 "AI概念"
    'news': str,           # 利好消息
    'stock_codes': list,   # 股票代码列表 ["600519.SH", ...]
    'topic_id': int        # 数据库ID
}
```

## 四、数据流

### 启动流程
```
topic_monitor.py → TopicMonitorPanel
        ↓
  _init_mcp() → MCPRunner 线程
        ↓
  _on_mcp_connected() → load_history()
        ↓
  refresh_grid() → 6个热点卡片
        ↓
  StockWidget(ts_code) → 自治加载分时
```

### 分时加载
```
StockWidget 创建
        ↓
  200ms 延迟 _start_load()
        ↓
  检查缓存 _minute_data_cache
        ↓
  有 → _render() 直接显示
        ↓
  无 → _fetch_minute() → AKShare
        ↓
  渲染 KLineChart
```

## 五、关键模块

### 1. topic_monitor.py
| 类/函数 | 用途 |
|---------|------|
| `TopicMonitorPanel` | 主面板 |
| `NewsDialog` | 利好弹窗 |
| `_call_mcp()` | 调用MCP工具 |

### 2. mcp_runner.py
| 类 | 用途 |
|-----|------|
| `MCPRunner` | 异步调用MCP |

信号：`result_ready`, `connected`, `error`

### 3. stock_widget.py
| 类/函数 | 用途 |
|---------|------|
| `StockWidget` | 自治股票组件 |
| `normalize_code()` | 规范化代码 |

### 4. mcp_settings.py
| 函数 | 用途 |
|------|------|
| `get_mcp_url()` | MCP服务地址 |
| `get_fullscreen()` | 是否全屏 |
| `MCPSettingsDialog` | 设置弹窗 |

## 六、关键函数说明

### TopicMonitorPanel 方法
```python
def add_topic(self):
    # 调用 MCP 添加热点
    self._call_mcp("add_topic_history", {...})

def load_history(self):
    # 加载热点列表，MCP返回后刷新网格

def refresh_grid(self):
    # 重建6个热点卡片，每个包含6个StockWidget

def create_topic_card(self, topic):
    # 创建单个热点卡片
    # 只显示：名称 + 利好 + 代码列表
    for code in stock_codes:
        sw = self._create_stock_widget(code)  # StockWidget自治

def _create_stock_widget(self, ts_code):
    return StockWidget(ts_code)  # 传入代码字符串
```

### StockWidget 方法
```python
def __init__(self, ts_code):
    # 传入代码如 "600519.SH"
    # 延迟500ms后加载

def _fetch_minute(self):
    # 后台线程 → minute_service.get()
    # 使用 Qt Signal 回调主线程渲染
```

### minute_service 使用
```python
from viewer.minute_service import MinuteDataService

service = MinuteDataService()
df = service.get('600519.SH')  # 自动缓存

# 批量获取（顺序，每只0.5秒）
results = service.get_batch(['600519.SH', '000001.SZ'])
```

## 七、性能优化

### 1. 自治模式
- 每个StockWidget独立加载，不阻塞其他组件

### 2. 缓存策略
- 分时数据：SQLite 缓存（minute_cache.db）
- 股票名称：模块级缓存

### 3. 请求间隔
```python
# 全局调度，每只股票间隔0.5秒
_request_interval = 0.5
```

### 4. 延迟启动
```python
QTimer.singleShot(500, self._fetch_minute)
# 让父组件先渲染完成
```

## 八、编码规范

### 导入顺序
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

### 创��组件
```python
# ✅ StockWidget 传入代码字符串
StockWidget("600519.SH")

# ❌ 不要传字典
StockWidget({"ts_code": "600519.SH", "name": "贵州茅台"})
```

### 调用 MCP
```python
def _call_mcp(self, tool_name, params, callback):
    import uuid
    call_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"
    self._pending_calls[call_id] = callback
    self._mcp.call_tool(call_id, tool_name, params)
```

## 九、模块级缓存访问

由于缓存在独立模块中，不同模块访问方式：

```python
# stock_widget.py 定义
_stock_name_cache = {}

def get_stock_name_cache():
    return _stock_name_cache

# 其他模块导入
from viewer.stock_widget import get_stock_name_cache
cache = get_stock_name_cache()
cache["600519.SH"] = "贵州茅台"
```

## 十、调试日志

```python
# MCP 调用
[MCP →] add_topic_history | params: {'name': 'AI概念'}
[MCP ←] add_topic_history | success: True

# AKShare
[AKShare] 获取分时数据失败: ...

# 组件加载
[StockWidget] 600519.SH 加载中...
[StockWidget] 600519.SH 渲染完成
```

## 十一、常见问题

### Q1: 界面卡
- 检查 StockWidget 是否在主线程加载 AKShare
- 确保使用 QTimer.singleShot 延迟

### Q2: MCP 连接失败
- 检查 MCP 服务是否启动：`python -m mcp_server.server`
- 检查端口：9876

### Q3: 分时图不显示
- 检查 AKShare 是否正常：`python -c "import akshare; print(akshare.__version__)"`
- 检查缓存：`print(get_minute_data_cache())`

## 十二、相关文件

| 文件 | 用途 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 完整架构文档 |
| [topic_monitor.py](topic_monitor.py) | 主界面 |
| [stock_widget.py](stock_widget.py) | 股票组件 |
| [mcp_runner.py](mcp_runner.py) | MCP客户端 |
| [mcp_settings.py](mcp_settings.py) | 设置 |