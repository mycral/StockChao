# -*- coding: utf-8 -*-
"""
概念板块数据获取模块
使用 akshare 获取概念板块数据和成分股信息
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'depends', 'akshare'))

import akshare as ak
import pandas as pd


class ConceptSource:
    """概念板块数据源"""

    def get_all_concepts(self) -> pd.DataFrame:
        """获取所有概念板块列表

        Returns:
            DataFrame，列名：
            concept_code, concept_name, rank, latest_price, changeAmt,
            pct_chg, total_mv, turnover_rate, up_count, down_count,
            top_stock, top_stock_pct
        """
        df = ak.stock_board_concept_name_em()

        # 列名转换
        rename_map = {
            '板块名称': 'concept_name',
            '板块代码': 'concept_code',
            '排名': 'rank',
            '最新价': 'latest_price',
            '涨跌额': 'changeAmt',
            '涨跌幅': 'pct_chg',
            '总市值': 'total_mv',
            '换手率': 'turnover_rate',
            '上涨家数': 'up_count',
            '下跌家数': 'down_count',
            '领涨股票': 'top_stock',
            '领涨股票-涨跌幅': 'top_stock_pct'
        }

        df = df.rename(columns=rename_map)
        return df

    def get_concept_stocks(self, concept_name: str) -> pd.DataFrame:
        """获取指定概念的成分股

        Args:
            concept_name: 概念名称，如 '锂矿概念'

        Returns:
            DataFrame，列名：
            ts_code, symbol, name, latest_price, pct_chg, changeAmt,
            vol, amount, amplitude, high, low, open, pre_close, turnover_rate
        """
        df = ak.stock_board_concept_cons_em(symbol=concept_name)

        if df is None or len(df) == 0:
            return df

        # 列名转换
        rename_map = {
            '代码': 'symbol',
            '名称': 'name',
            '最新价': 'latest_price',
            '涨跌幅': 'pct_chg',
            '涨跌额': 'changeAmt',
            '成交量': 'vol',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '最高': 'high',
            '最低': 'low',
            '今开': 'open',
            '昨收': 'pre_close',
            '换手率': 'turnover_rate'
        }

        df = df.rename(columns=rename_map)

        # 转换代码为 ts_code 格式
        def to_ts_code(symbol):
            symbol = str(symbol)
            if symbol.startswith('6'):
                return f"{symbol}.SH"
            else:
                return f"{symbol}.SZ"

        df['ts_code'] = df['symbol'].apply(to_ts_code)

        # 添加概念名称
        df['concept_name'] = concept_name

        # 获取概念代码
        concepts_df = self.get_all_concepts()
        concept_row = concepts_df[concepts_df['concept_name'] == concept_name]
        if len(concept_row) > 0:
            df['concept_code'] = concept_row.iloc[0]['concept_code']
        else:
            df['concept_code'] = None

        return df

    def get_all_industries(self) -> pd.DataFrame:
        """获取所有行业板块列表

        Returns:
            DataFrame，列名：
            industry_code, industry_name, rank, latest_price, changeAmt,
            pct_chg, total_mv, turnover_rate, up_count, down_count,
            top_stock, top_stock_pct
        """
        df = ak.stock_board_industry_name_em()

        # 列名转换
        rename_map = {
            '板块名称': 'industry_name',
            '板块代码': 'industry_code',
            '排名': 'rank',
            '最新价': 'latest_price',
            '涨跌额': 'changeAmt',
            '涨跌幅': 'pct_chg',
            '总市值': 'total_mv',
            '换手率': 'turnover_rate',
            '上涨家数': 'up_count',
            '下跌家数': 'down_count',
            '领涨股票': 'top_stock',
            '领涨股票-涨跌幅': 'top_stock_pct'
        }

        df = df.rename(columns=rename_map)
        return df

    def get_industry_stocks(self, industry_name: str) -> pd.DataFrame:
        """获取指定行业的成分股

        Args:
            industry_name: 行业名称，如 '银行'

        Returns:
            DataFrame，列名：
            ts_code, symbol, name, latest_price, pct_chg, changeAmt,
            vol, amount, amplitude, high, low, open, pre_close, turnover_rate
        """
        df = ak.stock_board_industry_cons_em(symbol=industry_name)

        if df is None or len(df) == 0:
            return df

        # 列名转换
        rename_map = {
            '代码': 'symbol',
            '名称': 'name',
            '最新价': 'latest_price',
            '涨跌幅': 'pct_chg',
            '涨跌额': 'changeAmt',
            '成交量': 'vol',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '最高': 'high',
            '最低': 'low',
            '今开': 'open',
            '昨收': 'pre_close',
            '换手率': 'turnover_rate'
        }

        df = df.rename(columns=rename_map)

        # 转换代码为 ts_code 格式
        def to_ts_code(symbol):
            symbol = str(symbol)
            if symbol.startswith('6'):
                return f"{symbol}.SH"
            else:
                return f"{symbol}.SZ"

        df['ts_code'] = df['symbol'].apply(to_ts_code)

        # 添加行业名称
        df['industry_name'] = industry_name

        # 获取行业代码
        industries_df = self.get_all_industries()
        industry_row = industries_df[industries_df['industry_name'] == industry_name]
        if len(industry_row) > 0:
            df['industry_code'] = industry_row.iloc[0]['industry_code']
        else:
            df['industry_code'] = None

        return df

    def get_all_regions(self, trade_date: str = None) -> pd.DataFrame:
        """获取所有地区板块列表（使用 Tushare 通达信接口）

        Args:
            trade_date: 交易日期 YYYYMMDD，默认使用最新日期

        Returns:
            DataFrame，列名：
            region_code, region_name, idx_type, idx_count,
            total_share, float_share, total_mv, float_mv, trade_date
        """
        from config import get_pro_api

        pro = get_pro_api()
        if trade_date is None:
            trade_date = '20260327'  # 默认日期

        df = pro.tdx_index(trade_date=trade_date, idx_type='地区板块')

        if df is None or len(df) == 0:
            return df

        # 重命名列以匹配数据库字段
        rename_map = {
            'ts_code': 'region_code',
            'name': 'region_name',
        }
        df = df.rename(columns=rename_map)

        return df

    def get_region_stocks(self, region_code: str, trade_date: str = None) -> pd.DataFrame:
        """获取指定地区的成分股（使用 Tushare 通达信接口）

        Args:
            region_code: 地区板块代码，如 '880207.TDX'
            trade_date: 交易日期 YYYYMMDD，默认使用最新日期

        Returns:
            DataFrame，列名：
            ts_code (成分股票代码), con_name (成分股票名称)
        """
        from config import get_pro_api

        pro = get_pro_api()
        if trade_date is None:
            trade_date = '20260327'  # 默认日期

        df = pro.tdx_member(ts_code=region_code, trade_date=trade_date)

        if df is None or len(df) == 0:
            return df

        # 重命名列以匹配数据库字段
        rename_map = {
            'con_code': 'ts_code',
            'con_name': 'name',
            'ts_code': 'region_code',
            'trade_date': 'trade_date'
        }
        df = df.rename(columns=rename_map)

        return df


if __name__ == '__main__':
    # 测试
    source = ConceptSource()

    print("=" * 50)
    print("测试概念板块获取")
    print("=" * 50)

    # 获取所有概念
    print("\n1. 获取所有概念板块:")
    df = source.get_all_concepts()
    print(f"   共 {len(df)} 个概念")
    print(df.head(3).to_string())

    # 获取某概念的成分股
    print("\n2. 获取锂矿概念成分股:")
    df = source.get_concept_stocks('锂矿概念')
    print(f"   共 {len(df)} 只股票")
    print(df.head(3).to_string())
