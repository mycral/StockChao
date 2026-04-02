# -*- coding: utf-8 -*-
"""
分时数据本地缓存
使用 SQLite 存储分时数据
"""
import sqlite3
import os
import time
import pickle
from datetime import datetime


class MinuteCache:
    """分时数据本地缓存（SQLite）"""

    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.db_path = os.path.join(self.cache_dir, 'minute_cache.db')
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS minute_cache (
                ts_code TEXT,
                trade_date TEXT,
                data BLOB,
                updated_at INTEGER,
                PRIMARY KEY (ts_code, trade_date)
            )
        """)
        conn.close()

    def get(self, ts_code: str, trade_date: str) -> any:
        """获取缓存数据

        Args:
            ts_code: 股票代码，如 '600519.SH'
            trade_date: 交易日期，如 '20260402'

        Returns:
            DataFrame 或 None（无缓存或已过期）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT data, updated_at FROM minute_cache WHERE ts_code=? AND trade_date=?",
            (ts_code, trade_date)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            try:
                return pickle.loads(row[0])
            except Exception:
                return None
        return None

    def set(self, ts_code: str, trade_date: str, data: any):
        """设置缓存数据

        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            data: DataFrame 数据
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO minute_cache VALUES (?, ?, ?, ?)",
                (ts_code, trade_date, pickle.dumps(data), int(time.time()))
            )
            conn.commit()
        finally:
            conn.close()

    def clear(self, ts_code: str = None, trade_date: str = None):
        """清理缓存

        Args:
            ts_code: 股票代码（None 表示全部）
            trade_date: 交易日期（None 表示全部）
        """
        conn = sqlite3.connect(self.db_path)
        try:
            if ts_code and trade_date:
                conn.execute(
                    "DELETE FROM minute_cache WHERE ts_code=? AND trade_date=?",
                    (ts_code, trade_date)
                )
            elif ts_code:
                conn.execute("DELETE FROM minute_cache WHERE ts_code=?", (ts_code,))
            else:
                conn.execute("DELETE FROM minute_cache")
            conn.commit()
        finally:
            conn.close()

    def clear_expired(self, ttl: int = 300):
        """清理过期缓存

        Args:
            ttl: 缓存有效期（秒），默认5分钟
        """
        expire_time = int(time.time()) - ttl
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("DELETE FROM minute_cache WHERE updated_at < ?", (expire_time,))
            conn.commit()
        finally:
            conn.close()