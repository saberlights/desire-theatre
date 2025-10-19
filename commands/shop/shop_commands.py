"""
商店命令
"""

import re
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api

from ...core.models import DTCharacter
from ...features.shop.shop_system import ShopSystem


class DTShopCommand(BaseCommand):
    """查看商店命令"""

    command_name = "dt_shop"
    command_description = "查看商店"
    command_pattern = r"^/(商店|shop|商城)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色数据
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            await self.send_text("❌ 还没有创建角色！\n使用 /开始 <人格> 来开始游戏")
            return True, "角色未创建", True

        # 获取可购买的道具和服装
        available_items = await ShopSystem.get_available_items(user_id, chat_id)
        available_outfits = await ShopSystem.get_available_outfits(user_id, chat_id)

        # 使用图片输出
        try:
            from ...utils.help_image_generator import HelpImageGenerator

            sections = []

            # 道具商店
            if available_items:
                item_list = []
                for item in available_items:
                    rarity_emoji = {
                        1: "⭐", 2: "⭐", 3: "✨",
                        4: "✨", 5: "💫", 6: "💫",
                        7: "🌟", 8: "🌟", 9: "💥", 10: "💥"
                    }.get(item["intensity_level"], "⭐")

                    item_list.append(
                        f"{rarity_emoji} {item['item_name']} - {item['price']}💰\n"
                        f"   {item['effect_description']}"
                    )
                sections.append(("📦 道具商店", item_list))
            else:
                sections.append(("📦 道具商店", ["暂无可购买道具（可能需要提升属性解锁）"]))

            # 服装商店
            if available_outfits:
                outfit_list = []
                for outfit in available_outfits:
                    category_emoji = {
                        "normal": "👔",
                        "sexy": "👗",
                        "cosplay": "🎭",
                        "lingerie": "💋"
                    }.get(outfit["outfit_category"], "👔")

                    outfit_list.append(
                        f"{category_emoji} {outfit['outfit_name']} - {outfit['unlock_cost']}💰\n"
                        f"   {outfit['description']}"
                    )
                sections.append(("👗 服装商店", outfit_list))
            else:
                sections.append(("👗 服装商店", ["暂无可购买服装（可能需要提升属性解锁或已全部拥有）"]))

            # 购买方式
            sections.append(("💡 购买方式", [
                "/买道具 <名称> [数量] - 购买道具",
                "/买服装 <名称> - 购买服装",
                "",
                "例如: /买道具 巧克力",
                "      /买服装 女仆装",
                "",
                f"💰 你的爱心币: {char['coins']}"
            ]))

            img_bytes, img_base64 = HelpImageGenerator.generate_help_image(
                "商店", sections, width=900
            )

            await self.send_image(img_base64)
            return True, "显示商店", True

        except Exception as e:
            # 降级到文本模式
            pass

        # 文本模式
        shop_text = f"""🏪 【欲望剧场 - 商店】

💰 你的爱心币: {char['coins']}

━━━ 📦 道具商店 ━━━
"""

        if available_items:
            for item in available_items:
                rarity_emoji = {
                    1: "⭐", 2: "⭐", 3: "✨",
                    4: "✨", 5: "💫", 6: "💫",
                    7: "🌟", 8: "🌟", 9: "💥", 10: "💥"
                }.get(item["intensity_level"], "⭐")

                shop_text += f"\n{rarity_emoji} {item['item_name']} - {item['price']}💰"
                shop_text += f"\n   {item['effect_description']}"
        else:
            shop_text += "\n暂无可购买道具（可能需要提升属性解锁）"

        shop_text += f"""

━━━ 👗 服装商店 ━━━
"""

        if available_outfits:
            for outfit in available_outfits:
                category_emoji = {
                    "normal": "👔",
                    "sexy": "👗",
                    "cosplay": "🎭",
                    "lingerie": "💋"
                }.get(outfit["outfit_category"], "👔")

                shop_text += f"\n{category_emoji} {outfit['outfit_name']} - {outfit['unlock_cost']}💰"
                shop_text += f"\n   {outfit['description']}"
        else:
            shop_text += "\n暂无可购买服装（可能需要提升属性解锁或已全部拥有）"

        shop_text += """

━━━ 💡 购买方式 ━━━
/买道具 <名称> [数量]   购买道具
/买服装 <名称>         购买服装

例如: /买道具 巧克力
      /买服装 女仆装

💡 Tip: 通过互动、打工等方式获得爱心币！
"""

        await self.send_text(shop_text.strip())
        return True, "显示商店", True


class DTBuyItemCommand(BaseCommand):
    """购买道具命令"""

    command_name = "dt_buy_item"
    command_description = "购买道具"
    command_pattern = r"^/(买道具|买|buy)\s+(.+?)(?:\s+(\d+))?$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("❌ 格式错误\n\n使用方法: /买道具 <道具名称> [数量]\n例如: /买道具 巧克力 2")
            return False, "格式错误", False

        item_name = match.group(2).strip()
        quantity_str = match.group(3)
        quantity = int(quantity_str) if quantity_str else 1

        if quantity <= 0 or quantity > 99:
            await self.send_text("❌ 数量必须在1-99之间")
            return False, "数量无效", False

        # 根据名称查找道具ID
        from ...core.models import DTItem
        all_items = await database_api.db_get(
            DTItem,
            filters={"item_name": item_name},
            single_result=True
        )

        if not all_items:
            await self.send_text(f"❌ 未找到道具: {item_name}\n\n使用 /商店 查看可购买道具")
            return False, "道具不存在", False

        item_id = all_items["item_id"]

        # 购买道具
        success, message = await ShopSystem.buy_item(user_id, chat_id, item_id, quantity)

        if success:
            await self.send_text(f"✅ {message}")
        else:
            await self.send_text(f"❌ {message}")

        return success, message, success


class DTBuyOutfitCommand(BaseCommand):
    """购买服装命令"""

    command_name = "dt_buy_outfit"
    command_description = "购买服装"
    command_pattern = r"^/(买服装|买衣服)\s+(.+)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("❌ 格式错误\n\n使用方法: /买服装 <服装名称>\n例如: /买服装 女仆装")
            return False, "格式错误", False

        outfit_name = match.group(2).strip()

        # 根据名称查找服装ID
        from ...core.models import DTOutfit
        outfit = await database_api.db_get(
            DTOutfit,
            filters={"outfit_name": outfit_name},
            single_result=True
        )

        if not outfit:
            await self.send_text(f"❌ 未找到服装: {outfit_name}\n\n使用 /商店 查看可购买服装")
            return False, "服装不存在", False

        outfit_id = outfit["outfit_id"]

        # 购买服装
        success, message = await ShopSystem.buy_outfit(user_id, chat_id, outfit_id)

        if success:
            await self.send_text(f"✅ {message}")
        else:
            await self.send_text(f"❌ {message}")

        return success, message, success
