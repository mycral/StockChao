# -*- coding: utf-8 -*-
"""
冲高回落次日高开 选股技能
筛选第一天冲高回落，第二天高开收盘涨幅不超过3%的股票
"""
import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from skills.skill_base import BaseSkill, SkillMeta, Condition
from config import DB_PATH


meta = SkillMeta(
    name='冲高回落次日高开',
    description='筛选第一天冲高回落，第二天高开收盘涨幅不超过3%的股票',
    version='1.0',
    author='',
    tags=[],
)

conditions = [
    Condition(name='upper_shadow_pct', label='上影线比例(%)', type='number', default=2),
    Condition(name='max_gain_pct', label='次日最大涨幅(%)', type='number', default=3),
    Condition(name='max_results', label='最大结果数', type='number', default=200),
]


class Skill(BaseSkill):
    """具体选股实现"""

    def screen(self, conditions=None):
        """执行选股"""
        if conditions is None:
            conditions = self.get_default_conditions()

        upper_shadow_pct = conditions.get('upper_shadow_pct', 2) / 100
        max_gain_pct = conditions.get('max_gain_pct', 3)
        max_results = conditions.get('max_results', 200)

        conn = sqlite3.connect(self.db_path)

        # 获取最近2个交易日的所有日线数据
        sql = '''
            WITH latest_dates AS (
                SELECT DISTINCT trade_date
                FROM daily
                ORDER BY trade_date DESC
                LIMIT 2
            )
            SELECT
                d.ts_code,
                d.trade_date,
                d.open,
                d.high,
                d.low,
                d.close,
                d.pct_chg,
                d.pre_close
            FROM daily d
            INNER JOIN latest_dates ld ON d.trade_date = ld.trade_date
            ORDER BY d.ts_code, d.trade_date DESC
        '''
        df = pd.read_sql_query(sql, conn)
        conn.close()

        if df.empty:
            return pd.DataFrame()

        results = []

        for ts_code, group in df.groupby('ts_code'):
            if len(group) < 2:
                continue

            group = group.sort_values('trade_date', ascending=False)
            day1 = group.iloc[1]  # 前一天
            day2 = group.iloc[0]  # 今天

            # 条件1: 第一天冲高回落（上影线占比超过指定比例，收盘下跌）
            day1_upper_shadow = (day1['high'] - day1['close']) / day1['close'] if day1['close'] > 0 else 0
            day1_is_surge = day1_upper_shadow > upper_shadow_pct and day1['pct_chg'] < 0

            if not day1_is_surge:
                continue

            # 条件2: 第二天高开收盘涨幅不超过指定比例
            day2_open_higher = day2['open'] > day1['close']  # 高开
            day2_gain_ok = 0 < day2['pct_chg'] <= max_gain_pct  # 涨幅在范围内

            if day2_open_higher and day2_gain_ok:
                # 获取股票名称
                conn2 = sqlite3.connect(self.db_path)
                name_sql = 'SELECT name FROM stock_basic WHERE ts_code = ?'
                name_df = pd.read_sql_query(name_sql, conn2, params=[ts_code])
                conn2.close()
                name = name_df.iloc[0]['name'] if len(name_df) > 0 else 'Unknown'

                results.append({
                    'ts_code': ts_code,
                    'name': name,
                    'day1_date': day1['trade_date'],
                    'day1_open': day1['open'],
                    'day1_high': day1['high'],
                    'day1_close': day1['close'],
                    'day1_pct': day1['pct_chg'],
                    'day2_date': day2['trade_date'],
                    'day2_open': day2['open'],
                    'day2_close': day2['close'],
                    'day2_pct': day2['pct_chg'],
                })

        result_df = pd.DataFrame(results)

        if len(result_df) > 0:
            result_df = result_df.sort_values('day2_pct', ascending=False)
            result_df = result_df.head(max_results)

        return result_df


if __name__ == '__main__':
    skill = Skill()
    print(f"执行技能: {skill.get_meta().name}")
    result = skill.run()
    if result is not None and len(result) > 0:
        print(f"找到 {len(result)} 只股票")
        print(result.head())
