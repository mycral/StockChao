# -*- coding: utf-8 -*-
"""
Tushare 镜像库 - 数据查询工具
"""
import sqlite3
import pandas as pd
from datetime import datetime


class QueryDB:
    """数据库查询类"""

    def __init__(self, db_path):
        """初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_stock_basic(self, ts_code=None, market=None):
        """查询股票列表

        Args:
            ts_code: 股票代码（如 '601988.SH'）
            market: 市场类型（'主板'/'创业板'/'科创板'/'北交所'）

        Returns:
            DataFrame
        """
        sql = "SELECT * FROM stock_basic WHERE 1=1"
        params = []

        if ts_code:
            sql += " AND ts_code = ?"
            params.append(ts_code)

        if market:
            sql += " AND market = ?"
            params.append(market)

        return pd.read_sql_query(sql, self.conn, params=params)

    def get_daily(self, ts_code, start_date=None, end_date=None):
        """查询日线数据

        Args:
            ts_code: 股票代码（如 '601988.SH'）
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）

        Returns:
            DataFrame
        """
        sql = "SELECT * FROM daily WHERE ts_code = ?"
        params = [ts_code]

        if start_date:
            sql += " AND trade_date >= ?"
            params.append(start_date)

        if end_date:
            sql += " AND trade_date <= ?"
            params.append(end_date)

        sql += " ORDER BY trade_date"

        return pd.read_sql_query(sql, self.conn, params=params)

    def get_daily_batch(self, ts_codes: list, limit: int = 30):
        """批量查询多只股票的最近日线数据

        Args:
            ts_codes: 股票代码列表（如 ['600519.SH', '000001.SZ']）
            limit: 每只股票返回的交易日数，默认30

        Returns:
            dict: {股票代码: [日线数据列表]}
        """
        if not ts_codes or len(ts_codes) == 0:
            return {}

        # 限制股票数量
        if len(ts_codes) > 30:
            ts_codes = ts_codes[:30]

        result = {}
        for ts_code in ts_codes:
            try:
                sql = f"""
                    SELECT * FROM daily
                    WHERE ts_code = ?
                    ORDER BY trade_date DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(sql, self.conn, params=[ts_code, limit])
                if df is not None and len(df) > 0:
                    # 按日期升序排列（ oldest first）
                    result[ts_code] = df.sort_values('trade_date').to_dict('records')
                else:
                    result[ts_code] = []
            except Exception as e:
                result[ts_code] = [{"error": str(e)}]

        return result

    def get_daily_basic(self, ts_code, start_date=None, end_date=None):
        """查询每日指标

        Args:
            ts_code: 股票代码
            start_date: 开始日期（YYYYMMDD）
            end_date: 结束日期（YYYYMMDD）

        Returns:
            DataFrame
        """
        sql = "SELECT * FROM daily_basic WHERE ts_code = ?"
        params = [ts_code]

        if start_date:
            sql += " AND trade_date >= ?"
            params.append(start_date)

        if end_date:
            sql += " AND trade_date <= ?"
            params.append(end_date)

        sql += " ORDER BY trade_date"

        return pd.read_sql_query(sql, self.conn, params=params)

    def get_latest_date(self, table_name, date_column='trade_date'):
        """获取表中最新日期

        Args:
            table_name: 表名
            date_column: 日期列名

        Returns:
            最新日期字符串（YYYYMMDD），无数据返回 None
        """
        sql = f"SELECT MAX({date_column}) FROM {table_name}"
        cursor = self.conn.execute(sql)
        result = cursor.fetchone()[0]
        return result

    def get_stock_count(self):
        """获取股票数量"""
        sql = "SELECT COUNT(*) FROM stock_basic"
        cursor = self.conn.execute(sql)
        return cursor.fetchone()[0]

    def get_stock_concepts(self, ts_code=None, name=None):
        """查询股票所属概念板块

        Args:
            ts_code: 股票代码（如 '002131.SZ'）
            name: 股票名称（如 '利欧股份'）

        Returns:
            DataFrame，包含 concept_code, concept_name
        """
        if not ts_code and not name:
            return pd.DataFrame()

        # 如果提供名称，先查 ts_code
        if name:
            stock_df = pd.read_sql_query(
                "SELECT ts_code FROM stock_basic WHERE name = ?",
                self.conn,
                params=[name]
            )
            if len(stock_df) > 0:
                ts_code = stock_df.iloc[0]['ts_code']
            else:
                return pd.DataFrame()

        # 查询概念
        sql = "SELECT concept_code, concept_name FROM stock_concept WHERE ts_code = ?"
        return pd.read_sql_query(sql, self.conn, params=[ts_code])

    def get_concept_stocks(self, concept_name=None, concept_code=None):
        """查询概念板块的成分股

        Args:
            concept_name: 概念名称（如 'AI概念'）
            concept_code: 概念代码（如 'BK1172'）

        Returns:
            DataFrame，包含 ts_code, symbol, name, latest_price, pct_chg
        """
        # 先获取成分股
        if concept_code:
            sql = "SELECT ts_code, symbol, name FROM stock_concept WHERE concept_code = ?"
            df_stocks = pd.read_sql_query(sql, self.conn, params=[concept_code])
        elif concept_name:
            sql = "SELECT ts_code, symbol, name FROM stock_concept WHERE concept_name = ?"
            df_stocks = pd.read_sql_query(sql, self.conn, params=[concept_name])
        else:
            return pd.DataFrame()

        if df_stocks is None or len(df_stocks) == 0:
            return df_stocks

        # 获取最新日期
        latest_date = pd.read_sql_query(
            "SELECT MAX(trade_date) FROM daily",
            self.conn
        ).iloc[0, 0]

        if not latest_date:
            return df_stocks

        # 获取这些股票的最新价格
        ts_codes = df_stocks['ts_code'].tolist()
        placeholders = ','.join(['?'] * len(ts_codes))
        sql_price = f"""
            SELECT ts_code, close as latest_price, pct_chg
            FROM daily
            WHERE trade_date = ? AND ts_code IN ({placeholders})
        """
        df_price = pd.read_sql_query(sql_price, self.conn, params=[latest_date] + ts_codes)

        # 合并数据
        df_stocks = df_stocks.merge(df_price, on='ts_code', how='left')

        return df_stocks

    def get_all_concepts(self):
        """查询所有概念板块"""
        return pd.read_sql_query("SELECT * FROM concept_board ORDER BY rank", self.conn)

    # ==================== 行业板块查询 ====================

    def get_stock_industries(self, ts_code=None, name=None):
        """查询股票所属行业板块

        Args:
            ts_code: 股票代码（如 '002131.SZ'）
            name: 股票名称（如 '利欧股份'）

        Returns:
            DataFrame，包含 industry_code, industry_name
        """
        if not ts_code and not name:
            return pd.DataFrame()

        # 如果提供名称，先查 ts_code
        if name:
            stock_df = pd.read_sql_query(
                "SELECT ts_code FROM stock_basic WHERE name = ?",
                self.conn,
                params=[name]
            )
            if len(stock_df) > 0:
                ts_code = stock_df.iloc[0]['ts_code']
            else:
                return pd.DataFrame()

        # 查询行业
        sql = "SELECT industry_code, industry_name FROM stock_industry WHERE ts_code = ?"
        return pd.read_sql_query(sql, self.conn, params=[ts_code])

    def get_industry_stocks(self, industry_name=None, industry_code=None):
        """查询行业板块的成分股

        Args:
            industry_name: 行业名称（如 '银行'）
            industry_code: 行业代码

        Returns:
            DataFrame，包含 ts_code, symbol, name, latest_price, pct_chg
        """
        # 先获取成分股
        if industry_code:
            sql = "SELECT ts_code, symbol, name FROM stock_industry WHERE industry_code = ?"
            df_stocks = pd.read_sql_query(sql, self.conn, params=[industry_code])
        elif industry_name:
            sql = "SELECT ts_code, symbol, name FROM stock_industry WHERE industry_name = ?"
            df_stocks = pd.read_sql_query(sql, self.conn, params=[industry_name])
        else:
            return pd.DataFrame()

        if df_stocks is None or len(df_stocks) == 0:
            return df_stocks

        # 获取最新日期
        latest_date = pd.read_sql_query(
            "SELECT MAX(trade_date) FROM daily",
            self.conn
        ).iloc[0, 0]

        if not latest_date:
            return df_stocks

        # 获取这些股票的最新价格
        ts_codes = df_stocks['ts_code'].tolist()
        placeholders = ','.join(['?'] * len(ts_codes))
        sql_price = f"""
            SELECT ts_code, close as latest_price, pct_chg
            FROM daily
            WHERE trade_date = ? AND ts_code IN ({placeholders})
        """
        df_price = pd.read_sql_query(sql_price, self.conn, params=[latest_date] + ts_codes)

        # 合并数据
        df_stocks = df_stocks.merge(df_price, on='ts_code', how='left')

        return df_stocks

    def get_all_industries(self):
        """查询所有行业板块"""
        return pd.read_sql_query("SELECT * FROM industry_board ORDER BY rank", self.conn)

    # ==================== 地区板块查询 ====================

    def get_stock_regions(self, ts_code=None, name=None):
        """查询股票所属地区板块

        Args:
            ts_code: 股票代码（如 '002131.SZ'）
            name: 股票名称（如 '利欧股份'）

        Returns:
            DataFrame，包含 region_code, region_name
        """
        if not ts_code and not name:
            return pd.DataFrame()

        # 如果提供名称，先查 ts_code
        if name:
            stock_df = pd.read_sql_query(
                "SELECT ts_code FROM stock_basic WHERE name = ?",
                self.conn,
                params=[name]
            )
            if len(stock_df) > 0:
                ts_code = stock_df.iloc[0]['ts_code']
            else:
                return pd.DataFrame()

        # 查询地区
        sql = "SELECT region_code, region_name FROM stock_region WHERE ts_code = ?"
        return pd.read_sql_query(sql, self.conn, params=[ts_code])

    def get_region_stocks(self, region_name=None, region_code=None):
        """查询地区板块的成分股

        Args:
            region_name: 地区名称（如 '北京地区'）
            region_code: 地区代码（如 '880207.TDX'）

        Returns:
            DataFrame，包含 ts_code, name, latest_price, pct_chg
        """
        # 先获取成分股
        if region_code:
            sql = "SELECT ts_code, name FROM stock_region WHERE region_code = ?"
            df_stocks = pd.read_sql_query(sql, self.conn, params=[region_code])
        elif region_name:
            sql = "SELECT ts_code, name FROM stock_region WHERE region_name = ?"
            df_stocks = pd.read_sql_query(sql, self.conn, params=[region_name])
        else:
            return pd.DataFrame()

        if df_stocks is None or len(df_stocks) == 0:
            return df_stocks

        # 获取最新日期
        latest_date = pd.read_sql_query(
            "SELECT MAX(trade_date) FROM daily",
            self.conn
        ).iloc[0, 0]

        if not latest_date:
            return df_stocks

        # 获取这些股票的最新价格
        ts_codes = df_stocks['ts_code'].tolist()
        placeholders = ','.join(['?'] * len(ts_codes))
        sql_price = f"""
            SELECT ts_code, close as latest_price, pct_chg
            FROM daily
            WHERE trade_date = ? AND ts_code IN ({placeholders})
        """
        df_price = pd.read_sql_query(sql_price, self.conn, params=[latest_date] + ts_codes)

        # 合并数据
        df_stocks = df_stocks.merge(df_price, on='ts_code', how='left')

        return df_stocks

    def get_all_regions(self):
        """查询所有地区板块"""
        # 兼容新旧两种 schema
        # 新 schema: idx_count DESC (推荐)
        # 旧 schema: rank DESC (兼容)
        try:
            return pd.read_sql_query("SELECT * FROM region_board ORDER BY idx_count DESC", self.conn)
        except:
            return pd.read_sql_query("SELECT * FROM region_board ORDER BY rank DESC", self.conn)

    # ==================== 热点历史 ====================

    def add_topic_history(self, name: str, concept_codes: list = None,
                          news: str = None, stock_codes: list = None,
                          stock_names: list = None):
        """写入热点记录（自动填充关联信息）

        Args:
            name: 热点名称
            concept_codes: 关联板块代码列表（可选，手动指定）
            news: 利好消息
            stock_codes: 关联股票代码列表（可选）
            stock_names: 关联股票名称列表（可选）
        """
        import json
        from core.field_format import now_ms

        created_at = now_ms()

        # 1. 如果未指定 concept_codes，通过 name 模糊搜索 concept_board 填充
        resolved_codes = concept_codes or []
        resolved_board_names = []
        resolved_stock_codes = stock_codes or []
        resolved_stock_names = stock_names or []

        if not resolved_codes and name:
            # 从 concept_board 找所有匹配
            cursor = self.conn.execute(
                "SELECT concept_code, concept_name FROM concept_board WHERE concept_name LIKE ?",
                (f'%{name}%',)
            )
            results = cursor.fetchall()
            if results:
                resolved_codes = [r[0] for r in results]
                resolved_board_names = [r[1] for r in results]

        # 2. 通过 concept_codes 填充 board_names（如果还未填充）
        if resolved_codes and not resolved_board_names:
            placeholders = ','.join(['?' for _ in resolved_codes])
            cursor = self.conn.execute(
                f"SELECT concept_code, concept_name FROM concept_board WHERE concept_code IN ({placeholders})",
                resolved_codes
            )
            results = cursor.fetchall()
            if results:
                resolved_board_names = [r[1] for r in results]

        # 3. 通过 concept_codes 填充股票列表（仅当用户未手动指定时）
        if resolved_codes and (not stock_codes or stock_codes == []):
            placeholders = ','.join(['?' for _ in resolved_codes])
            cursor = self.conn.execute(
                f"SELECT ts_code, name FROM stock_concept WHERE concept_code IN ({placeholders}) LIMIT 100",
                resolved_codes
            )
            stocks = cursor.fetchall()
            if stocks:
                resolved_stock_codes = [s[0] for s in stocks]
                resolved_stock_names = [s[1] for s in stocks]

        sql = """
            INSERT INTO topic_history (name, concept_codes, board_names, news, stock_codes, stock_names, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            name,
            json.dumps(resolved_codes, ensure_ascii=False),
            json.dumps(resolved_board_names, ensure_ascii=False),
            news or '',
            json.dumps(resolved_stock_codes, ensure_ascii=False),
            json.dumps(resolved_stock_names, ensure_ascii=False),
            created_at
        ]
        cursor = self.conn.execute(sql, params)
        self.conn.commit()
        return cursor.lastrowid

    def get_topic_history(self, limit: int = 50):
        """读取热点历史

        Args:
            limit: 返回数量限制

        Returns:
            DataFrame，包含 id, name, concept_codes, board_names, news,
            stock_codes, stock_names, created_at
        """
        import json
        from core.field_format import ts_to_str

        sql = f"""
            SELECT id, name, concept_codes, board_names, news, stock_codes, stock_names, created_at
            FROM topic_history
            ORDER BY created_at DESC
            LIMIT ?
        """
        df = pd.read_sql_query(sql, self.conn, params=[limit])

        # 反序列化 JSON 字段
        if 'concept_codes' in df.columns:
            df['concept_codes'] = df['concept_codes'].apply(
                lambda x: json.loads(x) if x else []
            )
        if 'board_names' in df.columns:
            df['board_names'] = df['board_names'].apply(
                lambda x: json.loads(x) if x else []
            )
        if 'stock_codes' in df.columns:
            df['stock_codes'] = df['stock_codes'].apply(
                lambda x: json.loads(x) if x else []
            )
        if 'stock_names' in df.columns:
            df['stock_names'] = df['stock_names'].apply(
                lambda x: json.loads(x) if x else []
            )

        # ms时间戳 -> 可读字符串
        if 'created_at' in df.columns:
            df['created_at'] = df['created_at'].apply(ts_to_str)

        return df

    def get_topic_minute_data(self, ts_code: str, trade_date: str = None):
        """从 minute_5min 表读取分时数据

        Args:
            ts_code: 股票代码（如 '600519.SH'）
            trade_date: 日期（如 '20260329'），默认当天

        Returns:
            DataFrame，按时间排序
        """
        if trade_date is None:
            from datetime import datetime
            trade_date = datetime.now().strftime('%Y%m%d')

        sql = """
            SELECT ts_code, trade_time, open, high, low, close, vol, amount
            FROM minute_5min
            WHERE ts_code = ? AND trade_time LIKE ?
            ORDER BY trade_time
        """
        return pd.read_sql_query(sql, self.conn, params=[ts_code, f'{trade_date}%'])

    def get_latest_topics(self, limit: int = 20):
        """获取当日热门热点（从 concept_board 涨跌幅排序）

        Args:
            limit: 返回数量限制

        Returns:
            DataFrame，包含 concept_name, concept_code, pct_chg, up_count
        """
        sql = f"""
            SELECT concept_name, concept_code, pct_chg, up_count, down_count
            FROM concept_board
            ORDER BY pct_chg DESC
            LIMIT ?
        """
        return pd.read_sql_query(sql, self.conn, params=[limit])

    # ==================== 模糊查询 ====================

    def fuzzy_search(self, keyword: str, item_type: str = None, limit: int = 20):
        """模糊查询名称

        Args:
            keyword: 关键词（支持拼音首字母、简称、全拼）
            item_type: 类型过滤（stock/concept/industry/region），None 表示全部
            limit: 返回数量限制

        Returns:
            DataFrame，包含 id, name, name_pinyin, name_short, item_type, code
        """
        if not keyword:
            return pd.DataFrame()

        # 构建查询
        sql = """
            SELECT id, name, name_pinyin, name_short, item_type, code, extra
            FROM fuzzy_search
            WHERE name LIKE ?
               OR name_pinyin LIKE ?
               OR name_short LIKE ?
        """
        params = [f'%{keyword}%', f'%{keyword}%', f'%{keyword}%']

        if item_type:
            sql += " AND item_type = ?"
            params.append(item_type)

        sql += f" ORDER BY item_type, name LIMIT {limit}"

        return pd.read_sql_query(sql, self.conn, params=params)

    def build_fuzzy_search_table(self):
        """从各表重建模糊查询表

        从 stock_basic、concept_board、industry_board、region_board 收集所有名称
        """
        import pandas as pd
        import re

        records = []

        # 1. 股票名称
        sql = "SELECT ts_code, name FROM stock_basic WHERE name IS NOT NULL AND name != ''"
        stocks = pd.read_sql_query(sql, self.conn)
        for _, row in stocks.iterrows():
            records.append({
                'name': row['name'],
                'name_pinyin': self._to_pinyin(row['name']),
                'name_short': self._to_short_name(row['name']),
                'item_type': 'stock',
                'code': row['ts_code'],
                'extra': None
            })

        # 2. 概念板块
        sql = "SELECT concept_code, concept_name FROM concept_board WHERE concept_name IS NOT NULL"
        concepts = pd.read_sql_query(sql, self.conn)
        for _, row in concepts.iterrows():
            records.append({
                'name': row['concept_name'],
                'name_pinyin': self._to_pinyin(row['concept_name']),
                'name_short': self._to_short_name(row['concept_name']),
                'item_type': 'concept',
                'code': row['concept_code'],
                'extra': None
            })

        # 3. 行业板块
        sql = "SELECT industry_code, industry_name FROM industry_board WHERE industry_name IS NOT NULL"
        industries = pd.read_sql_query(sql, self.conn)
        for _, row in industries.iterrows():
            records.append({
                'name': row['industry_name'],
                'name_pinyin': self._to_pinyin(row['industry_name']),
                'name_short': self._to_short_name(row['industry_name']),
                'item_type': 'industry',
                'code': row['industry_code'],
                'extra': None
            })

        # 4. 地区板块
        sql = "SELECT region_code, region_name FROM region_board WHERE region_name IS NOT NULL"
        regions = pd.read_sql_query(sql, self.conn)
        for _, row in regions.iterrows():
            records.append({
                'name': row['region_name'],
                'name_pinyin': self._to_pinyin(row['region_name']),
                'name_short': self._to_short_name(row['region_name']),
                'item_type': 'region',
                'code': row['region_code'],
                'extra': None
            })

        return pd.DataFrame(records)

    def _to_pinyin(self, name: str) -> str:
        """获取汉字拼音首字母"""
        # 简单实现，实际使用时可以用 pypinyin 库
        try:
            import pypinyin
            pinyin_list = pypinyin.lazy_pinyin(name)
            return ''.join([p[0] if p else '' for p in pinyin_list])
        except ImportError:
            return ''

    def _to_short_name(self, name: str) -> str:
        """获取简称（去括号内容取前N个字符）"""
        import re
        # 去掉括号及其内容
        name = re.sub(r'[（(].*?[）)]', '', name)
        # 取前4个字符
        return name[:4] if len(name) >= 4 else name


if __name__ == '__main__':
    from config import DB_PATH

    with QueryDB(DB_PATH) as db:
        # 示例查询
        print(f"股票总数: {db.get_stock_count()}")

        # 查询中国银行日线
        df = db.get_daily('601988.SH', start_date='20260301')
        print(f"\n中国银行日线数据 ({len(df)} 条):")
        print(df.tail())
