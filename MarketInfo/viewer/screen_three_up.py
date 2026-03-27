# -*- coding: utf-8 -*-
"""
三连阳选股脚本
筛选连续三天上涨的股票，保存到自选股列表
暂时不维护了。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import sqlite3
import pandas as pd
from config import DB_PATH

def screen_three_consecutive_up(days=3):
    """筛选连续N天上涨的股票

    Args:
        days: 连续上涨天数，默认3天

    Returns:
        符合条件的股票列表 DataFrame
    """
    conn = sqlite3.connect(DB_PATH)

    # 获取所有股票的最新数据（按日期排序）
    sql = """
        SELECT ts_code, trade_date, close, pct_chg
        FROM daily
        ORDER BY ts_code, trade_date DESC
    """
    df = pd.read_sql_query(sql, conn)

    if df.empty:
        print("数据库中无日线数据")
        conn.close()
        return pd.DataFrame()

    conn.close()

    # 按股票分组，找出连续上涨的股票
    results = []

    for ts_code, group in df.groupby('ts_code'):
        # 按日期降序排列（最近的在前面）
        group = group.sort_values('trade_date', ascending=False)

        # 检查是否连续N天上涨
        consecutive_up = 0
        for _, row in group.head(days).iterrows():
            if row['pct_chg'] > 0:
                consecutive_up += 1
            else:
                break

        if consecutive_up >= days:
            # 获取股票名称
            conn2 = sqlite3.connect(DB_PATH)
            name_sql = "SELECT name FROM stock_basic WHERE ts_code = ?"
            name_df = pd.read_sql_query(name_sql, conn2, params=[ts_code])
            conn2.close()

            name = name_df.iloc[0]['name'] if len(name_df) > 0 else 'Unknown'

            # 获取最新价格和涨幅
            latest = group.iloc[0]
            results.append({
                'ts_code': ts_code,
                'name': name,
                'latest_date': latest['trade_date'],
                'close': latest['close'],
                'pct_chg': latest['pct_chg'],
                'consecutive_days': consecutive_up
            })

    result_df = pd.DataFrame(results)

    if len(result_df) > 0:
        # 按连续上涨天数降序，然后按涨幅降序
        result_df = result_df.sort_values(['consecutive_days', 'pct_chg'], ascending=[False, False])

    return result_df


def save_to_watchlist(result_df, watchlist_file):
    """保存到自选股列表

    Args:
        result_df: 选股结果
        watchlist_file: 自选股文件路径
    """
    if result_df.empty:
        print("没有符合条件的股票")
        return

    # 保存到CSV（格式：ts_code, name）
    watchlist_df = result_df[['ts_code', 'name']].copy()
    watchlist_df.to_csv(watchlist_file, index=False)
    print(f"已保存 {len(watchlist_df)} 只股票到自选股列表: {watchlist_file}")


if __name__ == '__main__':
    import os

    watchlist_file = os.path.join(os.path.dirname(__file__), 'watchlist.csv')

    print("=" * 50)
    print("三连阳选股")
    print("=" * 50)

    # 筛选三连阳
    result = screen_three_consecutive_up(days=3)

    if result.empty:
        print("没有找到三连阳的股票")
    else:
        print(f"\n找到 {len(result)} 只三连阳股票:")
        print("-" * 60)
        for _, row in result.head(20).iterrows():
            print(f"  {row['ts_code']} {row['name']:8} | "
                  f"最新: {row['close']:.2f} | "
                  f"涨幅: {row['pct_chg']:+.2f}% | "
                  f"连续上涨: {row['consecutive_days']} 天")

        if len(result) > 20:
            print(f"  ... 还有 {len(result) - 20} 只")

        # 保存到自选股
        save_to_watchlist(result, watchlist_file)

        print("\n现在可以运行 kline_viewer.py 查看K线图")
