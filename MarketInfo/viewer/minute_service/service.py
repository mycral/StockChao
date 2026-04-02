# -*- coding: utf-8 -*-
"""
分时数据服务
统一获取接口，支持多数据源和并发
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import pandas as pd

from .base import MinuteSource
from .sina_source import SinaMinuteSource
from .cache import MinuteCache


class MinuteDataService:
    """分时数据服务"""

    def __init__(
        self,
        source: MinuteSource = None,
        max_workers: int = 6,
        cache_ttl: int = 300
    ):
        """初始化

        Args:
            source: 数据源（默认新浪）
            max_workers: 最大并发数
            cache_ttl: 缓存有效期（秒），默认5分钟
        """
        self._source = source or SinaMinuteSource()
        self._max_workers = max_workers
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
        # 默认今天
        if trade_date is None:
            trade_date = date.today().strftime('%Y%m%d')

        # 1. 检查缓存
        cached = self._cache.get(ts_code, trade_date)
        if cached is not None:
            return cached

        # 2. 获取数据
        df = self._source.fetch(ts_code)
        if df is not None and len(df) > 0:
            # 3. 过滤最后交易日
            df = self._filter_last_day(df)
            # 4. 保存缓存
            if df is not None and len(df) > 0:
                self._cache.set(ts_code, trade_date, df)
        return df

    def get_batch(self, ts_codes: list, trade_date: str = None) -> dict:
        """并发获取多只股票

        Args:
            ts_codes: 股票代码列表
            trade_date: 交易日期（默认今天）

        Returns:
            {ts_code: DataFrame 或 None, ...}
        """
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {
                code: executor.submit(self.get, code, trade_date)
                for code in ts_codes
            }
            return {code: f.result() for code, f in futures.items()}

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