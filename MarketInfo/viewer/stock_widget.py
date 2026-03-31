# -*- coding: utf-8 -*-
"""
StockWidget - 自治股票组件（简化版）
暂时只显示代码，不加载分时图
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


def normalize_code(code: str) -> str:
    """规范化股票代码"""
    if not code:
        return ''
    symbol = code.split('.')[0]
    if len(symbol) == 6:
        return f"{symbol}.SH" if symbol.startswith('6') else f"{symbol}.SZ"
    return code


class StockWidget(QWidget):
    """简化版股票组件：只显示代码"""

    def __init__(self, ts_code: str, parent=None):
        super().__init__(parent)
        self.ts_code = normalize_code(ts_code or '')
        self._loading = True
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("background-color: #1e1e1e; border-radius: 4px; padding: 2px;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)

        # 显示代码文本
        self.code_label = QLabel(self.ts_code)
        self.code_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self.code_label.setAlignment(Qt.AlignCenter)
        self.code_label.setStyleSheet("color: #ffb700; background: transparent; padding: 1px;")
        layout.addWidget(self.code_label)

        self.setLayout(layout)

    def close(self):
        self._loading = False
        super().close()