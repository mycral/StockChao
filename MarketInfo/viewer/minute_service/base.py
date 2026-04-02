# -*- coding: utf-8 -*-
"""
分时数据源抽象基类
定义数据源接口
"""
from abc import ABC, abstractmethod
import pandas as pd


class MinuteSource(ABC):
    """分时数据源抽象基类"""

    @abstractmethod
    def fetch(self, ts_code: str) -> pd.DataFrame:
        """获取单只股票分时数据

        Args:
            ts_code: 股票代码，如 '600519.SH'

        Returns:
            DataFrame，列: day, open, high, low, close, volume, amount
            返回 None 表示获取失败
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        pass

    def convert_code(self, ts_code: str) -> tuple:
        """转换股票代码为 AKShare 格式

        Args:
            ts_code: 如 '600519.SH'

        Returns:
            (symbol, market) - 如 ('sh600519', 'SH')
        """
        code = ts_code.split('.')[0]
        suffix = ts_code.split('.')[1].upper()
        ak_symbol = f"sh{code}" if suffix == "SH" else f"sz{code}"
        return ak_symbol, suffix