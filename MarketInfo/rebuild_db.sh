#!/bin/bash
# 完全重建 MarketInfo 数据库
# 用法: bash rebuild_db.sh

set -e

echo "=================================================="
echo "完全重建 MarketInfo 数据库"
echo "=================================================="

# 1. 删除旧数据库
echo ""
echo "[1/8] 删除旧数据库..."
rm -f data/MarketInfo.db
echo "      完成"

# 2. 初始化数据库（创建所有表）
echo ""
echo "[2/8] 初始化数据库..."
python main.py init
echo "      完成"

# 3. 更新概念板块
echo ""
echo "[3/8] 更新概念板块（需等待约10分钟）..."
python main.py concept
echo "      完成"

# 4. 更新行业板块
echo ""
echo "[4/8] 更新行业板块（需等待约5分钟）..."
python main.py industry
echo "      完成"

# 5. 更新地区板块
echo ""
echo "[5/8] 更新地区板块（需等待约5分钟）..."
python main.py region
echo "      完成"

# 6. 重建模糊查询表
echo ""
echo "[6/8] 重建模糊查询表..."
python main.py rebuild_fuzzy_search
echo "      完成"

# 7. 更新日线数据（从 DAILY_START_DATE=20200101 开始同步）
echo ""
echo "[7/8] 更新日线数据（从 2020-01-01 至今）..."
python main.py sync
echo "      完成"

# 8. 查看数据库状态
echo ""
echo "[8/8] 数据库状态："
echo "      ----------"
python tools/db_status.py 2>/dev/null || echo "      (db_status.py 不可用)"
echo "      ----------"

echo ""
echo "=================================================="
echo "数据库重建完成！"
echo "=================================================="
