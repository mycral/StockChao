# -*- coding: utf-8 -*-
"""
Tushare 镜像库配置文件
"""
import os

# ==================== API 配置 ====================
# Tushare Token（优先读取环境变量，其次使用默认值）
TUSHARE_TOKEN = '1d89f870ad0edaeebd1f72ed6836262f488448d555a60240723a217a4190'

# 第三方接口地址（必须设置，否则无法获取数据）
TUSHARE_HTTP_URL = 'http://139.196.25.182'

# ==================== 数据库配置 ====================
# 数据库路径
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DATA_DIR, 'MarketInfo.db')

# 股票列表文件
STOCK_LIST_FILE = os.path.join(os.path.dirname(__file__), 'stock_list.csv')

# 日线数据起止日期
DAILY_START_DATE = '20200101'  # 2020年1月1日开始

# 分钟数据起止日期
MINUTE_START_DATE = '20200101'  # 分钟数据量较大，根据需要调整

# 每批下载条数
BATCH_SIZE = 5000

# 请求间隔（秒），避免触发限流
REQUEST_INTERVAL = 0.5


# ==================== API 初始化辅助函数 ====================
def get_pro_api():
    """获取已正确初始化的 tushare pro API 实例

    Returns:
        tushare pro API 实例
    """
    import tushare as ts

    token = TUSHARE_TOKEN
    pro = ts.pro_api(token)
    pro._DataApi__token = token
    pro._DataApi__http_url = TUSHARE_HTTP_URL
    return pro
