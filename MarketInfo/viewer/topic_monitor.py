# -*- coding: utf-8 -*-
"""
热点监控面板
基于PyQt5 + Matplotlib（深色主题）
数据通过 MCP 服务器访问
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
import json
import threading
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QMessageBox, QDialog, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPalette, QColor

import akshare as ak

from viewer.kline_viewer import KLineChart
from viewer.mcp_settings import MCPSettingsDialog, get_mcp_url


class MCPRunner(QObject):
    """MCP 后台运行器（独立线程 + 独立事件循环 + fastmcp.Client）"""
    # 信号：工具调用结果返回
    result_ready = pyqtSignal(str, str, object)  # call_id, tool_name, result
    connected = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        # streamable-http endpoint: http://127.0.0.1:9876/mcp
        self.url = url
        self._thread = None
        self._loop = None
        self._client = None
        self._running = False

    def start(self):
        """启动 MCP 后台线程"""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        """后台线程运行 asyncio 事件循环"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._setup())
        self._loop.run_forever()

    async def _setup(self):
        """初始化 MCP 连接"""
        try:
            print(f"[MCP] 正在连接 {self.url}...")
            from fastmcp import Client
            self._client = Client(self.url)
            await self._client.__aenter__()
            print(f"[MCP] 连接成功!")
            self.connected.emit()
            # 保持连接，等待工具调用
            await asyncio.Event().wait()
        except Exception as e:
            print(f"[MCP] 连接失败: {e}")
            self.error.emit(str(e))
            self._client = None

    def call_tool(self, call_id: str, tool_name: str, params: dict = None):
        """从主线程调用 MCP 工具（不阻塞）"""
        print(f"[MCP →] {tool_name} | params: {params}")
        if self._loop is None or self._client is None:
            print(f"[MCP ←] {tool_name} | 结果: None (未连接)")
            self.result_ready.emit(call_id, tool_name, None)
            return
        asyncio.run_coroutine_threadsafe(
            self._do_call(call_id, tool_name, params or {}),
            self._loop
        )

    async def _do_call(self, call_id: str, tool_name: str, params: dict):
        """在后台事件循环中执行 MCP 调用"""
        try:
            result = await self._client.call_tool(tool_name, params)
            # 打印详细返回值
            if result and hasattr(result, 'content'):
                print(f"[MCP ←] {tool_name} | content count: {len(result.content)}")
                for i, c in enumerate(result.content):
                    text = c.text[:100] if hasattr(c, 'text') and c.text else 'None'
                    print(f"[MCP ←] {tool_name} | content[{i}]: {text}...")
            else:
                print(f"[MCP ←] {tool_name} | result: {result}")
            self.result_ready.emit(call_id, tool_name, result)
        except Exception as e:
            print(f"[MCP ←] {tool_name} | 失败: {e}")
            self.result_ready.emit(call_id, tool_name, None)

# ==================== 深色主题样式 ====================
DARK_STYLE = """
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}
QLabel { color: #e0e0e0; }
QLineEdit {
    background-color: #2d2d2d; color: #e0e0e0;
    border: 1px solid #404040; border-radius: 4px; padding: 4px 8px;
}
QLineEdit:focus { border: 1px solid #0078d4; }
QLineEdit::placeholder { color: #808080; }
QPushButton {
    background-color: #0078d4; color: #ffffff;
    border: none; border-radius: 4px; padding: 6px 16px; min-width: 80px;
}
QPushButton:hover { background-color: #1a8cff; }
QPushButton:pressed { background-color: #005a9e; }
QPushButton[secondary="true"] { background-color: #3c3c3c; color: #e0e0e0; }
QPushButton[secondary="true"]:hover { background-color: #505050; }
QPushButton[secondary="true"]:pressed { background-color: #2a2a2a; }
QPushButton[danger="true"] { background-color: #c42b1c; color: #ffffff; }
QPushButton[danger="true"]:hover { background-color: #d73429; }
QFrame#card {
    background-color: #252526; border: 1px solid #3c3c3c;
    border-radius: 8px; padding: 8px;
}
QFrame#card:hover { border: 1px solid #0078d4; }
"""


