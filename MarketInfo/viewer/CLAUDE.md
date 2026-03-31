# MarketInfo/viewer - Claude Code AI 开发指南

## 项目是什么

viewer 是 MarketInfo 的 GUI 可视化模块，基于 PySide6 实现热点监控面板。

**核心能力**：
- 实时监控股票热点板块
- 股票分时图显示
- MCP 服务调用

**依赖**：
- MarketInfo 主项目（MCP 服务、数据库）
- PySide6（GUI 框架）
- Matplotlib（K线图表）
- AKShare（实时行情）

---

## 文档体系

| 文件 | 谁读 | 内容 |
|------|------|------|
| **CLAUDE.md** | AI 开发前必读 | 项目概览、模块划分、**性能优化** |
| [ARCHITECTURE.md](ARCHITECTURE.md) | AI 开发时参考 | 完整架构、数据流 |
| [CODING_GUIDE.md](CODING_GUIDE.md) | AI 写代码时参考 | 关键函数、编码规范 |
| [mcp_settings.py](mcp_settings.py) | 用户配置 | MCP 服务地址 |

---

## 模块划分

```
viewer/
├── topic_monitor.py    # 主界面入口（~300行）
├── mcp_runner.py        # MCP 异步客户端（~80行）
├── stock_widget.py     # 自治股票组件（~130行）
├── mcp_settings.py     # 设置弹窗（~140行）
├── kline_viewer.py     # K线/分时图组件（第三方）
├── screen_three_up.py  # 选股策略（未用）
└── __init__.py
```

---

## 数据流

```
topic_monitor.py
    │
    ├── mcp_runner.py → MCP Server:9876
    │         add_topic_history
    │         get_topic_history
    │         delete_topic_history
    │
    └── stock_widget.py → AKShare 实时行情
```

---

## 关键概念

### 1. 自治模式
每个 StockWidget 独立管理自己的数据加载，互不阻塞。

### 2. MCP 调用
通过 MCPRunner 异步调用，远离子线程执行。

### 3. 缓存策略
- 分时数据：5分钟有效
- 股票名称：模块级缓存

---

## 数据模型

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

### StockWidget 传入参数
```python
# ✅ 正确：传入代码字符串
StockWidget("600519.SH")

# ❌ 错误：传入字典
StockWidget({"ts_code": "600519.SH", "name": "贵州茅台"})
```

---

## 字段格式

股票代码格式：`6位数字.市场后缀`
- `600519.SH`（上海主板）
- `000001.SZ`（深圳主板）
- `688001.SH`（科创板）

---

## 架构分层

```
UI 层：topic_monitor.py
  ├── TopicMonitorPanel（主面板）
  ├── NewsDialog（利好弹窗）
  └── StockWidget（股票组件）

异步层：mcp_runner.py + stock_widget.py
  ├── MCPRunner（MCP 客户端）
  └── StockWidget（自治加载）

数据层
  ├── MCP Server（热点数据）
  └── AKShare（实时行情）
```

---

## 快速启动

```bash
# 1. 启动 MCP 服务
cd MarketInfo
python -m mcp_server.server

# 2. 启动热点监控（方式1：直接运行）
python viewer/topic_monitor.py

# 3. 启动热点监控（方式2：通过服务管理器）
cd MarketInfo
python start.bat
```

---

## 性能优化（重要）

### 1. 自治模式（核心）
每个 StockWidget 独立管理自己的数据加载，**不阻塞主线程**。

```python
# ✅ 正确：组件自治加载
class StockWidget(QWidget):
    def __init__(self, ts_code):
        QTimer.singleShot(200, self._start_load)  # 延迟启动

# ❌ 错误：集中加载
for stock in stocks:
    df = fetch_realtime_minute(ts_code)  # 阻塞主线程！
```

### 2. 模块级缓存
全局缓存避免重复请求。

```python
# stock_widget.py
_stock_name_cache = {}      # 股票名称缓存
_minute_data_cache = {}       # 分时数据缓存（5分钟有效）
```

### 3. 延迟启动
创建组件后延迟 200ms 再加载，让 UI 先渲染完成。

### 4. 编码规范
```python
# 禁止在主线程同步访问网络
# def fetch_data():  # ← 禁止同步调用
#     return akshare.stock_zh_a_minute(...)

# ✅ 正确：组件内部延迟加载
class StockWidget(QWidget):
    def _start_load(self):
        QTimer.singleShot(200, self._load_data)
```

---

## AI 开发约定

### 1. 新增模块
在 `viewer/` 目录下创建新 Python 文件。

### 2. 新增组件
继承 `QWidget` 或 `QDialog`。

### 3. 导入规范
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

### 4. 缓存访问
```python
from viewer.stock_widget import get_stock_name_cache, get_minute_data_cache
```

---

## 调试日志

```python
# MCP 调用
[MCP] 正在连接 http://127.0.0.1:9876/mcp
[MCP] 连接成功!
[MCP →] get_topic_history | params: {'limit': 6}
[MCP ←] get_topic_history | success

# AKShare
[StockWidget] 600519.SH 加载中...
[StockWidget] 渲染完成
```

---

## 常见问题

### Q1: MCP 连接失败
- 检查 MCP 服务是否启动
- 检查端口 9876 是否可用

### Q2: 界面卡顿
- 确保 StockWidget 使用自治加载
- 使用 QTimer.singleShot 延迟启动

### Q3: 分时图不显示
- 检查 AKShare 是否正常
- 查看控制台错误日志

---

## 相关文件位置

| 用途 | 路径 |
|------|------|
| 启动入口 | `MarketInfo/start.bat` |
| 服务管理 | `MarketInfo/service_manager.py` |
| MCP 服务 | `MarketInfo/mcp_server/server.py` |
| 用户配置 | `~/.marketinfo/settings.json` |