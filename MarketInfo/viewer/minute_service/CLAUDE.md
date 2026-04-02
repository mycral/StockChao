# minute_service - 分时数据服务

## 项目概述

提供多数据源的分时数据获取和本地缓存支持。

## 目录结构

```
viewer/minute_service/
├── __init__.py          # 模块导出
├── base.py              # 数据源抽象基类
├── sina_source.py       # 新浪分时数据源
├── service.py           # 分时服务主类
└── cache.py             # SQLite 本地缓存
```

## 数据流

```
SinaMinuteSource (sina_source.py)
    │
    ▼ AKShare API
    ak.stock_zh_a_minute()
    │
    ▼ 返回 DataFrame
    列: day, open, high, low, close, volume, amount
    类型: 全部为 string
    行数: ~1970 (历史多天数据)
    │
    ▼ MinuteDataService.get()
    │
    ├── _filter_last_day() - 筛选最后交易日
    │   - 转换 day 为 datetime
    │   - 筛选最后一天数据 (~238行)
    │   - 转换数值列为 float64/int64
    │
    ├── 缓存写入 (cache.py)
    │   - 使用 pickle 序列化 DataFrame
    │   - 存储到 SQLite
    │
    ▼ 返回 DataFrame (最终格式)
    列: day, open, high, low, close, volume, amount
    类型:
        - day: datetime64[us]
        - open/high/low/close: float64
        - volume: int64
        - amount: float64
    行数: ~238 (仅最后交易日)
```

## 数据格式

### AKShare 原始返回

| 列名 | 类型 | 说明 |
|------|------|------|
| day | string | 时间，格式 `YYYY-MM-DD HH:MM:SS` |
| open | string | 开盘价 |
| high | string | 最高价 |
| low | string | 最低价 |
| close | string | 收盘价 |
| volume | string | 成交量 |
| amount | string | 成交额 |

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

- **存储位置**: `viewer/minute_service/cache/minute_cache.db`
- **存储方式**: SQLite + pickle 序列化 DataFrame
- **缓存键**: `(ts_code, trade_date)` - 股票代码 + 交易日期
- **有效期**: 默认 5 分钟（可配置）

## 使用方式

```python
from viewer.minute_service import MinuteDataService

# 创建服务
service = MinuteDataService()

# 获取单只股票分时
df = service.get('600519.SH')  # 默认今天

# 指定日期获取
df = service.get('600519.SH', '20260402')

# 批量获取（并发）
results = service.get_batch(['600519.SH', '601398.SH', '000001.SZ'])
```

## KLineChart 兼容性

[KLineChart.plot_minute()](kline_viewer.py#L193) 兼容以下列名：

- 时间列: `trade_time`, `时间`, `day`（已兼容）
- 成交量列: `vol`, `volume`（已兼容）

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

## 配置项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| source | SinaMinuteSource | 数据源 |
| max_workers | 6 | 并发数 |
| cache_ttl | 300 | 缓存有效期（秒） |