def fetch_realtime_minute(symbol: str) -> pd.DataFrame:
    """通过AKShare获取个股分时数据"""
    try:
        code = symbol.split('.')[0]
        suffix = symbol.split('.')[1].upper()
        ak_symbol = f"sh{code}" if suffix == "SH" else f"sz{code}"
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
        self.topics = []       # 当前监控的热点列表
        self._pending_calls = {}  # 待处理的 MCP 调用 {tool_name: callback}

        self.init_ui()
        self._init_mcp()
        # 等 MCP 连接成功后再加载数据（在 _on_mcp_connected 中触发）

    def _init_mcp(self):
        """初始化 MCP 后台线程"""
        self.status_label.setText("正在连接 MCP...")
        try:
            base_url = get_mcp_url().rstrip('/')
            # MCP 服务器使用 streamable-http 传输
            url = f"{base_url}/mcp"
            self._mcp = MCPRunner(url)
            self._mcp.result_ready.connect(self._on_mcp_result)
            self._mcp.connected.connect(self._on_mcp_connected)
            self._mcp.start()
        except Exception as e:
            print(f"[MCP] 初始化失败: {e}")
            self.status_label.setText("MCP 连接失败")
            self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")
            self._mcp = None

    def _on_mcp_connected(self):
        """MCP 连接成功回调"""
        print("[MCP] 连接已就绪，开始加载数据")
        self.status_label.setText("MCP 已连接")
        self.status_label.setStyleSheet("color: #4caf50; font-size: 12px;")
        self.load_history()

    def _on_mcp_result(self, call_id: str, tool_name: str, result):
        """MCP 调用结果回调"""
        if call_id in self._pending_calls:
            callback = self._pending_calls.pop(call_id)
            callback(result)

    def _call_mcp(self, tool_name: str, params: dict = None, callback=None):
        """调用 MCP 工具（异步，不阻塞主线程）"""
        if self._mcp is None:
            if callback:
                callback(None)
            return
        import uuid
        call_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"
        self._pending_calls[call_id] = callback or (lambda r: None)
        self._mcp.call_tool(call_id, tool_name, params)

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

        # 连接状态标签
        self.status_label = QLabel("正在连接 MCP...")
        self.status_label.setStyleSheet("color: #808080; font-size: 12px;")
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()

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

        # 设置按钮
        settings_btn = QPushButton("设置")
        settings_btn.setProperty("secondary", "true")
        settings_btn.setToolTip("MCP 服务设置")
        settings_btn.clicked.connect(self._open_settings)
        control_layout.addWidget(settings_btn)

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
        self.timer.start(30000)

    def _open_settings(self):
        """打开设置弹窗"""
        dialog = MCPSettingsDialog(self)
        if dialog.exec_():
            # 重连 MCP
            self._init_mcp()

    def add_topic(self):
        """添加热点（通过 MCP）"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入热点名称")
            return

        news = self.news_input.text().strip()
        if len(news) > 100:
            news = news[:100]

        try:
            # MCP 异步调用
            self._call_mcp("add_topic_history", {
                "name": name,
                "news": news
            }, lambda result: self._on_add_topic_result(result, name, news))

        except Exception as e:
            QMessageBox.warning(self, "错误", f"添加热点失败: {e}")

    def _on_add_topic_result(self, result, name, news):
        """添加热点结果回调"""
        topic_id = None
        if result and hasattr(result, 'content'):
            for item in result.content:
                if hasattr(item, 'text') and item.text:
                    import json
                    try:
                        data = json.loads(item.text)
                        if isinstance(data, dict) and data.get('success'):
                            topic_id = data.get('id')
                            break
                    except:
                        pass

        if topic_id:
            # 成功后查询完整数据
            def on_history(history):
                topics = []
                if history and hasattr(history, 'content'):
                    for item in history.content:
                        if hasattr(item, 'text') and item.text:
                            import json
                            try:
                                data = json.loads(item.text)
                                if isinstance(data, list):
                                    topics.extend(data)
                            except:
                                pass
                for row in topics:
                    rid = row.get('id')
                    if rid == topic_id:
                        self._add_topic_from_row(row, topic_id)
                        break
                self.name_input.clear()
                self.news_input.clear()
                self.refresh_grid()

            self._call_mcp("get_topic_history", {"limit": 6}, on_history)
        else:
            # 需要在主线程中显示消息
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "错误", "MCP 服务不可用，无法添加热点"))


    def _add_topic_from_row(self, row, topic_id=None):
        """从记录行构建并添加热点"""
        if isinstance(row, dict):
            stock_codes = row.get('stock_codes', []) or []
            stock_names = row.get('stock_names', []) or []
            board_names = row.get('board_names', []) or []
            topic_id = topic_id or row.get('id')
        else:
            stock_codes = json.loads(row['stock_codes']) if row['stock_codes'] else []
            stock_names = json.loads(row['stock_names']) if row['stock_names'] else []
            board_names = json.loads(row['board_names']) if row['board_names'] else []
            topic_id = topic_id or row['id']

        stocks = []
        for i in range(min(6, len(stock_codes))):
            stocks.append({
                'ts_code': stock_codes[i],
                'name': stock_names[i] if i < len(stock_names) else ''
            })

        self.topics.append({
            'name': row.get('name', '') if isinstance(row, dict) else row['name'],
            'board_names': board_names,
            'news': row.get('news', '') if isinstance(row, dict) else (row['news'] or ''),
            'stocks': stocks,
            'topic_id': topic_id
        })

    def refresh_grid(self):
        """刷新热点网格（固定6格，3x2）"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
            QFrame#card { background-color: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 10px; }
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
            QFrame#card { background-color: #252526; border: 1px solid #3c3c3c; border-radius: 8px; padding: 16px; }
            QFrame#card:hover { border: 1px solid #0078d4; }
        """)

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
            QPushButton { background-color: #404040; color: #e0e0e0; border: none; border-radius: 16px; font-size: 20px; font-weight: bold; padding: 0; }
            QPushButton:hover { background-color: #c42b1c; color: #ffffff; }
        """)
        close_btn.clicked.connect(lambda _, t=topic: self.remove_topic(t))

        # 卡片顶部水平布局
        card_top_layout = QHBoxLayout()
        card_top_layout.setSpacing(8)
        card_top_layout.addWidget(name_label, 1)
        card_top_layout.addWidget(close_btn)

        # 主垂直布局
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(card_top_layout)

        # 利好消息
        news = topic.get('news', '')
        if news:
            news_short = news[:60] + ('...' if len(news) > 60 else '')
            news_btn = QPushButton(f"📢 {news_short}")
            news_btn.setFlat(True)
            news_btn.setFixedHeight(30)
            news_btn.setStyleSheet("""
                QPushButton { color: #a0a0a0; border: none; text-align: left; padding: 4px 0; font-size: 16px; background: transparent; }
                QPushButton:hover { color: #e0e0e0; }
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
            stock_widget = self._create_stock_widget(stocks[i]) if i < len(stocks) else self._create_empty_stock_widget()
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

        name = stock.get('name', '')
        if not name:
            ts_code = stock.get('ts_code', '')
            # 通过 MCP 获取股票名称
            result = self._call_mcp("get_stock_info", {"code": ts_code})
            if result and isinstance(result, dict):
                name = result.get('name', ts_code) or ts_code
            else:
                name = ts_code

        stock_label = QLabel(f"{name}({stock.get('ts_code', '')})")
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
        """绘制分时图（通过 AKShare 获取数据）"""
        if not ts_code:
            return
        try:
            # 通过 AKShare 获取分时数据
            df = fetch_realtime_minute(ts_code)
            if df is not None and len(df) > 0:
                # 获取股票名称（走 MCP）
                name = ts_code
                result = self._call_mcp("get_stock_info", {"code": ts_code})
                if result and isinstance(result, dict):
                    name = result.get('name', ts_code) or ts_code
                chart.plot_minute(df, ts_code, name)
        except Exception as e:
            print(f"[ERROR] 绘制分时图失败 {ts_code}: {e}")

    def refresh_all(self):
        """刷新：重新加载热点列表 + 刷新所有分时图"""
        self.load_history()

    def remove_topic(self, topic: dict):
        """移除热点（通过 MCP）"""
        topic_id = topic.get('topic_id')
        if topic_id:
            self._call_mcp("delete_topic_history", {"topic_id": topic_id})
        if topic in self.topics:
            self.topics.remove(topic)
        self.refresh_grid()

    def clear_topics(self):
        """清除所有热点（通过 MCP）"""
        reply = QMessageBox.question(self, "确认", "确定要清空所有热点历史记录吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._call_mcp("clear_all_topic_history", {})
            self.topics.clear()
            self.refresh_grid()

    def start_refresh(self):
        """手动刷新"""
        self.load_history()

    def load_history(self):
        """加载历史热点（通过 MCP，异步）"""
        def on_result(result):
            # 解析 MCP 返回结果
            topics = []
            if result and hasattr(result, 'content'):
                for item in result.content:
                    if hasattr(item, 'text') and item.text:
                        import json
                        try:
                            data = json.loads(item.text)
                            if isinstance(data, list):
                                topics.extend(data)
                        except:
                            pass

            if topics:
                self.topics.clear()
                for row in topics:
                    self._add_topic_from_row(row)
            else:
                self.topics.clear()
            self.refresh_grid()

        self._call_mcp("get_topic_history", {"limit": 6}, on_result)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

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