# -*- coding: utf-8 -*-
"""
新浪分时数据源
通过 AKShare 获取新浪财经分时数据
"""
import akshare as ak
from .base import MinuteSource


class SinaMinuteSource(MinuteSource):
    """新浪分时数据源"""

    @property
    def name(self) -> str:
        return "sina"

    def fetch(self, ts_code: str) -> pd.DataFrame:
        """获取分时数据

        Args:
            ts_code: 股票代码，如 '600519.SH'

        Returns:
            DataFrame 或 None
        """
        try:
            ak_symbol, _ = self.convert_code(ts_code)
            df = ak.stock_zh_a_minute(symbol=ak_symbol, period='1', adjust='')
            return df
        except Exception as e:
            print(f"[SinaMinuteSource] 获取 {ts_code} 失败: {e}")
            return None