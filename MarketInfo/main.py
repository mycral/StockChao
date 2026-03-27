# -*- coding: utf-8 -*-
"""
MarketInfo 主入口

用法:
    python main.py init                          # 初始化数据库
    python main.py download --type daily        # 下载数据
    python main.py sync                          # 增量同步日线
    python main.py update                        # 更新镜像库（更新股票列表 + 增量同步）
    python main.py query --code 601988.SH      # 查询数据
    python main.py concept                       # 更新所有概念板块
    python main.py concept --name 锂矿概念       # 更新指定概念
    python main.py industry                      # 更新所有行业板块
    python main.py industry --name 银行          # 更新指定行业
    python main.py region                        # 更新所有地区板块
    python main.py region --name 浙江            # 更新指定地区
    python main.py rebuild_fuzzy_search         # 重建模糊查询表
"""
import argparse
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(__file__))

from config import DB_PATH
from core import database, DataFetcher
from core.query import QueryDB
from core.data_source_concept import ConceptSource
from sync.sync import sync_all


def init_db():
    """初始化数据库"""
    print("初始化数据库...")
    database.create_database(DB_PATH)
    print("下载股票列表...")
    fetcher = DataFetcher()
    fetcher.get_stock_basic(save=True)
    print("\n初始化完成!")


def download_data(data_type, ts_code=None, start_date=None, end_date=None, replace=False):
    """下载数据"""
    fetcher = DataFetcher()

    if data_type == 'stock_basic':
        fetcher.get_stock_basic(save=True)
    elif data_type == 'daily':
        if not ts_code:
            print("错误: 需要指定 --code")
            return
        fetcher.get_daily(ts_code, start_date, end_date, save=True)
    elif data_type == 'daily_basic':
        if not ts_code:
            print("错误: 需要指定 --code")
            return
        fetcher.get_daily_basic(ts_code, start_date, end_date, save=True)
    elif data_type == 'adj_factor':
        if not ts_code:
            print("错误: 需要指定 --code")
            return
        fetcher.get_adj_factor(ts_code, start_date, end_date, save=True)
    elif data_type == 'minute':
        if not ts_code:
            print("错误: 需要指定 --code")
            return
        fetcher.get_minute(ts_code, '5min', start_date, end_date, save=True)
    elif data_type == 'all':
        print("=" * 50)
        print("开始下载全部数据...")
        print("=" * 50)

        # 1. 股票列表（如果没有）
        with QueryDB(DB_PATH) as q:
            count = q.get_stock_count()
        if count == 0:
            print("\n[1/4] 下载股票列表...")
            fetcher.get_stock_basic(save=True)

        # 2. 日线数据
        print("\n[2/4] 下载日线数据...")
        # 下载所有股票需要遍历，这里简化处理
        if ts_code:
            fetcher.get_daily(ts_code, start_date, end_date, save=True)

        # 3. 每日指标
        print("\n[3/4] 下载每日指标...")
        if ts_code:
            fetcher.get_daily_basic(ts_code, start_date, end_date, save=True)

        # 4. 复权因子
        print("\n[4/4] 下载复权因子...")
        if ts_code:
            fetcher.get_adj_factor(ts_code, start_date, end_date, save=True)

        print("\n" + "=" * 50)
        print("全部数据下载完成!")
        print("=" * 50)
    else:
        print(f"未知数据类型: {data_type}")
        print("可选: stock_basic, daily, daily_basic, adj_factor, minute, all")


def sync_data():
    """增量同步"""
    sync_all(DB_PATH)


def update_data():
    """更新镜像库（更新股票列表 + 增量同步）"""
    print("=" * 50)
    print("Tushare 镜像库 - 更新镜像")
    print("=" * 50)

    # 1. 更新股票列表
    print("\n[1/2] 更新股票列表...")
    fetcher = DataFetcher()
    fetcher.get_stock_basic(save=True)

    # 2. 增量同步
    print("\n[2/2] 增量同步数据...")
    sync_all(DB_PATH)

    print("\n" + "=" * 50)
    print("镜像库更新完成!")
    print("=" * 50)


