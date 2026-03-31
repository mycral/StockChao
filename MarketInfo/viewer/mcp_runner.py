# -*- coding: utf-8 -*-
"""
MCPRunner - MCP 后台运行器
独立线程调用 MCP 工具
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
import threading
from PySide6.QtCore import QObject, Signal


class MCPRunner(QObject):
    """MCP 后台运行器"""
    # 信号：call_id, tool_name, result
    result_ready = Signal(str, str, object)
    connected = Signal()
    error = Signal(str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self._thread = None
        self._loop = None
        self._client = None
        self._running = False

    def start(self):
        """启动后台线程"""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._setup())
        self._loop.run_forever()

    async def _setup(self):
        try:
            print(f"[MCP] 正在连接 {self.url}...")
            from fastmcp import Client
            self._client = Client(self.url)
            await self._client.__aenter__()
            print(f"[MCP] 连接成功!")
            self.connected.emit()
            await asyncio.Event().wait()
        except Exception as e:
            print(f"[MCP] 连接失败: {e}")
            self.error.emit(str(e))
            self._client = None

    def call_tool(self, call_id: str, tool_name: str, params: dict = None):
        """调用 MCP 工具"""
        if self._loop is None or self._client is None:
            self.result_ready.emit(call_id, tool_name, None)
            return
        asyncio.run_coroutine_threadsafe(
            self._do_call(call_id, tool_name, params or {}),
            self._loop
        )

    async def _do_call(self, call_id: str, tool_name: str, params: dict):
        try:
            result = await self._client.call_tool(tool_name, params)
            self.result_ready.emit(call_id, tool_name, result)
        except Exception as e:
            print(f"[MCP ←] {tool_name} | 失败: {e}")
            self.result_ready.emit(call_id, tool_name, None)

    def stop(self):
        """停止"""
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)