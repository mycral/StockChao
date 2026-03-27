# MarketInfo - A股数据仓库

本地化的 A股历史数据仓库，支持 Tushare Pro 和 Akshare 双数据源，自动降级。

## 功能特性

- **双数据源**：优先 Akshare（免费），失败自动降级 Tushare
- **多数据类型**：日线、分钟线、财务数据、概念/行业/地区板块
- **SQLite 本地存储**：无需外部数据库
- **增量同步**：自动跳过已有数据
- **统一查询接口**：支持命令行和代码调用
- **MCP 服务**：支持大模型调用

## 目录结构

```
MarketInfo/
├── config.py                  # 配置文件
├── main.py                   # 主入口
├── requirements.txt          # 依赖
│
├── core/                    # 核心模块
│   ├── database.py          # 数据库初始化/建表
│   ├── query.py            # 数据查询接口
│   ├── field_format.py     # 字段格式规范（ts_code, concept_code 等）
│   ├── data_source.py      # 数据源抽象基类
│   ├── data_source_tushare.py   # Tushare 适配器
│   ├── data_source_akshare.py  # Akshare 适配器
│   ├── data_source_concept.py  # 概念/行业/地区板块适配器
│   └── data_fetcher.py     # 统一数据获取器
│
├── sync/                    # 同步脚本
│   └── sync.py             # 增量同步
│
├── mcp_server/              # MCP 服务器
│   ├── server.py          # MCP 服务主入口
│   ├── tools/             # MCP 工具
│   │   ├── search.py      # 搜索工具
│   │   ├── stock.py      # 股票查询工具
│   │   ├── board.py      # 板块查询工具
│   │   └── topic.py      # 热点监控工具
│   └── prompts/          # 分析提示模板
│
├── tools/                  # 独立工具
│   ├── db_status.py       # 数据库状态查看
│   └── test_server.py     # 服务器测试
│
├── viewer/                 # 可视化工具
│   ├── kline_viewer.py    # K线查看器
│   └── screen_three_up.py # 三连阳选股
│
├── skills/                 # 选股技能
│   ├── skill_base.py
│   ├── skill_manager.py
│   └── ...
│
└── data/                  # 数据文件
    ├── MarketInfo.db      # SQLite 数据库
    └── skill_results/     # 选股结果
```

---

## 命令详解

所有命令均通过 `python main.py <command>` 调用。

### 1. init - 初始化数据库

创建数据库表结构，并下载股票列表。

```bash
python main.py init
```

**输出示例：**
```
初始化数据库...
创建表: stock_basic
创建表: daily
...
数据库创建完成
下载股票列表...
获取到 5493 只股票

初始化完成!
```

---

### 2. sync - 增量同步日线数据

多线程增量同步所有股票的日线数据（优先 Akshare）。

```bash
python main.py sync
```

**输出示例：**
```
==================================================
Tushare 镜像库 - 增量同步（DataFetcher + 多线程）
并发线程数: 5, 最大重试: 3
优先 akshare，失败后降级 tushare
==================================================
最新交易日: 20260327

------------------------------
同步日线数据（5 线程，仅用 akshare）...
   000001.SZ 平安银行 +1条
   000002.SZ 万科A +2条
   ...
日线同步完成: 成功 500, 跳过 4993, 失败 0

同步完成!
```

**特点：**
- 5 线程并发
- 自动跳过已同步的数据（根据本地最新日期判断）
- 实时打印每只股票的同步状态

---

### 3. update - 更新镜像库

更新股票列表 + 增量同步日线数据。

```bash
python main.py update
```

相当于依次执行：
1. `python main.py download --type stock_basic`
2. `python main.py sync`

---

### 4. download - 下载数据

下载指定类型的数据，支持单只股票或批量下载。

#### 4.1 下载股票列表

```bash
python main.py download --type stock_basic
```

#### 4.2 下载单只股票日线

```bash
python main.py download --type daily --code 601988.SH --start 20200101 --end 20260327
```

**参数说明：**
| 参数 | 说明 |
|-----|------|
| `--type` | 数据类型 |
| `--code` / `-c` | 股票代码（如 `601988.SH`、`002131.SZ`） |
| `--start` / `-s` | 开始日期（YYYYMMDD） |
| `--end` / `-e` | 结束日期（YYYYMMDD） |
| `--replace` / `-r` | 是否替换已有数据 |

#### 4.3 下载每日指标

```bash
python main.py download --type daily_basic --code 601988.SH
```

#### 4.4 下载复权因子

```bash
python main.py download --type adj_factor --code 601988.SH
```

#### 4.5 下载分钟数据

```bash
python main.py download --type minute --code 601988.SH --start 20260301 --end 20260327
```

---

### 5. query - 查询数据

查询本地数据库中的数据。