def query_data(ts_code=None, start_date=None, end_date=None, data_type='daily', name=None):
    """查询数据

    Args:
        ts_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        data_type: 数据类型 (daily, daily_basic, stock_basic, concept)
        name: 股票名称（用于概念查询）
    """
    with QueryDB(DB_PATH) as q:
        if data_type == 'daily':
            if not ts_code:
                print("错误: 需要指定 --code")
                return
            df = q.get_daily(ts_code, start_date, end_date)
        elif data_type == 'daily_basic':
            if not ts_code:
                print("错误: 需要指定 --code")
                return
            df = q.get_daily_basic(ts_code, start_date, end_date)
        elif data_type == 'stock_basic':
            if not ts_code:
                print("错误: 需要指定 --code")
                return
            df = q.get_stock_basic(ts_code)
        elif data_type == 'concept':
            # 查询概念板块
            if ts_code:
                df = q.get_stock_concepts(ts_code=ts_code)
            elif name:
                df = q.get_stock_concepts(name=name)
            else:
                print("错误: 需要指定 --code 或 --name")
                return
            if df is not None and len(df) > 0:
                print(f"\n{ts_code or name} 所属概念板块 ({len(df)} 个):")
                print(df.to_string(index=False))
            else:
                print("无数据")
            return
        elif data_type == 'concept_stocks':
            # 查询概念的成分股
            if not ts_code and not name:
                print("错误: 需要指定 --code 或 --name")
                return
            if ts_code:
                df = q.get_concept_stocks(concept_code=ts_code)
                desc = f"概念 {ts_code}"
            else:
                df = q.get_concept_stocks(concept_name=name)
                desc = f"概念 {name}"
            if df is not None and len(df) > 0:
                print(f"\n{desc} 成分股 ({len(df)} 只):")
                print(df.to_string(index=False))
            else:
                print("无数据")
            return
        elif data_type == 'concepts':
            # 查询所有概念板块
            df = q.get_all_concepts()
            if df is not None and len(df) > 0:
                print(f"\n所有概念板块 ({len(df)} 个):")
                print(df.to_string(index=False))
            else:
                print("无数据")
            return
        elif data_type == 'industry':
            # 查询股票所属行业
            if ts_code:
                df = q.get_stock_industries(ts_code=ts_code)
            elif name:
                df = q.get_stock_industries(name=name)
            else:
                print("错误: 需要指定 --code 或 --name")
                return
            if df is not None and len(df) > 0:
                print(f"\n{ts_code or name} 所属行业板块 ({len(df)} 个):")
                print(df.to_string(index=False))
            else:
                print("无数据")
            return
        elif data_type == 'industry_stocks':
            # 查询行业板块的成分股
            if not ts_code and not name:
                print("错误: 需要指定 --code 或 --name")
                return
            if ts_code:
                df = q.get_industry_stocks(industry_code=ts_code)
                desc = f"行业 {ts_code}"
            else:
                df = q.get_industry_stocks(industry_name=name)
                desc = f"行业 {name}"
            if df is not None and len(df) > 0:
                print(f"\n{desc} 成分股 ({len(df)} 只):")
                print(df.to_string(index=False))
            else:
                print("无数据")
            return
        elif data_type == 'industries':
            # 查询所有行业板块
            df = q.get_all_industries()
            if df is not None and len(df) > 0:
                print(f"\n所有行业板块 ({len(df)} 个):")
                print(df.to_string(index=False))
            else:
                print("无数据")
            return
        elif data_type == 'region':
            # 查询股票所属地区
            if ts_code:
                df = q.get_stock_regions(ts_code=ts_code)
            elif name:
                df = q.get_stock_regions(name=name)
            else:
                print("错误: 需要指定 --code 或 --name")
                return
            if df is not None and len(df) > 0:
                print(f"\n{ts_code or name} 所属地区板块 ({len(df)} 个):")
                print(df.to_string(index=False))
            else:
                print("无数据")
            return
        elif data_type == 'region_stocks':
            # 查询地区板块的成分股
            if not ts_code and not name:
                print("错误: 需要指定 --code 或 --name")
                return
            if ts_code:
                df = q.get_region_stocks(region_code=ts_code)
                desc = f"地区 {ts_code}"
            else:
                df = q.get_region_stocks(region_name=name)
                desc = f"地区 {name}"
            if df is not None and len(df) > 0:
                print(f"\n{desc} 成分股 ({len(df)} 只):")
                print(df.to_string(index=False))
            else:
                print("无数据")
            return
        elif data_type == 'regions':
            # 查询所有地区板块
            df = q.get_all_regions()
            if df is not None and len(df) > 0:
                print(f"\n所有地区板块 ({len(df)} 个):")
                print(df.to_string(index=False))
            else:
                print("无数据")
                print("提示: Akshare 暂未提供地区板块数据接口")
            return
        else:
            print(f"未知数据类型: {data_type}")
            return

        if df is not None and len(df) > 0:
            print(f"\n{ts_code} {data_type} 数据 ({len(df)} 条):")
            print(df.tail(10))
        else:
            print("无数据")


