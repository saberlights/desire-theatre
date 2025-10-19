"""
道具命令
"""

import re
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api

from ..core.models import DTCharacter, DTItem, DTUserInventory
from ..core.attribute_system import AttributeSystem
from ..extensions.item_system import ItemSystem


class DTInventoryCommand(BaseCommand):
    """查看背包命令"""

    command_name = "dt_inventory"
    command_description = "查看道具背包"
    command_pattern = r"^/(背包|包|inv(entory)?)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        inventory = await database_api.db_get(
            DTUserInventory,
            filters={"user_id": user_id, "chat_id": chat_id}
        )

        if not inventory:
            await self.send_text("🎒 背包是空的")
            return True, "空背包", True

        message = "🎒 【道具背包】\\n\\n"

        for inv in inventory:
            item = await database_api.db_get(
                DTItem,
                filters={"item_id": inv["item_id"]},
                single_result=True
            )

            if item:
                message += f"📦 {item['item_name']} x{inv['quantity']}\\n"
                message += f"   {item['description']}\\n"
                message += f"   效果: {item['effect_description']}\\n"
                message += f"   使用次数: {inv['times_used']}\\n\\n"

        message += "\\n使用 /用 <道具名> 来使用道具"

        await self.send_text(message.strip())
        return True, "显示背包", True


class DTUseItemCommand(BaseCommand):
    """使用道具命令"""

    command_name = "dt_use_item"
    command_description = "使用道具"
    command_pattern = r"^/用\\s+(.+)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("使用方法: /用 <道具名>")
            return False, "格式错误", False

        item_name = match.group(1).strip()
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 查找道具
        all_items = await database_api.db_get(DTItem, filters={})
        target_item = None

        for item in all_items:
            if item["item_name"] == item_name or item["item_id"] == item_name:
                target_item = item
                break

        if not target_item:
            await self.send_text(f"❌ 找不到道具: {item_name}")
            return False, "道具不存在", False

        # 使用道具
        success, result = await ItemSystem.use_item(user_id, chat_id, target_item["item_id"])

        if not success:
            await self.send_text("❌ 你没有这个道具或数量不足")
            return False, "使用失败", False

        # 应用效果到角色
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if char:
            for attr, change in result["effects"].items():
                if attr in char:
                    new_value = AttributeSystem.clamp(char[attr] + change)
                    char[attr] = new_value

            await database_api.db_save(
                DTCharacter,
                data=char,
                key_field="user_id",
                key_value=user_id
            )

        duration_text = ""
        if result["duration_minutes"] > 0:
            duration_text = f"\\n⏱️ 持续时间: {result['duration_minutes']}分钟"

        await self.send_text(f"✨ 使用了 {target_item['item_name']}\\n\\n💫 {result['description']}{duration_text}")
        return True, f"使用{item_name}", True
