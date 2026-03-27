# -*- coding: utf-8 -*-
"""
热点监控面板
基于PyQt5 + Matplotlib（深色主题）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QMessageBox, QDialog, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

import akshare as ak

from config import DB_PATH
from core.query import QueryDB
from viewer.kline_viewer import KLineChart

# ==================== 深色主题样式 ====================
DARK_STYLE = """
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}
QLabel {
    color: #e0e0e0;
}
QLineEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 4px 8px;
}
QLineEdit:focus {
    border: 1px solid #0078d4;
}
QLineEdit::placeholder {
    color: #808080;
}
QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    min-width: 80px;
}
QPushButton:hover {
    background-color: #1a8cff;
}
QPushButton:pressed {
    background-color: #005a9e;
}
QPushButton[secondary="true"] {
    background-color: #3c3c3c;
    color: #e0e0e0;
}
QPushButton[secondary="true"]:hover {
    background-color: #505050;
}
QPushButton[secondary="true"]:pressed {
    background-color: #2a2a2a;
}
QPushButton[danger="true"] {
    background-color: #c42b1c;
    color: #ffffff;
}
QPushButton[danger="true"]:hover {
    background-color: #d73429;
}
QScrollArea {
    background-color: #1e1e1e;
    border: none;
}
QFrame#card {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 8px;
    padding: 8px;
}
QFrame#card:hover {
    border: 1px solid #0078d4;
}
"""


def fetch_realtime_minute(symbol: str) -> pd.DataFrame:
    """通过AKShare获取个股分时数据

    Args:
        symbol: 股票代码（如 '600519.SH'）

    Returns:
        DataFrame: 分时数据
    """
    try:
        code = symbol.split('.')[0]
        suffix = symbol.split('.')[1].upper()

        if suffix == "SH":
            ak_symbol = f"sh{code}"
        else:
            ak_symbol = f"sz{code}"

        df = ak.stock_zh_a_minute(symbol=ak_symbol, period='1', adjust='')
        return df
    except Exception as e:
        print(f"[AKShare] 获取分时数据失败: {e}")
        return pd.DataFrame()


class NewsDialog(QDialog):
    """利好消息弹窗（深色主题）"""

    def __init__(self, news, parent=None):
        super().__init__(parent)
        self.setWindowTitle("利好消息")
        self.setStyleSheet(DARK_STYLE)
        self.resize(450, 220)

        layout = QVBoxLayout()
        label = QLabel(news if news else "无利好消息")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(label)

        btn = QPushButton("关闭")
        btn.setProperty("secondary", "true")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

        self.setLayout(layout)


class TopicMonitorPanel(QWidget):
    """热点监控面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.topics = []  # 当前监控的热点列表
        self.timer = None

        self.init_ui()
        self.load_history()

    def keyPressEvent(self, event):
        """ESC 退出全屏"""
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        super().keyPressEvent(event)

    def init_ui(self):
        """初始化界面（深色主题）"""
        self.setStyleSheet(DARK_STYLE)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 顶部控制栏
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        # 添加热点
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入热点名称，如 AI概念")
        lbl1 = QLabel("热点:")
        lbl1.setStyleSheet("color: #808080; padding: 0 4px;")
        control_layout.addWidget(lbl1)
        control_layout.addWidget(self.name_input, 1)

        # 利好消息
        self.news_input = QLineEdit()
        self.news_input.setPlaceholderText("利好消息（最多100字）")
        lbl2 = QLabel("利好:")
        lbl2.setStyleSheet("color: #808080; padding: 0 4px;")
        control_layout.addWidget(lbl2)
        control_layout.addWidget(self.news_input, 1)

        # 添加按钮
        add_btn = QPushButton("添加")
        add_btn.setToolTip("添加热点到监控列表")
        add_btn.clicked.connect(self.add_topic)
        control_layout.addWidget(add_btn)

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setProperty("secondary", "true")
        refresh_btn.setToolTip("立即刷新所有分时图（每30秒自动刷新）")
        refresh_btn.clicked.connect(self.start_refresh)
        control_layout.addWidget(refresh_btn)

        # 清除按钮
        clear_btn = QPushButton("清除")
        clear_btn.setProperty("secondary", "true")
        clear_btn.clicked.connect(self.clear_topics)
        control_layout.addWidget(clear_btn)

        main_layout.addLayout(control_layout)

        # 热点网格（固定6格，3x2，无滚动）
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(12)
        self.grid_layout.setRowStretch(0, 1)
        self.grid_layout.setRowStretch(1, 1)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 1)
        self.grid_widget.setLayout(self.grid_layout)

        main_layout.addWidget(self.grid_widget)

        self.setLayout(main_layout)

        # 定时器（30秒自动刷新）
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(30000)  # 启动自动刷新

    def add_topic(self):
        """添加热点（自动关联板块和股票）"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入热点名称")
            return

        news = self.news_input.text().strip()
        if len(news) > 100:
            news = news[:100]

        try:
            # 直接写入，query.py 自动填充关联信息
            with QueryDB(DB_PATH) as q:
                topic_id = q.add_topic_history(name=name, news=news)

            # 查询刚写入的记录，用 topic_id 精确定位
            with QueryDB(DB_PATH) as q:
                sql = "SELECT * FROM topic_history WHERE id = ?"
                df = pd.read_sql_query(sql, q.conn, params=[topic_id])
                if df is not None and len(df) > 0:
                    row = df.iloc[0]
                    stock_codes = json.loads(row['stock_codes']) if row['stock_codes'] else []
                    stock_names = json.loads(row['stock_names']) if row['stock_names'] else []
                    board_names = json.loads(row['board_names']) if row['board_names'] else []

                    # 构建 stocks 列表（最多6只）
                    stocks = []
                    for i in range(min(6, len(stock_codes))):
                        stocks.append({
                            'ts_code': stock_codes[i],
                            'name': stock_names[i] if i < len(stock_names) else ''
                        })

                    self.topics.append({
                        'name': row['name'],
                        'board_names': board_names,
                        'news': row['news'] or '',
                        'stocks': stocks,
                        'topic_id': topic_id
                    })

            # 清空输入
            self.name_input.clear()
            self.news_input.clear()

            # 刷新界面
            self.refresh_grid()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"添加热点失败: {e}")

    def refresh_grid(self):
        """刷新热点网格（固定6格，3x2）"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 固定3列 x 2行 = 6个热点槽位
        cols = 3
        for slot in range(6):
            row = slot // cols
            col = slot % cols
            if slot < len(self.topics):
                card = self.create_topic_card(self.topics[slot])
            else:
                card = self.create_empty_card()
            self.grid_layout.addWidget(card, row, col)

    def create_empty_card(self) -> QWidget:
        """创建空热点卡片"""
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(780)
        card.setStyleSheet("""
            QFrame#card {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout = QVBoxLayout()
        label = QLabel("暂无热点")
        label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #505050; background: transparent;")
        layout.addWidget(label)
        card.setLayout(layout)
        return card

    def create_topic_card(self, topic: dict) -> QWidget:
        """创建热点卡片（深色主题，大字体）"""
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(780)
        card.setStyleSheet("""
            QFrame#card {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 16px;
            }
            QFrame#card:hover {
                border: 1px solid #0078d4;
            }
        """)

        # 热点名称 + 板块名称
        name = topic.get('name', '')
        board_names = topic.get('board_names', [])
        board_text = ' / '.join(board_names) if board_names else ''
        name_text = f"【{name}】" + (f"\n({board_text})" if board_text else "")
        name_label = QLabel(name_text)
        name_label.setFixedHeight(90)
        name_label.setFont(QFont("Microsoft YaHei", 42, QFont.Bold))
        name_label.setStyleSheet("color: #ff6b6b; background: transparent;")
        name_label.setAlignment(Qt.AlignCenter)

        # 删除按钮 - 右上角圆形X
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: #e0e0e0;
                border: none;
                border-radius: 16px;
                font-size: 20px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #c42b1c;
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(lambda _, t=topic: self.remove_topic(t))

        # 卡片顶部水平布局（热点名称 + 删除按钮）
        card_top_layout = QHBoxLayout()
        card_top_layout.setSpacing(8)
        card_top_layout.addWidget(name_label, 1)
        card_top_layout.addWidget(close_btn)

        # 主垂直布局
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        # 热点名称 + 删除按钮
        layout.addLayout(card_top_layout)

        # 利好消息（大字体，点击弹窗显示全部）
        news = topic.get('news', '')
        if news:
            news_short = news[:60] + ('...' if len(news) > 60 else '')
            news_btn = QPushButton(f"📢 {news_short}")
            news_btn.setFlat(True)
            news_btn.setFixedHeight(30)
            news_btn.setStyleSheet("""
                QPushButton {
                    color: #a0a0a0;
                    border: none;
                    text-align: left;
                    padding: 4px 0;
                    font-size: 16px;
                    background: transparent;
                }
                QPushButton:hover {
                    color: #e0e0e0;
                }
            """)
            news_btn.clicked.connect(lambda _, n=news: NewsDialog(n, self).exec_())
            layout.addWidget(news_btn)

        # 股票分时图网格（2列，显示6只股票）
        stock_grid = QGridLayout()
        stock_grid.setSpacing(6)

        stocks = topic.get('stocks', [])
        for i in range(6):
            r = i // 2
            c = i % 2
            if i < len(stocks):
                stock = stocks[i]
                stock_widget = self._create_stock_widget(stock)
            else:
                stock_widget = self._create_empty_stock_widget()
            stock_grid.addWidget(stock_widget, r, c)

        layout.addLayout(stock_grid)

        card.setLayout(layout)
        return card

    def _create_stock_widget(self, stock: dict) -> QWidget:
        """创建股票分时图组件"""
        stock_widget = QWidget()
        stock_widget.setStyleSheet("background-color: #1e1e1e; border-radius: 4px; padding: 4px;")
        stock_layout = QVBoxLayout()
        stock_layout.setContentsMargins(2, 2, 2, 2)

        # 股票名称+代码：贵州茅台(600519.SH)
        stock_label = QLabel(f"{stock.get('name', '')}({stock.get('ts_code', '')})")
        stock_label.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        stock_label.setAlignment(Qt.AlignCenter)
        stock_label.setStyleSheet("color: #ffb700; background: transparent; padding: 2px;")
        stock_layout.addWidget(stock_label)

        chart = KLineChart(width=4, height=2.5, dpi=90)
        self.plot_minute_chart(chart, stock.get('ts_code', ''))
        stock_layout.addWidget(chart)

        stock_widget.setLayout(stock_layout)
        return stock_widget

    def _create_empty_stock_widget(self) -> QWidget:
        """创建空股票槽位"""
        stock_widget = QWidget()
        stock_widget.setStyleSheet("background-color: #1a1a1a; border-radius: 4px; padding: 4px;")
        stock_layout = QVBoxLayout()
        stock_layout.setContentsMargins(2, 2, 2, 2)

        label = QLabel("—")
        label.setFont(QFont("Microsoft YaHei", 16))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #404040; background: transparent;")
        stock_layout.addWidget(label)
        stock_widget.setLayout(stock_layout)
        return stock_widget

    def plot_minute_chart(self, chart: KLineChart, ts_code: str):
        """绘制分时图"""
        if not ts_code:
            return

        try:
            from core.query import QueryDB

            with QueryDB(DB_PATH) as q:
                df = q.get_topic_minute_data(ts_code)

            if df is None or len(df) == 0:
                df = fetch_realtime_minute(ts_code)

            if df is not None and len(df) > 0:
                name = ts_code
                try:
                    with QueryDB(DB_PATH) as q:
                        basic = q.get_stock_basic(ts_code=ts_code)
                        if basic is not None and len(basic) > 0:
                            name = basic.iloc[0].get('name', ts_code)
                except:
                    pass

                chart.plot_minute(df, ts_code, name)
        except Exception as e:
            print(f"[ERROR] 绘制分时图失败 {ts_code}: {e}")

    def refresh_all(self):
        """刷新：重新加载热点列表 + 刷新所有分时图"""
        self.load_history()

    def refresh_card_charts(self, card: QWidget):
        """刷新卡片内的分时图"""
        for child in card.findChildren(KLineChart):
            # 获取股票组件的内部布局
            stock_widget = child.parent()
            internal_layout = stock_widget.layout()
            if internal_layout:
                # 遍历股票组件内部的widget，找到股票名称
                for i in range(internal_layout.count()):
                    widget = internal_layout.itemAt(i).widget()
                    if isinstance(widget, QLabel):
                        text = widget.text()
                        if '(' in text and ')' in text:
                            ts_code = text.split('(')[-1].replace(')', '').strip()
                            if ts_code and '.' in ts_code:
                                self.plot_minute_chart(child, ts_code)
                                break

    def remove_topic(self, topic: dict):
        """移除热点"""
        if topic in self.topics:
            self.topics.remove(topic)
            self.refresh_grid()

    def clear_topics(self):
        """清除所有热点"""
        self.topics.clear()
        self.refresh_grid()

    def start_refresh(self):
        """手动刷新"""
        self.load_history()  # load_history 内部已调用 refresh_grid

    def load_history(self):
        """加载历史热点作为初始监控列表"""
        try:
            self.topics.clear()  # 先清空
            with QueryDB(DB_PATH) as q:
                df = q.get_topic_history(limit=6)  # 最多6个热点
                if df is not None and len(df) > 0:
                    for _, row in df.iterrows():
                        stock_codes = row.get('stock_codes', []) or []
                        stock_names = row.get('stock_names', []) or []
                        board_names = row.get('board_names', []) or []

                        stocks = []
                        for i in range(min(6, len(stock_codes))):  # 每热点最多6只股票
                            stocks.append({
                                'ts_code': stock_codes[i],
                                'name': stock_names[i] if i < len(stock_names) else ''
                            })

                        self.topics.append({
                            'name': row.get('name', ''),
                            'board_names': board_names,
                            'news': row.get('news', ''),
                            'stocks': stocks,
                            'topic_id': row.get('id')
                        })
                    self.refresh_grid()
        except Exception as e:
            print(f"[ERROR] 加载历史热点失败: {e}")


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 深色 palette
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.Base, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(0, 120, 212))
    dark_palette.setColor(QPalette.ToolTipText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.Text, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.Button, QColor(0, 120, 212))
    dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.Highlight, QColor(0, 120, 212))
    dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(dark_palette)

    panel = TopicMonitorPanel()
    panel.setWindowTitle("热点监控面板")
    panel.showFullScreen()
    app.exec_()