def update_concept(concept_name=None):
    """更新概念板块数据

    Args:
        concept_name: 概念名称，为空则更新所有概念板块和成分股
    """
    import sqlite3

    # 确保新表已创建
    import core.database as db_module
    for table_name, sql in db_module.CREATE_TABLES_SQL.items():
        if 'concept' in table_name:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone() is None:
                print(f"创建新表: {table_name}")
                cursor.execute(sql)
                conn.commit()
            conn.close()

    source = ConceptSource()

    if concept_name:
        # 更新指定概念
        print(f"更新概念板块: {concept_name}")
        _update_single_concept(source, concept_name)
    else:
        # 更新所有概念板块
        print("=" * 50)
        print("更新所有概念板块数据...")
        print("=" * 50)

        # 1. 更新概念板块列表
        print("\n[1/2] 更新概念板块列表...")
        df = source.get_all_concepts()
        print(f"   获取到 {len(df)} 个概念")

        conn = sqlite3.connect(DB_PATH)
        df.to_sql('concept_board', conn, if_exists='replace', index=False)
        conn.commit()
        conn.close()
        print(f"   已写入 concept_board 表")

        # 2. 更新所有概念的成分股（5线程）
        print("\n[2/2] 更新概念成分股（5线程）...")

        def _update_concept_stocks(row):
            """更新单个概念的成分股"""
            import sqlite3
            name = row['concept_name']
            concept_code = row['concept_code']
            try:
                stocks_df = source.get_concept_stocks(name)
                if stocks_df is not None and len(stocks_df) > 0:
                    cols = ['ts_code', 'symbol', 'name', 'concept_code', 'concept_name']
                    stocks_df = stocks_df[[c for c in cols if c in stocks_df.columns]]
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("DELETE FROM stock_concept WHERE concept_code = ?", (concept_code,))
                    stocks_df.to_sql('stock_concept', conn, if_exists='append', index=False)
                    conn.commit()
                    conn.close()
                    return name, len(stocks_df), None
            except Exception as e:
                return name, 0, str(e)
            return name, 0, None

        args_list = [(row,) for _, row in df.iterrows()]
        total_stocks = 0
        success_count = 0
        fail_count = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(_update_concept_stocks, row): row['concept_name'] for _, row in df.iterrows()}

            for i, future in enumerate(as_completed(futures)):
                name, count, error = future.result()
                if error:
                    fail_count += 1
                else:
                    success_count += 1
                    total_stocks += count
                    print(f"   {name}: {count} 只股票")

                if (i + 1) % 100 == 0:
                    print(f"   进度: [{i+1}/{len(df)}]")

        print(f"\n概念成分股更新完成: 成功 {success_count}, 失败 {fail_count}, 共 {total_stocks} 条")