#### 5.1 查询日线数据

```bash
python main.py query --code 601988.SH --type daily
python main.py query --code 601988.SH --type daily --start 20260301 --end 20260327
```

#### 5.2 查询每日指标

```bash
python main.py query --code 601988.SH --type daily_basic
```

#### 5.3 查询股票基本信息

```bash
python main.py query --code 601988.SH --type stock_basic
```

#### 5.4 查询股票所属概念

```bash
# 通过股票代码查询
python main.py query --code 002131.SZ --type concept

# 通过股票名称查询
python main.py query --name 利欧股份 --type concept
```

**输出示例：**
```
002131.SZ 所属概念板块 (33 个):
concept_code concept_name
      BK0447        互联医疗
      BK0506        直播概念
      BK0568        中证500
      ...
```

#### 5.5 查询概念成分股

```bash
# 通过概念名称查询
python main.py query --name AI概念 --type concept_stocks

# 通过概念代码查询
python main.py query --code BK1172 --type concept_stocks
```

**输出示例：**
```
概念 AI概念 成分股 (50 只):
  ts_code symbol  name
 002131.SZ  002131  利欧股份
 300124.SZ  300124  汇川技术
  ...
```

#### 5.6 查询所有概念板块

```bash
python main.py query --type concepts
```

**输出示例：**
```
所有概念板块 (483 个):
 rank concept_name concept_code  latest_price  pct_chg  up_count  down_count
    1       锂矿概念     BK1173      2256.70     5.52        37           2
    2       单抗概念     BK0870      1751.70     5.01        49           0
    3       阿兹海默     BK0894      2076.35     4.96        20           0
    ...
```

---

### 6. concept - 更新概念板块数据

从 Akshare 获取概念板块和成分股数据。

#### 6.1 更新所有概念板块

```bash
python main.py concept
```

**输出示例：**
```
==================================================
更新所有概念板块数据...
==================================================

[1/2] 更新概念板块列表...
   获取到 483 个概念
   已写入 concept_board 表

[2/2] 更新概念成分股（5线程）...
   锂矿概念: 39 只股票
   单抗概念: 45 只股票
   ...
概念成分股更新完成: 成功 483, 失败 0, 共 21000 条
```

#### 6.2 更新指定概念

```bash
python main.py concept --name 锂矿概念
```

---

### 7. industry - 更新行业板块数据

从 Akshare 获取行业板块和成分股数据。

#### 7.1 更新所有行业板块

```bash
python main.py industry
```

**输出示例：**
```
==================================================
更新所有行业板块数据...
==================================================

[1/2] 更新行业板块列表...
   获取到 86 个行业
   已写入 industry_board 表

[2/2] 更新行业成分股（5线程）...
   银行: 42 只股票
   房地产: 132 只股票
   ...
行业成分股更新完成: 成功 86, 失败 0, 共 5000+ 条
```

#### 7.2 更新指定行业

```bash
python main.py industry --name 银行
```

---

### 8. region - 更新地区板块数据

从 Tushare 通达信接口获取地区板块和成分股数据。

#### 8.1 更新所有地区板块

```bash
python main.py region
python main.py region --date 20260327
```

**输出示例：**
```
==================================================
更新所有地区板块数据...
==================================================

[1/2] 获取地区板块列表...
   获取到 32 个地区
   已写入 region_board 表

[2/2] 更新地区成分股（5线程）...
   北京地区: 484 只股票
   上海地区: 378 只股票
   ...
地区成分股更新完成: 成功 32, 失败 0, 共 15000+ 条
```

#### 8.2 更新指定地区

```bash
python main.py region --name 北京
```

---

**数据来源**: Tushare `tdx_index` 和 `tdx_member` 接口
- 地区板块信息: `tdx_index(idx_type='地区板块')`
- 地区成分股: `tdx_member(ts_code='880207.TDX')`

#### 8.2 更新指定地区

```bash
python main.py region --name 浙江
```

---

### 9. rebuild_fuzzy_search - 重建模糊查询表

重建 fuzzy_search 表，用于通过名称快速查找股票、概念、行业、地区。

```bash
python main.py rebuild_fuzzy_search
```

**输出示例：**
```
==================================================
重建模糊查询表
==================================================

清空现有数据...
  已清空 fuzzy_search 表

收集各表数据...
  收集到 5800 条记录

写入数据库...
  写入完成

按类型统计:
  stock: 5000 条
  concept: 483 条
  industry: 86 条
  region: 32 条

==================================================
模糊查询表重建完成!
==================================================

演示查询（关键词 '贵州'）:
   name  name_pinyin  ...    item_type         code
0  贵州茅台       gzmj  ...        stock   600519.SH
1  贵州百灵       gzbl  ...        stock   002424.SH
```

---

## 模糊查询表详解

