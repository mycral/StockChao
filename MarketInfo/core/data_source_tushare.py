# -*- coding: utf-8 -*-
"""
Tushare 数据源适配器
实现 DataSource 接口，数据格式直接对齐数据库表结构
"""
import pandas as pd
from .data_source import DataSource
from config import get_pro_api, DAILY_START_DATE


class TushareSource(DataSource):
    """Tushare 数据源适配器"""

    def __init__(self):
        self._pro = None

    @property
    def pro(self):
        if self._pro is None:
            self._pro = get_pro_api()
        return self._pro

    def get_daily(self, ts_code, start_date, end_date) -> pd.DataFrame:
        """获取日线数据"""
        if not start_date:
            start_date = DAILY_START_DATE
        return self.pro.daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )

    def get_minute(self, ts_code, freq, start_date, end_date) -> pd.DataFrame:
        """获取分钟数据"""
        # stk_mins 需要 YYYY-MM-DD HH:MM:SS 格式
        if start_date and len(start_date) == 8:
            start_date = start_date + ' 09:00:00'
        if end_date and len(end_date) == 8:
            end_date = end_date + ' 15:00:00'

        # tushare freq 参数: 1/5/15/30/60
        freq_map = {
            '1min': '1',
            '5min': '5',
            '15min': '15',
            '30min': '30',
            '60min': '60'
        }
        tushare_freq = freq_map.get(freq, '5')

        df = self.pro.stk_mins(
            ts_code=ts_code,
            freq=tushare_freq,
            start_date=start_date,
            end_date=end_date
        )
        return df

    def get_stock_basic(self) -> pd.DataFrame:
        """获取股票列表"""
        return self.pro.stock_basic(
            exchange='',
            list_status='L',
            fields='ts_code,symbol,name,area,industry,market,list_date,delist_date,is_hs'
        )

    def get_adj_factor(self, ts_code, start_date, end_date) -> pd.DataFrame:
        """获取复权因子"""
        if not start_date:
            start_date = DAILY_START_DATE
        return self.pro.adj_factor(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )

    def get_daily_basic(self, ts_code, start_date, end_date) -> pd.DataFrame:
        """获取每日指标"""
        if not start_date:
            start_date = DAILY_START_DATE
        return self.pro.daily_basic(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )

    def get_trade_dates(self, start_date, end_date) -> pd.DataFrame:
        """获取交易日历"""
        return self.pro.trade_cal(
            start_date=start_date,
            end_date=end_date
        )