def _update_single_concept(source, concept_name):
    """更新单个概念板块"""
    import sqlite3

    # 更新概念信息
    concepts_df = source.get_all_concepts()
    concept_row = concepts_df[concepts_df['concept_name'] == concept_name]
    if len(concept_row) > 0:
        conn = sqlite3.connect(DB_PATH)
        concept_row.to_sql('concept_board', conn, if_exists='replace', index=False)
        conn.commit()
        conn.close()
        print(f"  概念信息已更新")

    # 更新成分股
    stocks_df = source.get_concept_stocks(concept_name)
    if stocks_df is not None and len(stocks_df) > 0:
        cols = ['ts_code', 'symbol', 'name', 'concept_code', 'concept_name']
        stocks_df = stocks_df[[c for c in cols if c in stocks_df.columns]]

        conn = sqlite3.connect(DB_PATH)
        # 先删除该概念已存在的成分股
        conn.execute("DELETE FROM stock_concept WHERE concept_name = ?", (concept_name,))
        stocks_df.to_sql('stock_concept', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        print(f"  成分股 {len(stocks_df)} 只已更新")


def update_industry(industry_name=None):
    """更新行业板块数据

    Args:
        industry_name: 行业名称，为空则更新所有行业板块和成分股
    """
    import sqlite3

    # 确保新表已创建
    import core.database as db_module
    for table_name, sql in db_module.CREATE_TABLES_SQL.items():
        if 'industry' in table_name:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone() is None:
                print(f"创建新表: {table_name}")
                cursor.execute(sql)
                conn.commit()
            conn.close()

    source = ConceptSource()

    if industry_name:
        # 更新指定行业
        print(f"更新行业板块: {industry_name}")
        _update_single_industry(source, industry_name)
    else:
        # 更新所有行业板块
        print("=" * 50)
        print("更新所有行业板块数据...")
        print("=" * 50)

        # 1. 更新行业板块列表
        print("\n[1/2] 更新行业板块列表...")
        df = source.get_all_industries()
        print(f"   获取到 {len(df)} 个行业")

        conn = sqlite3.connect(DB_PATH)
        df.to_sql('industry_board', conn, if_exists='replace', index=False)
        conn.commit()
        conn.close()
        print(f"   已写入 industry_board 表")

        # 2. 更新所有行业的成分股（5线程）
        print("\n[2/2] 更新行业成分股（5线程）...")

        def _update_industry_stocks(row):
            """更新单个行业的成分股"""
            import sqlite3
            name = row['industry_name']
            industry_code = row['industry_code']
            try:
                stocks_df = source.get_industry_stocks(name)
                if stocks_df is not None and len(stocks_df) > 0:
                    cols = ['ts_code', 'symbol', 'name', 'industry_code', 'industry_name']
                    stocks_df = stocks_df[[c for c in cols if c in stocks_df.columns]]
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("DELETE FROM stock_industry WHERE industry_code = ?", (industry_code,))
                    stocks_df.to_sql('stock_industry', conn, if_exists='append', index=False)
                    conn.commit()
                    conn.close()
                    return name, len(stocks_df), None
            except Exception as e:
                return name, 0, str(e)
            return name, 0, None

        total_stocks = 0
        success_count = 0
        fail_count = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(_update_industry_stocks, row): row['industry_name'] for _, row in df.iterrows()}

            for i, future in enumerate(as_completed(futures)):
                name, count, error = future.result()
                if error:
                    fail_count += 1
                else:
                    success_count += 1
                    total_stocks += count
                    print(f"   {name}: {count} 只股票")

                if (i + 1) % 50 == 0:
                    print(f"   进度: [{i+1}/{len(df)}]")

        print(f"\n行业成分股更新完成: 成功 {success_count}, 失败 {fail_count}, 共 {total_stocks} 条")


