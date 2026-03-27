# 数据库表结构说明

数据库文件: `data/MarketInfo.db`

## 字段格式规范

所有字段格式定义在 `core/field_format.py`，验证工具函数请参考该文件。

### ts_code（股票代码）

| 前缀 | 市场 | 示例 |
|------|------|------|
| `6` | 上海主板 (SH) | `600000.SH`, `600519.SH` |
| `0` | 深圳主板 (SZ) | `000001.SZ`, `000002.SZ` |
| `3` | 创业板 (SZ) | `300001.SZ`, `300750.SZ` |
| `8`/`4` | 北交所 (BJ) | `830809.BJ`, `430090.BJ` |

**格式**: `6位数字.市场后缀`（正则: `^\d{6}\.(SH|SZ|BJ)$`）

**注意**：所有关联表（如 `stock_concept`、`stock_industry`、`stock_region`）中的 `ts_code` 必须与此格式一致。

### concept_code / industry_code（板块代码）

| 类型 | 格式 | 示例 |
|------|------|------|
| 概念板块 | `BKxxxx` | `BK1173`, `BK0447` |
| 行业板块 | `BKxxxx` | `BK1621`, `BK0438` |

**格式**: `BK` + 4位数字（正则: `^BK\d{4}$`）

### region_code（地区板块代码）

| 格式 | 示例 |
|------|------|
| `xxxxxx.TDX` | `880207.TDX`, `880216.TDX` |

**格式**: 6位数字 + `.TDX`（正则: `^\d{6}\.TDX$`）

### trade_date（交易日期）

| 格式 | 示例 |
|------|------|
| `YYYYMMDD` | `20260329`, `20260101` |

### trade_time（交易时间，分钟数据）

| 格式 | 示例 |
|------|------|
| `YYYYMMDDHHMMSS` | `20260329103000`, `20260329150000` |

### timestamp（记录型时间戳）

| 格式 | 示例 |
|------|------|
| `YYYYMMDD HHMMSS` | `20260329 103000` |

用于 `topic_history` 等记录型表的创建/更新时间。

### rank（排名）

| 格式 | 说明 |
|------|------|
| 整数，从1开始 | `1` = 涨幅最大 |

---

## 股票基础信息

### stock_basic - 股票列表

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码 (主键)，格式见上 |
| symbol | TEXT | 股票符号，6位纯数字，如 `600519` |
| name | TEXT | 股票名称 |
| area | TEXT | 地域 |
| industry | TEXT | 所属行业 |
| market | TEXT | 市场 |
| list_date | TEXT | 上市日期 (YYYYMMDD) |
| delist_date | TEXT | 退市日期 (YYYYMMDD)，无则 NULL |
| is_hs | TEXT | 是否沪深港通 |
| latest_price | REAL | 最新收盘价 |

---

## 行情数据

### daily - 日线数据

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码 |
| trade_date | TEXT | 交易日期 (YYYYMMDD) |
| open | REAL | 开盘价 |
| high | REAL | 最高价 |
| low | REAL | 最低价 |
| close | REAL | 收盘价 |
| pre_close | REAL | 前收价 |
| change | REAL | 涨跌额 |
| pct_chg | REAL | 涨跌幅 (%) |
| vol | REAL | 成交量 (手) |
| amount | REAL | 成交额 (元) |

**主键**: `(ts_code, trade_date)`

### daily_basic - 每日指标

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码 |
| trade_date | TEXT | 交易日期 (YYYYMMDD) |
| close | REAL | 收盘价 |
| turnover_rate | REAL | 换手率 (%) |
| turnover_rate_f | REAL | 流通换手率 (%) |
| volume_ratio | REAL | 量比 |
| pe | REAL | 市盈率 |
| pe_ttm | REAL | 市盈率 TTM |
| pb | REAL | 市净率 |
| ps | REAL | 市销率 |
| ps_ttm | REAL | 市销率 TTM |
| dv_ratio | REAL | 股息率 |
| dv_ttm | REAL | 股息率 TTM |
| total_share | REAL | 总股本 (万股) |
| float_share | REAL | 流通股本 (万股) |
| free_share | REAL | 自由流通股本 (万股) |
| total_mv | REAL | 总市值 (万元) |
| circ_mv | REAL | 流通市值 (万元) |

