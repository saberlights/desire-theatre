"""
道具系统
"""

import json
import time
from typing import Tuple, Dict, Optional

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ..core.models import DTItem, DTUserInventory

logger = get_logger("dt_item_system")


class ItemSystem:
    """道具管理系统"""

    DEFAULT_ITEMS = [
        {
            "item_id": "love_potion",
            "item_name": "爱情药水",
            "category": "consumable",
            "description": "会让人变得更加...敏感",
            "effect_description": "+20兴奋度，+15欲望值",
            "attribute_effects": {"arousal": 20, "desire": 15},
            "duration_minutes": 0,
            "tags": ["consumable", "arousal"],
            "intensity_level": 3,
            "price": 50
        },
        {
            "item_id": "aphrodisiac",
            "item_name": "催情剂",
            "category": "consumable",
            "description": "强效的催情药物",
            "effect_description": "+30兴奋度，-20抵抗力，-15羞耻心",
            "attribute_effects": {"arousal": 30, "resistance": -20, "shame": -15},
            "duration_minutes": 60,
            "tags": ["consumable", "powerful"],
            "intensity_level": 7,
            "unlock_condition": {"corruption": 50},
            "price": 200
        },
        {
            "item_id": "red_wine",
            "item_name": "红酒",
            "category": "consumable",
            "description": "微醺的红酒，能让人放松下来",
            "effect_description": "-10抵抗力，+5亲密度，+5兴奋度",
            "attribute_effects": {"resistance": -10, "intimacy": 5, "arousal": 5},
            "duration_minutes": 0,
            "tags": ["consumable", "alcohol"],
            "intensity_level": 2,
            "price": 30
        },
        {
            "item_id": "chocolate",
            "item_name": "巧克力",
            "category": "consumable",
            "description": "甜蜜的巧克力，让人心情愉悦",
            "effect_description": "+8好感度，+5信任度",
            "attribute_effects": {"affection": 8, "trust": 5},
            "duration_minutes": 0,
            "tags": ["consumable", "gift"],
            "intensity_level": 1,
            "price": 20
        },
        {
            "item_id": "collar",
            "item_name": "项圈",
            "category": "toy",
            "description": "象征顺从的项圈",
            "effect_description": "+15顺从度，-10羞耻心，+8堕落度",
            "attribute_effects": {"submission": 15, "shame": -10, "corruption": 8},
            "duration_minutes": 0,
            "tags": ["toy", "bdsm"],
            "intensity_level": 6,
            "unlock_condition": {"corruption": 40},
            "price": 150
        },
        {
            "item_id": "blindfold",
            "item_name": "眼罩",
            "category": "toy",
            "description": "遮住视线，增强其他感官",
            "effect_description": "+12兴奋度，-8抵抗力，+10敏感度",
            "attribute_effects": {"arousal": 12, "resistance": -8, "desire": 10},
            "duration_minutes": 0,
            "tags": ["toy", "sensory"],
            "intensity_level": 4,
            "unlock_condition": {"intimacy": 50},
            "price": 80
        },
        {
            "item_id": "perfume",
            "item_name": "香水",
            "category": "consumable",
            "description": "诱人的香气",
            "effect_description": "+6好感度，+8欲望值",
            "attribute_effects": {"affection": 6, "desire": 8},
            "duration_minutes": 0,
            "tags": ["consumable", "fragrance"],
            "intensity_level": 2,
            "price": 40
        },
        {
            "item_id": "handcuffs",
            "item_name": "手铐",
            "category": "toy",
            "description": "限制自由的道具",
            "effect_description": "+18顺从度，-15抵抗力，+12堕落度",
            "attribute_effects": {"submission": 18, "resistance": -15, "corruption": 12},
            "duration_minutes": 0,
            "tags": ["toy", "bdsm", "restraint"],
            "intensity_level": 8,
            "unlock_condition": {"corruption": 60, "submission": 60},
            "price": 300
        },
        {
            "item_id": "massage_oil",
            "item_name": "按摩油",
            "category": "consumable",
            "description": "滑腻的按摩精油",
            "effect_description": "+10亲密度，+15兴奋度，-5羞耻心",
            "attribute_effects": {"intimacy": 10, "arousal": 15, "shame": -5},
            "duration_minutes": 0,
            "tags": ["consumable", "intimate"],
            "intensity_level": 4,
            "unlock_condition": {"intimacy": 40},
            "price": 60
        },
        {
            "item_id": "rose",
            "item_name": "玫瑰花",
            "category": "gift",
            "description": "浪漫的玫瑰花",
            "effect_description": "+12好感度，+8亲密度，+5信任度",
            "attribute_effects": {"affection": 12, "intimacy": 8, "trust": 5},
            "duration_minutes": 0,
            "tags": ["gift", "romantic"],
            "intensity_level": 1,
            "price": 25
        },
    ]

    @staticmethod
    async def initialize_items():
        """初始化默认道具"""
        for item_data in ItemSystem.DEFAULT_ITEMS:
            existing = await database_api.db_get(
                DTItem,
                filters={"item_id": item_data["item_id"]},
                single_result=True
            )

            if not existing:
                await database_api.db_save(
                    DTItem,
                    data={
                        "item_id": item_data["item_id"],
                        "item_name": item_data["item_name"],
                        "item_category": item_data["category"],
                        "description": item_data["description"],
                        "effect_description": item_data["effect_description"],
                        "attribute_effects": json.dumps(item_data["attribute_effects"]),
                        "duration_minutes": item_data["duration_minutes"],
                        "tags": json.dumps(item_data["tags"]),
                        "intensity_level": item_data["intensity_level"],
                        "unlock_condition": json.dumps(item_data.get("unlock_condition", {})),
                        "price": item_data.get("price", 0)
                    },
                    key_field="item_id",
                    key_value=item_data["item_id"]
                )

        logger.info("道具系统初始化完成")

    @staticmethod
    async def use_item(
        user_id: str,
        chat_id: str,
        item_id: str,
        character: Dict = None
    ) -> Tuple[bool, Dict]:
        """
        使用道具 (增强版 - 带心理场景)

        返回: (是否成功, 结果字典)
        结果字典包含: effects, duration_minutes, description, scene_description, extra_effects
        """
        # 检查库存
        inventory = await database_api.db_get(
            DTUserInventory,
            filters={"user_id": user_id, "chat_id": chat_id, "item_id": item_id},
            single_result=True
        )

        if not inventory or inventory["quantity"] <= 0:
            return False, {}

        # 获取道具信息
        item = await database_api.db_get(
            DTItem,
            filters={"item_id": item_id},
            single_result=True
        )

        if not item:
            return False, {}

        # 消耗道具（如果是消耗品）
        if item["item_category"] == "consumable":
            new_quantity = inventory["quantity"] - 1
            inventory["quantity"] = new_quantity

            await database_api.db_save(
                DTUserInventory,
                data=inventory,
                key_field="id",
                key_value=inventory["id"]
            )

        # 更新使用统计
        is_first_use = (inventory["times_used"] == 0)
        inventory["times_used"] = inventory["times_used"] + 1
        inventory["last_used"] = time.time()

        await database_api.db_save(
            DTUserInventory,
            data=inventory,
            key_field="id",
            key_value=inventory["id"]
        )

        # 返回基础效果
        effects = json.loads(item["attribute_effects"])
        result = {
            "effects": effects,
            "duration_minutes": item["duration_minutes"],
            "description": item["effect_description"]
        }

        # === 【新增】生成心理场景和额外效果 ===
        if character:
            scene_description, extra_effects = ItemSystem._generate_item_scene(item, character)
            result["scene_description"] = scene_description
            result["extra_effects"] = extra_effects

            # 【新增】为重要道具创建记忆
            if is_first_use:
                await ItemSystem._create_item_memory(user_id, chat_id, item, character)

        return True, result

    @staticmethod
    async def add_item(user_id: str, chat_id: str, item_id: str, quantity: int = 1):
        """添加道具到背包"""
        existing = await database_api.db_get(
            DTUserInventory,
            filters={"user_id": user_id, "chat_id": chat_id, "item_id": item_id},
            single_result=True
        )

        if existing:
            # 增加数量
            existing["quantity"] = existing["quantity"] + quantity
            await database_api.db_save(
                DTUserInventory,
                data=existing,
                key_field="id",
                key_value=existing["id"]
            )
        else:
            # 创建新道具
            await database_api.db_save(
                DTUserInventory,
                data={
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "item_id": item_id,
                    "quantity": quantity,
                    "acquired_at": time.time(),
                    "times_used": 0,
                    "last_used": None
                }
            )

        logger.info(f"添加道具: {item_id} x{quantity} for {user_id}")

    # === 【新增】心理效果系统 ===
    @staticmethod
    def _generate_item_scene(item: Dict, character: Dict) -> Tuple[Optional[str], Optional[Dict]]:
        """生成道具使用场景 (委托给增强模块)"""
        from .item_system_enhanced import ItemPsychologySystem
        return ItemPsychologySystem.generate_item_use_scene(item, character)

    @staticmethod
    async def _create_item_memory(user_id: str, chat_id: str, item: Dict, character: Dict):
        """创建道具记忆 (委托给增强模块)"""
        from .item_system_enhanced import ItemPsychologySystem
        await ItemPsychologySystem.create_item_memory(user_id, chat_id, item, character)
