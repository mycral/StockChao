# minute_service - 分时数据服务

## 项目概述

提供多数据源的分时数据获取和本地缓存支持。

## 目录结构

```
viewer/minute_service/
├── __init__.py          # 模块导出
├── base.py              # 数据源抽象基类
├── sina_source.py       # 新浪分时数据源
├── pytdx_source.py      # Pytdx 分时数据源（支持自动服务器发现）
├── service.py           # 分时服务主类
└── cache.py             # SQLite 本地缓存（WAL模式）
```

## 数据源

### SinaMinuteSource (新浪)

- 接口: `ak.stock_zh_a_minute`
- 优点: 无需配置，直接可用
- 缺点: 接口不稳定，有时返回空数据

### PytdxMinuteSource (Pytdx) - 推荐

- 接口: `get_history_minute_time_data` + `get_minute_time_data`
- 优点: 实时数据，更稳定，响应更快，支持分钟级数据
- 缺点: 需要能连接行情服务器

### 数据获取策略

```
9:30之前:
  └── get_history_minute_time_data (昨天数据)

9:30之后:
  ├── get_minute_time_data (今天实时数据)
  │     ↓ 数据不足
  ├── get_history_minute_time_data (今天)
  │     ↓ 数据不足
  └── get_history_minute_time_data (昨天)
```

## PytdxMinuteSource 详解

### 核心特性

#### 1. 服务器地址管理

**问题**: 用户使用通达信软件 (TdxW.exe) 连接行情服务器，但服务器地址可能变化。

**解决方案**: 
- 启动时从数据库读取缓存的服务器地址
- 后台线程每 5 分钟检测 TdxW.exe 的连接地址
- 检测到新地址自动添加到服务器列表

#### 2. 自动重连机制

```
获取数据流程:
1. 尝试当前服务器 (host:port)
   ↓ 失败
2. 从服务器列表获取其他可用服务器
   ↓ 全部失败
3. 移除失败服务器，继续尝试下一个
   ↓ 全部不可用
4. 返回 None
```

#### 3. 服务器列表管理

| 操作 | 说明 |
|------|------|
| `add_server()` | 添加服务器到列表 |
| `remove_server()` | 移除服务器（连接失败时） |
| `get_server_list()` | 获取所有可用服务器 |
| `get_server()` | 获取当前主服务器 |
| `set_server()` | 设置当前主服务器 |

### 类参数

```python
PytdxMinuteSource(
    host='123.60.164.122',      # 默认服务器
    port=7709,                   # 默认端口
    auto_refresh=True,           # 自动检测TdxW服务器变化
    refresh_interval=300          # 检测间隔(秒)，默认5分钟
)
```

### 后台线程

启动时创建后台线程，定期执行：
1. 调用 `get_tdxw_server()` 获取 TdxW.exe 当前地址
2. 若发现新地址，添加到服务器列表

### 使用示例

```python
from viewer.minute_service import MinuteDataService, PytdxMinuteSource

# 默认使用 Pytdx（自动检测）
service = MinuteDataService()

# 自定义配置
source = PytdxMinuteSource(
    auto_refresh=True,
    refresh_interval=300  # 5分钟检测一次
)
service = MinuteDataService(source=source)

# 获取数据
df = service.get('600519.SH')
```

## 数据流

```
数据请求
    │
    ▼ MinuteDataService.get()
    │
    ├── 检查缓存 (cache.py)
    │   └── 命中 → 返回 DataFrame
    │
    ▼ 数据源获取
    │
    ├── SinaMinuteSource
    │   └── ak.stock_zh_a_minute()
    │
    └── PytdxMinuteSource (默认)
        ├── 检查当前连接
        │   └── 失败 → 尝试列表中其他服务器
        │
        ▼ pytdx API
        get_security_bars(3, market, code, 0, 240)
        │
        ▼ 数据处理
        ├── 转换为 DataFrame
        ├── 列名映射 (vol → volume)
        └── 过滤最后交易日
        │
        ▼ 保存缓存
        └── pickle → SQLite
        │
        ▼ 返回 DataFrame
```

## 数据格式

### Pytdx API 返回格式

| API | 列名 | 类型 | 说明 |
|-----|------|------|------|
| get_history_minute_time_data | price, vol | float64 | 分钟价格和成交量 |
| get_minute_time_data | price, vol | float64 | 实时分钟数据 |
| get_security_bars | open, high, low, close, vol, amount, datetime | - | OHLCV格式 |

### Service 输出（最终格式）

| 列名 | 类型 | 说明 |
|------|------|------|
| day | datetime64[us] | 时间 |
| open | float64 | 开盘价 |
| high | float64 | 最高价 |
| low | float64 | 最低价 |
| close | float64 | 收盘价 |
| volume | int64 | 成交量（手） |
| amount | float64 | 成交额（元） |

## 缓存机制

### 数据库

- **位置**: `viewer/minute_service/cache/minute_cache.db`
- **模式**: WAL (Write-Ahead Logging)
- **存储**: pickle 序列化 DataFrame

### 表结构

```sql
-- 分时数据缓存
CREATE TABLE minute_cache (
    ts_code TEXT,           -- 股票代码
    trade_date TEXT,        -- 交易日期
    data BLOB,              -- 序列化数据
    updated_at INTEGER,    -- 更新时间
    PRIMARY KEY (ts_code, trade_date)
);

-- 服务器缓存
CREATE TABLE server_cache (
    key TEXT PRIMARY KEY,  -- 键名
    host TEXT,              -- 服务器地址
    port INTEGER,           -- 服务器端口
    updated_at INTEGER      -- 更新时间
);
```

### 缓存 API

```python
from viewer.minute_service import MinuteDataService
from viewer.minute_service.cache import MinuteCache

# 服务使用
service = MinuteDataService()
df = service.get('600519.SH')

# 缓存管理
cache = MinuteCache()
cache.get('600519.SH', '20260402')   # 获取缓存
cache.set('600519.SH', '20260402', df)  # 设置缓存
cache.clear('600519.SH')             # 清理缓存

# 服务器管理
cache.get_server()                   # 获取主服务器
cache.set_server('123.60.164.122', 7709)  # 设置主服务器
cache.get_server_list()              # 获取服务器列表
cache.add_server('123.60.164.122', 7709)  # 添加到列表
cache.remove_server('123.60.164.122', 7709)  # 移除
```

## 工具函数

### get_tdxw_server()

获取 TdxW.exe 连接的远程服务器地址。

```python
from viewer.minute_service import get_tdxw_server

server = get_tdxw_server()  # 返回 "123.60.164.122:7709" 或 ""
```

**实现原理**:
1. 通过 PowerShell 获取 TdxW.exe 进程 ID
2. 查询该进程的 TCP 连接
3. 筛选 Established 状态的连接
4. 提取远程地址和端口

## 配置项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| source | PytdxMinuteSource | 数据源 |
| max_workers | 6 | 并发数 |
| cache_ttl | 300 | 缓存有效期（秒） |

## 新增数据源

继承 `MinuteSource` 基类：

```python
from viewer.minute_service import MinuteSource

class MySource(MinuteSource):
    @property
    def name(self) -> str:
        return "my_source"

    def fetch(self, ts_code: str) -> pd.DataFrame:
        # 返回 DataFrame，列: day, open, high, low, close, volume, amount
        ...

# 使用
service = MinuteDataService(source=MySource())
```