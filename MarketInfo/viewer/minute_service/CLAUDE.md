# minute_service - 分时数据服务

## 项目概述

提供多数据源的分时数据获取和本地缓存支持。

## 目录结构

```
viewer/minute_service/
├── __init__.py          # 模块导出
├── base.py              # 数据源抽象基类
├── sina_source.py       # 新浪分时数据源
├── pytdx_source.py      # Pytdx 分时数据源
├── service.py           # 分时服务主类
├── cache.py             # SQLite 本地缓存（WAL模式）
└── cache/               # 缓存数据库目录
    └── minute_cache.db  # SQLite 数据库
```

## 快速开始

```python
from viewer.minute_service import MinuteDataService

# 创建服务（默认使用 Pytdx）
service = MinuteDataService()

# 获取单只股票分时
df = service.get('600519.SH')
print(f"获取 {len(df)} 条数据")

# 批量获取（顺序，每只0.5秒）
results = service.get_batch(['600519.SH', '000001.SZ'])
```

## 数据源

### SinaMinuteSource (新浪)

- 接口: `ak.stock_zh_a_minute`
- 优点: 无需配置，直接可用
- 缺点: 接口不稳定

### PytdxMinuteSource (Pytdx) - 推荐

- 接口: `get_history_minute_time_data` + `get_minute_time_data`
- 优点: 实时数据，更稳定，支持分钟级数据
- 缺点: 需要能连接行情服务器

### 数据获取策略

```
9:30之前:
  └── get_history_minute_time_data (昨天数据)

9:30之后:
  ├── get_minute_time_data (今天实时)
  │     ↓ 数据不足
  ├── get_history_minute_time_data (今天)
  │     ↓ 数据不足
  └── get_history_minute_time_data (昨天)
```

## 核心特性

### 1. 请求间隔控制

避免并发请求，每只股票间隔 0.5 秒：

```python
# 全局调度器确保请求间隔
def _wait_for_interval():
    global _last_request_time
    with _request_interval:
        elapsed = time.time() - _last_request_time
        if elapsed < _request_interval:
            time.sleep(_request_interval - elapsed)
```

### 2. 连接有效性检测

每次请求前测试连接是否有效，无效则重连：

```python
def _connect(self):
    if self._api is not None:
        try:
            test_data = self._api.get_security_bars(...)
            if test_data:
                return True
        except:
            self._disconnect()
    # 重连逻辑...
```

### 3. 服务器地址管理

- 启动时从数据库读取缓存的服务器地址
- 后台线程每 5 分钟检测 TdxW.exe 连接地址
- 检测到新地址自动添加到服务器列表

### 4. 自动重连机制

```
获取数据流程:
1. 尝试当前服务器 (host:port)
   ↓ 失败
2. 从服务器列表获取其他可用服务器
   ↓ 失败
3. 移除失败服务器，继续尝试下一个
   ↓ 全部不可用
4. 返回 None
```

## 类参考

### MinuteDataService

```python
class MinuteDataService:
    def __init__(
        self,
        source: MinuteSource = None,  # 数据源，默认 Pytdx
        batch_interval: float = 0.5,   # 请求间隔（秒）
        cache_ttl: int = 300           # 缓存有效期（秒）
    )

    def get(self, ts_code: str, trade_date: str = None) -> pd.DataFrame
    def get_batch(self, ts_codes: list, trade_date: str = None) -> dict
    def clear_cache(self, ts_code: str = None, trade_date: str = None)
    @property def source_name(self) -> str
```

### PytdxMinuteSource

```python
class PytdxMinuteSource(MinuteSource):
    def __init__(
        self,
        host: str = '123.60.164.122',
        port: int = 7709,
        auto_refresh: bool = True,
        refresh_interval: int = 300
    )

    @property def name(self) -> str  # 返回 "pytdx"
    def fetch(self, ts_code: str) -> pd.DataFrame
    def close(self)
```

### MinuteCache

```python
class MinuteCache:
    def get(self, ts_code: str, trade_date: str) -> pd.DataFrame
    def set(self, ts_code: str, trade_date: str, data: pd.DataFrame)
    def clear(self, ts_code: str = None, trade_date: str = None)

    # 服务器管理
    def get_server(self) -> tuple  # (host, port)
    def set_server(self, host: str, port: int)
    def get_server_list(self) -> list  # [(host, port), ...]
    def add_server(self, host: str, port: int)
    def remove_server(self, host: str, port: int)
```

### MinuteSource (抽象基类)

```python
class MinuteSource(ABC):
    @property @abstractmethod
    def name(self) -> str: pass

    @abstractmethod
    def fetch(self, ts_code: str) -> pd.DataFrame:
        # 返回 DataFrame，列: day, open, high, low, close, volume, amount
        pass
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
    key TEXT PRIMARY KEY,  -- 键名 (tdxw_server 或 tdxw_server_{host}_{port})
    host TEXT,             -- 服务器地址
    port INTEGER,          -- 服务器端口
    updated_at INTEGER    -- 更新时间
);
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
| batch_interval | 0.5 | 请求间隔（秒） |
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
