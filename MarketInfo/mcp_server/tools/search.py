# -*- coding: utf-8 -*-
"""
搜索工具模块
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import DB_PATH
from core.query import QueryDB
from mcp_server.tools.stock import _resolve_code

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def tool_fuzzy_search(keyword: str, item_type: str = None, limit: int = 20) -> list[dict]:
    """模糊搜索股票/板块名称

    支持通过名称、拼音首字母、简称搜索股票、概念、行业、地区

    Args:
        keyword: str, 关键词（支持拼音首字母、简称、全拼）
        item_type: str|None, 类型过滤 (stock/concept/industry/region)，None 表示全部
        limit: int, 返回数量限制，默认20

    Returns:
        list[dict]: 搜索结果列表
        [
            {
                "id": int,
                "name": str,
                "name_pinyin": str,
                "name_short": str,
                "item_type": str,
                "code": str,
                "extra": None
            }
        ]
    """
    logger.info(f"[REQUEST] fuzzy_search | keyword={keyword}, item_type={item_type}, limit={limit}")
    try:
        with QueryDB(DB_PATH) as q:
            df = q.fuzzy_search(keyword, item_type, limit)
            result = df.to_dict('records') if df is not None and len(df) > 0 else []
            logger.info(f"[RESPONSE] fuzzy_search | count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] fuzzy_search | {e}")
        return [{"error": str(e)}]


def tool_search_stocks(keyword: str, limit: int = 10) -> list[dict]:
    """搜索股票

    Args:
        keyword: str, 股票名称或代码
        limit: int, 返回数量限制，默认10

    Returns:
        list[dict]: 股票列表
        [
            {
                "id": int,
                "name": str,
                "name_pinyin": str,
                "name_short": str,
                "item_type": "stock",
                "code": str,
                "extra": None
            }
        ]
    """
    return tool_fuzzy_search(keyword, item_type="stock", limit=limit)


def tool_search_concepts(keyword: str, limit: int = 10) -> list[dict]:
    """搜索概念板块

    Args:
        keyword: str, 概念名称
        limit: int, 返回数量限制，默认10

    Returns:
        list[dict]: 概念板块列表
        [
            {
                "id": int,
                "name": str,
                "name_pinyin": str,
                "name_short": str,
                "item_type": "concept",
                "code": str,
                "extra": None
            }
        ]
    """
    return tool_fuzzy_search(keyword, item_type="concept", limit=limit)


def tool_search_industries(keyword: str, limit: int = 10) -> list[dict]:
    """搜索行业板块

    Args:
        keyword: str, 行业名称
        limit: int, 返回数量限制，默认10

    Returns:
        list[dict]: 行业板块列表
        [
            {
                "id": int,
                "name": str,
                "name_pinyin": str,
                "name_short": str,
                "item_type": "industry",
                "code": str,
                "extra": None
            }
        ]
    """
    return tool_fuzzy_search(keyword, item_type="industry", limit=limit)


def tool_search_regions(keyword: str, limit: int = 10) -> list[dict]:
    """搜索地区板块

    Args:
        keyword: str, 地区名称
        limit: int, 返回数量限制，默认10

    Returns:
        list[dict]: 地区板块列表
        [
            {
                "id": int,
                "name": str,
                "name_pinyin": str,
                "name_short": str,
                "item_type": "region",
                "code": str,
                "extra": None
            }
        ]
    """
    return tool_fuzzy_search(keyword, item_type="region", limit=limit)


def tool_fuzzy_search_batch(keywords: list, item_type: str = None, limit_per_keyword: int = 5) -> list[dict]:
    """批量模糊搜索多个关键词

    Args:
        keywords: list, 关键词列表（如 ["茅台", "平安", "银行"]）
        item_type: str|None, 类型过滤 (stock/concept/industry/region)，None 表示全部
        limit_per_keyword: int, 每个关键词返回数量限制，默认5

    Returns:
        list[dict]: 所有搜索结果合并列表
        [
            {"keyword": str, "id": int, "name": str, "name_pinyin": str,
             "name_short": str, "item_type": str, "code": str, "extra": None},
            ...
        ]
    """
    logger.info(f"[REQUEST] fuzzy_search_batch | keywords_count={len(keywords)}, item_type={item_type}")

    results = []
    for keyword in keywords:
        try:
            with QueryDB(DB_PATH) as q:
                df = q.fuzzy_search(keyword, item_type, limit_per_keyword)
                if df is not None and len(df) > 0:
                    records = df.to_dict('records')
                    for r in records:
                        r['keyword'] = keyword  # 标记来源关键词
                    results.extend(records)
        except Exception as e:
            logger.error(f"[ERROR] fuzzy_search_batch | keyword={keyword}, error={e}")

    logger.info(f"[RESPONSE] fuzzy_search_batch | total_count={len(results)}")
    return results


def tool_resolve_code_batch(codes_or_names: list) -> list[dict]:
    """批量根据股票名称/代码解析为标准股票代码

    Args:
        codes_or_names: list, 股票代码或名称列表（如 ["贵州茅台", "600519.SH", "平安银行"]）

    Returns:
        list[dict]: 解析结果列表
        [
            {"input": str, "resolved_code": str, "name": str},
            ...
        ]
        input: 原始输入
        resolved_code: 解析后的代码（如 "600519.SH"），解析失败为 None
        name: 股票名称，解析失败为 None
    """
    logger.info(f"[REQUEST] resolve_code_batch | input_count={len(codes_or_names)}")

    results = []
    for code_or_name in codes_or_names:
        resolved = _resolve_code(code_or_name)
        name = None
        if resolved:
            try:
                with QueryDB(DB_PATH) as q:
                    df = q.get_stock_basic(ts_code=resolved)
                    if df is not None and len(df) > 0:
                        name = df.iloc[0].get('name')
            except:
                pass

        results.append({
            "input": code_or_name,
            "resolved_code": resolved,
            "name": name
        })

    logger.info(f"[RESPONSE] resolve_code_batch | success_count={sum(1 for r in results if r['resolved_code'])}")
    return results


# 向后兼容别名
fuzzy_search = tool_fuzzy_search
fuzzy_search_batch = tool_fuzzy_search_batch
resolve_code_batch = tool_resolve_code_batch
search_stocks = tool_search_stocks
search_concepts = tool_search_concepts
search_industries = tool_search_industries
search_regions = tool_search_regions
