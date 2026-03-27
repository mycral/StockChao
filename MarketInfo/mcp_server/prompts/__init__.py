# -*- coding: utf-8 -*-
"""
MCP 提示词模块

提供常用的分析提示模板
"""

STOCK_ANALYSIS_PROMPT = """
你是一个专业的股票分析师。请分析以下股票：

股票代码: {stock_code}
股票名称: {stock_name}

请提供以下分析：
1. 基本信息（上市时间、行业、地区）
2. 近期走势（最近5日收盘价和涨跌幅）
3. 所属概念板块
4. 所属行业板块
5. 所属地区板块

分析师提示：
- 在获取数据时，请先使用 fuzzy_search 搜索股票代码
- 使用 get_stock_info 获取基本信息
- 使用 get_stock_daily 获取日线数据
- 使用 get_stock_concepts 获取概念板块
- 使用 get_stock_industries 获取行业板块
"""

CONCEPT_SCREEN_PROMPT = """
你是一个专业的选股分析师。请帮我分析概念板块：

概念名称: {concept_name}

请提供以下分析：
1. 概念板块成分股列表（前20只）
2. 成分股的整体表现

分析师提示：
- 使用 fuzzy_search 搜索概念板块代码
- 使用 get_concept_stocks 获取成分股
"""

INDUSTRY_SCREEN_PROMPT = """
你是一个专业的选股分析师。请帮我分析行业板块：

行业名称: {industry_name}

请提供以下分析：
1. 行业板块成分股列表（前20只）
2. 行业整体表现

分析师提示：
- 使用 fuzzy_search 搜索行业板块代码
- 使用 get_industry_stocks 获取成分股
"""

REGION_SCREEN_PROMPT = """
你是一个专业的选股分析师。请帮我分析地区板块：

地区名称: {region_name}

请提供以下分析：
1. 地区板块成分股列表（前20只）
2. 地区整体表现

分析师提示：
- 使用 fuzzy_search 搜索地区板块代码
- 使用 get_region_stocks 获取成分股
"""

COMPARE_STOCKS_PROMPT = """
你是一个专业的股票分析师。请对比以下股票：

股票列表:
{stock_list}

请提供以下对比分析：
1. 基本信息对比（行业、地区）
2. 近期走势对比（最近5日涨跌幅）
3. 估值对比（市盈率、市净率）
4. 资金流向对比

分析师提示：
- 对每只股票分别使用 get_stock_info 和 get_stock_daily
- 使用 fuzzy_search 搜索股票代码
"""


def get_stock_analysis_prompt(stock_code: str = None, stock_name: str = None) -> str:
    """获取股票分析提示"""
    return STOCK_ANALYSIS_PROMPT.format(
        stock_code=stock_code or "{code}",
        stock_name=stock_name or "{name}"
    )


def get_concept_screen_prompt(concept_name: str = None) -> str:
    """获取概念选股提示"""
    return CONCEPT_SCREEN_PROMPT.format(
        concept_name=concept_name or "{concept_name}"
    )


def get_industry_screen_prompt(industry_name: str = None) -> str:
    """获取行业选股提示"""
    return INDUSTRY_SCREEN_PROMPT.format(
        industry_name=industry_name or "{industry_name}"
    )


def get_region_screen_prompt(region_name: str = None) -> str:
    """获取地区选股提示"""
    return REGION_SCREEN_PROMPT.format(
        region_name=region_name or "{region_name}"
    )


def get_compare_stocks_prompt(stock_list: list = None) -> str:
    """获取股票对比提示"""
    return COMPARE_STOCKS_PROMPT.format(
        stock_list=", ".join(stock_list) if stock_list else "{stock1}, {stock2}, ..."
    )
