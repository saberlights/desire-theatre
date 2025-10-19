"""
场景系统
"""

import json
import time
import random
from typing import Optional, Dict, List

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ...core.models import DTScene, DTVisitedScene

logger = get_logger("dt_scene_system")


class SceneSystem:
    """场景管理系统"""

    # 预定义场景
    DEFAULT_SCENES = [
        {
            "scene_id": "bedroom",
            "scene_name": "卧室",
            "category": "private",
            "description": "私密的个人空间，床铺整洁柔软",
            "unlock_condition": {},
            "available_actions": ["拥抱", "亲", "推倒"],
            "attribute_modifiers": {"intimacy_gain": 1.2, "arousal_gain": 1.1},
            "special_effects": ["可能触发特殊情节"],
            "is_default": True
        },
        {
            "scene_id": "bathroom",
            "scene_name": "浴室",
            "category": "private",
            "description": "弥漫着水汽的浴室",
            "unlock_condition": {"intimacy": 40},
            "available_actions": ["抱", "亲", "摸"],
            "attribute_modifiers": {"arousal_gain": 1.3, "shame_loss": 1.2},
            "special_effects": ["羞耻心降低加速"],
            "is_default": False
        },
        {
            "scene_id": "park",
            "scene_name": "公园",
            "category": "public",
            "description": "人来人往的公园，周围有路人",
            "unlock_condition": {},
            "available_actions": ["牵手", "抱"],
            "attribute_modifiers": {"affection_gain": 1.1, "shame_modifier": 10},
            "special_effects": ["公开场合羞耻感增加"],
            "is_default": True
        },
        {
            "scene_id": "classroom",
            "scene_name": "教室",
            "category": "semi_private",
            "description": "空无一人的教室",
            "unlock_condition": {"intimacy": 30},
            "available_actions": ["牵手", "抱", "亲"],
            "attribute_modifiers": {"arousal_gain": 1.2, "excitement_bonus": 5},
            "special_effects": ["禁忌感增加兴奋度"],
            "is_default": False
        },
        {
            "scene_id": "love_hotel",
            "scene_name": "情人旅馆",
            "category": "private",
            "description": "暧昧的房间，充满情色氛围",
            "unlock_condition": {"corruption": 50, "intimacy": 60},
            "available_actions": ["推倒", "调教", "侵犯"],
            "attribute_modifiers": {"arousal_gain": 1.5, "corruption_gain": 1.3},
            "special_effects": ["极大增强堕落效果"],
            "is_default": False
        },
        {
            "scene_id": "street",
            "scene_name": "街道",
            "category": "public",
            "description": "繁华的街道，人群拥挤",
            "unlock_condition": {"shame": "<30", "corruption": 40},
            "available_actions": ["牵手", "抱", "摸"],
            "attribute_modifiers": {"shame_loss": 1.5, "excitement_bonus": 10},
            "special_effects": ["公开羞耻play"],
            "is_default": False
        }
    ]

    @staticmethod
    async def initialize_scenes():
        """初始化默认场景"""
        for scene_data in SceneSystem.DEFAULT_SCENES:
            existing = await database_api.db_get(
                DTScene,
                filters={"scene_id": scene_data["scene_id"]},
                single_result=True
            )

            if not existing:
                await database_api.db_save(
                    DTScene,
                    data={
                        "scene_id": scene_data["scene_id"],
                        "scene_name": scene_data["scene_name"],
                        "scene_category": scene_data["category"],
                        "description": scene_data["description"],
                        "unlock_condition": json.dumps(scene_data["unlock_condition"]),
                        "available_actions": json.dumps(scene_data["available_actions"]),
                        "attribute_modifiers": json.dumps(scene_data["attribute_modifiers"]),
                        "special_effects": json.dumps(scene_data["special_effects"]),
                        "is_unlocked_by_default": scene_data["is_default"]
                    },
                    key_field="scene_id",
                    key_value=scene_data["scene_id"]
                )

        logger.info("场景系统初始化完成")

    @staticmethod
    async def get_unlocked_scenes(user_id: str, chat_id: str, character: Dict) -> List[Dict]:
        """获取已解锁的场景列表"""
        all_scenes = await database_api.db_get(DTScene, filters={})
        unlocked = []

        for scene in all_scenes:
            if scene["is_unlocked_by_default"]:
                unlocked.append(scene)
                continue

            # 检查解锁条件
            unlock_cond = json.loads(scene["unlock_condition"])
            meets_requirements = True

            for attr, required in unlock_cond.items():
                char_value = character.get(attr, 0)

                if isinstance(required, str) and required.startswith("<"):
                    threshold = int(required[1:])
                    if char_value >= threshold:
                        meets_requirements = False
                        break
                else:
                    threshold = int(required)
                    if char_value < threshold:
                        meets_requirements = False
                        break

            if meets_requirements:
                unlocked.append(scene)

        return unlocked

    @staticmethod
    async def visit_scene(user_id: str, chat_id: str, scene_id: str) -> Optional[Dict]:
        """访问场景"""
        # 获取场景信息
        scene = await database_api.db_get(
            DTScene,
            filters={"scene_id": scene_id},
            single_result=True
        )

        if not scene:
            return None

        # 记录访问
        await database_api.db_save(
            DTVisitedScene,
            data={
                "user_id": user_id,
                "chat_id": chat_id,
                "scene_id": scene_id,
                "visited_at": time.time()
            }
        )

        # 返回场景信息和修饰符
        return {
            "scene_name": scene["scene_name"],
            "description": scene["description"],
            "modifiers": json.loads(scene["attribute_modifiers"]),
            "available_actions": json.loads(scene["available_actions"]),
            "special_effects": json.loads(scene["special_effects"])
        }

    @staticmethod
    async def get_current_scene(user_id: str, chat_id: str) -> Optional[str]:
        """获取当前场景"""
        # 获取最近访问的场景
        visits = await database_api.db_get(
            DTVisitedScene,
            filters={"user_id": user_id, "chat_id": chat_id}
        )

        if not visits:
            return None

        # 返回最新的访问记录
        latest = max(visits, key=lambda x: x["visited_at"])
        return latest["scene_id"]
