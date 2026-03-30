# MarketInfo - AI 理解指南

## 项目是什么

MarketInfo 是一个本地化的 A股历史数据仓库，支持 Tushare Pro 和 Akshare 双数据源自动降级。数据存储在 SQLite 数据库中，支持命令行、代码调用、MCP 服务三种使用方式。

**核心能力**：查询股票行情、分析板块涨跌、监控热点题材、支撑大模型选股决策。

---

## 文档体系（必读）

| 文件 | 谁读 | 内容 |
|------|------|------|
| **CLAUDE.md** | AI 开发新功能前必读 | 项目概览、架构、设计约定 |
| [CODING_STANDARD.md](CODING_STANDARD.md) | AI 写代码时参考 | 字段格式规范、代码编写规范 |
| [README.md](README.md) | 用户/AI 理解功能 | 命令行用法、CLI 命令详解 |
| [DB_TABLES.md](DB_TABLES.md) | AI 理解数据库 | 数据库表结构、字段说明 |
| [mcp_server/README.md](mcp_server/README.md) | AI 调用 MCP 时参考 | MCP 工具列表、参数说明 |

**文档依赖关系**：
```
CLAUDE.md（总览）
  ├── CODING_STANDARD.md（代码规范，引用字段格式）
  ├── DB_TABLES.md（表结构，引用 CODING_STANDARD.md 中的字段格式）
  └── mcp_server/README.md（MCP 工具，引用 CODING_STANDARD.md 中的字段格式）
       └── tools/*.py（具体实现）
```

---

## 关键概念

### 数据模型

```
stock_basic (股票列表)
    │
    ├── daily / daily_basic / adj_factor (行情数据)
    ├── minute_1/5/15/30/60min (分钟数据)
    ├── stock_concept (概念关联) ← concept_board (概念板块)
    ├── stock_industry (行业关联) ← industry_board (行业板块)
    └── stock_region (地区关联) ← region_board (地区板块)

fuzzy_search (统一搜索表，从以上各表收集)
topic_history (热点监控历史记录)
```

### 字段格式（必须严格遵循）

| 字段 | 格式 | 示例 | 定义位置 |
|------|------|------|---------|
| ts_code（股票代码） | 6位数字.市场后缀 | `600519.SH`, `000001.SZ` | `core/field_format.py` |
| concept_code / industry_code | BKxxxx | `BK1173`, `BK1621` | `core/field_format.py` |
| region_code | xxxxxx.TDX | `880207.TDX` | `core/field_format.py` |
| trade_date（交易日期） | YYYYMMDD | `20260329` | `core/field_format.py` |
| trade_time（分钟时间） | YYYYMMDDHHMMSS | `20260329103000` | `core/field_format.py` |
| timestamp（记录时间） | INTEGER (ms) | `1774800853262` | `core/field_format.py` |

