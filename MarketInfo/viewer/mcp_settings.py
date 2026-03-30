# -*- coding: utf-8 -*-
"""
MCP 设置管理
- 加载/保存用户配置到 ~/.marketinfo/settings.json
- 提供设置弹窗界面
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt

# 设置文件路径
SETTINGS_DIR = Path.home() / ".marketinfo"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

# 默认值
DEFAULT_MCP_URL = "http://127.0.0.1:9876"

# 全局设置
_settings = None


def get_settings() -> dict:
    """加载设置，返回设置字典"""
    global _settings
    if _settings is not None:
        return _settings

    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                _settings = json.load(f)
        except Exception:
            _settings = {"mcp_server_url": DEFAULT_MCP_URL}
    else:
        _settings = {"mcp_server_url": DEFAULT_MCP_URL}
    return _settings


def save_settings(settings: dict):
    """保存设置到文件"""
    global _settings
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    _settings = settings


def get_mcp_url() -> str:
    """获取 MCP 服务地址"""
    return get_settings().get("mcp_server_url", DEFAULT_MCP_URL)


class MCPSettingsDialog(QDialog):
    """MCP 设置弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MCP 服务设置")
        self.setStyleSheet("""
            QWidget { background-color: #252526; color: #e0e0e0; font-family: "Microsoft YaHei", sans-serif; }
            QLineEdit { background-color: #1e1e1e; color: #e0e0e0; border: 1px solid #404040; border-radius: 4px; padding: 6px; }
            QPushButton { background-color: #0078d4; color: #fff; border: none; border-radius: 4px; padding: 6px 20px; }
            QPushButton:hover { background-color: #1a8cff; }
        """)
        self.resize(420, 140)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # MCP 服务地址
        url_layout = QHBoxLayout()
        url_label = QLabel("MCP 服务地址:")
        url_label.setStyleSheet("color: #a0a0a0;")
        self.url_input = QLineEdit()
        self.url_input.setText(get_mcp_url())
        self.url_input.setPlaceholderText("http://127.0.0.1:9876")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input, 1)
        layout.addLayout(url_layout)

        # 连接状态
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #808080; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton { background-color: #3c3c3c; color: #e0e0e0; }
            QPushButton:hover { background-color: #505050; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _on_save(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入 MCP 服务地址")
            return
        if not url.startswith("http://") and not url.startswith("https://"):
            QMessageBox.warning(self, "提示", "地址必须以 http:// 或 https:// 开头")
            return

        save_settings({"mcp_server_url": url})
        self.status_label.setText(f"✓ 已保存: {url}")
        self.status_label.setStyleSheet("color: #4caf50; font-size: 12px;")
        QMessageBox.information(self, "成功", f"MCP 服务地址已保存:\n{url}")
        self.accept()