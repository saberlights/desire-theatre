"""
商店系统 - 道具和服装购买
"""

import json
from typing import Tuple, List, Dict, Optional

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ..core.models import DTCharacter, DTItem, DTOutfit, DTUserInventory, DTUserOutfit
from .item_system import ItemSystem
from .outfit_system import OutfitSystem

logger = get_logger("dt_shop_system")


class ShopSystem:
    """商店管理系统"""

    @staticmethod
    async def get_available_items(user_id: str, chat_id: str) -> List[Dict]:
        """获取可购买的道具列表"""
        # 获取角色数据
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            return []

        # 获取所有道具
        all_items = await database_api.db_get(DTItem)
        available_items = []

        for item in all_items:
            # 检查解锁条件
            unlock_condition = json.loads(item.get("unlock_condition", "{}"))
            if ShopSystem._check_unlock_condition(char, unlock_condition):
                available_items.append(item)

        return available_items

    @staticmethod
    async def get_available_outfits(user_id: str, chat_id: str) -> List[Dict]:
        """获取可购买的服装列表"""
        # 获取角色数据
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            return []

        # 获取所有服装
        all_outfits = await database_api.db_get(DTOutfit)
        available_outfits = []

        for outfit in all_outfits:
            # 跳过默认免费服装
            if outfit.get("is_unlocked_by_default", False):
                continue

            # 检查是否已拥有
            owned = await database_api.db_get(
                DTUserOutfit,
                filters={"user_id": user_id, "chat_id": chat_id, "outfit_id": outfit["outfit_id"]},
                single_result=True
            )

            if owned:
                continue  # 已拥有，不显示

            # 检查解锁条件
            unlock_condition = json.loads(outfit.get("unlock_condition", "{}"))
            if ShopSystem._check_unlock_condition(char, unlock_condition):
                available_outfits.append(outfit)

        return available_outfits

    @staticmethod
    def _check_unlock_condition(character: Dict, condition: Dict) -> bool:
        """检查解锁条件"""
        if not condition:
            return True  # 无条件限制

        for attr, value in condition.items():
            char_value = character.get(attr, 0)

            if isinstance(value, str) and value.startswith("<"):
                # 小于条件
                threshold = int(value[1:])
                if char_value >= threshold:
                    return False
            else:
                # 大于等于条件
                threshold = int(value)
                if char_value < threshold:
                    return False

        return True

    @staticmethod
    async def buy_item(user_id: str, chat_id: str, item_id: str, quantity: int = 1) -> Tuple[bool, str]:
        """购买道具"""
        # 获取角色
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            return False, "角色不存在"

        # 获取道具信息
        item = await database_api.db_get(
            DTItem,
            filters={"item_id": item_id},
            single_result=True
        )

        if not item:
            return False, "道具不存在"

        # 检查解锁条件
        unlock_condition = json.loads(item.get("unlock_condition", "{}"))
        if not ShopSystem._check_unlock_condition(char, unlock_condition):
            return False, "未满足解锁条件"

        # 计算总价
        total_price = item["price"] * quantity

        # 检查金币是否足够
        if char["coins"] < total_price:
            return False, f"爱心币不足！需要{total_price}币，当前只有{char['coins']}币"

        # 扣除金币
        char["coins"] = char["coins"] - total_price

        await database_api.db_save(
            DTCharacter,
            data=char,
            key_field="user_id",
            key_value=user_id
        )

        # 添加道具到背包
        await ItemSystem.add_item(user_id, chat_id, item_id, quantity)

        logger.info(f"购买道具: {user_id} - {item_id} x{quantity}, 花费{total_price}币")
        return True, f"成功购买 {item['item_name']} x{quantity}，花费{total_price}💰"

    @staticmethod
    async def buy_outfit(user_id: str, chat_id: str, outfit_id: str) -> Tuple[bool, str]:
        """购买服装"""
        # 获取角色
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            return False, "角色不存在"

        # 获取服装信息
        outfit = await database_api.db_get(
            DTOutfit,
            filters={"outfit_id": outfit_id},
            single_result=True
        )

        if not outfit:
            return False, "服装不存在"

        # 检查是否已拥有
        owned = await database_api.db_get(
            DTUserOutfit,
            filters={"user_id": user_id, "chat_id": chat_id, "outfit_id": outfit_id},
            single_result=True
        )

        if owned:
            return False, "你已经拥有这件服装了"

        # 检查解锁条件
        unlock_condition = json.loads(outfit.get("unlock_condition", "{}"))
        if not ShopSystem._check_unlock_condition(char, unlock_condition):
            return False, "未满足解锁条件"

        # 获取价格
        price = outfit.get("unlock_cost", 0)

        # 检查金币是否足够
        if char["coins"] < price:
            return False, f"爱心币不足！需要{price}币，当前只有{char['coins']}币"

        # 扣除金币
        char["coins"] = char["coins"] - price

        await database_api.db_save(
            DTCharacter,
            data=char,
            key_field="user_id",
            key_value=user_id
        )

        # 解锁服装
        await OutfitSystem.unlock_outfit(user_id, chat_id, outfit_id)

        logger.info(f"购买服装: {user_id} - {outfit_id}, 花费{price}币")
        return True, f"成功购买 {outfit['outfit_name']}，花费{price}💰\n现在可以使用 /穿 {outfit['outfit_name']} 来穿上它"
