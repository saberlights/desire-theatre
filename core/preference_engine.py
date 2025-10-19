"""
偏好学习引擎
"""

import time
from typing import List, Dict

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from .models import DTPreference

logger = get_logger("dt_preference_engine")


class PreferenceEngine:
    """偏好学习引擎"""

    @staticmethod
    async def learn_preference(
        user_id: str,
        chat_id: str,
        preference_type: str,
        content: str,
        weight: int = 10,
        learned_from: str = None
    ):
        """学习新偏好"""
        # 检查是否已存在
        existing = await database_api.db_get(
            DTPreference,
            filters={
                "user_id": user_id,
                "chat_id": chat_id,
                "preference_type": preference_type,
                "content": content
            },
            single_result=True
        )

        if existing:
            # 增加权重
            new_weight = min(100, existing["weight"] + weight)
            existing["weight"] = new_weight
            existing["trigger_count"] = existing["trigger_count"] + 1
            existing["confidence"] = min(1.0, existing["confidence"] + 0.1)

            await database_api.db_save(
                DTPreference,
                data=existing,
                key_field="id",
                key_value=existing["id"]
            )
        else:
            # 创建新偏好
            await database_api.db_save(
                DTPreference,
                data={
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "preference_type": preference_type,
                    "content": content,
                    "weight": weight,
                    "trigger_count": 1,
                    "positive_reactions": 0,
                    "negative_reactions": 0,
                    "learned_from": learned_from,
                    "confidence": 0.5,
                    "created_at": time.time(),
                    "last_triggered": time.time()
                }
            )

        logger.debug(f"学习偏好: {preference_type} - {content}")

    @staticmethod
    async def get_preferences(
        user_id: str,
        chat_id: str,
        preference_type: str = None,
        min_weight: int = 10
    ) -> List[Dict]:
        """获取偏好列表"""
        filters = {"user_id": user_id, "chat_id": chat_id}

        if preference_type:
            filters["preference_type"] = preference_type

        preferences = await database_api.db_get(
            DTPreference,
            filters=filters,
            order_by="-weight"
        )

        if not preferences:
            return []

        # 筛选权重
        return [p for p in preferences if p["weight"] >= min_weight]
