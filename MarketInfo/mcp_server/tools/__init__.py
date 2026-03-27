# -*- coding: utf-8 -*-
"""
MCP 工具模块

导出所有可用的 MCP 工具
"""
from mcp_server.tools.search import (
    fuzzy_search,
    search_stocks,
    search_concepts,
    search_industries,
    search_regions,
)

from mcp_server.tools.stock import (
    get_stock_info,
    get_stock_daily,
    get_stock_concepts,
    get_stock_industries,
    get_stock_regions,
)

from mcp_server.tools.board import (
    get_all_concepts,
    get_all_industries,
    get_all_regions,
    get_concept_stocks,
    get_industry_stocks,
    get_region_stocks,
)

from mcp_server.tools.topic import (
    add_topic_history,
    get_topic_history,
    get_latest_topics,
)

__all__ = [
    # 搜索工具
    "fuzzy_search",
    "search_stocks",
    "search_concepts",
    "search_industries",
    "search_regions",
    # 股票查询工具
    "get_stock_info",
    "get_stock_daily",
    "get_stock_concepts",
    "get_stock_industries",
    "get_stock_regions",
    # 板块查询工具
    "get_all_concepts",
    "get_all_industries",
    "get_all_regions",
    "get_concept_stocks",
    "get_industry_stocks",
    "get_region_stocks",
    # 热点工具
    "add_topic_history",
    "get_topic_history",
    "get_latest_topics",
]
