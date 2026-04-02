# -*- coding: utf-8 -*-
"""
分时数据服务
统一获取接口，支持多数据源
"""
from datetime import date, datetime, timedelta
import pandas as pd
import time
import threading

from .base import MinuteSource
from .sina_source import SinaMinuteSource
from .pytdx_source import PytdxMinuteSource
from .cache import MinuteCache


# 全局请求调度器
_request_lock = threading.Lock()
_last_request_time = 0
_request_interval = 0.5  # 默认0.5秒间隔


def _wait_for_interval():
    """等待请求间隔"""
    global _last_request_time
    with _request_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < _request_interval:
            wait_time = _request_interval - elapsed
            time.sleep(wait_time)
        _last_request_time = time.time()


class MinuteDataService:
    """分时数据服务"""

    def __init__(
        self,
        source: MinuteSource = None,
        batch_interval: float = 0.5,
        cache_ttl: int = 300
    ):
        """初始化

        Args:
            source: 数据源（默认 Pytdx）
            batch_interval: 批量获取间隔（秒），默认0.5秒
            cache_ttl: 缓存有效期（秒），默认5分钟
        """
        global _request_interval
        # 默认使用 Pytdx（更稳定，响应更快）
        self._source = source or PytdxMinuteSource()
        self._batch_interval = batch_interval
        _request_interval = float(batch_interval)  # 同步全局间隔
        self._cache = MinuteCache()
        self._cache_ttl = cache_ttl

    def get(self, ts_code: str, trade_date: str = None) -> pd.DataFrame:
        """获取单只股票分时

        Args:
            ts_code: 股票代码，如 '600519.SH'
            trade_date: 交易日期，如 '20260402'（默认今天）

        Returns:
            DataFrame 或 None
        """
        # 0. 等待请求间隔
        _wait_for_interval()

        # 1. 检查缓存（先尝试请求的日期，再尝试昨天）
        if trade_date is None:
            trade_date = date.today().strftime('%Y%m%d')

        # 先尝试请求的日期
        cached = self._cache.get(ts_code, trade_date)
        if cached is not None:
            return cached

        # 尝试昨天的缓存（今天没数据时）
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        cached = self._cache.get(ts_code, yesterday)
        if cached is not None:
            return cached

        # 2. 获取数据
        df = self._source.fetch(ts_code)
        if df is not None and len(df) > 0:
            # 3. 过滤最后交易日
            df = self._filter_last_day(df)
            # 4. 根据实际数据日期存储缓存
            if df is not None and len(df) > 0:
                actual_date = df['day'].max().strftime('%Y%m%d')
                self._cache.set(ts_code, actual_date, df)
        return df

    def get_batch(self, ts_codes: list, trade_date: str = None) -> dict:
        """顺序获取多只股票（每只间隔 batch_interval 秒）

        Args:
            ts_codes: 股票代码列表
            trade_date: 交易日期（默认今天）

        Returns:
            {ts_code: DataFrame 或 None, ...}
        """
        results = {}
        for code in ts_codes:
            results[code] = self.get(code, trade_date)
            # 每只股票间隔一段时间，避免并发请求
            if code != ts_codes[-1]:
                time.sleep(self._batch_interval)
        return results

    def _filter_last_day(self, df: pd.DataFrame) -> pd.DataFrame:
        """筛选最后一个交易日的数据"""
        if df is None or len(df) == 0:
            return df

        # 转换日期列
        if not pd.api.types.is_datetime64_any_dtype(df['day']):
            df['day'] = pd.to_datetime(df['day'])

        # 获取最后日期
        last_date = str(df['day'].max().date())
        mask = df['day'].astype(str).str.startswith(last_date)
        df_filtered = df[mask].copy()

        # 转换数值类型（AKShare 返回字符串）
        cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
        for col in cols:
            if col in df_filtered.columns:
                df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce').fillna(0)

        return df_filtered

    def clear_cache(self, ts_code: str = None, trade_date: str = None):
        """清理缓存

        Args:
            ts_code: 股票代码（None 表示全部）
            trade_date: 交易日期（None 表示全部）
        """
        self._cache.clear(ts_code, trade_date)

    @property
    def source_name(self) -> str:
        """当前数据源名称"""
        return self._source.name