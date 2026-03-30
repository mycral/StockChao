# -*- coding: utf-8 -*-
"""测试 MCP 客户端连接"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio

async def test_sse_client():
    """使用 SSE 客户端测试"""
    try:
        from mcp.client.sse import sse_client
        url = "http://127.0.0.1:9876/mcp"
        async with sse_client(url) as (rx, tx):
            from mcp import ClientSession
            session = ClientSession(rx, tx)
            await session.initialize()
            print("SSE客户端: 连接成功!")

            # 测试调用工具
            result = await session.call_tool("get_topic_history", {"limit": 5})
            print(f"get_topic_history 结果: {result}")
            await session.close()
    except Exception as e:
        print(f"SSE客户端失败: {e}")

async def test_streamable_client():
    """使用 streamable-http 客户端测试"""
    try:
        from mcp.client.streamable_http import streamable_http_client
        url = "http://127.0.0.1:9876"
        async with streamable_http_client(url) as (rx, tx, get_session_id):
            from mcp import ClientSession
            session = ClientSession(rx, tx)
            await session.initialize()
            print("streamable-http客户端: 连接成功!")

            # 测试调用工具
            result = await session.call_tool("get_topic_history", {"limit": 5})
            print(f"get_topic_history 结果: {result}")
            await session.close()
    except Exception as e:
        print(f"streamable-http客户端失败: {e}")

async def test_requests_sse():
    """使用 requests 库手动发送 SSE 请求"""
    try:
        import requests
        import json

        # 发送 MCP 请求
        url = "http://127.0.0.1:9876/mcp"
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }

        # 初始化请求
        init_req = {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }

        response = requests.post(url, json=init_req, headers=headers, stream=True)
        print(f"初始化响应状态: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")

    except Exception as e:
        print(f"requests SSE 失败: {e}")

async def main():
    print("=" * 50)
    print("测试 MCP 客户端连接")
    print("=" * 50)

    print("\n[1] 测试 SSE 客户端...")
    await test_sse_client()

    print("\n[2] 测试 streamable-http 客户端...")
    await test_streamable_client()

    print("\n[3] 测试 requests SSE...")
    await test_requests_sse()

if __name__ == "__main__":
    asyncio.run(main())