### 表结构

```sql
fuzzy_search (
    id INTEGER PRIMARY KEY,      -- 自增ID
    name TEXT NOT NULL,          -- 原始名称
    name_pinyin TEXT,           -- 拼音首字母
    name_short TEXT,             -- 简称
    item_type TEXT NOT NULL,     -- 类型: stock/concept/industry/region
    code TEXT NOT NULL,          -- 代码
    extra TEXT                   -- 备用字段
)
```

### 数据来源

| 源表 | 收集字段 | 示例 |
|-----|---------|------|
| stock_basic | ts_code, name | 600519.SH, 贵州茅台 |
| concept_board | concept_code, concept_name | BK0447, 互联医疗 |
| industry_board | industry_code, industry_name | BK1621, 银行 |
| region_board | ts_code, name | 880207.TDX, 北京地区 |

### 辅助字段生成算法

#### 1. name_pinyin（拼音首字母）

```python
def _to_pinyin(name: str) -> str:
    # 使用 pypinyin 库
    "贵州茅台" → ["gu", "zhou", "mao", "tai"]
    # 取首字母拼接: "gzmj"
```

#### 2. name_short（简称）

```python
def _to_short_name(name: str) -> str:
    # 去掉括号及其内容
    "贵州茅台 (600519)" → "贵州茅台"
    # 取前4个字符
    "贵州茅台" → "贵州"
```

### 查询算法

```python
def fuzzy_search(keyword, item_type=None, limit=20):
    # 在3个字段上模糊匹配
    WHERE name LIKE '%keyword%'        -- 原始名称
       OR name_pinyin LIKE '%keyword%' -- 拼音首字母
       OR name_short LIKE '%keyword%'  -- 简称
```

**匹配示例：**

| 关键词 | 匹配字段 | 匹配结果 |
|-------|---------|---------|
| `贵州` | name | 贵州茅台、贵州百灵 |
| `gzmj` | name_pinyin | 贵州茅台 |
| `贵州茅` | name_short | 贵州茅台 |

### 索引优化

```sql
CREATE INDEX idx_fuzzy_name ON fuzzy_search(name);
CREATE INDEX idx_fuzzy_name_pinyin ON fuzzy_search(name_pinyin);
CREATE INDEX idx_fuzzy_name_short ON fuzzy_search(name_short);
CREATE INDEX idx_fuzzy_type ON fuzzy_search(item_type);
```

### 更新流程

```bash
# 1. 更新各源表数据
python main.py concept    # 更新概念板块
python main.py industry   # 更新行业板块
python main.py region     # 更新地区板块

# 2. 重建模糊查询表（先清空，再收集）
python main.py rebuild_fuzzy_search
```

### API 调用示例

```python
from core.query import QueryDB
from config import DB_PATH

with QueryDB(DB_PATH) as q:
    # 模糊搜索
    result = q.fuzzy_search('贵州')
    # result: 贵州茅台(stock), 贵州百灵(stock), ...

    # 按类型过滤
    result = q.fuzzy_search('银行', item_type='industry')
    # result: 银行(industry)

    # 获取代码后查询具体数据
    result = q.fuzzy_search('茅台')
    if len(result) > 0:
        code = result.iloc[0]['code']  # '600519.SH'
        item_type = result.iloc[0]['item_type']  # 'stock'
```

### 代码开发注意事项

1. **name_pinyin 依赖 pypinyin 库**，如未安装则返回空字符串
2. **name_short 最大长度为4个字符**，超过截断
3. **查询使用 LIKE '%keyword%'**，性能较差，避免在大数据量场景频繁查询
4. **item_type 可选值**: `stock`, `concept`, `industry`, `region`
5. **重建前需确保源表已有数据**，否则 fuzzy_search 为空

---

## 命令汇总表

| 命令 | 说明 | 关键参数 |
|-----|------|---------|
| `init` | 初始化数据库 | - |
| `sync` | 增量同步日线数据 | - |
| `update` | 更新股票列表+同步 | - |
| `download` | 下载指定数据 | `--type`, `--code`, `--start`, `--end` |
| `query` | 查询数据 | `--type`, `--code`, `--name` |
| `concept` | 更新概念板块 | `--name` |
| `industry` | 更新行业板块 | `--name` |
| `region` | 更新地区板块 | `--name` |
| `rebuild_fuzzy_search` | 重建模糊查询表 | - |

---

## 数据类型说明

