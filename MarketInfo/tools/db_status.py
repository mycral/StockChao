# -*- coding: utf-8 -*-
"""
数据库状态查看工具
显示每个表的最新数据日期和数据量
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import sqlite3
import pandas as pd
from datetime import datetime

# Windows 终端编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入配置获取数据库路径
from config import DB_PATH


def get_table_info(db_path):
    """获取数据库中所有表的信息

    Args:
        db_path: 数据库文件路径

    Returns:
        DataFrame，包含表名、行数、最新日期
    """
    conn = sqlite3.connect(db_path)

    # 获取所有表名
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    results = []

    for table in tables:
        # 获取行数
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]

        # 获取表结构，判断主键或日期列
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]

        # 尝试找日期列
        date_column = None
        for col in columns:
            col_lower = col.lower()
            if 'date' in col_lower or 'time' in col_lower or col_lower == 'period':
                date_column = col
                break

        # 获取最新日期
        latest_date = None
        if date_column:
            try:
                if date_column == 'period':
                    # 财报期间可能是 YYYYMM 或 YYYYMMDD 格式
                    sql = f"SELECT MAX({date_column}) FROM {table}"
                else:
                    sql = f"SELECT MAX({date_column}) FROM {table}"
                cursor.execute(sql)
                latest_date = cursor.fetchone()[0]
            except Exception:
                pass

        results.append({
            '表名': table,
            '行数': row_count,
            '最新数据日期': latest_date,
            '日期列': date_column or '-'
        })

    conn.close()
    return pd.DataFrame(results)


def print_table_status(db_path):
    """打印表格状态"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return

    print("=" * 70)
    print(f"数据库状态查看 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库路径: {db_path}")
    print(f"数据库大小: {os.path.getsize(db_path) / 1024 / 1024:.2f} MB")
    print("=" * 70)

    df = get_table_info(db_path)

    # 按行数降序排列
    df = df.sort_values('行数', ascending=False)

    print(f"\n{'表名':<20} {'行数':>12} {'最新数据日期':<12} {'日期列':<15}")
    print("-" * 70)

    for _, row in df.iterrows():
        row_count = f"{row['行数']:,}" if row['行数'] else '0'
        latest_date = row['最新数据日期'] or '-'
        print(f"{row['表名']:<20} {row['行数']:>12,} {str(latest_date):<12} {row['日期列']:<15}")

    print("-" * 70)
    print(f"共 {len(df)} 个表，总行数: {df['行数'].sum():,}")

    # 数据日期统计
    print("\n" + "=" * 70)
    print("各表最新数据日期汇总（用于判断数据更新状态）:")
    print("=" * 70)

    date_tables = df[df['最新数据日期'].notna()].sort_values('最新数据日期', ascending=False)
    for _, row in date_tables.iterrows():
        print(f"  {row['表名']:<20} 最新: {row['最新数据日期']}  ({row['行数']:,} 条)")


def get_detailed_status(db_path, table_name):
    """获取某个表的详细状态（最近几条数据）"""
    conn = sqlite3.connect(db_path)

    # 获取日期列
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]

    date_col = None
    for col in columns:
        if 'date' in col.lower() or 'time' in col.lower() or col.lower() == 'period':
            date_col = col
            break

    print(f"\n表 [{table_name}] 详细信息:")
    print(f"  行数: {pd.read_sql_query(f'SELECT COUNT(*) as cnt FROM {table_name}', conn)['cnt'][0]:,}")

    if date_col:
        df = pd.read_sql_query(
            f"SELECT * FROM {table_name} ORDER BY {date_col} DESC LIMIT 5",
            conn
        )
        print(f"  最近5条数据 ({date_col}):")
        print(df.to_string(index=False))
    else:
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
        print("  前5条数据:")
        print(df.to_string(index=False))

    conn.close()


if __name__ == '__main__':
    import sys

    print_table_status(DB_PATH)

    # 如果传了参数，显示指定表的详细信息
    if len(sys.argv) > 1:
        table = sys.argv[1]
        get_detailed_status(DB_PATH, table)