**主键**: `(ts_code, trade_date)`

### adj_factor - 复权因子

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码 |
| trade_date | TEXT | 交易日期 (YYYYMMDD) |
| adj_factor | REAL | 复权因子 |

**主键**: `(ts_code, trade_date)`

### minute_1min / minute_5min / minute_15min / minute_30min / minute_60min - 分钟数据

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码 |
| trade_time | TEXT | 交易时间 (YYYYMMDDHHMMSS) |
| open | REAL | 开盘价 |
| high | REAL | 最高价 |
| low | REAL | 最低价 |
| close | REAL | 收盘价 |
| vol | INTEGER | 成交量 (手) |
| amount | REAL | 成交额 (元) |

**主键**: `(ts_code, trade_time)`

### weekly / monthly - 周线/月线数据

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码 |
| trade_date | TEXT | 交易日期 (YYYYMMDD) |
| open | REAL | 开盘价 |
| high | REAL | 最高价 |
| low | REAL | 最低价 |
| close | REAL | 收盘价 |
| pre_close | REAL | 前收价 |
| change | REAL | 涨跌额 |
| pct_chg | REAL | 涨跌幅 (%) |
| vol | REAL | 成交量 (手) |
| amount | REAL | 成交额 (元) |

**主键**: `(ts_code, trade_date)`

---

## 财务报表

### income - 利润表

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码 |
| ann_date | TEXT | 公告日期 (YYYYMMDD) |
| f_ann_date | TEXT | 实际公告日期 (YYYYMMDD) |
| period | TEXT | 报告期 (YYYYMM) |
| report_type | INTEGER | 报告类型 |
| comp_type | INTEGER | 公司类型 |
| basic_eps | REAL | 基本每股收益 |
| diluted_eps | REAL | 稀释每股收益 |
| total_revenue | REAL | 营业总收入 |
| revenue | REAL | 营业收入 |
| oper_income | REAL | 营业利润 |
| operate_profit | REAL | 利润总额 |
| total_profit | REAL | 净利润 |
| net_profit | REAL | 归属于母公司净利润 |
| income_tax | REAL | 所得税 |
| n_income | REAL | 净利润(含少数股东损益) |
| ebit | REAL | 息税前利润 |
| ebitda | REAL | EBITDA |

**主键**: `(ts_code, ann_date, period)`

### balancesheet - 资产负债表

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码 |
| ann_date | TEXT | 公告日期 (YYYYMMDD) |
| f_ann_date | TEXT | 实际公告日期 (YYYYMMDD) |
| period | TEXT | 报告期 (YYYYMM) |
| report_type | INTEGER | 报告类型 |
| total_assets | REAL | 资产总计 |
| total_liab | REAL | 负债合计 |
| total_hldr_eqy_inc_min_int | REAL | 归属母公司股东权益 |
| liab_payable | REAL | 应付账款 |
| total_current_assets | REAL | 流动资产合计 |
| total_current_liab | REAL | 流动负债合计 |

**主键**: `(ts_code, ann_date, period)`

### cashflow - 现金流量表

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码 |
| ann_date | TEXT | 公告日期 (YYYYMMDD) |
| f_ann_date | TEXT | 实际公告日期 (YYYYMMDD) |
| period | TEXT | 报告期 (YYYYMM) |
| report_type | INTEGER | 报告类型 |
| net_profit | REAL | 净利润 |
| n_cashflow_act | REAL | 经营活动现金流量净额 |
| n_cashflow_inv_act | REAL | 投资活动现金流量净额 |
| n_cash_flows_fnc_act | REAL | 筹资活动现金流量净额 |
| c_cash_equ_end_period | REAL | 期末现金及现金等价物余额 |

