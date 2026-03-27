# -*- coding: utf-8 -*-
"""
数据库迁移脚本：将 region_board 表的 name 字段改为 region_name，ts_code 改为 region_code
以及 stock_region 表中对应的 name 字段
"""
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import DB_PATH


def migrate_region_field():
    """迁移 region_board 和 stock_region 表的 name 字段为 region_name"""
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查 region_board 表的实际列名
    cursor.execute("PRAGMA table_info(region_board)")
    region_board_cols = [col[1] for col in cursor.fetchall()]
    print(f"region_board 表现有列: {region_board_cols}")

    # 检查 stock_region 表的实际列名
    cursor.execute("PRAGMA table_info(stock_region)")
    stock_region_cols = [col[1] for col in cursor.fetchall()]
    print(f"stock_region 表现有列: {stock_region_cols}")

    # 迁移 region_board 表
    # 旧表: ts_code, trade_date, name, idx_type, idx_count, total_share, float_share, total_mv, float_mv
    # 新表: region_code, region_name, rank, latest_price, changeAmt, pct_chg, total_mv, turnover_rate,
    #       up_count, down_count, top_stock, top_stock_pct
    if 'name' in region_board_cols and 'region_name' not in region_board_cols:
        print("\n正在迁移 region_board 表: ts_code->region_code, name -> region_name")
        # 创建临时表，使用新结构
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS region_board_new (
                region_code TEXT PRIMARY KEY,
                region_name TEXT,
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
        """)
        # 复制数据: ts_code -> region_code, name -> region_name
        # 旧表没有的字段设为 NULL
        cursor.execute("""
            INSERT INTO region_board_new (region_code, region_name, rank, latest_price,
                changeAmt, pct_chg, total_mv, turnover_rate, up_count, down_count,
                top_stock, top_stock_pct)
            SELECT ts_code, name, idx_count, NULL, NULL, NULL,
                total_mv, NULL, NULL, NULL, NULL, NULL
            FROM region_board
        """)
        # 删除旧表
        cursor.execute("DROP TABLE region_board")
        # 重命名新表
        cursor.execute("ALTER TABLE region_board_new RENAME TO region_board")
        conn.commit()
        print("  region_board 表迁移完成")
    elif 'region_name' in region_board_cols:
        print("\nregion_board 表已经是 region_name 字段，无需迁移")
    else:
        print("\nregion_board 表没有 name 或 region_name 字段")

    # 迁移 stock_region 表
    # stock_region 表中 region_name 已经存在，只是 name 字段需要保留（这是股票名称）
    # 检查是否需要其他迁移
    if 'region_name' in stock_region_cols:
        print("\nstock_region 表已经有 region_name 字段，无需迁移 name（股票名称）")

    conn.close()
    print("\n迁移完成!")


if __name__ == '__main__':
    migrate_region_field()


if __name__ == '__main__':
    migrate_region_field()