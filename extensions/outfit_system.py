"""
服装系统 (增强版 - 心理效果系统)
"""

import json
import time
from typing import Optional, Dict, Tuple

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ..core.models import DTOutfit, DTUserOutfit, DTCurrentOutfit, DTMemory

logger = get_logger("dt_outfit_system")


class OutfitSystem:
    """服装管理系统"""

    # 预定义服装库
    DEFAULT_OUTFITS = [
        {
            "outfit_id": "casual",
            "outfit_name": "日常便装",
            "category": "normal",
            "description": "普通的日常服装",
            "attribute_modifiers": {},
            "arousal_bonus": 0,
            "shame_modifier": 0,
            "is_default": True,
            "price": 0  # 默认免费
        },
        {
            "outfit_id": "school_uniform",
            "outfit_name": "学生制服",
            "category": "normal",
            "description": "清纯的学生制服",
            "attribute_modifiers": {"affection_gain": 1.1},
            "arousal_bonus": 5,
            "shame_modifier": 0,
            "is_default": True,
            "price": 50
        },
        {
            "outfit_id": "sexy_dress",
            "outfit_name": "性感连衣裙",
            "category": "sexy",
            "description": "紧身的黑色连衣裙",
            "attribute_modifiers": {"arousal_gain": 1.2},
            "arousal_bonus": 15,
            "shame_modifier": -10,
            "unlock_condition": {"intimacy": 50},
            "is_default": False,
            "price": 200
        },
        {
            "outfit_id": "bunny_suit",
            "outfit_name": "兔女郎装",
            "category": "cosplay",
            "description": "经典的兔女郎服装",
            "attribute_modifiers": {"arousal_gain": 1.3},
            "arousal_bonus": 20,
            "shame_modifier": -15,
            "unlock_condition": {"corruption": 40},
            "is_default": False,
            "price": 400
        },
        {
            "outfit_id": "lingerie_set",
            "outfit_name": "情趣内衣",
            "category": "lingerie",
            "description": "若隐若现的蕾丝内衣",
            "attribute_modifiers": {"arousal_gain": 1.5},
            "arousal_bonus": 30,
            "shame_modifier": -25,
            "unlock_condition": {"corruption": 60, "shame": "<40"},
            "is_default": False,
            "price": 600
        },
        {
            "outfit_id": "maid_outfit",
            "outfit_name": "女仆装",
            "category": "cosplay",
            "description": "可爱的女仆装扮",
            "attribute_modifiers": {"submission_gain": 1.2},
            "arousal_bonus": 18,
            "shame_modifier": -12,
            "unlock_condition": {"submission": 50},
            "is_default": False,
            "price": 300
        },
        {
            "outfit_id": "nothing",
            "outfit_name": "一丝不挂",
            "category": "lingerie",
            "description": "完全不穿...",
            "attribute_modifiers": {"arousal_gain": 2.0, "shame_loss": 2.0},
            "arousal_bonus": 50,
            "shame_modifier": -50,
            "unlock_condition": {"shame": "<10", "corruption": 80},
            "is_default": False,
            "price": 1000
        }
    ]

    @staticmethod
    async def initialize_outfits():
        """初始化默认服装"""
        for outfit_data in OutfitSystem.DEFAULT_OUTFITS:
            existing = await database_api.db_get(
                DTOutfit,
                filters={"outfit_id": outfit_data["outfit_id"]},
                single_result=True
            )

            if not existing:
                await database_api.db_save(
                    DTOutfit,
                    data={
                        "outfit_id": outfit_data["outfit_id"],
                        "outfit_name": outfit_data["outfit_name"],
                        "outfit_category": outfit_data["category"],
                        "description": outfit_data["description"],
                        "unlock_condition": json.dumps(outfit_data.get("unlock_condition", {})),
                        "attribute_modifiers": json.dumps(outfit_data["attribute_modifiers"]),
                        "arousal_bonus": outfit_data["arousal_bonus"],
                        "shame_modifier": outfit_data["shame_modifier"],
                        "special_effects": "[]",
                        "is_unlocked_by_default": outfit_data.get("is_default", False),
                        "unlock_cost": outfit_data.get("price", 0)
                    },
                    key_field="outfit_id",
                    key_value=outfit_data["outfit_id"]
                )

        logger.info("服装系统初始化完成")

    @staticmethod
    async def get_current_outfit(user_id: str, chat_id: str) -> Optional[Dict]:
        """获取当前穿着"""
        current = await database_api.db_get(
            DTCurrentOutfit,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not current:
            return None

        outfit = await database_api.db_get(
            DTOutfit,
            filters={"outfit_id": current["outfit_id"]},
            single_result=True
        )

        return outfit

    @staticmethod
    async def equip_outfit(user_id: str, chat_id: str, outfit_id: str, character: Dict = None) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        装备服装 (增强版 - 带心理反应)

        返回: (是否成功, 心理反应消息, 即时属性效果)
        """
        # 检查是否拥有
        owned = await database_api.db_get(
            DTUserOutfit,
            filters={"user_id": user_id, "chat_id": chat_id, "outfit_id": outfit_id},
            single_result=True
        )

        if not owned:
            return False, None, None

        # 获取服装信息
        outfit = await database_api.db_get(
            DTOutfit,
            filters={"outfit_id": outfit_id},
            single_result=True
        )

        if not outfit:
            return False, None, None

        # 更新当前装备
        await database_api.db_save(
            DTCurrentOutfit,
            data={
                "user_id": user_id,
                "chat_id": chat_id,
                "outfit_id": outfit_id,
                "equipped_at": time.time()
            },
            key_field="user_id",
            key_value=user_id
        )

        # 更新使用统计
        is_first_time = (owned["times_worn"] == 0)
        owned["times_worn"] = owned["times_worn"] + 1
        owned["last_worn"] = time.time()

        await database_api.db_save(
            DTUserOutfit,
            data=owned,
            key_field="id",
            key_value=owned["id"]
        )

        # === 【新增】生成心理反应 ===
        if character:
            psychological_message, instant_effects = OutfitSystem._generate_outfit_reaction(
                outfit, character, is_first_time
            )

            # 【新增】创建记忆 - 服装留下心理印象
            if is_first_time:
                await OutfitSystem._create_outfit_memory(user_id, chat_id, outfit, character)

            return True, psychological_message, instant_effects

        return True, None, None

    @staticmethod
    async def unlock_outfit(user_id: str, chat_id: str, outfit_id: str):
        """解锁服装"""
        # 检查是否已拥有
        existing = await database_api.db_get(
            DTUserOutfit,
            filters={"user_id": user_id, "chat_id": chat_id, "outfit_id": outfit_id},
            single_result=True
        )

        if existing:
            return  # 已拥有

        # 解锁
        await database_api.db_save(
            DTUserOutfit,
            data={
                "user_id": user_id,
                "chat_id": chat_id,
                "outfit_id": outfit_id,
                "unlocked_at": time.time(),
                "times_worn": 0,
                "last_worn": None
            }
        )

        logger.info(f"解锁服装: {outfit_id} for {user_id}")

    # === 【新增】心理效果系统 ===
    @staticmethod
    def _generate_outfit_reaction(outfit: Dict, character: Dict, is_first_time: bool) -> Tuple[Optional[str], Optional[Dict]]:
        """生成换装心理反应 (委托给增强模块)"""
        from .outfit_system_enhanced import OutfitPsychologySystem
        return OutfitPsychologySystem.generate_outfit_reaction(outfit, character, is_first_time)

    @staticmethod
    async def _create_outfit_memory(user_id: str, chat_id: str, outfit: Dict, character: Dict):
        """创建服装记忆 (委托给增强模块)"""
        from .outfit_system_enhanced import OutfitPsychologySystem
        await OutfitPsychologySystem.create_outfit_memory(user_id, chat_id, outfit, character)