def _update_single_industry(source, industry_name):
    """更新单个行业板块"""
    import sqlite3

    # 更新行业信息
    industries_df = source.get_all_industries()
    industry_row = industries_df[industries_df['industry_name'] == industry_name]
    if len(industry_row) > 0:
        conn = sqlite3.connect(DB_PATH)
        industry_row.to_sql('industry_board', conn, if_exists='replace', index=False)
        conn.commit()
        conn.close()
        print(f"  行业信息已更新")

    # 更新成分股
    stocks_df = source.get_industry_stocks(industry_name)
    if stocks_df is not None and len(stocks_df) > 0:
        cols = ['ts_code', 'symbol', 'name', 'industry_code', 'industry_name']
        stocks_df = stocks_df[[c for c in cols if c in stocks_df.columns]]

        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM stock_industry WHERE industry_name = ?", (industry_name,))
        stocks_df.to_sql('stock_industry', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        print(f"  成分股 {len(stocks_df)} 只已更新")


def update_region(region_name=None, trade_date=None):
    """更新地区板块数据

    Args:
        region_name: 地区名称，如 '北京'，为空则更新所有地区板块和成分股
        trade_date: 交易日期 YYYYMMDD，默认使用最新日期
    """
    import sqlite3

    # 确保新表已创建
    import core.database as db_module
    for table_name, sql in db_module.CREATE_TABLES_SQL.items():
        if 'region' in table_name:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone() is None:
                print(f"创建新表: {table_name}")
                cursor.execute(sql)
                conn.commit()
            conn.close()

    source = ConceptSource()

    # 获取最新交易日期
    if trade_date is None:
        with QueryDB(DB_PATH) as q:
            trade_date = q.get_latest_date('daily', 'trade_date')
        if trade_date is None:
            trade_date = '20260327'

    if region_name:
        # 更新指定地区
        print(f"更新地区板块: {region_name}")
        _update_single_region(source, region_name, trade_date)
    else:
        # 更新所有地区板块
        print("=" * 50)
        print("更新所有地区板块数据...")
        print("=" * 50)

        # 1. 获取所有地区板块列表
        print("\n[1/2] 获取地区板块列表...")
        df = source.get_all_regions(trade_date)
        if df is None or len(df) == 0:
            print("   获取地区板块失败，请检查网络连接")
            return
        print(f"   获取到 {len(df)} 个地区")

        # 写入 region_board 表
        conn = sqlite3.connect(DB_PATH)
        df.to_sql('region_board', conn, if_exists='replace', index=False)
        conn.commit()
        conn.close()
        print(f"   已写入 region_board 表")

        # 2. 更新所有地区的成分股（5线程）
        print("\n[2/2] 更新地区成分股（5线程）...")

        def _update_region_stocks(row):
            """更新单个地区的成分股"""
            import sqlite3
            name = row['region_name']  # 地区名称
            region_code = row['ts_code']  # 地区代码
            try:
                stocks_df = source.get_region_stocks(region_code, trade_date)
                if stocks_df is not None and len(stocks_df) > 0:
                    # 添加地区代码和名称
                    stocks_df['region_code'] = region_code
                    stocks_df['region_name'] = name
                    cols = ['ts_code', 'name', 'region_code', 'region_name']
                    stocks_df = stocks_df[[c for c in cols if c in stocks_df.columns]]
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("DELETE FROM stock_region WHERE region_code = ?", (region_code,))
                    stocks_df.to_sql('stock_region', conn, if_exists='append', index=False)
                    conn.commit()
                    conn.close()
                    return name, len(stocks_df), None
            except Exception as e:
                return name, 0, str(e)
            return name, 0, None

        total_stocks = 0
        success_count = 0
        fail_count = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(_update_region_stocks, row): row['region_name'] for _, row in df.iterrows()}

            for i, future in enumerate(as_completed(futures)):
                name, count, error = future.result()
                if error:
                    fail_count += 1
                else:
                    success_count += 1
                    total_stocks += count
                    print(f"   {name}: {count} 只股票")

                if (i + 1) % 10 == 0:
                    print(f"   进度: [{i+1}/{len(df)}]")

        print(f"\n地区成分股更新完成: 成功 {success_count}, 失败 {fail_count}, 共 {total_stocks} 条")


