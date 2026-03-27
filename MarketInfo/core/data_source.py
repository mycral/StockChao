# -*- coding: utf-8 -*-
"""
数据源抽象基类
定义统一的数据获取接口，供 DataFetcher 统一调用
"""
from abc import ABC, abstractmethod
import pandas as pd


class DataSource(ABC):
    """数据源抽象基类"""

    @abstractmethod
    def get_daily(self, ts_code, start_date, end_date) -> pd.DataFrame:
        """获取日线数据

        Args:
            ts_code: 股票代码，如 '000001.SZ'
            start_date: 开始日期，YYYYMMDD
            end_date: 结束日期，YYYYMMDD

        Returns:
            DataFrame，列名需对齐数据库表结构：
            ts_code, trade_date, open, high, low, close, pre_close,
            change, pct_chg, vol, amount
        """
        pass

    @abstractmethod
    def get_minute(self, ts_code, freq, start_date, end_date) -> pd.DataFrame:
        """获取分钟数据

        Args:
            ts_code: 股票代码，如 '000001.SZ'
            freq: 分钟周期 ('1min', '5min', '15min', '30min', '60min')
            start_date: 开始日期时间，YYYYMMDDHHMMSS 或 YYYY-MM-DD HH:MM:SS
            end_date: 结束日期时间，YYYYMMDDHHMMSS 或 YYYY-MM-DD HH:MM:SS

        Returns:
            DataFrame，列名需对齐数据库表结构：
            ts_code, trade_time, open, high, low, close, vol, amount
        """
        pass

    @abstractmethod
    def get_stock_basic(self) -> pd.DataFrame:
        """获取股票列表

        Returns:
            DataFrame，列名需对齐 stock_basic 表结构：
            ts_code, symbol, name, area, industry, market, list_date, delist_date, is_hs
        """
        pass

    @abstractmethod
    def get_adj_factor(self, ts_code, start_date, end_date) -> pd.DataFrame:
        """获取复权因子

        Args:
            ts_code: 股票代码，如 '000001.SZ'
            start_date: 开始日期，YYYYMMDD
            end_date: 结束日期，YYYYMMDD

        Returns:
            DataFrame，列名需对齐 adj_factor 表结构：
            ts_code, trade_date, adj_factor
        """
        pass

    @abstractmethod
    def get_daily_basic(self, ts_code, start_date, end_date) -> pd.DataFrame:
        """获取每日指标

        Args:
            ts_code: 股票代码，如 '000001.SZ'
            start_date: 开始日期，YYYYMMDD
            end_date: 结束日期，YYYYMMDD

        Returns:
            DataFrame，列名需对齐 daily_basic 表结构：
            ts_code, trade_date, close, turnover_rate, turnover_rate_f,
            volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm,
            total_share, float_share, free_share, total_mv, circ_mv
        """
        pass

    @abstractmethod
    def get_trade_dates(self, start_date, end_date) -> pd.DataFrame:
        """获取交易日历

        Args:
            start_date: 开始日期，YYYYMMDD
            end_date: 结束日期，YYYYMMDD

        Returns:
            DataFrame，包含 cal_date, is_open 列
        """
        pass
