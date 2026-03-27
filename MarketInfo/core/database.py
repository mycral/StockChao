# -*- coding: utf-8 -*-
"""
Tushare 镜像库 - 数据库初始化
"""
import sqlite3
import os


# 建表 SQL
CREATE_TABLES_SQL = {
    'stock_basic': '''
        CREATE TABLE IF NOT EXISTS stock_basic (
            ts_code TEXT PRIMARY KEY,
            symbol TEXT,
            name TEXT,
            area TEXT,
            industry TEXT,
            market TEXT,
            list_date TEXT,
            delist_date TEXT,
            is_hs TEXT,
            latest_price REAL
        )
    ''',

    'daily': '''
        CREATE TABLE IF NOT EXISTS daily (
            ts_code TEXT,
            trade_date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            pre_close REAL,
            change REAL,
            pct_chg REAL,
            vol REAL,
            amount REAL,
            PRIMARY KEY (ts_code, trade_date)
        )
    ''',

    'daily_basic': '''
        CREATE TABLE IF NOT EXISTS daily_basic (
            ts_code TEXT,
            trade_date TEXT,
            close REAL,
            turnover_rate REAL,
            turnover_rate_f REAL,
            volume_ratio REAL,
            pe REAL,
            pe_ttm REAL,
            pb REAL,
            ps REAL,
            ps_ttm REAL,
            dv_ratio REAL,
            dv_ttm REAL,
            total_share REAL,
            float_share REAL,
            free_share REAL,
            total_mv REAL,
            circ_mv REAL,
            PRIMARY KEY (ts_code, trade_date)
        )
    ''',

    'adj_factor': '''
        CREATE TABLE IF NOT EXISTS adj_factor (
            ts_code TEXT,
            trade_date TEXT,
            adj_factor REAL,
            PRIMARY KEY (ts_code, trade_date)
        )
    ''',

    'weekly': '''
        CREATE TABLE IF NOT EXISTS weekly (
            ts_code TEXT,
            trade_date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            pre_close REAL,
            change REAL,
            pct_chg REAL,
            vol REAL,
            amount REAL,
            PRIMARY KEY (ts_code, trade_date)
        )
    ''',

    'monthly': '''
        CREATE TABLE IF NOT EXISTS monthly (
            ts_code TEXT,
            trade_date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            pre_close REAL,
            change REAL,
            pct_chg REAL,
            vol REAL,
            amount REAL,
            PRIMARY KEY (ts_code, trade_date)
        )
    ''',

    'income': '''
        CREATE TABLE IF NOT EXISTS income (
            ts_code TEXT,
            ann_date TEXT,
            f_ann_date TEXT,
            period TEXT,
            report_type INTEGER,
            comp_type INTEGER,
            basic_eps REAL,
            diluted_eps REAL,
            total_revenue REAL,
            revenue REAL,
            oper_income REAL,
            operate_profit REAL,
            total_profit REAL,
            net_profit REAL,
            income_tax REAL,
            n_income REAL,
            ebit REAL,
            ebitda REAL,
            PRIMARY KEY (ts_code, ann_date, period)
        )
    ''',

    'balancesheet': '''
        CREATE TABLE IF NOT EXISTS balancesheet (
            ts_code TEXT,
            ann_date TEXT,
            f_ann_date TEXT,
            period TEXT,
            report_type INTEGER,
            total_assets REAL,
            total_liab REAL,
            total_hldr_eqy_inc_min_int REAL,
            liab_payable REAL,
            total_current_assets REAL,
            total_current_liab REAL,
            PRIMARY KEY (ts_code, ann_date, period)
        )
    ''',

    'cashflow': '''
        CREATE TABLE IF NOT EXISTS cashflow (
            ts_code TEXT,
            ann_date TEXT,
            f_ann_date TEXT,
            period TEXT,
            report_type INTEGER,
            net_profit REAL,
            n_cashflow_act REAL,
            n_cashflow_inv_act REAL,
            n_cash_flows_fnc_act REAL,
            c_cash_equ_end_period REAL,
            PRIMARY KEY (ts_code, ann_date, period)
        )
    ''',

    # ==================== 概念板块表 ====================
    'concept_board': '''
        CREATE TABLE IF NOT EXISTS concept_board (
            concept_code TEXT PRIMARY KEY,
            concept_name TEXT,
            rank INTEGER,
            latest_price REAL,
            changeAmt REAL,
            pct_chg REAL,
            total_mv REAL,
            turnover_rate REAL,
            up_count INTEGER,
            down_count INTEGER,
            top_stock TEXT,
            top_stock_pct REAL
        )
    ''',

    'stock_concept': '''
        CREATE TABLE IF NOT EXISTS stock_concept (
            ts_code TEXT,
            symbol TEXT,
            name TEXT,
            concept_code TEXT,
            concept_name TEXT,
            PRIMARY KEY (ts_code, concept_code)
        )
    ''',

    # ==================== 行业板块表 ====================
    'industry_board': '''
        CREATE TABLE IF NOT EXISTS industry_board (
            industry_code TEXT PRIMARY KEY,
            industry_name TEXT,
            rank INTEGER,
            latest_price REAL,
            changeAmt REAL,
            pct_chg REAL,
            total_mv REAL,
            turnover_rate REAL,
            up_count INTEGER,
            down_count INTEGER,
            top_stock TEXT,
            top_stock_pct REAL
        )
    ''',

    'stock_industry': '''
        CREATE TABLE IF NOT EXISTS stock_industry (
            ts_code TEXT,
            symbol TEXT,
            name TEXT,
            industry_code TEXT,
            industry_name TEXT,
            PRIMARY KEY (ts_code, industry_code)
        )
    ''',

    # ==================== 地区板块表 ====================
    'region_board': '''
        CREATE TABLE IF NOT EXISTS region_board (
            region_code TEXT PRIMARY KEY,
            region_name TEXT,
            idx_type TEXT,
            idx_count INTEGER,
            total_share REAL,
            float_share REAL,
            total_mv REAL,
            float_mv REAL,
            trade_date TEXT
        )
    ''',

    'stock_region': '''
        CREATE TABLE IF NOT EXISTS stock_region (
            ts_code TEXT,
            symbol TEXT,
            name TEXT,
            region_code TEXT,
            region_name TEXT,
            PRIMARY KEY (ts_code, region_code)
        )
    ''',

    # ==================== 模糊查询表 ====================
    'fuzzy_search': '''
        CREATE TABLE IF NOT EXISTS fuzzy_search (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_pinyin TEXT,
            name_short TEXT,
            item_type TEXT NOT NULL,
            code TEXT NOT NULL,
            extra TEXT
        )
    ''',

    # ==================== 热点历史表 ====================
    'topic_history': '''
        CREATE TABLE IF NOT EXISTS topic_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            concept_codes TEXT,
            board_names TEXT,
            news TEXT,
            stock_codes TEXT,
            stock_names TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER
        )
    ''',
}

