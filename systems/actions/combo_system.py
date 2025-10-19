"""
连击系统
"""

import time
from typing import Tuple
from src.plugin_system.apis import database_api
from ...core.models import DTEvent


class ComboSystem:
    """连击系统 - 连续互动获得加成"""

    @staticmethod
    async def calculate_combo_bonus(user_id: str, chat_id: str) -> Tuple[int, float]:
        """
        计算连击数和加成倍率
        返回: (连击数, 加成倍率)
        """
        # 获取最近5分钟内的互动次数
        recent_time = time.time() - 300  # 5分钟前

        recent_interactions = await database_api.db_get(
            DTEvent,
            filters={
                "user_id": user_id,
                "chat_id": chat_id,
                "event_type": "interaction"
            }
        )

        # 筛选5分钟内的
        if recent_interactions:
            recent_interactions = [e for e in recent_interactions if e.get("timestamp", 0) >= recent_time]

        combo_count = len(recent_interactions) if recent_interactions else 0

        # 连击加成倍率
        if combo_count >= 10:
            multiplier = 2.0      # 10连击: 2倍效果
        elif combo_count >= 7:
            multiplier = 1.7      # 7连击: 1.7倍
        elif combo_count >= 5:
            multiplier = 1.5      # 5连击: 1.5倍
        elif combo_count >= 3:
            multiplier = 1.3      # 3连击: 1.3倍
        else:
            multiplier = 1.0      # 无连击

        return combo_count, multiplier
