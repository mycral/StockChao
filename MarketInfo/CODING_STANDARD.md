# MarketInfo 代码规范（AI 设计指南）

本文档供 AI 在设计、修改、扩展 MarketInfo 代码时遵循。包含所有字段格式、代码规范、接口约定。

---

## 一、字段格式标准（必须严格遵循）

### 1.1 ts_code（股票代码）—— 最核心字段

**格式**: `6位数字.市场后缀`

| 前缀范围 | 市场后缀 | 示例 |
|---------|---------|------|
| `6` 开头 | `.SH` | `600519.SH`, `688001.SH` |
| `0/3` 开头 | `.SZ` | `000001.SZ`, `300750.SZ` |
| `4/8` 开头 | `.BJ` | `430090.BJ`, `830809.BJ` |

**正则**: `^\d{6}\.(SH|SZ|BJ)$`

**规范化函数**（在 `core/field_format.py`）:
```python
from core.field_format import to_ts_code, is_valid_ts_code, parse_ts_code

to_ts_code("600519")       # -> "600519.SH"  （自动判断市场）
to_ts_code("600519", "SH") # -> "600519.SH"
is_valid_ts_code("000001.SZ")  # -> True
parse_ts_code("600519.SH")     # -> ("600519", "SH")
```

**规范要求**:
- 所有表中的 `ts_code` 字段必须使用此格式
- 关联表 `stock_concept`、`stock_industry`、`stock_region` 中的 ts_code 必须与 stock_basic 一致
- 严禁使用无后缀的纯数字代码（如 `"600519"` 是非法的）
- 严禁使用错误后缀（如 `"600519.SZ"` 是非法的）

### 1.2 concept_code / industry_code（板块代码）

**格式**: `BK` + 4位数字

| 类型 | 格式 | 示例 |
|------|------|------|
| 概念板块 | `BKxxxx` | `BK1173`, `BK0447`, `BK0888` |
| 行业板块 | `BKxxxx` | `BK1621`, `BK0438` |

**正则**: `^BK\d{4}$`

**注意**: 两者格式相同，含义不同（concept vs industry），不得混用。

### 1.3 region_code（地区板块代码）

**格式**: `6位数字.TDX`

| 示例 | 说明 |
|------|------|
| `880207.TDX` | 北京地区 |
| `880216.TDX` | 上海地区 |

**正则**: `^\d{6}\.TDX$`

**来源**: 通达信（TongDaXin）板块系统。

### 1.4 trade_date（交易日期）

**格式**: `YYYYMMDD`

| 示例 | 说明 |
|------|------|
| `20260329` | 2026年3月29日 |
| `20260101` | 2026年1月1日 |

**正则**: `^\d{8}$`

### 1.5 trade_time（交易时间，分钟数据）

**格式**: `YYYYMMDDHHMMSS`

| 示例 | 说明 |
|------|------|
| `20260329103000` | 2026-03-29 10:30:00 |
| `20260329150000` | 2026-03-29 15:00:00 |

**正则**: `^\d{14}$`

**用途**: `minute_1min`、`minute_5min`、`minute_15min`、`minute_30min`、`minute_60min` 表的主键时间字段。

### 1.6 timestamp（记录型时间戳，ms级）

**格式**: INTEGER，毫秒级 Unix 时间戳

| 示例 | 说明 |
|------|------|
| `1774800853262` | 2026-03-30 00:14:13 |

**用途**: `topic_history` 等记录型表的创建/更新时间。

**辅助函数**（`core/field_format.py`）：
- `now_ms()`: 返回当前 ms 时间戳
- `ts_to_str(ts)`: ms时间戳 → `YYYYMMDD HHMMSS` 字符串
- `str_to_ts(s)`: 字符串 → ms时间戳

### 1.7 rank（排名）

**格式**: 正整数，从 1 开始

- `1` = 涨幅最大 / 最重要
- `2`, `3`, ... 依次递减

