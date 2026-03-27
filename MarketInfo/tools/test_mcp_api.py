# -*- coding: utf-8 -*-
"""
MCP 服务器接口测试脚本

测试所有接口，查看请求参数和返回结果
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_server.tools.search import fuzzy_search, search_stocks, search_concepts, search_industries, search_regions
from mcp_server.tools.stock import get_stock_info, get_stock_daily, get_stock_concepts, get_stock_industries, get_stock_regions
from mcp_server.tools.board import get_all_concepts, get_all_industries, get_all_regions, get_concept_stocks, get_industry_stocks, get_region_stocks
import json


def print_sep(title=""):
    print("\n" + "=" * 60)
    if title:
        print(title)
    print("=" * 60)


def test_all():
    """测试所有接口"""
    print_sep("MCP Server 接口测试")

    # 1. fuzzy_search
    print_sep("1. fuzzy_search")
    print("参数: keyword='茅台', item_type=None, limit=3")
    result = fuzzy_search("茅台", limit=3)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 2. search_stocks
    print_sep("2. search_stocks")
    print("参数: keyword='平安', limit=3")
    result = search_stocks("平安", limit=3)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 3. search_concepts
    print_sep("3. search_concepts")
    print("参数: keyword='AI', limit=3")
    result = search_concepts("AI", limit=3)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 4. search_industries
    print_sep("4. search_industries")
    print("参数: keyword='银行', limit=3")
    result = search_industries("银行", limit=3)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 5. search_regions
    print_sep("5. search_regions")
    print("参数: keyword='上海', limit=3")
    result = search_regions("上海", limit=3)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 6. get_stock_info
    print_sep("6. get_stock_info")
    print("参数: code='600519.SH'")
    result = get_stock_info("600519.SH")
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 7. get_stock_daily
    print_sep("7. get_stock_daily")
    print("参数: code='600519.SH', limit=3")
    result = get_stock_daily("600519.SH", limit=3)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 8. get_stock_concepts
    print_sep("8. get_stock_concepts")
    print("参数: code='600519.SH'")
    result = get_stock_concepts("600519.SH")
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 9. get_stock_industries
    print_sep("9. get_stock_industries")
    print("参数: code='600519.SH'")
    result = get_stock_industries("600519.SH")
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 10. get_stock_regions
    print_sep("10. get_stock_regions")
    print("参数: code='600519.SH'")
    result = get_stock_regions("600519.SH")
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 11. get_all_concepts
    print_sep("11. get_all_concepts")
    print("参数: limit=5")
    result = get_all_concepts(limit=5)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 12. get_all_industries
    print_sep("12. get_all_industries")
    print("参数: limit=5")
    result = get_all_industries(limit=5)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 13. get_all_regions
    print_sep("13. get_all_regions")
    print("参数: limit=5")
    result = get_all_regions(limit=5)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 14. get_concept_stocks
    print_sep("14. get_concept_stocks")
    print("参数: concept_name='AI概念', limit=5")
    result = get_concept_stocks("AI概念", limit=5)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 15. get_industry_stocks
    print_sep("15. get_industry_stocks")
    print("参数: industry_name='银行', limit=5")
    result = get_industry_stocks("银行", limit=5)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    # 16. get_region_stocks
    print_sep("16. get_region_stocks")
    print("参数: region_name='上海地区', limit=5")
    result = get_region_stocks("上海地区", limit=5)
    print(f"返回: {json.dumps(result, ensure_ascii=False)[:500]}...")

    print_sep("测试完成")


def test_single(api_name):
    """测试单个接口"""
    apis = {
        "fuzzy_search": lambda: fuzzy_search("茅台", limit=3),
        "search_stocks": lambda: search_stocks("平安", limit=3),
        "search_concepts": lambda: search_concepts("AI", limit=3),
        "search_industries": lambda: search_industries("银行", limit=3),
        "search_regions": lambda: search_regions("上海", limit=3),
        "get_stock_info": lambda: get_stock_info("600519.SH"),
        "get_stock_daily": lambda: get_stock_daily("600519.SH", limit=3),
        "get_stock_concepts": lambda: get_stock_concepts("600519.SH"),
        "get_stock_industries": lambda: get_stock_industries("600519.SH"),
        "get_stock_regions": lambda: get_stock_regions("600519.SH"),
        "get_all_concepts": lambda: get_all_concepts(limit=5),
        "get_all_industries": lambda: get_all_industries(limit=5),
        "get_all_regions": lambda: get_all_regions(limit=5),
        "get_concept_stocks": lambda: get_concept_stocks("AI概念", limit=5),
        "get_industry_stocks": lambda: get_industry_stocks("银行", limit=5),
        "get_region_stocks": lambda: get_region_stocks("上海地区", limit=5),
    }

    if api_name not in apis:
        print(f"未知接口: {api_name}")
        print(f"可用接口: {list(apis.keys())}")
        return

    print_sep(f"测试 {api_name}")
    result = apis[api_name]()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MCP Server 接口测试")
    parser.add_argument("api", nargs="?", help="指定接口名，不指定则测试全部")
    args = parser.parse_args()

    if args.api:
        test_single(args.api)
    else:
        test_all()