# 分钟数据表（不同周期）
MINUTE_TABLES = {
    '1min': 'minute_1min',
    '5min': 'minute_5min',
    '15min': 'minute_15min',
    '30min': 'minute_30min',
    '60min': 'minute_60min',
}

for freq, table_name in MINUTE_TABLES.items():
    CREATE_TABLES_SQL[table_name] = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            ts_code TEXT,
            trade_time TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            vol INTEGER,
            amount REAL,
            PRIMARY KEY (ts_code, trade_time)
        )
    '''


def create_database(db_path):
    """创建数据库和所有表

    Args:
        db_path: 数据库文件路径
    """
    # 确保目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建所有表
    for table_name, sql in CREATE_TABLES_SQL.items():
        print(f"创建表: {table_name}")
        cursor.execute(sql)

    # 创建索引（加速查询）
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_daily_date ON daily(trade_date)",
        "CREATE INDEX IF NOT EXISTS idx_daily_basic_date ON daily_basic(trade_date)",
        "CREATE INDEX IF NOT EXISTS idx_income_period ON income(period)",
        "CREATE INDEX IF NOT EXISTS idx_balancesheet_period ON balancesheet(period)",
        "CREATE INDEX IF NOT EXISTS idx_cashflow_period ON cashflow(period)",
        "CREATE INDEX IF NOT EXISTS idx_stock_concept_ts_code ON stock_concept(ts_code)",
        "CREATE INDEX IF NOT EXISTS idx_stock_concept_name ON stock_concept(concept_name)",
        "CREATE INDEX IF NOT EXISTS idx_stock_industry_ts_code ON stock_industry(ts_code)",
        "CREATE INDEX IF NOT EXISTS idx_stock_industry_name ON stock_industry(industry_name)",
        "CREATE INDEX IF NOT EXISTS idx_stock_region_ts_code ON stock_region(ts_code)",
        "CREATE INDEX IF NOT EXISTS idx_stock_region_name ON stock_region(region_name)",
        "CREATE INDEX IF NOT EXISTS idx_fuzzy_name ON fuzzy_search(name)",
        "CREATE INDEX IF NOT EXISTS idx_fuzzy_name_pinyin ON fuzzy_search(name_pinyin)",
        "CREATE INDEX IF NOT EXISTS idx_fuzzy_name_short ON fuzzy_search(name_short)",
        "CREATE INDEX IF NOT EXISTS idx_fuzzy_type ON fuzzy_search(item_type)",
        "CREATE INDEX IF NOT EXISTS idx_topic_created ON topic_history(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_topic_name ON topic_history(name)",
    ]

    for idx_sql in indexes:
        cursor.execute(idx_sql)

    conn.commit()
    conn.close()

    print(f"\n数据库创建完成: {db_path}")


def get_table_names(db_path):
    """获取数据库中所有表名

    Args:
        db_path: 数据库文件路径

    Returns:
        表名列表
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


if __name__ == '__main__':
    from config import DB_PATH
    create_database(DB_PATH)
    print("\n已创建的表:")
    for table in get_table_names(DB_PATH):
        print(f"  - {table}")