**用途**: `concept_board`、`industry_board` 按涨跌幅排序后的序号。

---

## 二、代码编写规范

### 2.1 股票代码处理

**禁止**:
```python
# 禁止：直接拼接无后缀代码
sql = f"WHERE ts_code = '{code}'"  # code 可能是 "600519" 而非 "600519.SH"

# 禁止：硬编码后缀判断
if code.endswith('.SZ')  # 过于简单，不通用
```

**必须**:
```python
# 必须：使用规范化函数
from core.field_format import to_ts_code
normalized_code = to_ts_code(code)

# 必须：在 MCP 工具中先规范化输入
from mcp_server.tools.stock import _resolve_code
resolved = _resolve_code(input_code)  # 自动处理名称->代码转换
```

### 2.2 MCP 工具命名

所有 MCP 工具函数必须使用 `tool_` 前缀，避免递归：

```python
# ✅ 正确：工具实现函数
def tool_get_stock_info(code: str) -> dict:
    ...

def tool_add_topic_history(...) -> dict:
    ...

# ❌ 错误：会与 server.py 中的 @app.tool() 函数名冲突，造成递归
def get_stock_info(code: str) -> dict:
    ...
```

server.py 中注册时使用无前缀名称（通过 `@app.tool()` 装饰器），内部调用 `tool_` 前缀函数。

### 2.3 数据库查询

**必须使用上下文管理器**:
```python
# ✅ 正确
from core.query import QueryDB
from config import DB_PATH

with QueryDB(DB_PATH) as q:
    df = q.get_daily('600519.SH', start_date='20260301')

# ❌ 错误
q = QueryDB(DB_PATH)
df = q.get_daily(...)
q.close()  # 容易忘记关闭，且异常时不会关闭
```

**异常处理返回格式**:
```python
try:
    with QueryDB(DB_PATH) as q:
        df = q.get_xxx(...)
    return df.to_dict('records') if df is not None and len(df) > 0 else []
except Exception as e:
    logger.error(f"[ERROR] xxx | {e}")
    return [{"error": str(e)}]  # MCP 工具返回格式
```

### 2.4 日志规范

```python
import logging
logger = logging.getLogger(__name__)

# MCP 工具日志格式
logger.info(f"[REQUEST] tool_name | param1={val1}, param2={val2}")
logger.info(f"[RESPONSE] tool_name | result_count={len(result)}")
logger.error(f"[ERROR] tool_name | {e}")
```

### 2.5 JSON 字段存储

`stock_codes`、`stock_names` 等 JSON 字段必须：
```python
import json

# 写入
json.dumps(stock_codes, ensure_ascii=False)

# 读取
df['stock_codes'] = df['stock_codes'].apply(lambda x: json.loads(x) if x else [])
```

---

## 三、数据库设计规范

### 3.1 建表

- 新表必须添加到 `core/database.py` 的 `CREATE_TABLES_SQL` 字典中
- 必须包含主键（PRIMARY KEY）
- 必须创建必要索引（在 `create_database` 函数的 `indexes` 列表中）

### 3.2 表命名

| 前缀 | 用途 |
|------|------|
| `stock_` | 股票关联关系表（stock_concept, stock_industry, stock_region） |
| `daily` | 日线数据 |
| `minute_` | 分钟数据（minute_1min, minute_5min...） |
| `fuzzy_` | 辅助查询表 |

### 3.3 新增表的步骤

1. 在 `core/database.py` 添加建表 SQL
2. 在 `core/database.py` 添加索引
3. 在 `core/query.py` 添加查询方法
4. 在 `mcp_server/tools/` 添加 MCP 工具（新建工具文件）
5. 在 `mcp_server/server.py` 注册工具
6. 在 `mcp_server/tools/__init__.py` 导出
7. 在 `DB_TABLES.md` 补充表结构文档
8. 手动执行建表或初始化数据库

---

## 四、MCP 服务规范

### 4.1 工具注册