**主键**: `(ts_code, ann_date, period)`

---

## 概念板块数据

### concept_board - 概念板块列表

| 字段 | 类型 | 说明 |
|-----|------|------|
| concept_code | TEXT | 概念板块代码 (主键)，如 `BK1173` |
| concept_name | TEXT | 概念名称，如 `锂矿概念` |
| rank | INTEGER | 排名 |
| latest_price | REAL | 板块最新价 |
| changeAmt | REAL | 涨跌额 |
| pct_chg | REAL | 涨跌幅 (%) |
| total_mv | REAL | 总市值 (元) |
| turnover_rate | REAL | 换手率 (%) |
| up_count | INTEGER | 上涨家数 |
| down_count | INTEGER | 下跌家数 |
| top_stock | TEXT | 领涨股票 |
| top_stock_pct | REAL | 领涨股票涨跌幅 (%) |

**主键**: `concept_code`

### stock_concept - 股票概念关系

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码，如 `000001.SZ` |
| symbol | TEXT | 股票代码，如 `000001` |
| name | TEXT | 股票名称 |
| concept_code | TEXT | 概念板块代码 |
| concept_name | TEXT | 概念名称 |

**主键**: `(ts_code, concept_code)`

---

## 行业板块数据

### industry_board - 行业板块列表

| 字段 | 类型 | 说明 |
|-----|------|------|
| industry_code | TEXT | 行业板块代码 (主键) |
| industry_name | TEXT | 行业名称，如 `银行` |
| rank | INTEGER | 排名 |
| latest_price | REAL | 板块最新价 |
| changeAmt | REAL | 涨跌额 |
| pct_chg | REAL | 涨跌幅 (%) |
| total_mv | REAL | 总市值 (元) |
| turnover_rate | REAL | 换手率 (%) |
| up_count | INTEGER | 上涨家数 |
| down_count | INTEGER | 下跌家数 |
| top_stock | TEXT | 领涨股票 |
| top_stock_pct | REAL | 领涨股票涨跌幅 (%) |

**主键**: `industry_code`

### stock_industry - 股票行业关系

| 字段 | 类型 | 说明 |
|-----|------|------|
| ts_code | TEXT | 股票代码，如 `000001.SZ` |
| symbol | TEXT | 股票代码，如 `000001` |
| name | TEXT | 股票名称 |
| industry_code | TEXT | 行业板块代码 |
| industry_name | TEXT | 行业名称 |

**主键**: `(ts_code, industry_code)`

---

## 地区板块数据

### region_board - 地区板块列表

**数据来源**: Tushare `tdx_index` 接口（通达信板块信息）

| 字段 | 类型 | 说明 | 数据来源 |
|-----|------|------|---------|
| region_code | TEXT | 地区板块代码 (主键)，如 `880207.TDX` | tdx_index.ts_code |
| region_name | TEXT | 地区名称，如 `北京地区` | tdx_index.name |
| idx_type | TEXT | 板块类型，如 `地区板块` | tdx_index.idx_type |
| idx_count | INTEGER | 成分股个数 | tdx_index.idx_count |
| total_share | REAL | 总股本(亿) | tdx_index.total_share |
| float_share | REAL | 流通股(亿) | tdx_index.float_share |
| total_mv | REAL | 总市值(亿元) | tdx_index.total_mv |
| float_mv | REAL | 流通市值(亿元) | tdx_index.float_mv |
| trade_date | TEXT | 交易日期 (YYYYMMDD) | tdx_index.trade_date |

**主键**: `region_code`

### stock_region - 股票地区关系

| 字段 | 类型 | 说明 | 数据来源 |
|-----|------|------|---------|
| ts_code | TEXT | 股票代码，如 `000001.SZ` | tdx_member.con_code |
| name | TEXT | 股票名称，如 `平安银行` | tdx_member.con_name |
| region_code | TEXT | 地区板块代码，如 `880207.TDX` | 查询参数 |
| region_name | TEXT | 地区名称，如 `北京地区` | 查询参数 |

