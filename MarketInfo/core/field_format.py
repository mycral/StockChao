# -*- coding: utf-8 -*-
"""
数据字段格式规范（Field Format Specification）

本文档定义数据库中各类特殊字段的标准格式，供所有模块统一遵循。
"""
import re

# ==================== 股票代码 ts_code ====================
# 格式: 6位数字 + "." + 市场后缀
# 示例: 600519.SH, 000001.SZ, 300750.SZ, 688001.SH, 430001.BJ
# 规则:
#   - 6开头 -> 上海 (.SH)
#   - 0/3/4/8开头 -> 深圳 (.SZ)
#   - 430/830开头 -> 北交所 (.BJ)  [预留]
TS_CODE_PATTERN = re.compile(r'^\d{6}\.(SH|SZ|BJ)$')
TS_CODE_MARKET = {
    'SH': 'Shanghai',
    'SZ': 'Shenzhen',
    'BJ': 'Beijing',
}


def parse_ts_code(ts_code: str) -> tuple[str, str]:
    """解析股票代码

    Args:
        ts_code: 如 "600519.SH"

    Returns:
        (symbol, market): 如 ("600519", "SH")
    """
    if not ts_code or '.' not in str(ts_code):
        return '', ''
    parts = ts_code.split('.')
    return parts[0], parts[1]


def to_ts_code(symbol: str, market: str = None) -> str:
    """构造标准股票代码

    Args:
        symbol: 6位股票代码，如 "600519"
        market: 市场后缀，默认自动判断
                - 6开头 -> SH
                - 其他 -> SZ

    Returns:
        标准格式，如 "600519.SH"
    """
    symbol = str(symbol).strip()
    if len(symbol) != 6:
        return symbol  # 已有后缀或非法

    if market:
        return f"{symbol}.{market.upper()}"

    if symbol.startswith('6'):
        return f"{symbol}.SH"
    elif symbol.startswith(('0', '3', '4', '8')):
        return f"{symbol}.SZ"
    else:
        return f"{symbol}.SZ"  # 默认深圳


# ==================== 概念代码 concept_code ====================
# 格式: BK + 4位数字
# 示例: BK1173, BK0477, BK0888
# 来源: 同花顺/东方财富概念板块
CONCEPT_CODE_PATTERN = re.compile(r'^BK\d{4}$')


# ==================== 行业代码 industry_code ====================
# 格式: BK + 4位数字
# 示例: BK1621, BK0438
# 来源: 同花顺/东方财富行业板块
# 注意: 与 concept_code 格式相同，但含义不同（行业 vs 概念）
INDUSTRY_CODE_PATTERN = re.compile(r'^BK\d{4}$')


# ==================== 地区代码 region_code ====================
# 格式: 6位数字 + ".TDX"
# 示例: 880216.TDX, 880207.TDX
# 来源: 通达信地区板块代码
REGION_CODE_PATTERN = re.compile(r'^\d{6}\.TDX$')


# ==================== 交易日期 trade_date ====================
# 格式: YYYYMMDD
# 示例: 20260329, 20260101
TRADE_DATE_PATTERN = re.compile(r'^\d{8}$')


# ==================== 交易时间 trade_time ====================
# 格式: YYYYMMDDHHMMSS
# 示例: 20260329103000, 20260329150000
# 说明: 用于分钟数据表 minute_5min 等
TRADE_TIME_PATTERN = re.compile(r'^\d{14}$')


# ==================== 时间戳 timestamp (ms) ====================
# 格式: INTEGER，毫秒级 Unix 时间戳
# 示例: 1743262080000 (2026-03-29 14:00:00)
# 说明: 用于 topic_history 等记录型表的时间戳，便于比较和排序


def now_ms() -> int:
    """返回当前毫秒时间戳"""
    import time as _time
    return int(_time.time() * 1000)


def ts_to_str(ts: int) -> str:
    """ms时间戳 -> 可读字符串，格式 YYYYMMDD HHMMSS

    Args:
        ts: 毫秒时间戳，如 1743262080000

    Returns:
        如 "20260329 140000"
    """
    if not ts:
        return ''
    from datetime import datetime
    return datetime.fromtimestamp(ts / 1000).strftime('%Y%m%d %H%M%S')


def str_to_ts(s: str) -> int:
    """字符串 -> ms时间戳

    Args:
        s: 时间字符串，格式 YYYYMMDD HHMMSS

    Returns:
        毫秒时间戳
    """
    if not s:
        return 0
    from datetime import datetime
    return int(datetime.strptime(s, '%Y%m%d %H%M%S').timestamp() * 1000)


# ==================== 板块排名 rank ====================
# 格式: 整数，从1开始
# 说明: concept_board / industry_board 按涨跌幅排序后的序号
# 示例: 1, 2, 3, ... (1=涨幅最大)


# ==================== 字段验证函数 ====================

def is_valid_ts_code(code: str) -> bool:
    return bool(TS_CODE_PATTERN.match(str(code)))


def is_valid_concept_code(code: str) -> bool:
    return bool(CONCEPT_CODE_PATTERN.match(str(code)))


def is_valid_region_code(code: str) -> bool:
    return bool(REGION_CODE_PATTERN.match(str(code)))


def is_valid_trade_date(date: str) -> bool:
    return bool(TRADE_DATE_PATTERN.match(str(date)))


def is_valid_trade_time(time: str) -> bool:
    return bool(TRADE_TIME_PATTERN.match(str(time)))


if __name__ == '__main__':
    # 验证示例
    tests = [
        ("600519.SH", is_valid_ts_code),
        ("000001.SZ", is_valid_ts_code),
        ("688001.SH", is_valid_ts_code),
        ("BK1173", is_valid_concept_code),
        ("880216.TDX", is_valid_region_code),
        ("20260329", is_valid_trade_date),
        ("20260329103000", is_valid_trade_time),
    ]
    for val, func in tests:
        print(f"{val:20s} -> {func(val)}")

    # 测试时间戳函数
    print("\n时间戳函数测试:")
    ts = now_ms()
    print(f"now_ms() = {ts}")
    s = ts_to_str(ts)
    print(f"ts_to_str({ts}) = {s}")
    ts2 = str_to_ts(s)
    print(f"str_to_ts('{s}') = {ts2}")
    print(f"ts == ts2: {ts == ts2}")