> 所有字段格式的详细定义、正则、验证工具函数都在 [CODING_STANDARD.md](CODING_STANDARD.md#一字段格式标准必须严格遵循)。

### 架构分层

```
数据来源层
├── Akshare（主，免费，开源）
└── Tushare（备，需要 token）

数据获取层
└── core/data_fetcher.py（自动降级逻辑）

数据存储层
└── SQLite (core/database.py 建表，core/query.py 查询)

服务层
├── main.py（CLI 命令行）
├── MCP 服务（core/server.py，21个工具）
└── viewer/（PyQt5 GUI 工具）注意，viewer是独立模块，通过mcp获取部分数据，不能直接读取数据库。也不引用其他文件夹的模块。
```

---

## 常用操作（AI 写代码时的标准模式）

### 1. 数据库查询（必须用上下文管理器）

```python
from core.query import QueryDB
from config import DB_PATH

with QueryDB(DB_PATH) as q:
    df = q.get_daily('600519.SH', start_date='20260301')
    stocks = q.get_concept_stocks(concept_name='AI概念')
```

### 2. 字段规范化

```python
from core.field_format import to_ts_code, is_valid_ts_code

code = to_ts_code("600519")  # -> "600519.SH"
if not is_valid_ts_code(code):
    raise ValueError("无效的股票代码")
```

### 3. MCP 工具命名

```python
# ✅ 实现函数用 tool_ 前缀
def tool_add_topic_history(name, concept_code=None, news=None):
    ...

# ✅ server.py 注册时用无前缀名称
@app.tool()
def add_topic_history(name, concept_code=None, news=None):
    return tool_add_topic_history(name, concept_code, news)
```

### 4. 写入热点历史（自动关联）

```python
# 用户只需提供 name，系统自动填充 concept_code/board_name/stock_codes/stock_names
q.add_topic_history(name='AI概念', news='政策利好')
```

---

## MCP 工具一览（21个）

| 类别 | 数量 | 工具 |
|------|------|------|
| 搜索 | 7 | fuzzy_search, fuzzy_search_batch, search_stocks/concepts/industries/regions, resolve_code_batch |
| 股票 | 7 | get_stock_info/info_batch/daily/daily_batch/concepts/industries/regions |
| 板块 | 6 | get_all_concepts/industries/regions, get_concept/industry/region_stocks |
| 热点 | 3 | add_topic_history, get_topic_history, get_latest_topics |

> 详细参数和返回值见 [mcp_server/README.md](mcp_server/README.md)

---

## 热点监控特殊设计

热点系统通过 `concept_code` 自动关联板块和股票。用户输入 `name`，系统通过模糊匹配 `concept_board` 找到 `concept_code`，再通过 `stock_concept` 填充关联股票。

```
用户输入 name → 模糊匹配 concept_board → concept_code + board_name
                                        → 查询 stock_concept → stock_codes + stock_names
```

---

## 目录结构

```
MarketInfo/
├── config.py              # DB_PATH 等配置
├── main.py                # CLI 入口
├── requirements.txt
│
├── core/
│   ├── database.py        # 建表 SQL (CREATE_TABLES_SQL)
│   ├── query.py           # QueryDB 查询类
│   ├── field_format.py   # 字段格式规范 + 验证工具
│   ├── data_fetcher.py   # 数据获取器（自动降级）
│   └── data_source_*.py  # 各数据源适配器
│
├── mcp_server/
│   ├── server.py          # FastMCP 服务主入口
│   ├── tools/
│   │   ├── search.py     # 7个搜索工具
│   │   ├── stock.py      # 6个股票工具
│   │   ├── board.py      # 6个板块工具
│   │   └── topic.py      # 3个热点工具
│   └── README.md          # MCP 工具文档
│
├── viewer/
│   ├── README.md          # GUI 工具文档
│   ├── kline_viewer.py    # K线+分时图组件
│   ├── topic_monitor.py   # 热点监控面板
│   ├── screen_three_up.py # 三连阳筛选
│   └── skills/            # 选股策略模块
│
├── migrate_topic_history.py  # 热点表字段迁移脚本
├── CODING_STANDARD.md       # 代码规范
├── DB_TABLES.md              # 数据库表结构
└── data/MarketInfo.db       # SQLite 数据库文件
```

---

## AI 开发约定

1. **新增表**：在 `core/database.py` 的 `CREATE_TABLES_SQL` 中添加，索引在 `create_database()` 中添加
2. **新增 MCP 工具**：在 `mcp_server/tools/` 下新建文件，用 `tool_` 前缀命名，server.py 注册
3. **字段格式**：所有代码中的字段格式必须符合 `core/field_format.py` 定义
4. **数据库查询**：始终使用 `with QueryDB(DB_PATH) as q:` 上下文管理器
5. **JSON 字段**：写入用 `json.dumps()`，读取用 `json.loads()`
6. **AKShare 字段映射**：AKShare 返回 `day`/`volume`，数据库用 `trade_time`/`vol`

---

## 快速启动

```bash
# 初始化数据库
python main.py init

# 更新板块数据
python main.py concept
python main.py industry
python main.py region

# 增量同步日线
python main.py sync

# 启动 MCP 服务
python -m mcp_server.server

# 启动热点监控面板
python viewer/topic_monitor.py

# 执行数据库迁移（字段重构后）
python migrate_topic_history.py
```