# -*- coding: utf-8 -*-
"""
Akshare 数据源适配器
实现 DataSource 接口，负责代码格式转换和列名转换
"""
import pandas as pd
import sys
import os

# 添加 akshare 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'depends', 'akshare'))

import akshare as ak
from .data_source import DataSource
from config import DAILY_START_DATE


def ts_code_to_symbol(ts_code):
    """将 tushare 代码格式转换为 akshare 格式

    Args:
        ts_code: 如 '000001.SZ' -> '000001'
    """
    return ts_code.split('.')[0] if '.' in ts_code else ts_code


def symbol_to_ts_code(symbol, market=None):
    """将纯数字代码转换为 tushare 格式

    Args:
        symbol: 纯数字代码，如 '000001'
        market: 市场标识，'SH'/'SZ'/'BJ'，可根据代码前缀判断
    """
    if market is None:
        if symbol.startswith('8') or symbol.startswith('4'):
            market = 'BJ'
        elif symbol.startswith('6'):
            market = 'SH'
        else:
            market = 'SZ'
    return f"{symbol}.{market}"


class AkshareSource(DataSource):
    """Akshare 数据源适配器"""

    def get_daily(self, ts_code, start_date, end_date) -> pd.DataFrame:
        """获取日线数据

        Akshare 返回列名: 日期, 股票代码, 开盘, 收盘, 最高, 最低, 成交量, 成交额,
                           振幅, 涨跌幅, 涨跌额, 换手率
        需要转换为数据库列名
        """
        symbol = ts_code_to_symbol(ts_code)
        if not start_date:
            start_date = DAILY_START_DATE

        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=""
        )

        if df is None or len(df) == 0:
            return df

        # 列名转换
        rename_map = {
            '日期': 'trade_date',
            '股票代码': 'ts_code',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'vol',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_chg',
            '涨跌额': 'change',
            '换手率': 'turnover_rate'
        }

        # 只保留需要的列并重命名
        df = df.rename(columns=rename_map)

        # 确保 ts_code 正确
        df['ts_code'] = ts_code

        # 转换 trade_date 为 YYYYMMDD 字符串格式
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y%m%d')

        # 添加 pre_close（前一交易日收盘价）
        df['pre_close'] = df['close'].shift(1)

        # 选择对齐数据库的列
        db_columns = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close',
                      'pre_close', 'change', 'pct_chg', 'vol', 'amount']
        for col in db_columns:
            if col not in df.columns:
                df[col] = None

        return df[db_columns]

    def get_minute(self, ts_code, freq, start_date, end_date) -> pd.DataFrame:
        """获取分钟数据

        Akshare 返回列名: 时间, 开盘, 收盘, 最高, 最低, 成交量, 成交额,
                           振幅, 涨跌幅, 涨跌额, 换手率
        需要转换为数据库列名
        """
        symbol = ts_code_to_symbol(ts_code)

        # 转换日期格式
        if start_date:
            if len(start_date) == 8:
                start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]} 09:00:00"
        if end_date:
            if len(end_date) == 8:
                end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]} 15:00:00"

        # akshare period: '1', '5', '15', '30', '60'
        period_map = {
            '1min': '1',
            '5min': '5',
            '15min': '15',
            '30min': '30',
            '60min': '60'
        }
        period = period_map.get(freq, '5')

        df = ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            adjust=""
        )

        if df is None or len(df) == 0:
            return df

        # 列名转换
        rename_map = {
            '时间': 'trade_time',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'vol',
            '成交额': 'amount'
        }

        df = df.rename(columns=rename_map)

        # 添加 ts_code
        df['ts_code'] = ts_code

        # 转换 trade_time 格式为 YYYYMMDDHHMMSS
        df['trade_time'] = df['trade_time'].str.replace('-', '').str.replace(' ', '').str.replace(':', '')

        # 选择对齐数据库的列
        db_columns = ['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount']
        for col in db_columns:
            if col not in df.columns:
                df[col] = None

        return df[db_columns]

    def get_stock_basic(self) -> pd.DataFrame:
        """获取股票列表

        Akshare 股票基本信息较少，仅返回 code, name
        数据库需要更多字段，所以此接口主要用作降级备选
        """
        df = ak.stock_info_a_code_name()

        if df is None or len(df) == 0:
            return df

        # 转换代码格式
        df['ts_code'] = df['code'].apply(symbol_to_ts_code)
        df['symbol'] = df['code']
        df['name'] = df['name']

        # Akshare 没有以下字段，设为空
        df['area'] = None
        df['industry'] = None
        df['market'] = None
        df['list_date'] = None
        df['delist_date'] = None
        df['is_hs'] = None

        db_columns = ['ts_code', 'symbol', 'name', 'area', 'industry', 'market',
                      'list_date', 'delist_date', 'is_hs']
        return df[db_columns]

    def get_adj_factor(self, ts_code, start_date, end_date) -> pd.DataFrame:
        """获取复权因子

        Akshare 没有单独的复权因子接口，此方法抛出异常，
        由 DataFetcher 降级到 tushare 获取
        """
        raise NotImplementedError("Akshare 没有单独的复权因子接口，请使用 tushare")

    def get_daily_basic(self, ts_code, start_date, end_date) -> pd.DataFrame:
        """获取每日指标

        Akshare 没有完整的每日指标接口，此方法抛出异常，
        由 DataFetcher 降级到 tushare 获取
        """
        raise NotImplementedError("Akshare 没有每日指标接口，请使用 tushare")

    def get_trade_dates(self, start_date, end_date) -> pd.DataFrame:
        """获取交易日历

        Akshare tool_trade_date_hist_sina() 返回所有交易日期列表
        返回格式转换为 YYYYMMDD 以匹配系统其他部分
        """
        df = ak.tool_trade_date_hist_sina()
        # 转换日期列为字符串 YYYY-MM-DD 格式
        df['trade_date'] = df['trade_date'].astype(str)
        # 转换为 YYYYMMDD 格式
        df['trade_date'] = df['trade_date'].str.replace('-', '')
        # 过滤日期范围
        df = df[(df['trade_date'] >= start_date) & (df['trade_date'] <= end_date)]
        df = df.rename(columns={'trade_date': 'cal_date'})
        df['is_open'] = 1  # 所有返回的日期都是交易日
        return df[['cal_date', 'is_open']]
