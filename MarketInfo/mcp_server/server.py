# -*- coding: utf-8 -*-
"""
MarketInfo MCP Server

MCP 服务器，供大模型调用 MarketInfo 数据库
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_server.tools.search import tool_fuzzy_search, tool_search_stocks, tool_search_concepts, tool_search_industries, tool_search_regions, tool_fuzzy_search_batch, tool_resolve_code_batch
from mcp_server.tools.stock import tool_get_stock_info, tool_get_stock_info_batch, tool_get_stock_daily, tool_get_stock_daily_batch, tool_get_stock_concepts, tool_get_stock_industries, tool_get_stock_regions
from mcp_server.tools.board import tool_get_all_concepts, tool_get_all_industries, tool_get_all_regions, tool_get_concept_stocks, tool_get_industry_stocks, tool_get_region_stocks
from mcp_server.tools.topic import tool_add_topic_history, tool_get_topic_history, tool_get_latest_topics, tool_delete_topic_history, tool_clear_all_topic_history

# MCP Server metadata
SERVER_NAME = "MarketInfo"
SERVER_VERSION = "1.0.0"
SERVER_DESCRIPTION = "股票行情和板块数据查询服务"

__all__ = [
    "fuzzy_search",
    "search_stocks",
    "search_concepts",
    "search_industries",
    "search_regions",
    "get_stock_info",
    "get_stock_info_batch",
    "get_stock_daily",
    "get_stock_daily_batch",
    "get_stock_concepts",
    "get_stock_industries",
    "get_stock_regions",
    "get_all_concepts",
    "get_all_industries",
    "get_all_regions",
    "get_concept_stocks",
    "get_industry_stocks",
    "get_region_stocks",
    "add_topic_history",
    "get_topic_history",
    "get_latest_topics",
    "delete_topic_history",
    "clear_all_topic_history",
]


def main(host: str = "127.0.0.1", port: int = 9876):
    """启动 MCP 服务器

    使用方式:
        python -m mcp_server.server

    支持参数:
        python -m mcp_server.server --host 0.0.0.0 --port 8080

    Args:
        host: 服务地址，默认 127.0.0.1
        port: 服务端口，默认 8000
    """
    import argparse

    parser = argparse.ArgumentParser(description="MarketInfo MCP Server")
    parser.add_argument("--host", default=host, help="服务地址")
    parser.add_argument("--port", type=int, default=port, help="服务端口")
    args = parser.parse_args()
    try:
        from fastmcp import FastMCP
    except ImportError:
        print("错误: 请先安装 fastmcp")
        print("  pip install fastmcp>=0.1.0")
        sys.exit(1)

    # 创建 FastMCP 应用
    app = FastMCP(
        name=SERVER_NAME,
        version=SERVER_VERSION,
    )

    # ==================== 搜索工具 ====================

    @app.tool()
    def fuzzy_search(
        keyword: str,
        item_type: str = None,
        limit: int = 20
    ) -> list[dict]:
        """模糊搜索股票/板块名称

        支持通过名称、拼音首字母、简称搜索股票、概念、行业、地区

        Args:
            keyword: str, 关键词（支持拼音首字母、简称、全拼）
            item_type: str|None, 类型过滤 (stock/concept/industry/region)，None 表示全部
            limit: int, 返回数量限制，默认20

        Returns:
            list[dict]: 搜索结果列表
            [
                {"id": int, "name": str, "name_pinyin": str, "name_short": str, "item_type": str, "code": str, "extra": None}
            ]
        """
        return tool_fuzzy_search(keyword, item_type, limit)

    @app.tool()
    def search_stocks(keyword: str, limit: int = 10) -> list[dict]:
        """搜索股票

        Args:
            keyword: str, 股票名称或代码
            limit: int, 返回数量限制，默认10

        Returns:
            list[dict]: 股票列表
            [
                {"id": int, "name": str, "name_pinyin": str, "name_short": str, "item_type": "stock", "code": str, "extra": None}
            ]
        """
        return tool_fuzzy_search(keyword, item_type="stock", limit=limit)

    @app.tool()
    def search_concepts(keyword: str, limit: int = 10) -> list[dict]:
        """搜索概念板块

        Args:
            keyword: str, 概念名称
            limit: int, 返回数量限制，默认10

        Returns:
            list[dict]: 概念板块列表
            [
                {"id": int, "name": str, "name_pinyin": str, "name_short": str, "item_type": "concept", "code": str, "extra": None}
            ]
        """
        return tool_fuzzy_search(keyword, item_type="concept", limit=limit)

    @app.tool()
    def search_industries(keyword: str, limit: int = 10) -> list[dict]:
        """搜索行业板块

        Args:
            keyword: str, 行业名称
            limit: int, 返回数量限制，默认10

        Returns:
            list[dict]: 行业板块列表
            [
                {"id": int, "name": str, "name_pinyin": str, "name_short": str, "item_type": "industry", "code": str, "extra": None}
            ]
        """
        return tool_fuzzy_search(keyword, item_type="industry", limit=limit)

    @app.tool()
    def search_regions(keyword: str, limit: int = 10) -> list[dict]:
        """搜索地区板块

        Args:
            keyword: str, 地区名称
            limit: int, 返回数量限制，默认10

        Returns:
            list[dict]: 地区板块列表
            [
                {"id": int, "name": str, "name_pinyin": str, "name_short": str, "item_type": "region", "code": str, "extra": None}
            ]
        """
        return tool_fuzzy_search(keyword, item_type="region", limit=limit)

    @app.tool()
    def fuzzy_search_batch(keywords: list, item_type: str = None, limit_per_keyword: int = 5) -> list[dict]:
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
        return tool_fuzzy_search_batch(keywords, item_type, limit_per_keyword)

    @app.tool()
    def resolve_code_batch(codes_or_names: list) -> list[dict]:
        """批量根据股票名称/代码解析为标准股票代码

        Args:
            codes_or_names: list, 股票代码或名称列表（如 ["贵州茅台", "600519.SH", "平安银行"]）

        Returns:
            list[dict]: 解析结果列表
            [
                {"input": str, "resolved_code": str, "name": str},
                ...
            ]
        """
        return tool_resolve_code_batch(codes_or_names)

    # ==================== 股票查询工具 ====================

    @app.tool()
    def get_stock_info(code: str) -> dict:
        """获取股票基本信息

        Args:
            code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）

        Returns:
            dict: 股票基本信息
            {
                "ts_code": str, "symbol": str, "name": str, "area": None, "industry": None,
                "market": None, "list_date": str, "delist_date": None, "is_hs": None
            }
        """
        return tool_get_stock_info(code)

    @app.tool()
    def get_stock_info_batch(codes: list) -> dict:
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
        """
        return tool_get_stock_info_batch(codes)

    @app.tool()
    def get_stock_daily(
        code: str,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> list[dict]:
        """获取股票日线数据

        Args:
            code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）
            start_date: str|None, 开始日期，格式 YYYYMMDD，如 "20260101"
            end_date: str|None, 结束日期，格式 YYYYMMDD，如 "20260329"
            limit: int, 返回条数限制，默认100

        Returns:
            list[dict]: 日线数据列表，最新日期在前
            [
                {"ts_code": str, "trade_date": str, "open": float, "high": float, "low": float,
                 "close": float, "pre_close": float, "change": float, "pct_chg": float, "vol": float, "amount": float}
            ]
        """
        return tool_get_stock_daily(code, start_date, end_date, limit)

    @app.tool()
    def get_stock_daily_batch(codes: list, limit: int = 30) -> dict:
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
        return tool_get_stock_daily_batch(codes, limit)

    @app.tool()
    def get_stock_concepts(code: str) -> list[dict]:
        """获取股票所属概念板块

        Args:
            code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）

        Returns:
            list[dict]: 概念板块列表
            [
                {"concept_code": str, "concept_name": str}
            ]
        """
        return tool_get_stock_concepts(code)

    @app.tool()
    def get_stock_industries(code: str) -> list[dict]:
        """获取股票所属行业板块

        Args:
            code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）

        Returns:
            list[dict]: 行业板块列表
            [
                {"industry_code": str, "industry_name": str}
            ]
        """
        return tool_get_stock_industries(code)

    @app.tool()
    def get_stock_regions(code: str) -> list[dict]:
        """获取股票所属地区板块

        Args:
            code: str, 股票代码（如 "600519.SH"）或名称（如 "贵州茅台"）

        Returns:
            list[dict]: 地区板块列表
            [
                {"region_code": str, "region_name": str}
            ]
        """
        return tool_get_stock_regions(code)

    # ==================== 板块查询工具 ====================

    @app.tool()
    def get_all_concepts(limit: int = 100) -> list[dict]:
        """获取所有概念板块

        Args:
            limit: int, 返回数量限制，默认100

        Returns:
            list[dict]: 概念板块列表，按排名排序
            [
                {"rank": int, "concept_name": str, "concept_code": str, "latest_price": float,
                 "changeAmt": float, "pct_chg": float, "total_mv": float, "turnover_rate": float,
                 "up_count": int, "down_count": int, "top_stock": str, "top_stock_pct": float}
            ]
        """
        return tool_get_all_concepts(limit)

    @app.tool()
    def get_all_industries(limit: int = 100) -> list[dict]:
        """获取所有行业板块

        Args:
            limit: int, 返回数量限制，默认100

        Returns:
            list[dict]: 行业板块列表，按排名排序
            [
                {"rank": int, "industry_name": str, "industry_code": str, "latest_price": float,
                 "changeAmt": float, "pct_chg": float, "total_mv": float, "turnover_rate": float,
                 "up_count": int, "down_count": int, "top_stock": str, "top_stock_pct": float}
            ]
        """
        return tool_get_all_industries(limit)

    @app.tool()
    def get_all_regions(limit: int = 50) -> list[dict]:
        """获取所有地区板块

        Args:
            limit: int, 返回数量限制，默认50

        Returns:
            list[dict]: 地区板块列表，按排名排序
            [
                {"rank": int, "region_name": str, "region_code": str, "latest_price": float,
                 "changeAmt": float, "pct_chg": float, "total_mv": float, "turnover_rate": float,
                 "up_count": int, "down_count": int, "top_stock": str, "top_stock_pct": float}
            ]
        """
        return tool_get_all_regions(limit)

    @app.tool()
    def get_concept_stocks(concept_name: str, limit: int = 100) -> list[dict]:
        """获取概念板块成分股

        Args:
            concept_name: str, 概念名称，如 "AI概念"、"人工智能"
            limit: int, 返回数量限制，默认100

        Returns:
            list[dict]: 成分股列表
            [
                {"ts_code": str, "symbol": str, "name": str, "latest_price": float, "pct_chg": float}
            ]
        """
        return tool_get_concept_stocks(concept_name, limit)

    @app.tool()
    def get_industry_stocks(industry_name: str, limit: int = 100) -> list[dict]:
        """获取行业板块成分股

        Args:
            industry_name: str, 行业名称，如 "银行"、"半导体"
            limit: int, 返回数量限制，默认100

        Returns:
            list[dict]: 成分股列表
            [
                {"ts_code": str, "symbol": str, "name": str, "latest_price": float, "pct_chg": float}
            ]
        """
        return tool_get_industry_stocks(industry_name, limit)

    @app.tool()
    def get_region_stocks(region_name: str, limit: int = 100) -> list[dict]:
        """获取地区板块成分股

        Args:
            region_name: str, 地区名称，如 "上海地区"、"北京地区"
            limit: int, 返回数量限制，默认100

        Returns:
            list[dict]: 成分股列表
            [
                {"ts_code": str, "name": str, "latest_price": float, "pct_chg": float}
            ]
        """
        return tool_get_region_stocks(region_name, limit)

    # ==================== 热点监控工具 ====================

    @app.tool()
    def add_topic_history(name: str, concept_codes: list = None, news: str = None, stock_codes: list = None) -> dict:
        """记录热点到历史列表

        自动填充关联信息（concept_codes/board_names/stock_codes/stock_names），
        用户只需提供热点名称，系统自动关联板块和股票。

        Args:
            name: str, 热点名称，如 "AI概念"
            concept_codes: list|None, 板块代码列表（如 ["BK1173", "BK0800"]），不填则自动查找
            news: str|None, 利好/刺激性消息（最多500字）
            stock_codes: list|None, 关联股票代码列表，不填则自动从板块获取

        Returns:
            dict: {"success": bool, "id": int}
        """
        return tool_add_topic_history(name, concept_codes, news, stock_codes)

    @app.tool()
    def get_topic_history(limit: int = 50) -> list[dict]:
        """获取历史热点列表

        Args:
            limit: int, 返回数量限制，默认50

        Returns:
            list[dict]: 历史热点列表
            [
                {"id": int, "name": str, "concept_code": str, "board_name": str,
                 "news": str, "stock_codes": list, "stock_names": list,
                 "created_at": str}
            ]
        """
        return tool_get_topic_history(limit)

    @app.tool()
    def get_latest_topics(limit: int = 20) -> list[dict]:
        """获取当日热门热点

        从 concept_board 表按涨跌幅排序获取热门概念

        Args:
            limit: int, 返回数量限制，默认20

        Returns:
            list[dict]: 热门热点列表
            [
                {"concept_name": str, "concept_code": str, "pct_chg": float,
                 "up_count": int, "down_count": int}
            ]
        """
        return tool_get_latest_topics(limit)

    @app.tool()
    def delete_topic_history(topic_id: int) -> dict:
        """删除指定热点记录

        Args:
            topic_id: int, 热点记录ID

        Returns:
            dict: {"success": bool, "deleted": bool}
        """
        return tool_delete_topic_history(topic_id)

    @app.tool()
    def clear_all_topic_history() -> dict:
        """清空所有热点历史记录

        Returns:
            dict: {"success": bool, "deleted_count": int}
        """
        return tool_clear_all_topic_history()

    # 打印服务信息
    print("=" * 50)
    print(f"{SERVER_NAME} MCP Server v{SERVER_VERSION}")
    print(f"描述: {SERVER_DESCRIPTION}")
    print("=" * 50)
    print(f"服务地址: http://{args.host}:{args.port}")
    print("通信方式: HTTP (MCP 协议)")
    print("数据来源: Akshare (主) + Tushare (备)")
    print("可用工具: 22 个")
    print("-" * 50)
    print("已注册工具:")
    print("  [搜索] fuzzy_search, fuzzy_search_batch, search_stocks,")
    print("         search_concepts, search_industries, search_regions")
    print("  [股票] get_stock_info, get_stock_info_batch, get_stock_daily, get_stock_daily_batch,")
    print("         resolve_code_batch, get_stock_concepts,")
    print("         get_stock_industries, get_stock_regions")
    print("  [板块] get_all_concepts, get_all_industries, get_all_regions,")
    print("         get_concept_stocks, get_industry_stocks, get_region_stocks")
    print("  [热点] add_topic_history, get_topic_history, get_latest_topics")
    print("-" * 50)
    print("服务已启动，正在等待请求...")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)

    # 运行 HTTP 服务器 (streamable-http)
    app.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