def _update_single_region(source, region_name, trade_date):
    """更新单个地区板块"""
    import sqlite3

    # 获取所有地区，找到匹配的
    regions_df = source.get_all_regions(trade_date)
    region_row = regions_df[regions_df['region_name'].str.contains(region_name)]
    if len(region_row) == 0:
        print(f"  未找到地区: {region_name}")
        return

    region_row = region_row.iloc[0]
    region_code = region_row['ts_code']

    # 更新地区信息
    conn = sqlite3.connect(DB_PATH)
    region_row.to_sql('region_board', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()
    print(f"  地区信息已更新")

    # 更新成分股
    stocks_df = source.get_region_stocks(region_code, trade_date)
    if stocks_df is not None and len(stocks_df) > 0:
        stocks_df['region_code'] = region_code
        stocks_df['region_name'] = region_name
        cols = ['ts_code', 'name', 'region_code', 'region_name']
        stocks_df = stocks_df[[c for c in cols if c in stocks_df.columns]]

        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM stock_region WHERE region_code = ?", (region_code,))
        stocks_df.to_sql('stock_region', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        print(f"  成分股 {len(stocks_df)} 只已更新")


def rebuild_fuzzy_search():
    """重建模糊查询表"""
    import sqlite3

    print("=" * 50)
    print("重建模糊查询表")
    print("=" * 50)

    # 确保 fuzzy_search 表已创建
    import core.database as db_module
    for table_name, sql in db_module.CREATE_TABLES_SQL.items():
        if 'fuzzy' in table_name:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone() is None:
                print(f"创建新表: {table_name}")
                cursor.execute(sql)
                conn.commit()
            conn.close()

    # 清空现有数据
    print("\n清空现有数据...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM fuzzy_search")
    conn.commit()
    conn.close()
    print("  已清空 fuzzy_search 表")

    # 重建数据
    print("\n收集各表数据...")

    with QueryDB(DB_PATH) as q:
        df = q.build_fuzzy_search_table()

    print(f"  收集到 {len(df)} 条记录")

    # 写入数据库
    print("\n写入数据库...")
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('fuzzy_search', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()
    print("  写入完成")

    # 按类型统计
    print("\n按类型统计:")
    type_counts = df.groupby('item_type').size()
    for item_type, count in type_counts.items():
        print(f"  {item_type}: {count} 条")

    print("\n" + "=" * 50)
    print("模糊查询表重建完成!")
    print("=" * 50)

    # 演示模糊查询
    print("\n演示查询（关键词 '贵州'）:")
    with QueryDB(DB_PATH) as q:
        result = q.fuzzy_search('贵州')
        print(result.to_string(index=False))


def refresh_price(code=None):
    """刷新股票最新价"""
    from core.data_fetcher import DataFetcher

    print("=" * 50)
    print("刷新股票最新价")
    print("=" * 50)

    fetcher = DataFetcher()
    count = fetcher.refresh_latest_price(code)
    print(f"\n更新完成: {count} 只股票")

    # 显示几只股票的最新价
    if count > 0:
        print("\n最新价（前5只）:")
        with QueryDB(DB_PATH) as q:
            df = q.get_stock_basic()
            df = df[df['latest_price'].notna()].head(5)
            for _, row in df.iterrows():
                print(f"  {row['ts_code']} {row['name']}: {row['latest_price']}")


def main():
    parser = argparse.ArgumentParser(description='Tushare 镜像库')
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # init 命令
    subparsers.add_parser('init', help='初始化数据库')

    # download 命令
    download_parser = subparsers.add_parser('download', help='下载数据')
    download_parser.add_argument('--type', '-t', default='all',
                                 help='数据类型: stock_basic, daily, daily_basic, adj_factor, minute, all')
    download_parser.add_argument('--code', '-c', default=None,
                                 help='股票代码，如 601988.SH')
    download_parser.add_argument('--start', '-s', default=None,
                                 help='开始日期 YYYYMMDD')
    download_parser.add_argument('--end', '-e', default=None,
                                 help='结束日期 YYYYMMDD')
    download_parser.add_argument('--replace', '-r', action='store_true',
                                 help='替换已有数据')

    # sync 命令
    subparsers.add_parser('sync', help='增量同步')

    # update 命令
    subparsers.add_parser('update', help='更新镜像库（更新股票列表 + 增量同步）')

    # query 命令
    query_parser = subparsers.add_parser('query', help='查询数据')
    query_parser.add_argument('--code', '-c', default=None,
                              help='股票代码，如 601988.SH 或 002131.SZ')
    query_parser.add_argument('--name', '-n', default=None,
                              help='股票名称，如 利欧股份（用于概念查询）')
    query_parser.add_argument('--type', '-t', default='daily',
                              help='数据类型: daily, daily_basic, stock_basic, concept, concept_stocks, concepts, industry, industry_stocks, industries, region, region_stocks, regions')
    query_parser.add_argument('--start', '-s', default=None,
                              help='开始日期 YYYYMMDD')
    query_parser.add_argument('--end', '-e', default=None,
                              help='结束日期 YYYYMMDD')

    # concept 命令
    concept_parser = subparsers.add_parser('concept', help='更新概念板块数据')
    concept_parser.add_argument('--name', '-n', default=None,
                               help='概念名称，如 锂矿概念，为空则更新所有')

    # industry 命令
    industry_parser = subparsers.add_parser('industry', help='更新行业板块数据')
    industry_parser.add_argument('--name', '-n', default=None,
                               help='行业名称，如 银行，为空则更新所有')

    # region 命令
    region_parser = subparsers.add_parser('region', help='更新地区板块数据')
    region_parser.add_argument('--name', '-n', default=None,
                               help='地区名称，如 浙江，为空则更新所有')
    region_parser.add_argument('--date', '-d', default=None,
                               help='交易日期 YYYYMMDD，默认使用本地最新日期')

    # rebuild_fuzzy_search 命令
    rebuild_parser = subparsers.add_parser('rebuild_fuzzy_search', help='重建模糊查询表')
    rebuild_parser.add_argument('--type', '-t', default='fuzzy',
                               help='重建类型: fuzzy（模糊查询表）')

    # refresh_price 命令
    price_parser = subparsers.add_parser('refresh_price', help='刷新股票最新价')
    price_parser.add_argument('--code', '-c', default=None,
                               help='股票代码，不指定则刷新所有股票')

    args = parser.parse_args()

    if args.command == 'init':
        init_db()
    elif args.command == 'download':
        download_data(args.type, args.code, args.start, args.end, args.replace)
    elif args.command == 'sync':
        sync_data()
    elif args.command == 'update':
        update_data()
    elif args.command == 'query':
        query_data(args.code, args.start, args.end, args.type, args.name)
    elif args.command == 'concept':
        update_concept(args.name)
    elif args.command == 'industry':
        update_industry(args.name)
    elif args.command == 'region':
        update_region(args.name, args.date)
    elif args.command == 'rebuild_fuzzy_search':
        rebuild_fuzzy_search()
    elif args.command == 'refresh_price':
        refresh_price(args.code)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
