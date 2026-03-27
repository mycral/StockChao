# -*- coding: utf-8 -*-
"""
板块查询工具模块
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


def tool_get_all_concepts(limit: int = 100) -> list[dict]:
    """获取所有概念板块

    Args:
        limit: int, 返回数量限制，默认100

    Returns:
        list[dict]: 概念板块列表，按排名排序
        [
            {
                "rank": int,            # 排名
                "concept_name": str,    # 概念名称，如 "AI概念"
                "concept_code": str,    # 概念代码，如 "BK1173"
                "latest_price": float,  # 最新点位
                "changeAmt": float,     # 涨跌额
                "pct_chg": float,       # 涨跌幅(%)
                "total_mv": float,      # 总市值(元)
                "turnover_rate": float, # 换手率(%)
                "up_count": int,        # 上涨家数
                "down_count": int,     # 下跌家数
                "top_stock": str,      # 领涨股票
                "top_stock_pct": float # 领涨股票涨幅(%)
            }
        ]
        当出错时返回: [{"error": str}]
    """
    logger.info(f"[REQUEST] get_all_concepts | limit={limit}")
    try:
        with QueryDB(DB_PATH) as q:
            df = q.get_all_concepts()
            if df is None or len(df) == 0:
                return []
            df = df.head(limit) if len(df) > limit else df
            result = df.to_dict('records')
            logger.info(f"[RESPONSE] get_all_concepts | count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_all_concepts | {e}")
        return [{"error": str(e)}]


def tool_get_all_industries(limit: int = 100) -> list[dict]:
    """获取所有行业板块

    Args:
        limit: int, 返回数量限制，默认100

    Returns:
        list[dict]: 行业板块列表，按排名排序
        [
            {
                "rank": int,            # 排名
                "industry_name": str,   # 行业名称，如 "银行"
                "industry_code": str,   # 行业代码，如 "BK1621"
                "latest_price": float,  # 最新点位
                "changeAmt": float,     # 涨跌额
                "pct_chg": float,       # 涨跌幅(%)
                "total_mv": float,      # 总市值(元)
                "turnover_rate": float, # 换手率(%)
                "up_count": int,        # 上涨家数
                "down_count": int,     # 下跌家数
                "top_stock": str,       # 领涨股票
                "top_stock_pct": float # 领涨股票涨幅(%)
            }
        ]
        当出错时返回: [{"error": str}]
    """
    logger.info(f"[REQUEST] get_all_industries | limit={limit}")
    try:
        with QueryDB(DB_PATH) as q:
            df = q.get_all_industries()
            if df is None or len(df) == 0:
                return []
            df = df.head(limit) if len(df) > limit else df
            result = df.to_dict('records')
            logger.info(f"[RESPONSE] get_all_industries | count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_all_industries | {e}")
        return [{"error": str(e)}]


def tool_get_all_regions(limit: int = 50) -> list[dict]:
    """获取所有地区板块

    Args:
        limit: int, 返回数量限制，默认50

    Returns:
        list[dict]: 地区板块列表，按排名排序
        [
            {
                "rank": int,            # 排名
                "region_name": str,     # 地区名称，如 "北京地区"
                "region_code": str,     # 地区代码，如 "880216.TDX"
                "latest_price": float,  # 最新点位
                "changeAmt": float,     # 涨跌额
                "pct_chg": float,       # 涨跌幅(%)
                "total_mv": float,      # 总市值(元)
                "turnover_rate": float, # 换手率(%)
                "up_count": int,        # 上涨家数
                "down_count": int,      # 下跌家数
                "top_stock": str,       # 领涨股票
                "top_stock_pct": float  # 领涨股票涨幅(%)
            }
        ]
        当出错时返回: [{"error": str}]
    """
    logger.info(f"[REQUEST] get_all_regions | limit={limit}")
    try:
        with QueryDB(DB_PATH) as q:
            df = q.get_all_regions()
            if df is None or len(df) == 0:
                return []
            df = df.head(limit) if len(df) > limit else df
            result = df.to_dict('records')
            logger.info(f"[RESPONSE] get_all_regions | count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_all_regions | {e}")
        return [{"error": str(e)}]


def tool_get_concept_stocks(concept_name: str, limit: int = 100) -> list[dict]:
    """获取概念板块成分股

    Args:
        concept_name: str, 概念名称，如 "AI概念"、"人工智能"
        limit: int, 返回数量限制，默认100

    Returns:
        list[dict]: 成分股列表
        [
            {
                "ts_code": str,         # 股票代码，如 "002265.SZ"
                "symbol": str,         # 股票符号，如 "002265"
                "name": str,           # 股票名称，如 "桂林旅游"
                "latest_price": float, # 最新价
                "pct_chg": float       # 涨跌幅(%)
            }
        ]
        当出错时返回: [{"error": str}]
    """
    logger.info(f"[REQUEST] get_concept_stocks | concept_name={concept_name}, limit={limit}")
    try:
        with QueryDB(DB_PATH) as q:
            df = q.get_concept_stocks(concept_name=concept_name)
            if df is None or len(df) == 0:
                return []
            df = df.head(limit) if len(df) > limit else df
            result = df.to_dict('records')
            logger.info(f"[RESPONSE] get_concept_stocks | count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_concept_stocks | {e}")
        return [{"error": str(e)}]


def tool_get_industry_stocks(industry_name: str, limit: int = 100) -> list[dict]:
    """获取行业板块成分股

    Args:
        industry_name: str, 行业名称，如 "银行"、"半导体"
        limit: int, 返回数量限制，默认100

    Returns:
        list[dict]: 成分股列表
        [
            {
                "ts_code": str,         # 股票代码，如 "601988.SH"
                "symbol": str,         # 股票符号，如 "601988"
                "name": str,           # 股票名称，如 "中国银行"
                "latest_price": float, # 最新价
                "pct_chg": float       # 涨跌幅(%)
            }
        ]
                "name": str        # 股票名称，如 "中国银行"
            }
        ]
        当出错时返回: [{"error": str}]
    """
    logger.info(f"[REQUEST] get_industry_stocks | industry_name={industry_name}, limit={limit}")
    try:
        with QueryDB(DB_PATH) as q:
            df = q.get_industry_stocks(industry_name=industry_name)
            if df is None or len(df) == 0:
                return []
            df = df.head(limit) if len(df) > limit else df
            result = df.to_dict('records')
            logger.info(f"[RESPONSE] get_industry_stocks | count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_industry_stocks | {e}")
        return [{"error": str(e)}]


def tool_get_region_stocks(region_name: str, limit: int = 100) -> list[dict]:
    """获取地区板块成分股

    Args:
        region_name: str, 地区名称，如 "上海地区"、"北京地区"
        limit: int, 返回数量限制，默认100

    Returns:
        list[dict]: 成分股列表
        [
            {
                "ts_code": str,         # 股票代码，如 "600000.SH"
                "name": str,           # 股票名称，如 "浦发银行"
                "latest_price": float, # 最新价
                "pct_chg": float       # 涨跌幅(%)
            }
        ]
            }
        ]
        当出错时返回: [{"error": str}]
    """
    logger.info(f"[REQUEST] get_region_stocks | region_name={region_name}, limit={limit}")
    try:
        with QueryDB(DB_PATH) as q:
            df = q.get_region_stocks(region_name=region_name)
            if df is None or len(df) == 0:
                return []
            df = df.head(limit) if len(df) > limit else df
            result = df.to_dict('records')
            logger.info(f"[RESPONSE] get_region_stocks | count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_region_stocks | {e}")
        return [{"error": str(e)}]

# 向后兼容别名
get_all_concepts = tool_get_all_concepts
get_all_industries = tool_get_all_industries
get_all_regions = tool_get_all_regions
get_concept_stocks = tool_get_concept_stocks
get_industry_stocks = tool_get_industry_stocks
get_region_stocks = tool_get_region_stocks
