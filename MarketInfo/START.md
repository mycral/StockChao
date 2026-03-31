# MarketInfo 启动脚本

## 启动命令

### 终端1: 启动 OpenClaw Gateway
```bash
openclaw gateway
```

### 终端2: 启动 MCP 服务器
```bash
cd C:/Users/34475/Desktop/Work/同花顺选股代码/MarketInfo
python -m mcp_server.server --port 9876
```

### 终端3: 启动热点监控面板（可选）
```bash
cd C:/Users/34475/Desktop/Work/同花顺选股代码/MarketInfo
python viewer/topic_monitor.py
```