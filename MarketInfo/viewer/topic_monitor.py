# -*- coding: utf-8 -*-
"""
热点监控面板
基于PySide6 + Matplotlib（深色主题）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QMessageBox, QDialog, QGridLayout, QFrame, QApplication,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPalette, QColor

# 从独立模块导入
from viewer.stock_widget import StockWidget
from viewer.mcp_runner import MCPRunner
from viewer.mcp_settings import MCPSettingsDialog, get_mcp_url, get_fullscreen


# 深色主题样式
DARK_STYLE = """
QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: "Microsoft YaHei"; }
QLineEdit { background-color: #2d2d2d; border: 1px solid #404040; border-radius: 4px; padding: 4px; }
QPushButton { background-color: #0078d4; color: #fff; border: none; border-radius: 4px; padding: 6px 16px; }
QPushButton:hover { background-color: #1a8cff; }
QPushButton[secondary="true"] { background-color: #3c3c3c; color: #e0e0e0; }
QFrame#card { background-color: #252526; border: 1px solid #3c3c3c; border-radius: 8px; padding: 8px; }
QFrame#card:hover { border: 1px solid #0078d4; }
"""


class NewsDialog(QDialog):
    def __init__(self, news, parent=None):
        super().__init__(parent)
        self.setWindowTitle("利好消息")
        self.setStyleSheet(DARK_STYLE)
        self.resize(400, 200)
        layout = QVBoxLayout()
        label = QLabel(news if news else "无利好消息")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(label)
        btn = QPushButton("关闭")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        self.setLayout(layout)


class TopicMonitorPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.topics = []
        self._pending_calls = {}
        self._loading = True
        self.init_ui()
        self._init_mcp()

    def _init_mcp(self):
        self.status_label.setText("正在连接 MCP...")
        try:
            base_url = get_mcp_url().rstrip('/')
            url = f"{base_url}/mcp"
            self._mcp = MCPRunner(url)
            self._mcp.result_ready.connect(self._on_mcp_result)
            self._mcp.connected.connect(self._on_mcp_connected)
            self._mcp.start()
        except Exception as e:
            print(f"[MCP] 初始化失败: {e}")
            self.status_label.setText("MCP 连接失败")

    def _on_mcp_connected(self):
        print("[MCP] 连接已就绪")
        self.status_label.setText("MCP 已连接")
        self.status_label.setStyleSheet("color: #4caf50;")
        self.load_history()

    def _on_mcp_result(self, call_id: str, tool_name: str, result):
        if call_id in self._pending_calls:
            callback = self._pending_calls.pop(call_id)
            callback(result)

    def _call_mcp(self, tool_name: str, params: dict = None, callback=None):
        if self._mcp is None:
            if callback:
                callback(None)
            return
        import uuid
        call_id = f"{tool_name}_{uuid.uuid4().hex[:8]}"
        self._pending_calls[call_id] = callback or (lambda r: None)
        self._mcp.call_tool(call_id, tool_name, params)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._loading = False
            self.close()
        super().keyPressEvent(event)

    def init_ui(self):
        self.setStyleSheet(DARK_STYLE)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 控制栏
        control_layout = QHBoxLayout()
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("color: #808080;")
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("热点名称")
        control_layout.addWidget(QLabel("热点:"))
        control_layout.addWidget(self.name_input, 1)

        self.news_input = QLineEdit()
        self.news_input.setPlaceholderText("利好消息")
        control_layout.addWidget(QLabel("利好:"))
        control_layout.addWidget(self.news_input, 1)

        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.add_topic)
        control_layout.addWidget(add_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setProperty("secondary", True)
        refresh_btn.clicked.connect(self.load_history)
        control_layout.addWidget(refresh_btn)

        settings_btn = QPushButton("设置")
        settings_btn.setProperty("secondary", True)
        settings_btn.clicked.connect(self._open_settings)
        control_layout.addWidget(settings_btn)

        main_layout.addLayout(control_layout)

        # 热点网格
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(12)
        self.grid_widget.setLayout(self.grid_layout)
        main_layout.addWidget(self.grid_widget)

        self.setLayout(main_layout)

        # ��时刷新
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_history)
        self.timer.start(60000)

    def _open_settings(self):
        dialog = MCPSettingsDialog(self)
        if dialog.exec():
            self._init_mcp()

    def add_topic(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入热点名称")
            return
        news = self.news_input.text().strip()[:100]
        self._call_mcp("add_topic_history", {"name": name, "news": news}, self._on_add_result)

    def _on_add_result(self, _result):
        self.name_input.clear()
        self.news_input.clear()
        self.load_history()

    def refresh_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for slot in range(6):
            row, col = slot // 3, slot % 3
            if slot < len(self.topics):
                card = self.create_topic_card(self.topics[slot])
            else:
                card = self.create_empty_card()
            self.grid_layout.addWidget(card, row, col)

    def create_empty_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet("background-color: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 10px;")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout()
        label = QLabel("暂无热点")
        label.setFont(QFont("Microsoft YaHei", 14))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #505050;")
        layout.addWidget(label)
        card.setLayout(layout)
        return card

    def create_topic_card(self, topic: dict) -> QWidget:
        """创建热点卡片：只显示名称、利好、股票代码"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet("background-color: #252526; border: 1px solid #3c3c3c; border-radius: 8px; padding: 8px;")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout()
        layout.setSpacing(4)

        # 热点名称
        name = topic.get('name', '')
        name_label = QLabel(f"【{name}】")
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        name_label.setStyleSheet("color: #ff6b6b;")
        name_label.setAlignment(Qt.AlignCenter)

        # 删除按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("background-color: #404040; color: #fff; border: none; border-radius: 10px;")
        close_btn.clicked.connect(lambda: self.remove_topic(topic))

        top_layout = QHBoxLayout()
        top_layout.addWidget(name_label, 1)
        top_layout.addWidget(close_btn)
        layout.addLayout(top_layout)

        # 利好消息
        news = topic.get('news', '')
        if news:
            news_btn = QPushButton(f"📢 {news[:30]}...")
            news_btn.setFlat(True)
            news_btn.setStyleSheet("color: #a0a0a0; border: none; text-align: left; font-size: 11px;")
            news_btn.clicked.connect(lambda: NewsDialog(news, self).exec())
            layout.addWidget(news_btn)

        # 股票网格（只传代码，StockWidget 自己查询名称和分时）
        stock_grid = QGridLayout()
        stock_codes = topic.get('stock_codes', []) or []
        for i in range(6):
            r, c = i // 2, i % 2
            if i < len(stock_codes):
                # 只传代码，StockWidget 自治加载
                sw = self._create_stock_widget(stock_codes[i])
            else:
                sw = self._create_empty_stock_widget()
            stock_grid.addWidget(sw, r, c)
        layout.addLayout(stock_grid)

        card.setLayout(layout)
        return card

    def _create_stock_widget(self, ts_code: str) -> QWidget:
        """创建股票组件：传入代码字符串，StockWidget自治加载"""
        return StockWidget(ts_code)

    def _create_empty_stock_widget(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout()
        label = QLabel("—")
        label.setFont(QFont("Microsoft YaHei", 12))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #404040;")
        layout.addWidget(label)
        w.setLayout(layout)
        return w

    def load_history(self):
        self._call_mcp("get_topic_history", {"limit": 6}, self._on_history_result)

    def _on_history_result(self, result):
        topics = []
        if result and hasattr(result, 'content'):
            for item in result.content:
                if hasattr(item, 'text') and item.text:
                    try:
                        data = json.loads(item.text)
                        if isinstance(data, list):
                            topics.extend(data)
                    except:
                        pass
        self.topics = topics
        self.refresh_grid()

    def remove_topic(self, topic: dict):
        tid = topic.get('topic_id')
        if tid:
            self._call_mcp("delete_topic_history", {"topic_id": tid})
        if topic in self.topics:
            self.topics.remove(topic)
        self.refresh_grid()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
    dark_palette.setColor(QPalette.Base, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.Text, QColor(224, 224, 224))
    app.setPalette(dark_palette)

    panel = TopicMonitorPanel()
    panel.setWindowTitle("热点监控面板")
    if get_fullscreen():
        panel.showFullScreen()
    else:
        panel.show()
    app.exec()