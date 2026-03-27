# -*- coding: utf-8 -*-
"""
股票查询工具模块
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import DB_PATH
from core.query import QueryDB

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _resolve_code(code: str) -> str:
    """解析股票代码

    如果传入的是名称，先搜索再返回代码
    """
    if code is None:
        return None

    # 如果已经是代码格式 (6位数字.XX)
    if '.' in str(code) and len(str(code)) == 10:
        return code

    # 如果是纯数字代码，尝试转换
    if str(code).isdigit() and len(str(code)) == 6:
        if code.startswith('6'):
            return f"{code}.SH"
        else:
            return f"{code}.SZ"

    # 如果是名称，搜索获取代码
    try:
        with QueryDB(DB_PATH) as q:
            df = q.fuzzy_search(code, item_type="stock", limit=1)
            if df is not None and len(df) > 0:
                return df.iloc[0]['code']
    except:
        pass

    return code


def tool_get_stock_info(code: str) -> dict:
    """获取股票基本信息

    Args:
        code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）

    Returns:
        dict: 股票基本信息
        {
            "ts_code": str,      # 股票代码，如 "600519.SH"
            "symbol": str,       # 股票符号，如 "600519"
            "name": str,         # 股票名称，如 "贵州茅台"
            "area": None,        # 所属地区
            "industry": None,    # 所属行业
            "market": None,      # 所属市场
            "list_date": str,    # 上市日期，如 "20010110"
            "delist_date": None, # 退市日期
            "is_hs": None,       # 是否沪深港通
            "latest_price": float # 最新收盘价
        }
        当出错时返回: {"error": str}
    """
    logger.info(f"[REQUEST] get_stock_info | code={code}")
    try:
        code = _resolve_code(code)
        if not code:
            return {"error": "无法解析股票代码"}

        with QueryDB(DB_PATH) as q:
            df = q.get_stock_basic(ts_code=code)
            if df is None or len(df) == 0:
                return {"error": f"未找到股票 {code}"}
            result = df.iloc[0].to_dict()
            logger.info(f"[RESPONSE] get_stock_info | code={code}, name={result.get('name')}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_stock_info | {e}")
        return {"error": str(e)}


def tool_get_stock_info_batch(codes: list) -> dict:
    """批量获取股票基本信息

    比逐个调用 get_stock_info 更高效，一次查询多只股票

    Args:
        codes: list, 股票代码列表（如 ["600519.SH", "000001.SZ"]）或名称列表
               最多50只股票，超出部分截断

    Returns:
        dict: 批量股票基本信息
        {
            "600519.SH": {"ts_code": "600519.SH", "symbol": "600519", "name": "贵州茅台", ...},
            "000001.SZ": {"ts_code": "000001.SZ", "symbol": "000001", "name": "平安银行", ...}
        }
        当出错时返回: {"error": str}
    """
    logger.info(f"[REQUEST] get_stock_info_batch | codes_count={len(codes)}")

    if len(codes) > 50:
        codes = codes[:50]

    # 解析所有股票代码
    resolved_codes = []
    for code in codes:
        resolved = _resolve_code(code)
        if resolved:
            resolved_codes.append(resolved)

    if not resolved_codes:
        return {"error": "无法解析股票代码"}

    try:
        with QueryDB(DB_PATH) as q:
            result = {}
            for code in resolved_codes:
                df = q.get_stock_basic(ts_code=code)
                if df is not None and len(df) > 0:
                    result[code] = df.iloc[0].to_dict()
            logger.info(f"[RESPONSE] get_stock_info_batch | result_count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_stock_info_batch | {e}")
        return {"error": str(e)}


def tool_get_stock_daily(code: str, start_date: str = None, end_date: str = None, limit: int = 100) -> list[dict]:
    """获取股票日线数据

    Args:
        code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）
        start_date: str|None, 开始日期，格式 YYYYMMDD，如 "20260101"
        end_date: str|None, 结束日期，格式 YYYYMMDD，如 "20260329"
        limit: int, 返回条数限制，默认100

    Returns:
        list[dict]: 日线数据列表，最新日期在前
        [
            {
                "ts_code": str,       # 股票代码，如 "600519.SH"
                "trade_date": str,    # 交易日期，如 "20260329"
                "open": float,        # 开盘价
                "high": float,        # 最高价
                "low": float,         # 最低价
                "close": float,       # 收盘价
                "pre_close": float,   # 昨收价
                "change": float,      # 涨跌额
                "pct_chg": float,     # 涨跌幅(%)
                "vol": float,         # 成交量(手)
                "amount": float       # 成交额(元)
            }
        ]
        当出错时返回: [{"error": str}]
    """
    logger.info(f"[REQUEST] get_stock_daily | code={code}, start={start_date}, end={end_date}, limit={limit}")
    try:
        code = _resolve_code(code)
        if not code:
            return [{"error": "无法解析股票代码"}]

        with QueryDB(DB_PATH) as q:
            df = q.get_daily(code, start_date, end_date)
            if df is None or len(df) == 0:
                return []
            # 限制返回条数并反转顺序（最新在前）
            df = df.tail(limit) if len(df) > limit else df
            result = df.to_dict('records')
            logger.info(f"[RESPONSE] get_stock_daily | count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_stock_daily | {e}")
        return [{"error": str(e)}]


def tool_get_stock_daily_batch(codes: list, limit: int = 30) -> dict:
    """批量获取多只股票的最近日线数据

    比逐个调用 get_stock_daily 更高效，一次查询多只股票

    Args:
        codes: list, 股票代码列表（如 ["600519.SH", "000001.SZ"]）或名称列表
               最多30只股票，超出部分截断
        limit: int, 每只股票返回的交易日数，默认30，最多30个

    Returns:
        dict: 批量日线数据
        {
            "600519.SH": [
                {"ts_code": str, "trade_date": str, "open": float, "high": float,
                 "low": float, "close": float, "pre_close": float, "change": float,
                 "pct_chg": float, "vol": float, "amount": float},
                ...
            ],
            "000001.SZ": [...]
        }
    """
    logger.info(f"[REQUEST] get_stock_daily_batch | codes_count={len(codes)}, limit={limit}")

    if len(codes) > 30:
        codes = codes[:30]
    if limit > 30:
        limit = 30

    # 解析所有股票代码
    resolved_codes = []
    for code in codes:
        resolved = _resolve_code(code)
        if resolved:
            resolved_codes.append(resolved)

    if not resolved_codes:
        return {"error": "无法解析股票代码"}

    try:
        with QueryDB(DB_PATH) as q:
            result = q.get_daily_batch(resolved_codes, limit)
            logger.info(f"[RESPONSE] get_stock_daily_batch | result_count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_stock_daily_batch | {e}")
        return {"error": str(e)}


def tool_get_stock_concepts(code: str) -> list[dict]:
    """获取股票所属概念板块

    Args:
        code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）

    Returns:
        list[dict]: 概念板块列表
        [
            {
                "concept_code": str,   # 概念代码，如 "BK0477"
                "concept_name": str    # 概念名称，如 "白酒概念"
            }
        ]
        当出错时返回: [{"error": str}]
    """
    try:
        code = _resolve_code(code)
        if not code:
            return [{"error": "无法解析股票代码"}]

        with QueryDB(DB_PATH) as q:
            df = q.get_stock_concepts(ts_code=code)
            logger.info(f"[RESPONSE] get_stock_concepts | count={len(df) if df is not None else 0}")
            return df.to_dict('records') if df is not None and len(df) > 0 else []
    except Exception as e:
        logger.error(f"[ERROR] get_stock_concepts | {e}")
        return [{"error": str(e)}]


def tool_get_stock_industries(code: str) -> list[dict]:
    """获取股票所属行业板块

    Args:
        code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）

    Returns:
        list[dict]: 行业板块列表
        [
            {
                "industry_code": str,   # 行业代码，如 "BK0438"
                "industry_name": str    # 行业名称，如 "食品饮料"
            }
        ]
        当出错时返回: [{"error": str}]
    """
    try:
        code = _resolve_code(code)
        if not code:
            return [{"error": "无法解析股票代码"}]

        with QueryDB(DB_PATH) as q:
            df = q.get_stock_industries(ts_code=code)
            logger.info(f"[RESPONSE] get_stock_industries | count={len(df) if df is not None else 0}")
            return df.to_dict('records') if df is not None and len(df) > 0 else []
    except Exception as e:
        logger.error(f"[ERROR] get_stock_industries | {e}")
        return [{"error": str(e)}]


def tool_get_stock_regions(code: str) -> list[dict]:
    """获取股票所属地区板块

    Args:
        code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）

    Returns:
        list[dict]: 地区板块列表
        [
            {
                "region_code": str,   # 地区代码，如 "880229.TDX"
                "region_name": str     # 地区名称，如 "贵州板块"
            }
        ]
        当出错时返回: [{"error": str}]
    """
    try:
        code = _resolve_code(code)
        if not code:
            return [{"error": "无法解析股票代码"}]

        with QueryDB(DB_PATH) as q:
            df = q.get_stock_regions(ts_code=code)
            logger.info(f"[RESPONSE] get_stock_regions | count={len(df) if df is not None else 0}")
            return df.to_dict('records') if df is not None and len(df) > 0 else []
    except Exception as e:
        logger.error(f"[ERROR] get_stock_regions | {e}")
        return [{"error": str(e)}]

# 向后兼容别名
get_stock_info = tool_get_stock_info
get_stock_info_batch = tool_get_stock_info_batch
get_stock_daily = tool_get_stock_daily
get_stock_daily_batch = tool_get_stock_daily_batch
get_stock_concepts = tool_get_stock_concepts
get_stock_industries = tool_get_stock_industries
get_stock_regions = tool_get_stock_regions
