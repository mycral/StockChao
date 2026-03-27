# MarketInfo MCP Server

MCP (Model Context Protocol) 服务器，供大模型调用 MarketInfo 数据库。21 个工具，支持股票搜索、行情查询、板块分析、热点监控。

---

## 字段格式约定（调用前必读）

> 详细字段格式规范请参阅：[CODING_STANDARD.md](../CODING_STANDARD.md#一字段格式标准必须严格遵循)

| 字段类型 | 格式 | 示例 | 说明 |
|---------|------|------|------|
| **股票代码** | `6位数字.市场后缀` | `600519.SH`, `000001.SZ`, `688001.SH` | `.SH`=上交所, `.SZ`=深交所, `.BJ`=北交所 |
| **概念/行业代码** | `BKxxxx` | `BK1173`, `BK1621` | 4位数字，同花顺板块代码 |
| **地区代码** | `xxxxxx.TDX` | `880207.TDX` | 通达信地区板块代码 |
| **交易日期** | `YYYYMMDD` | `20260329` | 8位数字 |
| **交易时间** | `YYYYMMDDHHMMSS` | `20260329103000` | 分钟数据时间 |
| **时间戳** | `YYYYMMDD HHMMSS` | `20260329 103000` | 返回时格式（内部存储为INTEGER ms） |

> **提示**：调用方可以使用股票名称代替代码，系统会自动解析。如 `get_stock_info("贵州茅台")` 会自动转换为 `600519.SH`。

---

## 工具详解

### 一、搜索工具（7个）

#### fuzzy_search
**功能**：模糊搜索股票、概念、行业、地区，支持拼音首字母。

**参数**：
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `keyword` | string | ✅ | 搜索关键词 | `"茅台"`, `"gzmj"`, `"AI"` |
| `item_type` | string | ❌ | 类型过滤，不填则搜索全部 | `stock` / `concept` / `industry` / `region` |
| `limit` | int | ❌ | 返回数量，默认20 | `10` |

**返回示例**：
```json
[
  {"name": "贵州茅台", "code": "600519.SH", "item_type": "stock"},
  {"name": "贵州百灵", "code": "002424.SZ", "item_type": "stock"}
]
```

**调用示例**：
```
fuzzy_search(keyword="茅台")
fuzzy_search(keyword="gzmj")              # 拼音首字母
fuzzy_search(keyword="银行", item_type="industry")
```

---

#### search_stocks / search_concepts / search_industries / search_regions
**功能**：搜索单一类型的实体，是 `fuzzy_search` 的快捷版本。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keyword` | string | ✅ | 搜索关键词 |
| `limit` | int | ❌ | 返回数量，默认10 |

**调用示例**：
```
search_stocks(keyword="茅台")
search_concepts(keyword="AI")
search_industries(keyword="银行")
search_regions(keyword="浙江")
```

---

#### fuzzy_search_batch
**功能**：批量搜索多个关键词，一次获取多批结果。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keywords` | list[string] | ✅ | 关键词列表，最多20个 |
| `item_type` | string | ❌ | 类型过滤 |
| `limit_per_keyword` | int | ❌ | 每个关键词返回数量，默认5 |

**返回示例**：
```json
[
  {"keyword": "茅台", "name": "贵州茅台", "code": "600519.SH", "item_type": "stock"},
  {"keyword": "平安", "name": "平安银行", "code": "000001.SZ", "item_type": "stock"}
]
```

**调用示例**：
```
fuzzy_search_batch(keywords=["茅台", "平安", "银行"])
```

---

#### resolve_code_batch
**功能**：批量将股票名称或代码转换为标准股票代码。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `codes_or_names` | list[string] | ✅ | 股票代码或名称列表 |

**返回示例**：
```json
[
  {"input": "贵州茅台", "resolved_code": "600519.SH", "name": "贵州茅台"},
  {"input": "600519.SH", "resolved_code": "600519.SH", "name": "贵州茅台"},
  {"input": "000001", "resolved_code": "000001.SZ", "name": "平安银行"}
]
```

---

### 二、股票查询工具（7个）

#### get_stock_info
**功能**：获取股票基本信息（含最新价）。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `code` | string | ✅ | 股票代码或名称 |

**返回示例**：
```json
{
  "ts_code": "600519.SH",
  "symbol": "600519",
  "name": "贵州茅台",
  "industry": "白酒",
  "market": "主板",
  "list_date": "20010110",
  "latest_price": 1688.0
}
```

**调用示例**：
```
get_stock_info("600519.SH")
get_stock_info("贵州茅台")
```

---

#### get_stock_info_batch
**功能**：批量获取股票基本信息。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `codes` | list[string] | ✅ | 股票代码或名称列表，最多50只 |

**返回示例**：
```json
{
  "600519.SH": {"ts_code": "600519.SH", "symbol": "600519", "name": "贵州茅台", "latest_price": 1688.0},
  "000001.SZ": {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", "latest_price": 12.5}
}
```

**调用示例**：
```
get_stock_info_batch(["600519.SH", "000001.SZ", "601988.SH"])
```

---

#### get_stock_daily
**功能**：获取股票日线数据。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `code` | string | ✅ | 股票代码或名称 |
| `start_date` | string | ❌ | 开始日期，格式 YYYYMMDD |
| `end_date` | string | ❌ | 结束日期，格式 YYYYMMDD |
| `limit` | int | ❌ | 返回条数，默认100，最新日期在前 |

**返回示例**：
```json
[
  {"trade_date": "20260327", "close": 1688.0, "pct_chg": 1.2, "vol": 23456},
  {"trade_date": "20260326", "close": 1668.0, "pct_chg": -0.5, "vol": 19876}
]
```

**调用示例**：
```
get_stock_daily("600519.SH", limit=5)
get_stock_daily("贵州茅台", start_date="20260301", end_date="20260329")
```

---

#### get_stock_daily_batch
**功能**：批量获取多只股票的日线数据，比逐个调用 `get_stock_daily` 更高效。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `codes` | list[string] | ✅ | 股票代码列表，最多30只 |
| `limit` | int | ❌ | 每只股票返回交易日数，默认30 |

**返回示例**：
```json
{
  "600519.SH": [{"trade_date": "20260327", "close": 1688.0}, ...],
  "000001.SZ": [{"trade_date": "20260327", "close": 12.5}, ...]
}
```

**调用示例**：
```
get_stock_daily_batch(codes=["600519.SH", "000001.SZ", "601988.SH"], limit=30)
```

---

#### get_stock_concepts / get_stock_industries / get_stock_regions
**功能**：获取股票所属的板块（概念/行业/地区）。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `code` | string | ✅ | 股票代码或名称 |

**返回示例**：
```json
// get_stock_concepts
[
  {"concept_code": "BK0477", "concept_name": "白酒概念"},
  {"concept_code": "BK0422", "concept_name": "茅概念"}
]

// get_stock_industries
[
  {"industry_code": "BK0438", "industry_name": "食品饮料"}
]

// get_stock_regions
[
  {"region_code": "880226.TDX", "region_name": "贵州板块"}
]
```

---

### 三、板块查询工具（6个）

#### get_all_concepts / get_all_industries / get_all_regions
**功能**：获取所有板块列表，按涨跌幅排名。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `limit` | int | ❌ | 返回数量，默认100/100/50 |

**返回示例**：
```json
// get_all_concepts
[
  {"rank": 1, "concept_name": "AI概念", "concept_code": "BK1173", "pct_chg": 5.52, "up_count": 37, "top_stock": "汇川技术"},
  {"rank": 2, "concept_name": "单抗概念", "concept_code": "BK0870", "pct_chg": 5.01, "up_count": 49}
]

// get_all_industries
[
  {"rank": 1, "industry_name": "银行", "industry_code": "BK1621", "pct_chg": 2.3}
]

// get_all_regions
[
  {"rank": 1, "region_name": "北京地区", "region_code": "880207.TDX"}
]
```

---

#### get_concept_stocks / get_industry_stocks / get_region_stocks
**功能**：获取指定板块的成分股列表。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `concept_name` / `industry_name` / `region_name` | string | ✅ | 板块名称 |
| `limit` | int | ❌ | 返回数量，默认100 |

**返回示例**：
```json
// get_concept_stocks
[
  {"ts_code": "002230.SZ", "symbol": "002230", "name": "科大讯飞", "latest_price": 45.6, "pct_chg": 3.2},
  {"ts_code": "300124.SZ", "symbol": "300124", "name": "汇川技术", "latest_price": 78.9, "pct_chg": 5.1}
]

// get_industry_stocks
[
  {"ts_code": "601988.SH", "symbol": "601988", "name": "中国银行", "latest_price": 4.5, "pct_chg": 1.8}
]

// get_region_stocks
[
  {"ts_code": "600519.SH", "name": "贵州茅台", "latest_price": 1688.0, "pct_chg": 1.2}
]
```

**调用示例**：
```
get_concept_stocks(concept_name="AI概念", limit=10)
get_industry_stocks(industry_name="银行")
get_region_stocks(region_name="北京地区")   # 注意：需要"地区"后缀
```

---

### 四、热点监控工具（3个）

> 自动关联机制：用户只需提供 `name`（热点名称），系统通过 name 模糊匹配 `concept_board` 自动填充 `concept_codes`、`board_names`，再通过 `concept_codes` 查询 `stock_concept` 填充 `stock_codes`、`stock_names`。用户也可手动指定 `concept_codes` 或 `stock_codes` 覆盖自动值。

#### add_topic_history
**功能**：记录热点到历史列表（自动关联板块和股票）。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 热点名称，如 `AI概念` |
| `concept_codes` | list[string] | ❌ | 板块代码列表（如 `["BK1173", "BK0800"]`），不填则自动查找 |
| `news` | string | ❌ | 利好/刺激性消息（最多500字） |
| `stock_codes` | list[string] | ❌ | 关联股票代码列表，不填则自动从板块获取 |

**返回示例**：
```json
{"success": true, "id": 1}
```

**调用示例**：
```
add_topic_history(name="AI概念", news="政策支持人工智能发展，行业景气度提升")
add_topic_history(name="机器人概念", concept_codes=["BK1188", "BK0800"], news="工信部发布机器人产业规划")
```

---

#### get_topic_history
**功能**：获取历史热点列表。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `limit` | int | ❌ | 返回数量，默认50 |

**返回示例**：
```json
[
  {
    "id": 1,
    "name": "AI概念",
    "concept_codes": ["BK1173", "BK0800"],
    "board_names": ["人工智能", "AI大模型"],
    "news": "政策支持人工智能发展...",
    "stock_codes": ["600519.SH", "000001.SZ"],
    "stock_names": ["贵州茅台", "平安银行"],
    "created_at": "20260330 001757"
  }
]
```

---

#### get_latest_topics
**功能**：获取当日热门热点（从概念板块涨跌幅排序）。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `limit` | int | ❌ | 返回数量，默认20 |

**返回示例**：
```json
[
  {"concept_name": "AI概念", "concept_code": "BK1173", "pct_chg": 5.52, "up_count": 37, "down_count": 2},
  {"concept_name": "机器人概念", "concept_code": "BK1188", "pct_chg": 4.83, "up_count": 52}
]
```

**调用示例**：
```
get_latest_topics(limit=10)   # 获取当日涨幅前10的热点
```

---

## 调用示例

### 示例1：查询股票日线
```
输入: 贵州茅台最近5天的收盘价

调用:
  1. get_stock_info("贵州茅台") -> ts_code="600519.SH"
  2. get_stock_daily("600519.SH", limit=5)

返回:
  2026-03-27: 1688.00元 (+1.2%)
  2026-03-26: 1668.00元 (-0.5%)
  ...
```

### 示例2：查找热门概念
```
输入: 今天哪些概念板块涨幅最大？

调用:
  get_latest_topics(limit=10)

返回:
  1. AI概念 (+5.52%) - 37只上涨
  2. 单抗概念 (+5.01%) - 49只上涨
  ...
```

### 示例3：批量分析多只股票
```
输入: 分析中国平安、招商银行、工商银行最近的股价表现

调用:
  1. resolve_code_batch(["中国平安", "招商银行", "工商银行"])
     -> ["000001.SZ", "600036.SH", "601398.SH"]
  2. get_stock_daily_batch(["000001.SZ", "600036.SH", "601398.SH"], limit=5)

返回: 三只股票的近5日日线数据
```

---

## 工具一览表

| 类别 | 工具 | 必填参数 | 说明 |
|------|------|---------|------|
| 搜索 | `fuzzy_search` | keyword | 通用模糊搜索 |
| 搜索 | `fuzzy_search_batch` | keywords | 批量模糊搜索 |
| 搜索 | `search_stocks` | keyword | 搜索股票 |
| 搜索 | `search_concepts` | keyword | 搜索概念板块 |
| 搜索 | `search_industries` | keyword | 搜索行业板块 |
| 搜索 | `search_regions` | keyword | 搜索地区板块 |
| 搜索 | `resolve_code_batch` | codes_or_names | 批量代码解析 |
| 股票 | `get_stock_info` | code | 股票基本信息 |
| 股票 | `get_stock_info_batch` | codes | 批量股票基本信息 |
| 股票 | `get_stock_daily` | code | 日线数据 |
| 股票 | `get_stock_daily_batch` | codes | 批量日线数据 |
| 股票 | `get_stock_concepts` | code | 股票概念板块 |
| 股票 | `get_stock_industries` | code | 股票行业板块 |
| 股票 | `get_stock_regions` | code | 股票地区板块 |
| 板块 | `get_all_concepts` | - | 所有概念板块 |
| 板块 | `get_all_industries` | - | 所有行业板块 |
| 板块 | `get_all_regions` | - | 所有地区板块 |
| 板块 | `get_concept_stocks` | concept_name | 概念成分股 |
| 板块 | `get_industry_stocks` | industry_name | 行业成分股 |
| 板块 | `get_region_stocks` | region_name | 地区成分股 |
| 热点 | `add_topic_history` | concept_name | 记录热点 |
| 热点 | `get_topic_history` | - | 历史热点列表 |
| 热点 | `get_latest_topics` | - | 热门热点 |

---

## 错误处理

所有工具异常时返回：
```json
// 单条: {"error": "错误信息"}
// 列表: [{"error": "错误信息"}]
```

> 更多代码规范（MCP 工具命名、数据库查询、日志等）请参阅：[CODING_STANDARD.md](../CODING_STANDARD.md)

---

## 安装与启动

```bash
# 安装依赖
pip install -r requirements_mcp.txt

# 启动服务（默认端口 9876）
python -m mcp_server.server

# 自定义端口
python -m mcp_server.server --port 8080

# 服务地址
http://127.0.0.1:9876/mcp
```