# -*- coding: utf-8 -*-
"""
Tushare 镜像库 - 增量同步脚本（多线程版本，使用 DataFetcher）
优先 akshare，失败后降级 tushare
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.data_fetcher import DataFetcher
from config import DB_PATH

# 并发线程数
MAX_WORKERS = 5

# 最大重试次数
MAX_RETRIES = 3

# 重试等待时间（秒）
RETRY_WAIT = 2


def _call_with_retry(func, *args, **kwargs):
    """带重试的调用"""
    last_error = None
    for retry in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs), None
        except Exception as e:
            last_error = e
            if retry < MAX_RETRIES - 1:
                wait_time = RETRY_WAIT * (retry + 1) + random.uniform(0, 1)
                time.sleep(wait_time)
    return None, str(last_error)


def _get_latest_trade_date(db_path, table_name, ts_code=None, date_column='trade_date'):
    """获取表中最新日期"""
    conn = sqlite3.connect(db_path)
    try:
        if ts_code:
            cursor = conn.execute(f"SELECT MAX({date_column}) FROM {table_name} WHERE ts_code = ?", (ts_code,))
        else:
            cursor = conn.execute(f"SELECT MAX({date_column}) FROM {table_name}")
        result = cursor.fetchone()[0]
        return result
    finally:
        conn.close()


def _next_date(date_str):
    """获取日期字符串的下一天"""
    d = datetime.strptime(date_str, '%Y%m%d')
    return (d + timedelta(days=1)).strftime('%Y%m%d')


def _sync_single_daily(args):
    """同步单只股票日线数据，仅用 akshare"""
    code, name, db_path, latest_trade_date = args

    from core.data_source_akshare import AkshareSource
    akshare = AkshareSource()

    # 获取本地最新日期
    local_latest = _get_latest_trade_date(db_path, 'daily', ts_code=code, date_column='trade_date')
    local_date = local_latest if local_latest else '20200101'

    if local_date >= latest_trade_date:
        return code, name, 0, 'skipped'

    start_date = _next_date(local_date)

    try:
        df = akshare.get_daily(code, start_date, latest_trade_date)
    except Exception as e:
        return code, name, 0, str(e)

    if df is None or len(df) == 0:
        return code, name, 0, 'no_data'

    try:
        # 过滤出新增数据
        if local_latest:
            df = df[df['trade_date'] > local_latest]

        if len(df) == 0:
            return code, name, 0, 'skipped'

        conn = sqlite3.connect(db_path)
        df.to_sql('daily', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        return code, name, len(df), 'success'
    except Exception as e:
        return code, name, 0, str(e)


def _sync_single_daily_basic(args):
    """同步单只股票每日指标"""
    code, db_path, latest_trade_date = args

    fetcher = DataFetcher(db_path)

    local_latest = _get_latest_trade_date(db_path, 'daily_basic', ts_code=code, date_column='trade_date')
    local_date = local_latest if local_latest else '20200101'

    if local_date >= latest_trade_date:
        return code, 0, 'skipped'

    start_date = _next_date(local_date)

    df, error = _call_with_retry(
        fetcher.get_daily_basic, code, start_date, latest_trade_date, save=False
    )

    if error:
        return code, 0, error
    if df is None or len(df) == 0:
        return code, 0, 'no_data'

    try:
        if local_latest:
            df = df[df['trade_date'] > local_latest]

        if len(df) == 0:
            return code, 0, 'skipped'

        conn = sqlite3.connect(db_path)
        df.to_sql('daily_basic', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        return code, len(df), 'success'
    except Exception as e:
        return code, 0, str(e)


def _sync_single_adj_factor(args):
    """同步单只股票复权因子"""
    code, db_path, latest_trade_date = args

    fetcher = DataFetcher(db_path)

    local_latest = _get_latest_trade_date(db_path, 'adj_factor', ts_code=code, date_column='trade_date')
    local_date = local_latest if local_latest else '20200101'

    if local_date >= latest_trade_date:
        return code, 0, 'skipped'

    start_date = _next_date(local_date)

    df, error = _call_with_retry(
        fetcher.get_adj_factor, code, start_date, latest_trade_date, save=False
    )

    if error:
        return code, 0, error
    if df is None or len(df) == 0:
        return code, 0, 'no_data'

    try:
        if local_latest:
            df = df[df['trade_date'] > local_latest]

        if len(df) == 0:
            return code, 0, 'skipped'

        conn = sqlite3.connect(db_path)
        df.to_sql('adj_factor', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        return code, len(df), 'success'
    except Exception as e:
        return code, 0, str(e)


def sync_all(db_path=None, max_workers=MAX_WORKERS):
    """同步所有数据（增量，多线程版本）"""
    if not db_path:
        db_path = DB_PATH

    print("=" * 50)
    print("Tushare 镜像库 - 增量同步（DataFetcher + 多线程）")
    print(f"并发线程数: {max_workers}, 最大重试: {MAX_RETRIES}")
    print("优先 akshare，失败后降级 tushare")
    print("=" * 50)

    # 获取最新交易日
    fetcher = DataFetcher(db_path)
    today = datetime.now().strftime('%Y%m%d')
    trade_cal = fetcher.get_trade_dates(today, today)

    if len(trade_cal) > 0 and trade_cal.iloc[0]['is_open'] == 1:
        latest_trade_date = today
    else:
        trade_cal = fetcher.get_trade_dates(
            (datetime.now() - timedelta(days=7)).strftime('%Y%m%d'), today
        )
        open_days = trade_cal[trade_cal['is_open'] == 1]
        if len(open_days) > 0:
            latest_trade_date = open_days.iloc[-1]['cal_date']
        else:
            print("无法获取交易日历")
            return

    print(f"最新交易日: {latest_trade_date}")
    print()

    # 同步日线数据
    _sync_daily_parallel(db_path, latest_trade_date, max_workers)

    print()
    print("同步完成!")


def _sync_daily_parallel(db_path, latest_trade_date, max_workers):
    """同步日线数据，多线程"""
    print("-" * 30)
    print(f"同步日线数据（{max_workers} 线程，仅用 akshare）...")

    conn = sqlite3.connect(db_path)
    stocks = pd.read_sql_query("SELECT ts_code, name FROM stock_basic", conn)
    conn.close()

    total = len(stocks)
    synced = 0
    skipped = 0
    failed = 0

    args_list = [(row['ts_code'], row.get('name', ''), db_path, latest_trade_date) for _, row in stocks.iterrows()]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_sync_single_daily, args): args[0] for args in args_list}

        for i, future in enumerate(as_completed(futures)):
            code, name, count, status = future.result()
            if status == 'success':
                synced += 1
                print(f"  {code} {name} +{count}条")
            elif status in ('skipped', 'no_data'):
                skipped += 1
            else:
                failed += 1
                if failed <= 5:
                    print(f"  失败 {code}: {status}")

            if (i + 1) % 500 == 0:
                print(f"进度: [{i+1}/{total}]")

    print(f"日线同步完成: 成功 {synced}, 跳过 {skipped}, 失败 {failed}")


def _sync_daily_basic_parallel(db_path, latest_trade_date, max_workers):
    """并行同步每日指标"""
    print("-" * 30)
    print("同步每日指标（多线程）...")

    conn = sqlite3.connect(db_path)
    stocks = pd.read_sql_query("SELECT ts_code FROM stock_basic", conn)
    conn.close()

    total = len(stocks)
    synced = 0
    skipped = 0
    failed = 0

    args_list = [(row['ts_code'], db_path, latest_trade_date) for _, row in stocks.iterrows()]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_sync_single_daily_basic, args): args[0] for args in args_list}

        for i, future in enumerate(as_completed(futures)):
            code, count, status = future.result()
            if status == 'success':
                synced += 1
            elif status in ('skipped', 'no_data'):
                skipped += 1
            else:
                failed += 1

            if (i + 1) % 500 == 0:
                print(f"进度: [{i+1}/{total}]")

    print(f"每日指标同步完成: 成功 {synced}, 跳过 {skipped}, 失败 {failed}")


def _sync_adj_factor_parallel(db_path, latest_trade_date, max_workers):
    """并行同步复权因子"""
    print("-" * 30)
    print("同步复权因子（多线程）...")

    conn = sqlite3.connect(db_path)
    stocks = pd.read_sql_query("SELECT ts_code FROM stock_basic", conn)
    conn.close()

    total = len(stocks)
    synced = 0
    skipped = 0
    failed = 0

    args_list = [(row['ts_code'], db_path, latest_trade_date) for _, row in stocks.iterrows()]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_sync_single_adj_factor, args): args[0] for args in args_list}

        for i, future in enumerate(as_completed(futures)):
            code, count, status = future.result()
            if status == 'success':
                synced += 1
            elif status in ('skipped', 'no_data'):
                skipped += 1
            else:
                failed += 1

            if (i + 1) % 500 == 0:
                print(f"进度: [{i+1}/{total}]")

    print(f"复权因子同步完成: 成功 {synced}, 跳过 {skipped}, 失败 {failed}")

    # 刷新最新股价
    print("-" * 30)
    print("刷新最新股价...")
    fetcher = DataFetcher(db_path)
    count = fetcher.refresh_latest_price()
    print(f"最新股价更新完成: {count} 只股票")


def sync_minute_1min(ts_code, start_date=None, end_date=None, db_path=None):
    """同步单只股票1分钟数据

    Args:
        ts_code: 股票代码，如 '000001.SZ'
        start_date: 开始日期，如 '20260301'，默认从 MINUTE_START_DATE 开始
        end_date: 结束日期，默认今天
        db_path: 数据库路径
    """
    from config import MINUTE_START_DATE

    if not db_path:
        db_path = DB_PATH

    fetcher = DataFetcher(db_path)

    if not start_date:
        start_date = MINUTE_START_DATE

    if not end_date:
        end_date = datetime.now().strftime('%Y%m%d')

    print(f"同步 {ts_code} 1分钟数据: {start_date} ~ {end_date}")

    local_latest = _get_latest_trade_date(db_path, 'minute_1min', ts_code=ts_code, date_column='trade_time')
    if local_latest:
        local_date = local_latest[:8]
        print(f"  本地已有数据到: {local_date}")
        if local_date >= end_date:
            print("  已是最新，无需同步")
            return

    df, error = _call_with_retry(
        fetcher.get_minute, ts_code, '1min', start_date, end_date, save=False
    )

    if error:
        print(f"  失败: {error}")
        return

    if df is None or len(df) == 0:
        print("  无数据")
        return

    # 过滤新增数据
    if local_latest:
        df = df[df['trade_time'] > local_latest]

    if len(df) == 0:
        print("  已是最新")
        return

    conn = sqlite3.connect(db_path)
    df.to_sql('minute_1min', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()

    print(f"  成功写入 {len(df)} 条数据")


if __name__ == '__main__':
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == 'min1':
        ts_code = sys.argv[2] if len(sys.argv) > 2 else None
        start_date = sys.argv[3] if len(sys.argv) > 3 else None
        end_date = sys.argv[4] if len(sys.argv) > 4 else None
        if not ts_code:
            print("用法: python sync.py min1 <股票代码> [开始日期] [结束日期]")
            print("示例: python sync.py min1 000001.SZ 20260301 20260325")
        else:
            sync_minute_1min(ts_code, start_date, end_date)
    else:
        sync_all()