```python
# 1. 在 tools/ 下创建独立文件（如 topic.py）
def tool_xxx(...) -> ...:
    """文档字符串（供AI理解工具用途）"""
    ...

# 2. 在 server.py 顶部导入
from mcp_server.tools.topic import tool_xxx

# 3. 在 server.py 注册
@app.tool()
def xxx(...) -> ...:
    """工具说明（含参数、返回值示例）"""
    return tool_xxx(...)

# 4. 更新工具计数
print("可用工具: X 个")  # 注意更新数量
```

### 4.2 参数类型注解

```python
@app.tool()
def get_stock_info(code: str) -> dict:
    """
    Args:
        code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）
    Returns:
        dict: {...}
    """
```

### 4.3 返回值规范

| 返回类型 | 格式 | 错误时 |
|---------|------|-------|
| 单条记录 | `dict` | `{"error": str}` |
| 列表 | `list[dict]` | `[{"error": str}]` |
| 批量数据 | `dict`（如 `{"600519.SH": [...], ...}`） | `{"error": str}` |

---

## 五、AKShare 字段映射

AKShare 返回的字段名与数据库字段名不同，使用时需要映射：

### 分时数据（ak.stock_zh_a_minute）

| AKShare 字段 | 数据库字段 | 说明 |
|-------------|-----------|------|
| `day` | `trade_time` | 时间，格式 YYYY-MM-DD HH:MM:SS |
| `open` | `open` | 开盘价 |
| `high` | `high` | 最高价 |
| `low` | `low` | 最低价 |
| `close` | `close` | 收盘价 |
| `volume` | `vol` | 成交量（AKShare用volume，数据库用vol） |
| `amount` | `amount` | 成交额 |

### 代码格式转换

```python
# ts_code -> AKShare 格式
def to_ak_symbol(ts_code: str) -> str:
    """600519.SH -> sh600519"""
    code, suffix = ts_code.split('.')
    prefix = 'sh' if suffix == 'SH' else 'sz'
    return f"{prefix}{code}"

# AKShare 格式 -> ts_code
def from_ak_symbol(ak_symbol: str) -> str:
    """sh600519 -> 600519.SH"""
    prefix = ak_symbol[:2]
    code = ak_symbol[2:]
    suffix = 'SH' if prefix == 'sh' else 'SZ'
    return f"{code}.{suffix}"
```

---

## 六、热点监控面板规范

### 6.1 热点数据结构

```python
Topic = {
    'name': str,        # 热点名称，如 "AI概念"
    'news': str,        # 利好消息（最多100字显示，超出点击弹窗）
    'stocks': list,     # 关联股票列表（5只），格式: [{'ts_code': '...', 'name': '...', ...}, ...]
}
```

### 6.2 分时图刷新

- 刷新周期：30 秒
- 数据源：优先 `minute_5min` 表，无数据时通过 AKShare 实时获取
- 绘制方法：复用 `KLineChart.plot_minute(df, ts_code, name)`

---

## 七、快速参考

```python
# 1. 验证股票代码
from core.field_format import is_valid_ts_code
is_valid_ts_code("600519.SH")  # True

# 2. 规范化股票代码
from core.field_format import to_ts_code
to_ts_code("600519")  # "600519.SH"

# 3. 数据库查询（标准写法）
from core.query import QueryDB
from config import DB_PATH
with QueryDB(DB_PATH) as q:
    df = q.get_daily('600519.SH')

# 4. 写入热点历史
with QueryDB(DB_PATH) as q:
    q.add_topic_history('AI概念', news='政策利好', stock_codes=['600519.SH'], stock_names=['贵州茅台'])

# 5. AKShare 分时
import akshare as ak
df = ak.stock_zh_a_minute(symbol='sh600519', period='1', adjust='')
# 返回列: day, open, high, low, close, volume, amount

# 6. MCP 工具正确命名
# 实现函数: def tool_xxx(...)
# 注册函数: @app.tool() def xxx(...): return tool_xxx(...)
```