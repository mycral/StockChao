# -*- coding: utf-8 -*-
"""
MarketInfo 服务管理器
内嵌日志窗口，双击按钮启动服务，关闭窗口进程退出
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QTabWidget, QTabBar, QMessageBox,
    QFrame, QScrollBar
)
from PySide6.QtCore import Qt, QProcess, Signal, QTimer, QProcessEnvironment
from PySide6.QtGui import QFont, QColor, QPalette, QTextCursor

# 服务配置
SERVICES = {
    "OpenClaw": {
        "command": "powershell",
        "args": ["-Command", "openclaw gateway"],
        "cwd": os.path.expanduser("~"),
        "description": "OpenClaw Gateway 服务"
    },
    "MCP Server": {
        "command": "python",
        "args": ["-m", "mcp_server.server", "--port", "9876"],
        "cwd": os.path.dirname(__file__),
        "description": "MCP 服务器"
    },
    "Topic Monitor": {
        "command": "python",
        "args": ["viewer/topic_monitor.py"],
        "cwd": os.path.dirname(__file__),
        "env": {"PYTHONUNBUFFERED": "1"},
        "description": "热点监控面板"
    }
}


class ServiceTab(QFrame):
    """服务标签页（包含日志输出）"""

    def __init__(self, name, config, parent=None):
        super().__init__(parent)
        self.name = name
        self.config = config
        self.process = None
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #3c3c3c;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部控制栏
        header = QFrame()
        header.setStyleSheet("background-color: #252526;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 8, 10, 8)

        self.status_label = QLabel("● 未启动")
        self.status_label.setStyleSheet("color: #808080; font-size: 13px; font-weight: bold;")

        self.start_btn = QPushButton("启动")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 70px;
            }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:disabled { background-color: #3c3c3c; color: #808080; }
        """)
        self.start_btn.clicked.connect(self.start_service)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #c42b1c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 70px;
            }
            QPushButton:hover { background-color: #d73429; }
            QPushButton:disabled { background-color: #3c3c3c; color: #808080; }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_service)

        # 清理日志按钮
        clear_btn = QPushButton("清理")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 60px;
            }
            QPushButton:hover { background-color: #505050; }
        """)
        clear_btn.clicked.connect(self.clear_log)

        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        header_layout.addWidget(self.start_btn)
        header_layout.addWidget(self.stop_btn)
        header.setLayout(header_layout)

        # 日志输出区域
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setStyleSheet("""
            QTextEdit {
                background-color: #0c0c0c;
                color: #cccccc;
                border: none;
                font-family: 'Consolas', 'Microsoft YaHei', monospace;
                font-size: 12px;
            }
        """)
        self.log_edit.setFont(QFont("Consolas", 11))

        layout.addWidget(header)
        layout.addWidget(self.log_edit)
        self.setLayout(layout)

    def start_service(self):
        """启动服务"""
        config = self.config

        self.process = QProcess(self)
        self.process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())

        # 设置环境变量
        env_config = config.get("env", {})
        if env_config:
            env = self.process.processEnvironment()
            for key, value in env_config.items():
                env.insert(key, value)
            self.process.setProcessEnvironment(env)

        # 设置工作目录
        cwd = config.get("cwd")
        if cwd:
            self.process.setWorkingDirectory(cwd)

        # 连接信号
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)

        # 启动进程
        cmd = config["command"]
        args = config.get("args", [])
        self.log(f"[启动] {cmd} {' '.join(args)}\n")
        self.process.start(cmd, args)

        # 更新状态
        self.status_label.setText("● 运行中")
        self.status_label.setStyleSheet("color: #4caf50; font-size: 13px; font-weight: bold;")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_service(self):
        """停止服务"""
        if self.process and self.process.state() == QProcess.Running:
            self.process.terminate()
            self.process.waitForFinished(3000)
            if self.process.state() == QProcess.Running:
                self.process.kill()
        self._on_finished(0, QProcess.NormalExit)

    def _decode_output(self, data):
        """尝试多种编码解码输出"""
        # QByteArray 转 bytes
        raw = bytes(data)
        # Windows 控制台可能是 GBK，服务器输出通常是 UTF-8
        for encoding in ['utf-8', 'gbk', 'cp936']:
            try:
                return raw.decode(encoding)
            except (UnicodeDecodeError, AttributeError):
                continue
        return raw.decode('utf-8', errors='replace')

    def _on_stdout(self):
        """标准输出"""
        data = self.process.readAllStandardOutput()
        text = self._decode_output(data)
        self.log(text, color="#cccccc")

    def _on_stderr(self):
        """错误输出"""
        data = self.process.readAllStandardError()
        text = self._decode_output(data)
        self.log(text, color="#ff6b6b")

    def _on_finished(self, exitCode, exitStatus):
        """进程结束"""
        self.status_label.setText("● 已停止")
        self.status_label.setStyleSheet("color: #808080; font-size: 13px; font-weight: bold;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log(f"\n[退出] 进程已结束 (exitCode: {exitCode})\n")

    def log(self, text, color="#cccccc"):
        """追加日志"""
        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.End)

        # 设置颜色
        format = cursor.charFormat()
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)

        cursor.insertText(text)
        self.log_edit.setTextCursor(cursor)
        self.log_edit.ensureCursorVisible()

    def clear_log(self):
        """清理日志"""
        self.log_edit.clear()

    def close(self):
        """关闭时停止进程"""
        self.stop_service()


class ServiceManager(QMainWindow):
    """服务管理器主窗口"""

    def __init__(self):
        super().__init__()
        self.tabs = {}
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("MarketInfo 服务管理器")
        self.setGeometry(100, 100, 900, 600)

        # 深色主题
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
        dark_palette.setColor(QPalette.Base, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.Text, QColor(224, 224, 224))
        self.setPalette(dark_palette)

        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部标题栏
        header = QFrame()
        header.setStyleSheet("background-color: #1e1e1e; border-bottom: 1px solid #3c3c3c;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("MarketInfo 服务管理器")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")

        header_layout.addWidget(title)
        header_layout.addStretch()

        # 关于按钮
        about_btn = QPushButton("关于")
        about_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover { background-color: #505050; }
        """)
        about_btn.clicked.connect(self._show_about)
        header_layout.addWidget(about_btn)

        header.setLayout(header_layout)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #252526;
                color: #808080;
                padding: 10px 20px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border-top: 2px solid #0078d4;
            }
            QTabBar::tab:hover {
                background-color: #2d2d2d;
            }
        """)

        # 添加每个服务的标签页
        for name, config in SERVICES.items():
            tab = ServiceTab(name, config)
            self.tabs[name] = tab
            self.tab_widget.addTab(tab, name)

        layout.addWidget(header)
        layout.addWidget(self.tab_widget)
        central.setLayout(layout)

    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", """
            <h3>MarketInfo 服务管理器</h3>
            <p>版本: 1.0.0</p>
            <p>基于 PySide6 构建</p>
            <p>管理 OpenClaw、MCP 服务器等服务的启动和停止</p>
        """)

    def closeEvent(self, event):
        """关闭时确认"""
        # 检查是否有服务在运行
        running = []
        for name, tab in self.tabs.items():
            if tab.process and tab.process.state() == QProcess.Running:
                running.append(name)

        if running:
            reply = QMessageBox.question(
                self, "确认退出",
                f"以下服务正在运行:\n{', '.join(running)}\n\n确定要退出吗？（将停止所有服务）",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

        # 停止所有服务
        for tab in self.tabs.values():
            tab.close()

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 设置样式
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
        }
    """)

    window = ServiceManager()
    window.show()
    app.exec()