| 类型 | 说明 | 支持的参数 |
|-----|------|----------|
| `daily` | 日线数据 | `--code`, `--start`, `--end` |
| `daily_basic` | 每日指标 | `--code`, `--start`, `--end` |
| `stock_basic` | 股票列表 | - |
| `adj_factor` | 复权因子 | `--code`, `--start`, `--end` |
| `minute` | 分钟数据 | `--code`, `--start`, `--end` |
| `concept` | 股票概念 | `--code` 或 `--name` |
| `concept_stocks` | 概念成分股 | `--code` 或 `--name` |
| `concepts` | 所有概念板块 | - |
| `industry` | 股票行业 | `--code` 或 `--name` |
| `industry_stocks` | 行业成分股 | `--code` 或 `--name` |
| `industries` | 所有行业板块 | - |
| `region` | 股票地区 | `--code` 或 `--name` |
| `region_stocks` | 地区成分股 | `--code` 或 `--name` |
| `regions` | 所有地区板块 | - |

---

## 配置说明

配置文件：`config.py`

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `DB_PATH` | `data/MarketInfo.db` | 数据库路径 |
| `DAILY_START_DATE` | `20200101` | 日线数据起始日期 |
| `MINUTE_START_DATE` | `20200101` | 分钟数据起始日期 |
| `TUSHARE_TOKEN` | 环境变量 | Tushare Pro Token |
| `TUSHARE_HTTP_URL` | 第三方接口 | Tushare 镜像地址 |

---

## 数据库表结构

详细表结构请参考 [DB_TABLES.md](DB_TABLES.md)。

---

## MCP 服务器

MCP 服务器供大模型调用 MarketInfo 数据库。

### 数据来源

- **主数据源**: Akshare (免费开源)
- **备份数据源**: Tushare Pro (需 token)
- **数据内容**: 股票列表、日线数据、概念板块、行业板块、地区板块

### 安装

```bash
pip install -r requirements_mcp.txt
```

### 启动

```bash
# 方式1: 使用 Python 模块 (默认端口 9876)
python -m mcp_server.server

# 方式2: 直接运行
python mcp_server/server.py

# 自定义端口
python -m mcp_server.server --port 8080
```

服务地址: `http://127.0.0.1:9876/mcp`

### 工具列表

| 类别 | 工具 | 说明 |
|-----|------|------|
| 搜索 | `fuzzy_search` | 模糊搜索（股票/概念/行业/地区） |
| 搜索 | `search_stocks` | 搜索股票 |
| 搜索 | `search_concepts` | 搜索概念板块 |
| 搜索 | `search_industries` | 搜索行业板块 |
| 搜索 | `search_regions` | 搜索地区板块 |
| 股票 | `get_stock_info` | 获取股票基本信息 |
| 股票 | `get_stock_daily` | 获取股票日线数据 |
| 股票 | `get_stock_concepts` | 获取股票概念板块 |
| 股票 | `get_stock_industries` | 获取股票行业板块 |
| 股票 | `get_stock_regions` | 获取股票地区板块 |
| 板块 | `get_all_concepts` | 获取所有概念板块 |
| 板块 | `get_all_industries` | 获取所有行业板块 |
| 板块 | `get_all_regions` | 获取所有地区板块 |
| 板块 | `get_concept_stocks` | 获取概念成分股 |
| 板块 | `get_industry_stocks` | 获取行业成分股 |
| 板块 | `get_region_stocks` | 获取地区成分股 |
| 热点 | `add_topic_history` | 记录热点到历史列表 |
| 热点 | `get_topic_history` | 获取历史热点列表 |
| 热点 | `get_latest_topics` | 获取当日热门热点 |

详细文档请参考 [mcp_server/README.md](mcp_server/README.md)。

---

## 注意事项

1. **数据源优先级**：日线和分钟数据优先使用 Akshare（免费），失败后降级到 Tushare
2. **增量同步**：自动根据本地最新日期跳过已有数据
3. **概念数据**：存储在 `concept_board` 和 `stock_concept` 表，需通过 `python main.py concept` 更新
4. **行业数据**：存储在 `industry_board` 和 `stock_industry` 表，需通过 `python main.py industry` 更新
5. **地区数据**：存储在 `region_board` 和 `stock_region` 表，需通过 `python main.py region` 更新
6. **模糊查询**：更新板块数据后需运行 `python main.py rebuild_fuzzy_search` 重建模糊搜索表
7. **数据库路径**：默认为 `data/MarketInfo.db`，约 4GB
8. **MCP 只读**：MCP 服务仅提供数据查询，不提供数据写入

---

## 常见问题

**Q: 提示 "每分钟访问接口1次权限的权利"？**
A: Tushare API 限流，DataFetcher 会自动降级到 Akshare 获取数据。

**Q: 下载中断怎么办？**
A: 使用 `python main.py sync` 进行增量同步，会自动从断点继续。

**Q: 如何清理数据库？**
A: 删除 `data/MarketInfo.db` 文件，然后重新 `python main.py init`。

**Q: 概念数据是空白的？**
A: 运行 `python main.py concept` 更新概念板块数据。
