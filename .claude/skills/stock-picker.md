# 选股技能

## 技能用途

当你被要求进行**数据库选股**（基于 tushare_mirror 数据库）时，加载此技能并按照本指南执行。

## 技能系统架构

```
tushare_mirror/
├── skills/                      # 技能目录
│   ├── skill_base.py           # 技能基类
│   ├── skill_manager.py        # 技能管理器
│   ├── three_consecutive_up_skill.py  # 三连阳技能
│   └── xxx_skill.py           # 其他技能
├── skill_results/              # 选股结果缓存
├── kline_viewer.py            # K线查看器
├── tushare.db                 # 数据库
└── ...
```

## 数据库表结构

| 表名 | 字段 | 说明 |
|------|------|------|
| stock_basic | ts_code, symbol, name, area, industry, market, list_date | 股票列表 |
| daily | trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount | 日线数据 |
| daily_basic | pe, pb, turnover_rate, volume_ratio, total_mv, circ_mv 等 | 每日指标 |

## 已有技能

使用前，先列出已有技能：

```bash
cd tushare_mirror && python -c "
from skills.skill_manager import SkillManager
m = SkillManager()
m.load_skills()
m.print_skills()
"
```

### 1. 三连阳 (three_consecutive_up_skill)

**描述**: 筛选连续N天上涨的股票

**参数**:
- consecutive_days: 连续上涨天数 (默认 3)
- min_pct_chg: 每日最小涨幅% (默认 0)
- max_results: 最大结果数量 (默认 100)

## 执行流程

### 步骤 1：理解用户需求

用户可能说：
- "帮我选三连阳的股票"
- "帮我选低PE低PB的股票"
- "帮我选成交量放大的股票"
- "帮我选xxx条件的股票"

### 步骤 2：检查是否有现成技能

运行命令查看已有技能：

```bash
cd "c:/Users/34475/Desktop/Work/同花顺选股代码/tushare_mirror" && python -c "
from skills.skill_manager import SkillManager
m = SkillManager()
m.load_skills()
m.print_skills()
"
```

### 步骤 3：执行选股

**使用已有技能**：

```bash
cd "c:/Users/34475/Desktop/Work/同花顺选股代码/tushare_mirror" && python -c "
from skills.skill_manager import SkillManager
m = SkillManager()
m.load_skills()
result = m.run_skill('三连阳', conditions={'consecutive_days': 3})
print(result)
"
```

**使用默认参数**：

```bash
cd "c:/Users/34475/Desktop/Work/同花顺选股代码/tushare_mirror" && python -c "
from skills.skill_manager import SkillManager
m = SkillManager()
m.load_skills()
result = m.run_skill('技能名称')
print(result)
"
```

### 步骤 4：创建新技能（如果没有合适的）

当没有现成技能时，需要创建新技能：

1. 使用 skill_manager 创建：

```bash
cd tushare_mirror && python -c "
from skills.skill_manager import SkillManager
m = SkillManager()
m.load_skills()
m.create_skill('技能名称', '技能描述', [
    {'name': 'param1', 'label': '参数1', 'type': 'number', 'default': 10},
])
"
```

2. 编辑生成的技能文件 `skills/xxx_skill.py`，实现 screen() 方法

3. 刷新技能列表：

```bash
cd tushare_mirror && python -c "
from skills.skill_manager import SkillManager
m = SkillManager()
m.load_skills()
m.print_skills()
"
```

### 步骤 5：返回结果

选股结果是一个 DataFrame，包含以下列：
- ts_code: 股票代码
- name: 股票名称
- latest_date: 最新日期
- close: 最新收盘价
- pct_chg: 涨跌幅
- 其他根据技能不同而异的列

**向用户展示结果**：

```
找到 X 只符合条件的股票：

| 代码 | 名称 | 最新价 | 涨幅 | 连续天数 |
|------|------|--------|------|---------|
| 000001.SZ | 平安银行 | 12.34 | +5.67% | 3天 |
| ... | ... | ... | ... | ... |
```

## 常用选股模式

### 1. 三连阳（已有技能）

```python
conditions = {'consecutive_days': 3}
result = m.run_skill('三连阳', conditions)
```

### 2. 自定义连续上涨

```python
conditions = {'consecutive_days': 5, 'min_pct_chg': 1}
result = m.run_skill('三连阳', conditions)
```

### 3. 直接编写 SQL 选股

当需要快速实现时，可以直接写 Python 脚本：

```python
import sqlite3
import pandas as pd
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)

# 示例：选 PE<20 的股票
sql = """
SELECT b.ts_code, b.name, d.close, db.pe, db.pb
FROM stock_basic b
INNER JOIN daily d ON b.ts_code = d.ts_code
INNER JOIN daily_basic db ON b.ts_code = db.ts_code AND d.trade_date = db.trade_date
WHERE d.trade_date = (SELECT MAX(trade_date) FROM daily)
AND db.pe > 0 AND db.pe < 20
ORDER BY db.pe
LIMIT 50
"""
result = pd.read_sql_query(sql, conn)
conn.close()
print(result)
```

## 重要注意事项

1. **数据库路径**: `c:/Users/34475/Desktop/Work/同花顺选股代码/tushare_mirror/tushare.db`

2. **日期格式**: trade_date 格式为 YYYYMMDD 字符串

3. **市净率/市盈率**: 在 daily_basic 表中，注意有些股票可能没有 PE/PB 数据

4. **结果数量限制**: 技能默认返回最多 100 条，可通过 max_results 参数调整

## 快速命令备忘

```bash
# 查看技能列表
cd tushare_mirror && python -c "from skills.skill_manager import SkillManager; m=SkillManager(); m.load_skills(); m.print_skills()"

# 运行技能
cd tushare_mirror && python -c "from skills.skill_manager import SkillManager; m=SkillManager(); m.load_skills(); r=m.run_skill('三连阳'); print(r)"

# 查看数据库状态
cd tushare_mirror && python db_status.py
```
