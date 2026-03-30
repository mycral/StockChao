# -*- coding: utf-8 -*-
"""
热点监控工具模块
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import DB_PATH
from core.query import QueryDB

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def tool_add_topic_history(name: str, concept_codes: list = None, news: str = None, stock_codes: list = None) -> dict:
    """记录热点到历史列表

    自动填充关联信息（concept_codes/board_names/stock_codes/stock_names），
    用户只需提供热点名称，系统自动关联板块和股票。

    Args:
        name: str, 热点名称，如 "AI概念"
        concept_codes: list|None, 板块代码列表（如 ["BK1173", "BK0800"]），不填则自动查找
        news: str|None, 利好/刺激性消息（最多500字）
        stock_codes: list|None, 关联股票代码列表，不填则自动从板块获取

    Returns:
        dict: {"success": bool, "id": int}
        当出错时返回: {"success": False, "error": str}
    """
    logger.info(f"[REQUEST] add_topic_history | name={name}, concept_codes={concept_codes}")
    try:
        with QueryDB(DB_PATH) as q:
            topic_id = q.add_topic_history(
                name=name,
                concept_codes=concept_codes,
                news=news,
                stock_codes=stock_codes
            )
            logger.info(f"[RESPONSE] add_topic_history | success, id={topic_id}")
            return {"success": True, "id": topic_id}
    except Exception as e:
        logger.error(f"[ERROR] add_topic_history | {e}")
        return {"success": False, "error": str(e)}


def tool_get_topic_history(limit: int = 50) -> list[dict]:
    """获取历史热点列表

    Args:
        limit: int, 返回数量限制，默认50

    Returns:
        list[dict]: 历史热点列表
        [
            {"id": int, "name": str, "concept_codes": list, "board_names": list,
             "news": str, "stock_codes": list, "stock_names": list,
             "created_at": str}
        ]
        当出错时返回: [{"error": str}]
    """
    logger.info(f"[REQUEST] get_topic_history | limit={limit}")
    try:
        with QueryDB(DB_PATH) as q:
            df = q.get_topic_history(limit=limit)
            result = df.to_dict('records') if df is not None and len(df) > 0 else []
            logger.info(f"[RESPONSE] get_topic_history | count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_topic_history | {e}")
        return [{"error": str(e)}]


def tool_get_latest_topics(limit: int = 20) -> list[dict]:
    """获取当日热门热点

    从 concept_board 表按涨跌幅排序获取热门概念

    Args:
        limit: int, 返回数量限制，默认20

    Returns:
        list[dict]: 热门热点列表
        [
            {"concept_name": str, "concept_code": str, "pct_chg": float,
             "up_count": int, "down_count": int}
        ]
        当出错时返回: [{"error": str}]
    """
    logger.info(f"[REQUEST] get_latest_topics | limit={limit}")
    try:
        with QueryDB(DB_PATH) as q:
            df = q.get_latest_topics(limit=limit)
            result = df.to_dict('records') if df is not None and len(df) > 0 else []
            logger.info(f"[RESPONSE] get_latest_topics | count={len(result)}")
            return result
    except Exception as e:
        logger.error(f"[ERROR] get_latest_topics | {e}")
        return [{"error": str(e)}]


def tool_delete_topic_history(topic_id: int) -> dict:
    """删除指定热点记录

    Args:
        topic_id: int, 热点记录ID

    Returns:
        dict: {"success": bool, "deleted": bool}
    """
    logger.info(f"[REQUEST] delete_topic_history | topic_id={topic_id}")
    try:
        with QueryDB(DB_PATH) as q:
            q.delete_topic_history(topic_id)
            logger.info(f"[RESPONSE] delete_topic_history | success")
            return {"success": True, "deleted": True}
    except Exception as e:
        logger.error(f"[ERROR] delete_topic_history | {e}")
        return {"success": False, "error": str(e)}


def tool_clear_all_topic_history() -> dict:
    """清空所有热点历史记录

    Returns:
        dict: {"success": bool, "deleted_count": int}
    """
    logger.info(f"[REQUEST] clear_all_topic_history")
    try:
        with QueryDB(DB_PATH) as q:
            count = q.clear_all_topic_history()
            logger.info(f"[RESPONSE] clear_all_topic_history | count={count}")
            return {"success": True, "deleted_count": count}
    except Exception as e:
        logger.error(f"[ERROR] clear_all_topic_history | {e}")
        return {"success": False, "error": str(e)}


# 向后兼容别名
add_topic_history = tool_add_topic_history
get_topic_history = tool_get_topic_history
get_latest_topics = tool_get_latest_topics
delete_topic_history = tool_delete_topic_history
clear_all_topic_history = tool_clear_all_topic_history