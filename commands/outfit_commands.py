"""
服装命令
"""

import re
import json
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api

from ..core.models import DTCharacter, DTOutfit, DTUserOutfit
from ..extensions.outfit_system import OutfitSystem


class DTOutfitListCommand(BaseCommand):
    """查看服装列表命令"""

    command_name = "dt_outfit_list"
    command_description = "查看拥有的服装"
    command_pattern = r"^/(衣柜|outfits?)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取拥有的服装
        owned = await database_api.db_get(
            DTUserOutfit,
            filters={"user_id": user_id, "chat_id": chat_id}
        )

        if not owned:
            await self.send_text("👗 还没有解锁任何服装\\n\\n提升属性来解锁更多服装！")
            return True, "无服装", True

        # 获取当前穿着
        current = await OutfitSystem.get_current_outfit(user_id, chat_id)
        current_id = current["outfit_id"] if current else None

        message = "👗 【服装列表】\\n\\n"

        for own in owned:
            outfit = await database_api.db_get(
                DTOutfit,
                filters={"outfit_id": own["outfit_id"]},
                single_result=True
            )

            if outfit:
                is_current = "✨" if own["outfit_id"] == current_id else "  "
                message += f"{is_current} {outfit['outfit_name']}\\n"
                message += f"   {outfit['description']}\\n"
                message += f"   兴奋+{outfit['arousal_bonus']} | 羞耻{outfit['shame_modifier']}\\n"
                message += f"   穿着次数: {own['times_worn']}\\n\\n"

        message += "\\n使用 /穿 <服装名> 来更换"

        await self.send_text(message.strip())
        return True, "显示服装", True


class DTWearOutfitCommand(BaseCommand):
    """穿上服装命令"""

    command_name = "dt_wear_outfit"
    command_description = "穿上指定服装"
    command_pattern = r"^/穿\\s+(.+)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("使用方法: /穿 <服装名>")
            return False, "格式错误", False

        outfit_name = match.group(1).strip()
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 查找服装
        all_outfits = await database_api.db_get(DTOutfit, filters={})
        target_outfit = None

        for outfit in all_outfits:
            if outfit["outfit_name"] == outfit_name or outfit["outfit_id"] == outfit_name:
                target_outfit = outfit
                break

        if not target_outfit:
            await self.send_text(f"❌ 找不到服装: {outfit_name}")
            return False, "服装不存在", False

        # 尝试装备
        success = await OutfitSystem.equip_outfit(user_id, chat_id, target_outfit["outfit_id"])

        if not success:
            await self.send_text(f"❌ 你还没有解锁这件服装")
            return False, "未解锁", False

        await self.send_text(f"✨ 已换上: {target_outfit['outfit_name']}\\n{target_outfit['description']}")
        return True, f"穿上{outfit_name}", True
