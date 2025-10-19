"""
成就系统
"""

import json
import time
from typing import List, Dict

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ..core.models import DTAchievement, DTUserAchievement

logger = get_logger("dt_achievement_system")


class AchievementSystem:
    """成就管理系统"""

    DEFAULT_ACHIEVEMENTS = [
        {
            "achievement_id": "first_kiss",
            "name": "初吻",
            "category": "milestone",
            "description": "第一次亲密接触",
            "hint": "提升亲密度到30",
            "conditions": {"intimacy": ">=30"},
            "is_hidden": False,
            "reward_points": 10,
            "rarity": "common"
        },
        {
            "achievement_id": "corruption_start",
            "name": "堕落开始",
            "category": "milestone",
            "description": "踏上堕落之路",
            "hint": "堕落度达到30",
            "conditions": {"corruption": ">=30"},
            "is_hidden": False,
            "reward_points": 15,
            "rarity": "common"
        },
        {
            "achievement_id": "complete_corruption",
            "name": "完全堕落",
            "category": "milestone",
            "description": "彻底堕落为欲望的奴隶",
            "hint": "堕落度和顺从度都达到90",
            "conditions": {"corruption": ">=90", "submission": ">=90"},
            "is_hidden": False,
            "reward_points": 50,
            "rarity": "legendary"
        },
    ]

    @staticmethod
    async def initialize_achievements():
        """初始化成就"""
        for ach_data in AchievementSystem.DEFAULT_ACHIEVEMENTS:
            existing = await database_api.db_get(
                DTAchievement,
                filters={"achievement_id": ach_data["achievement_id"]},
                single_result=True
            )

            if not existing:
                await database_api.db_save(
                    DTAchievement,
                    data={
                        "achievement_id": ach_data["achievement_id"],
                        "achievement_name": ach_data["name"],
                        "achievement_category": ach_data["category"],
                        "description": ach_data["description"],
                        "hint": ach_data["hint"],
                        "unlock_conditions": json.dumps(ach_data["conditions"]),
                        "is_hidden": ach_data["is_hidden"],
                        "reward_points": ach_data["reward_points"],
                        "reward_items": "[]",
                        "rarity": ach_data["rarity"]
                    },
                    key_field="achievement_id",
                    key_value=ach_data["achievement_id"]
                )

        logger.info("成就系统初始化完成")

    @staticmethod
    async def check_achievements(
        user_id: str,
        chat_id: str,
        character: Dict
    ) -> List[Dict]:
        """检查可解锁的成就"""
        # 获取所有成就
        all_achievements = await database_api.db_get(DTAchievement, filters={})

        # 获取已解锁的成就
        unlocked = await database_api.db_get(
            DTUserAchievement,
            filters={"user_id": user_id, "chat_id": chat_id}
        )
        unlocked_ids = [a["achievement_id"] for a in unlocked] if unlocked else []

        newly_unlocked = []

        for ach in all_achievements:
            if ach["achievement_id"] in unlocked_ids:
                continue

            # 检查条件
            conditions = json.loads(ach["unlock_conditions"])
            all_met = True

            for attr, requirement in conditions.items():
                char_value = character.get(attr, 0)

                if ">=" in requirement:
                    threshold = int(requirement.replace(">=", ""))
                    if char_value < threshold:
                        all_met = False
                        break
                elif "<=" in requirement:
                    threshold = int(requirement.replace("<=", ""))
                    if char_value > threshold:
                        all_met = False
                        break

            if all_met:
                # 解锁成就
                await database_api.db_save(
                    DTUserAchievement,
                    data={
                        "user_id": user_id,
                        "chat_id": chat_id,
                        "achievement_id": ach["achievement_id"],
                        "unlocked_at": time.time(),
                        "progress": 1.0
                    }
                )

                newly_unlocked.append(ach)

        return newly_unlocked