**主键**: `(ts_code, region_code)`

---

## 模糊查询表

### fuzzy_search - 统一模糊查询表

用于通过名称快速查找股票、概念、行业、地区等。

**数据来源**: 从 `stock_basic`、`concept_board`、`industry_board`、`region_board` 收集

| 字段 | 类型 | 说明 | 示例 |
|-----|------|------|------|
| id | INTEGER | 自增主键 | 1 |
| name | TEXT | 名称 | `贵州茅台` |
| name_pinyin | TEXT | 拼音首字母 | `gzmj` |
| name_short | TEXT | 简称 | `贵州` |
| item_type | TEXT | 类型 | `stock/concept/industry/region` |
| code | TEXT | 代码 | `600519.SH` |
| extra | TEXT | 额外信息 | NULL |

**索引**:
- `idx_fuzzy_name` - 按名称索引
- `idx_fuzzy_name_pinyin` - 按拼音索引
- `idx_fuzzy_name_short` - 按简称索引
- `idx_fuzzy_type` - 按类型索引

---

## 热点历史

### topic_history - 热点监控历史记录

用于记录热点监控面板中添加的历史热点。系统通过 `concept_codes` 自动关联板块和股票。

| 字段 | 类型 | 说明 | 示例 |
|-----|------|------|------|
| id | INTEGER | 自增主键 | 1 |
| name | TEXT | 热点名称（用户定义），如 `AI概念` | `AI概念` |
| concept_codes | TEXT | 关联板块代码，JSON数组格式 | `["BK1173","BK0800"]` |
| board_names | TEXT | 板块名称，JSON数组格式（自动从 concept_board 填充） | `["人工智能","AI大模型"]` |
| news | TEXT | 利好/刺激性消息（最多500字） | `政策支持人工智能发展...` |
| stock_codes | TEXT | 关联股票代码，JSON数组格式 | `["600519.SH","000001.SZ"]` |
| stock_names | TEXT | 关联股票名称，JSON数组格式 | `["贵州茅台","平安银行"]` |
| created_at | INTEGER | 创建时间（ms级Unix时间戳） | `1774800853262` |
| updated_at | INTEGER | 更新时间（ms级Unix时间戳），无则 NULL | `1774800853262` |

**注意**: `created_at` 和 `updated_at` 存储为 ms 时间戳（INTEGER），返回时自动转为 `YYYYMMDD HHMMSS` 字符串格式。

**数据流**：用户输入 `name` → 系统通过 `name` 模糊匹配 `concept_board` 填充 `concept_codes` 和 `board_names` → 通过 `concept_codes` 查询 `stock_concept` 填充 `stock_codes` 和 `stock_names`

**注意**: `concept_codes`、`board_names`、`stock_codes`、`stock_names` 字段存储为 JSON 字符串，解析时应使用 `json.loads()`。

---

## 索引

以下索引用于加速查询：

```sql
CREATE INDEX idx_daily_date ON daily(trade_date);
CREATE INDEX idx_daily_basic_date ON daily_basic(trade_date);
CREATE INDEX idx_income_period ON income(period);
CREATE INDEX idx_balancesheet_period ON balancesheet(period);
CREATE INDEX idx_cashflow_period ON cashflow(period);
CREATE INDEX idx_stock_concept_ts_code ON stock_concept(ts_code);
CREATE INDEX idx_stock_concept_name ON stock_concept(concept_name);
CREATE INDEX idx_stock_industry_ts_code ON stock_industry(ts_code);
CREATE INDEX idx_stock_industry_name ON stock_industry(industry_name);
CREATE INDEX idx_stock_region_ts_code ON stock_region(ts_code);
CREATE INDEX idx_stock_region_name ON stock_region(region_name);
CREATE INDEX idx_topic_created ON topic_history(created_at DESC);
CREATE INDEX idx_topic_name ON topic_history(name);
```
