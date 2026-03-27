# -*- coding: utf-8 -*-
"""
统一数据获取器
优先 akshare，失败后自动降级到 tushare
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

from .data_source import DataSource
from .data_source_akshare import AkshareSource
from .data_source_tushare import TushareSource
from .database import create_database
from config import DB_PATH, DAILY_START_DATE


class DataFetcher:
    """统一数据获取器，优先 akshare，失败后降级 tushare"""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.akshare = AkshareSource()
        self.tushare = TushareSource()
        self._ensure_db()

    def _ensure_db(self):
        """确保数据库存在，只在数据库文件不存在时才创建"""
        import os
        if not os.path.exists(self.db_path):
            create_database(self.db_path)

    def _get_latest_date(self, table_name, date_column='trade_date', ts_code=None):
        """获取本地最新日期"""
        conn = sqlite3.connect(self.db_path)
        try:
            if ts_code:
                sql = f"SELECT MAX({date_column}) FROM {table_name} WHERE ts_code = ?"
                cursor = conn.execute(sql, (ts_code,))
            else:
                sql = f"SELECT MAX({date_column}) FROM {table_name}"
                cursor = conn.execute(sql)
            result = cursor.fetchone()[0]
            return result
        finally:
            conn.close()

    def _next_date(self, date_str):
        """获取日期字符串的下一天"""
        d = datetime.strptime(date_str, '%Y%m%d')
        return (d + timedelta(days=1)).strftime('%Y%m%d')

    def _save_to_db(self, table_name, df, ts_code=None):
        """保存数据到数据库"""
        if df is None or len(df) == 0:
            return 0

        conn = sqlite3.connect(self.db_path)
        try:
            if ts_code:
                # 删除该股票已有数据
                conn.execute(f"DELETE FROM {table_name} WHERE ts_code = ?", (ts_code,))
            df.to_sql(table_name, conn, if_exists='append', index=False)
            conn.commit()
            return len(df)
        finally:
            conn.close()

    # ==================== 数据获取接口 ====================

    def get_daily(self, ts_code, start_date=None, end_date=None, save=True) -> pd.DataFrame:
        """获取日线数据，优先 akshare

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            save: 是否保存到数据库

        Returns:
            DataFrame
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        # 优先 akshare
        try:
            df = self.akshare.get_daily(ts_code, start_date, end_date)
            if df is not None and len(df) > 0:
                if save:
                    self._save_to_db('daily', df, ts_code)
                return df
        except Exception as e:
            print(f"[降级] akshare.get_daily 失败: {e}")

        # 降级到 tushare
        print(f"[DataFetcher] {ts_code} 日线使用 tushare")
        df = self.tushare.get_daily(ts_code, start_date, end_date)
        if save and df is not None and len(df) > 0:
            self._save_to_db('daily', df, ts_code)
        return df

    def get_minute(self, ts_code, freq='5min', start_date=None, end_date=None, save=True) -> pd.DataFrame:
        """获取分钟数据，优先 akshare

        Args:
            ts_code: 股票代码
            freq: 分钟周期 ('1min', '5min', '15min', '30min', '60min')
            start_date: 开始日期
            end_date: 结束日期
            save: 是否保存到数据库

        Returns:
            DataFrame
        """
        # 优先 akshare
        try:
            df = self.akshare.get_minute(ts_code, freq, start_date, end_date)
            if df is not None and len(df) > 0:
                if save:
                    table_name = f"minute_{freq}"
                    self._save_to_db(table_name, df, ts_code)
                return df
        except Exception as e:
            print(f"[降级] akshare.get_minute 失败: {e}")

        # 降级到 tushare
        print(f"[DataFetcher] {ts_code} {freq} 分钟数据使用 tushare")
        df = self.tushare.get_minute(ts_code, freq, start_date, end_date)
        if save and df is not None and len(df) > 0:
            table_name = f"minute_{freq}"
            self._save_to_db(table_name, df, ts_code)
        return df

    def get_stock_basic(self, save=True) -> pd.DataFrame:
        """获取股票列表，优先 tushare（字段更完整）"""
        # tushare 字段更完整，优先使用
        try:
            df = self.tushare.get_stock_basic()
            if df is not None and len(df) > 0:
                if save:
                    self._save_to_db('stock_basic', df)
                return df
        except Exception as e:
            print(f"[降级] tushare.get_stock_basic 失败: {e}")

        # 降级到 akshare
        print(f"[DataFetcher] 股票列表使用 akshare")
        df = self.akshare.get_stock_basic()
        if save and df is not None and len(df) > 0:
            self._save_to_db('stock_basic', df)
        return df

    def get_adj_factor(self, ts_code, start_date=None, end_date=None, save=True) -> pd.DataFrame:
        """获取复权因子，仅使用 tushare"""
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        df = self.tushare.get_adj_factor(ts_code, start_date, end_date)
        if save and df is not None and len(df) > 0:
            self._save_to_db('adj_factor', df, ts_code)
        return df

    def get_daily_basic(self, ts_code, start_date=None, end_date=None, save=True) -> pd.DataFrame:
        """获取每日指标，仅使用 tushare"""
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        df = self.tushare.get_daily_basic(ts_code, start_date, end_date)
        if save and df is not None and len(df) > 0:
            self._save_to_db('daily_basic', df, ts_code)
        return df

    def get_trade_dates(self, start_date, end_date) -> pd.DataFrame:
        """获取交易日历，优先 akshare"""
        try:
            return self.akshare.get_trade_dates(start_date, end_date)
        except Exception as e:
            print(f"[降级] akshare.get_trade_dates 失败: {e}")
            return self.tushare.get_trade_dates(start_date, end_date)

    # ==================== 增量同步接口 ====================

    def refresh_daily(self, ts_code, end_date=None) -> int:
        """增量刷新单只股票的日线数据

        Args:
            ts_code: 股票代码
            end_date: 结束日期，默认今天

        Returns:
            新增数据条数
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        # 获取本地最新日期
        local_latest = self._get_latest_date('daily', 'trade_date', ts_code)
        if local_latest and local_latest >= end_date:
            print(f"{ts_code} 日线已是最新 ({local_latest})")
            return 0

        start_date = self._next_date(local_latest) if local_latest else DAILY_START_DATE

        # 获取数据
        df = self.get_daily(ts_code, start_date, end_date, save=False)
        if df is None or len(df) == 0:
            return 0

        # 过滤出新增数据
        if local_latest:
            df = df[df['trade_date'] > local_latest]

        if len(df) == 0:
            return 0

        # 保存
        self._save_to_db('daily', df, ts_code)
        return len(df)

    def refresh_daily_basic(self, ts_code, end_date=None) -> int:
        """增量刷新单只股票的每日指标"""
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        local_latest = self._get_latest_date('daily_basic', 'trade_date', ts_code)
        if local_latest and local_latest >= end_date:
            return 0

        start_date = self._next_date(local_latest) if local_latest else DAILY_START_DATE

        df = self.get_daily_basic(ts_code, start_date, end_date, save=False)
        if df is None or len(df) == 0:
            return 0

        if local_latest:
            df = df[df['trade_date'] > local_latest]

        if len(df) == 0:
            return 0

        self._save_to_db('daily_basic', df, ts_code)
        return len(df)

    def refresh_adj_factor(self, ts_code, end_date=None) -> int:
        """增量刷新单只股票的复权因子"""
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        local_latest = self._get_latest_date('adj_factor', 'trade_date', ts_code)
        if local_latest and local_latest >= end_date:
            return 0

        start_date = self._next_date(local_latest) if local_latest else DAILY_START_DATE

        df = self.get_adj_factor(ts_code, start_date, end_date, save=False)
        if df is None or len(df) == 0:
            return 0

        if local_latest:
            df = df[df['trade_date'] > local_latest]

        if len(df) == 0:
            return 0

        self._save_to_db('adj_factor', df, ts_code)
        return len(df)

    def refresh_latest_price(self, ts_code=None) -> int:
        """刷新股票的最新收盘价

        Args:
            ts_code: 股票代码，None 表示刷新所有股票

        Returns:
            更新的股票数量
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # 获取最新的交易日期
            latest_date = pd.read_sql_query(
                "SELECT MAX(trade_date) as max_date FROM daily",
                conn
            )['max_date'].iloc[0]

            if not latest_date:
                return 0

            # 获取该日期的所有收盘价
            if ts_code:
                df_daily = pd.read_sql_query(
                    "SELECT ts_code, close FROM daily WHERE trade_date = ? AND ts_code = ?",
                    conn, params=[latest_date, ts_code]
                )
            else:
                df_daily = pd.read_sql_query(
                    "SELECT ts_code, close FROM daily WHERE trade_date = ?",
                    conn, params=[latest_date]
                )

            if df_daily is None or len(df_daily) == 0:
                return 0

            # 重命名列
            df_daily = df_daily.rename(columns={'close': 'latest_price'})

            # 使用 UPDATE 语句更新
            for _, row in df_daily.iterrows():
                conn.execute(
                    "UPDATE stock_basic SET latest_price = ? WHERE ts_code = ?",
                    (row['latest_price'], row['ts_code'])
                )
            conn.commit()

            return len(df_daily)
        finally:
            conn.close()

    def refresh_minute(self, ts_code, freq='5min', end_date=None) -> int:
        """增量刷新单只股票的分钟数据"""
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')

        table_name = f"minute_{freq}"
        local_latest = self._get_latest_date(table_name, 'trade_time', ts_code)

        if local_latest:
            local_date = local_latest[:8]
            if local_date >= end_date:
                print(f"{ts_code} {freq} 已是最新")
                return 0
            start_date = self._next_date(local_date)
        else:
            start_date = DAILY_START_DATE

        df = self.get_minute(ts_code, freq, start_date, end_date, save=False)
        if df is None or len(df) == 0:
            return 0

        if local_latest:
            df = df[df['trade_time'] > local_latest]

        if len(df) == 0:
            return 0

        self._save_to_db(table_name, df, ts_code)
        return len(df)


if __name__ == '__main__':
    # 测试
    fetcher = DataFetcher()

    print("=" * 50)
    print("测试 DataFetcher")
    print("=" * 50)

    # 测试获取股票列表
    print("\n1. 测试 get_stock_basic:")
    df = fetcher.get_stock_basic(save=False)
    print(f"   获取到 {len(df)} 只股票")
    print(df.head(3))

    # 测试获取日线数据
    print("\n2. 测试 get_daily (000001.SZ):")
    df = fetcher.get_daily('000001.SZ', '20260301', '20260327', save=False)
    print(f"   获取到 {len(df)} 条数据")
    print(df.head(3))

    # 测试获取分钟数据
    print("\n3. 测试 get_minute (000001.SZ, 5min):")
    df = fetcher.get_minute('000001.SZ', '5min', '20260325', '20260327', save=False)
    print(f"   获取到 {len(df)} 条数据")
    print(df.head(3))
