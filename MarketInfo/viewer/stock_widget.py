# -*- coding: utf-8 -*-
"""
StockWidget - 自治股票组件
通过 MCP 获取股票名称 + 分时服务获取分时图
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import threading
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from viewer.kline_viewer import KLineChart
from viewer.minute_service import MinuteDataService


def normalize_code(code: str) -> str:
    """规范化股票代码"""
    if not code:
        return ''
    symbol = code.split('.')[0]
    if len(symbol) == 6:
        return f"{symbol}.SH" if symbol.startswith('6') else f"{symbol}.SZ"
    return code


# 股票名称缓存（模块级）
_stock_name_cache = {}

# 分时数据服务（模块级，单例）
_minute_service = MinuteDataService()


def get_stock_name_from_cache(ts_code: str) -> str:
    return _stock_name_cache.get(ts_code, ts_code)


def update_stock_name_cache(stock_data: dict):
    _stock_name_cache.update(stock_data)


class StockWidget(QWidget):
    """股票组件：显示名称 + 分时图"""

    def __init__(self, ts_code: str, mcp_call_func=None, parent=None):
        """
        Args:
            ts_code: 股票代码
            mcp_call_func: MCP调用函数，签名为 func(tool_name, params, callback)
        """
        super().__init__(parent)
        self.ts_code = normalize_code(ts_code or '')
        self.name = get_stock_name_from_cache(self.ts_code)
        self._mcp_call = mcp_call_func
        self._loading = True
        self._chart = None

        self._init_ui()

        # 延迟加载：先尝试名称，再加载分时
        if self.name == self.ts_code and mcp_call_func:
            QTimer.singleShot(300, self._fetch_name)
        QTimer.singleShot(500, self._fetch_minute)

    def _init_ui(self):
        self.setStyleSheet("background-color: #1e1e1e; border-radius: 4px; padding: 2px;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)

        # 名称标签
        self.name_label = QLabel(f"{self.name}({self.ts_code})")
        self.name_label.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("color: #ffb700; background: transparent; padding: 1px;")
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)

        # 图表占位（加载中）
        self.placeholder = QLabel("加载中...")
        self.placeholder.setFont(QFont("Microsoft YaHei", 8))
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("color: #606060; background: transparent;")
        layout.addWidget(self.placeholder)

        self.setLayout(layout)

    def _fetch_name(self):
        if not self._loading or not self._mcp_call:
            return

        self.name = get_stock_name_from_cache(self.ts_code)
        if self.name != self.ts_code:
            self._update_name_label()
            return

        try:
            self._mcp_call("get_stock_info", {"code": self.ts_code}, self._on_name_result)
        except Exception as e:
            print(f"[StockWidget] MCP查询失败 {self.ts_code}: {e}")

    def _on_name_result(self, result):
        if not self._loading:
            return
        if result and hasattr(result, 'content'):
            for item in result.content:
                if hasattr(item, 'text') and item.text:
                    try:
                        import json
                        data = json.loads(item.text)
                        if isinstance(data, dict):
                            name = data.get('name', self.ts_code)
                            update_stock_name_cache({self.ts_code: name})
                            self.name = name
                            QTimer.singleShot(0, self._update_name_label)
                    except:
                        pass

    def _update_name_label(self):
        self.name_label.setText(f"{self.name}({self.ts_code})")

    def _fetch_minute(self):
        if not self._loading:
            return

        # 直接通过服务获取（服务内部有缓存）
        thread = threading.Thread(target=self._fetch_minute_bg, daemon=True)
        thread.start()

    def _fetch_minute_bg(self):
        """后台线程获取分时数据"""
        if not self._loading:
            return
        try:
            # 使用分时服务获取（已处理类型转换和最后交易日过滤）
            df = _minute_service.get(self.ts_code)

            if df is not None and len(df) > 0:
                print(f"[StockWidget] {self.ts_code} 分时数据获取完成，行数: {len(df)}")
                # 回到主线程渲染（检查加载状态）
                QTimer.singleShot(0, lambda: self._loading and self._render_chart(df))
            else:
                print(f"[StockWidget] {self.ts_code} 无数据")
                QTimer.singleShot(0, self._show_error)
        except IndexError as e:
            # 分时数据源获取失败，可能是停牌或无数据
            print(f"[StockWidget] {self.ts_code} 无分时数据(可能停牌)")
            QTimer.singleShot(0, self._show_error)
        except Exception as e:
            print(f"[StockWidget] {self.ts_code} 获取失败: {e}")
            QTimer.singleShot(0, self._show_error)

    def _render_chart(self, df):
        if not self._loading or df is None or len(df) == 0:
            return

        # 移除占位
        if self.placeholder:
            self.layout().removeWidget(self.placeholder)
            self.placeholder.deleteLater()
            self.placeholder = None

        # 隐藏名称标签，节省空间
        if self.name_label:
            self.name_label.setVisible(False)

        # 创建图表
        chart = KLineChart(width=3, height=1.5, dpi=80)
        chart.plot_minute(df, self.ts_code, self.name)
        self.layout().addWidget(chart)
        self._chart = chart

    def _show_error(self):
        if self.name_label:
            self.name_label.setVisible(False)
        if self.placeholder:
            self.placeholder.setText("加载失败")
            self.placeholder.setStyleSheet("color: #c42b1c;")

    def close(self):
        self._loading = False
        super().close()