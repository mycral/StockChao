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
        conn.execute("PRAGMA journal_mode=WAL")
        # 分时数据缓存表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS minute_cache (
                ts_code TEXT,
                trade_date TEXT,
                data BLOB,
                updated_at INTEGER,
                PRIMARY KEY (ts_code, trade_date)
            )
        """)
        # 服务器地址缓存表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS server_cache (
                key TEXT PRIMARY KEY,
                host TEXT,
                port INTEGER,
                updated_at INTEGER
            )
        """)
        conn.close()

    def _connect(self):
        """创建数据库连接（启用 WAL 模式）"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def get(self, ts_code: str, trade_date: str) -> any:
        """获取缓存数据

        Args:
            ts_code: 股票代码，如 '600519.SH'
            trade_date: 交易日期，如 '20260402'

        Returns:
            DataFrame 或 None（无缓存或已过期）
        """
        conn = self._connect()
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
        conn = self._connect()
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
        conn = self._connect()
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
        conn = self._connect()
        try:
            conn.execute("DELETE FROM minute_cache WHERE updated_at < ?", (expire_time,))
            conn.commit()
        finally:
            conn.close()

    def get_server(self) -> tuple:
        """获取缓存的服务器地址

        Returns:
            tuple: (host, port) 或 (None, None)
        """
        conn = self._connect()
        cursor = conn.execute(
            "SELECT host, port FROM server_cache WHERE key = 'tdxw_server'"
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return (row[0], row[1])
        return (None, None)

    def set_server(self, host: str, port: int):
        """保存服务器地址到缓存

        Args:
            host: 服务器地址
            port: 服务器端口
        """
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO server_cache VALUES (?, ?, ?, ?)",
                ('tdxw_server', host, port, int(time.time()))
            )
            conn.commit()
        finally:
            conn.close()

    def get_server_list(self) -> list:
        """获取服务器地址列表

        Returns:
            list: [(host, port), ...]
        """
        conn = self._connect()
        cursor = conn.execute(
            "SELECT host, port FROM server_cache WHERE key LIKE 'tdxw_server_%' ORDER BY updated_at DESC"
        )
        rows = cursor.fetchall()
        conn.close()
        return [(row[0], row[1]) for row in rows]

    def add_server(self, host: str, port: int):
        """添加服务器到列表

        Args:
            host: 服务器地址
            port: 服务器端口
        """
        # 检查是否已存在
        conn = self._connect()
        cursor = conn.execute(
            "SELECT key FROM server_cache WHERE key = ?",
            (f'tdxw_server_{host}_{port}',)
        )
        exists = cursor.fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO server_cache VALUES (?, ?, ?, ?)",
                (f'tdxw_server_{host}_{port}', host, port, int(time.time()))
            )
            conn.commit()
        conn.close()

    def remove_server(self, host: str, port: int):
        """从列表中移除服务器

        Args:
            host: 服务器地址
            port: 服务器端口
        """
        conn = self._connect()
        conn.execute(
            "DELETE FROM server_cache WHERE key = ?",
            (f'tdxw_server_{host}_{port}',)
        )
        conn.commit()
        conn.close()

    def clear_servers(self):
        """清空服务器列表"""
        conn = self._connect()
        conn.execute("DELETE FROM server_cache WHERE key LIKE 'tdxw_server_%'")
        conn.commit()
        conn.close()