# -*- coding: utf-8 -*-
"""
topic_history 表字段重构迁移脚本

重构内容：
  - concept_name → name
  - 新增 board_name 字段
  - 通过 concept_code 自动填充 board_name, stock_codes, stock_names

执行方式：python migrate_topic_history.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import sqlite3
import json
from config import DB_PATH


def migrate():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    # 1. 检查当前表结构
    cursor.execute("PRAGMA table_info(topic_history)")
    columns = {row[1] for row in cursor.fetchall()}
    print(f"当前字段: {columns}")

    # 2. 检查是否有数据需要迁移
    cursor.execute("SELECT COUNT(*) FROM topic_history")
    count = cursor.fetchone()[0]
    print(f"需要迁移的记录数: {count}")

    if 'name' in columns and 'concept_name' not in columns:
        print("已迁移，跳过")
        conn.close()
        return

    # 3. 创建临时表（新结构）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_history_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            concept_code TEXT,
            board_name TEXT,
            news TEXT,
            stock_codes TEXT,
            stock_names TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    """)

    # 4. 迁移数据
    if count > 0:
        cursor.execute("SELECT id, concept_name, concept_code, news, stock_codes, stock_names, created_at, updated_at FROM topic_history")
        rows = cursor.fetchall()

        for row in rows:
            old_id, concept_name, concept_code, news, stock_codes, stock_names, created_at, updated_at = row

            # 使用 concept_name 作为 name
            name = concept_name or ''

            # 如果 concept_code 存在，填充 board_name, stock_codes, stock_names
            if concept_code:
                # 查 board_name
                cursor.execute("SELECT concept_name FROM concept_board WHERE concept_code = ?", (concept_code,))
                result = cursor.fetchone()
                board_name = result[0] if result else ''

                # 查 stock_codes 和 stock_names
                cursor.execute("SELECT ts_code, name FROM stock_concept WHERE concept_code = ?", (concept_code,))
                stocks = cursor.fetchall()
                if stocks:
                    # 仅在没有手动指定时才覆盖
                    if not stock_codes or stock_codes == '[]':
                        sc = [s[0] for s in stocks]
                        sn = [s[1] for s in stocks]
                        stock_codes = json.dumps(sc, ensure_ascii=False)
                        stock_names = json.dumps(sn, ensure_ascii=False)
            else:
                board_name = ''

            # 插入新表
            cursor.execute("""
                INSERT INTO topic_history_new (id, name, concept_code, board_name, news, stock_codes, stock_names, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (old_id, name, concept_code or '', board_name, news or '', stock_codes or '[]', stock_names or '[]', created_at, updated_at))

        conn.commit()
        print(f"已迁移 {len(rows)} 条记录")

    # 5. 删除旧表，重命名新表
    cursor.execute("DROP TABLE IF EXISTS topic_history")
    cursor.execute("ALTER TABLE topic_history_new RENAME TO topic_history")

    # 6. 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_topic_created ON topic_history(created_at DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_topic_name ON topic_history(name)")

    conn.commit()

    # 7. 验证
    cursor.execute("PRAGMA table_info(topic_history)")
    new_columns = {row[1] for row in cursor.fetchall()}
    print(f"新字段: {new_columns}")

    cursor.execute("SELECT COUNT(*) FROM topic_history")
    final_count = cursor.fetchone()[0]
    print(f"迁移后记录数: {final_count}")

    conn.close()
    print("迁移完成!")


if __name__ == '__main__':
    migrate()