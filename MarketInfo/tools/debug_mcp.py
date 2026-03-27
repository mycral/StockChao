# -*- coding: utf-8 -*-
"""
MCP 服务器交互式调试工具

逐个接口调试，查看请求参数和返回结果
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_server.tools.search import fuzzy_search, search_stocks, search_concepts, search_industries, search_regions
from mcp_server.tools.stock import get_stock_info, get_stock_daily, get_stock_concepts, get_stock_industries, get_stock_regions
from mcp_server.tools.board import get_all_concepts, get_all_industries, get_all_regions, get_concept_stocks, get_industry_stocks, get_region_stocks


def print_sep(title=""):
    print("\n" + "=" * 60)
    if title:
        print(title)
        print("=" * 60)


# 所有接口定义
APIS = {
    # 搜索工具
    "1": {"name": "fuzzy_search", "func": fuzzy_search, "params": ["keyword", "item_type(可选)", "limit"]},
    "2": {"name": "search_stocks", "func": search_stocks, "params": ["keyword", "limit"]},
    "3": {"name": "search_concepts", "func": search_concepts, "params": ["keyword", "limit"]},
    "4": {"name": "search_industries", "func": search_industries, "params": ["keyword", "limit"]},
    "5": {"name": "search_regions", "func": search_regions, "params": ["keyword", "limit"]},

    # 股票工具
    "6": {"name": "get_stock_info", "func": get_stock_info, "params": ["code"]},
    "7": {"name": "get_stock_daily", "func": get_stock_daily, "params": ["code", "start_date(可选)", "end_date(可选)", "limit"]},
    "8": {"name": "get_stock_concepts", "func": get_stock_concepts, "params": ["code"]},
    "9": {"name": "get_stock_industries", "func": get_stock_industries, "params": ["code"]},
    "10": {"name": "get_stock_regions", "func": get_stock_regions, "params": ["code"]},

    # 板块工具
    "11": {"name": "get_all_concepts", "func": get_all_concepts, "params": ["limit"]},
    "12": {"name": "get_all_industries", "func": get_all_industries, "params": ["limit"]},
    "13": {"name": "get_all_regions", "func": get_all_regions, "params": ["limit"]},
    "14": {"name": "get_concept_stocks", "func": get_concept_stocks, "params": ["concept_name", "limit"]},
    "15": {"name": "get_industry_stocks", "func": get_industry_stocks, "params": ["industry_name", "limit"]},
    "16": {"name": "get_region_stocks", "func": get_region_stocks, "params": ["region_name", "limit"]},
}


def show_menu():
    print_sep("MCP Server 接口调试")
    print("选择要调试的接口:\n")
    print("  [搜索工具]")
    for i in range(1, 6):
        api = APIS[str(i)]
        print(f"    {i}. {api['name']}")
    print("\n  [股票工具]")
    for i in range(6, 11):
        api = APIS[str(i)]
        print(f"    {i}. {api['name']}")
    print("\n  [板块工具]")
    for i in range(11, 17):
        api = APIS[str(i)]
        print(f"    {i}. {api['name']}")
    print("\n  0. 退出")
    print("-" * 60)


def get_params(api_info):
    """获取接口参数"""
    params = api_info["params"]
    args = {}

    for p in params:
        # 判断可选参数
        is_optional = p.startswith("(") and p.endswith(")")
        param_name = p.replace("(可选)", "").replace("(", "").replace(")", "").strip()

        if is_optional:
            # 可选参数，询问是否输入
            user_input = input(f"  {param_name} (可选，回车跳过): ").strip()
            if user_input:
                # 尝试转换为 int
                if user_input.isdigit():
                    args[param_name] = int(user_input)
                else:
                    args[param_name] = user_input
        else:
            # 必填参数
            user_input = input(f"  {param_name}: ").strip()
            if not user_input:
                print("    错误: 该参数必填")
                return None
            # 尝试转换为 int
            if user_input.isdigit():
                args[param_name] = int(user_input)
            else:
                args[param_name] = user_input

    return args


def call_api(api_info, args):
    """调用接口"""
    func = api_info["func"]

    print_sep(f"调用 {api_info['name']}")
    print(f"输入参数: {args}")

    try:
        result = func(**args)

        # 显示结果
        print_sep(f"返回结果 (共 {len(result) if isinstance(result, (list, dict)) else 1} 条)")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    except Exception as e:
        print(f"错误: {e}")
        return None


def main():
    while True:
        show_menu()
        choice = input("\n请选择接口编号: ").strip()

        if choice == "0":
            print("退出调试")
            break

        if choice not in APIS:
            print("无效选择，请重新输入")
            continue

        api_info = APIS[choice]
        print(f"\n选中: {api_info['name']}")
        print(f"参数: {api_info['params']}")

        # 获取参数
        args = get_params(api_info)
        if args is None:
            continue

        # 调用接口
        call_api(api_info, args)

        # 继续或退出
        print("\n")
        cont = input("继续调试? (y/n): ").strip().lower()
        if cont != "y":
            break


if __name__ == "__main__":
    main()
