# -*- coding: utf-8 -*-
"""测试 Tushare 镜像服务器连接"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import requests
from config import TUSHARE_TOKEN, TUSHARE_HTTP_URL

print("=" * 50)
print("Tushare 镜像服务器测试")
print("=" * 50)

# 1. 测试 HTTP 服务器连通性
print(f"\n1. 测试服务器: {TUSHARE_HTTP_URL}")
try:
    resp = requests.get(TUSHARE_HTTP_URL, timeout=10)
    print(f"   状态码: {resp.status_code}")
    print(f"   响应: {resp.text[:200] if resp.text else '空'}")
except Exception as e:
    print(f"   连接失败: {e}")

# 2. 测试 Tushare API
print(f"\n2. 测试 Tushare API")
import tushare as ts

token = TUSHARE_TOKEN
pro = ts.pro_api(token)
#pro._DataApi__token = token
#pro._DataApi__http_url = TUSHARE_HTTP_URL

# 测试交易日历
try:
    df = pro.trade_cal(start_date='20260301', end_date='20260327')
    print(f"   trade_cal 返回: {len(df)} 条")
    print(f"   列名: {df.columns.tolist()}")
    if len(df) > 0:
        print(df.head())
except Exception as e:
    print(f"   API 调用失败: {e}")

# 3. 测试日线数据
print(f"\n3. 测试日线数据")
try:
    df = pro.daily(ts_code='000001.SZ', start_date='20260301', end_date='20260327')
    print(f"   daily 返回: {len(df)} 条")
    if len(df) > 0:
        print(df.head())
except Exception as e:
    print(f"   API 调用失败: {e}")

print("\n" + "=" * 50)
