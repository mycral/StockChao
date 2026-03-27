# -*- coding: utf-8 -*-
"""
选股技能模板
创建新技能时可以复制这个文件作为起点
"""
import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from skills.skill_base import BaseSkill, SkillMeta, Condition
from config import DB_PATH


# ==================== 技能元信息 ====================
meta = SkillMeta(
    name='策略名称',
    description='策略描述，说明这个策略做什么',
    version='1.0',
    author='',
    tags=['技术面', '价量'],
)

# ==================== 选股条件 ====================
conditions = [
    Condition(
        name='consecutive_days',
        label='连续上涨天数',
        type='number',
        default=3,
    ),
    Condition(
        name='min_pct_chg',
        label='每日最小涨幅(%)',
        type='number',
        default=0,
    ),
]


# ==================== 选股逻辑 ====================
class Skill(BaseSkill):
    """具体选股实现"""

    def screen(self, conditions=None):
        """
        执行选股

        Args:
            conditions: 条件参数字典
                - consecutive_days: 连续上涨天数
                - min_pct_chg: 每日最小涨幅

        Returns:
            DataFrame: 选股结果
        """
        if conditions is None:
            conditions = self.get_default_conditions()

        consecutive_days = conditions.get('consecutive_days', 3)
        min_pct_chg = conditions.get('min_pct_chg', 0)

        conn = sqlite3.connect(self.db_path)

        # 获取所有股票的最新数据（按日期排序）
        sql = """
            SELECT ts_code, trade_date, close, pct_chg
            FROM daily
            ORDER BY ts_code, trade_date DESC
        """
        df = pd.read_sql_query(sql, conn)

        if df.empty:
            conn.close()
            return pd.DataFrame()

        conn.close()

        # 按股票分组，找出连续N天上涨的股票
        results = []

        for ts_code, group in df.groupby('ts_code'):
            # 按日期降序排列（最近的在前面）
            group = group.sort_values('trade_date', ascending=False)

            # 检查是否连续N天上涨
            is_valid = True
            for i in range(min(consecutive_days, len(group))):
                if group.iloc[i]['pct_chg'] <= min_pct_chg:
                    is_valid = False
                    break

            if is_valid:
                # 获取股票名称
                conn2 = sqlite3.connect(self.db_path)
                name_sql = "SELECT name FROM stock_basic WHERE ts_code = ?"
                name_df = pd.read_sql_query(name_sql, conn2, params=[ts_code])
                conn2.close()

                name = name_df.iloc[0]['name'] if len(name_df) > 0 else 'Unknown'

                # 获取最新价格和涨幅
                latest = group.iloc[0]
                results.append({
                    'ts_code': ts_code,
                    'name': name,
                    'latest_date': latest['trade_date'],
                    'close': latest['close'],
                    'pct_chg': latest['pct_chg'],
                    'consecutive_days': consecutive_days,
                })

        result_df = pd.DataFrame(results)

        if len(result_df) > 0:
            result_df = result_df.sort_values('pct_chg', ascending=False)

        return result_df


# ==================== 便捷执行 ====================
if __name__ == '__main__':
    skill = Skill()
    print(f"执行技能: {skill.get_meta().name}")

    result = skill.run()

    if result is not None and len(result) > 0:
        print(f"\n找到 {len(result)} 只符合条件的股票:")
        print(result.head(20))
    else:
        print("没有找到符合条件的股票")
