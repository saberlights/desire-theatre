"""
扩展命令 - 服装、道具、场景、游戏
"""

import re
import json
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api, send_api
from src.common.logger import get_logger

from ...core.models import DTCharacter
from ...systems.attributes.attribute_system import AttributeSystem
from ...features.outfits.outfit_system import OutfitSystem
from ...features.items.item_system import ItemSystem
from ...features.scenes.scene_system import SceneSystem
from ...features.games.game_system import GameSystem

logger = get_logger("dt_extension_commands")


class DTOutfitListCommand(BaseCommand):
    """查看服装列表"""

    command_name = "dt_outfit_list"
    command_description = "查看所有可用服装"
    command_pattern = r"^/(服装列表|outfits?)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not character:
            await self.send_text("❌ 你还没有开始游戏！使用 /开始 来开始")
            return False, "角色不存在", False

        # 获取所有服装
        from ...core.models import DTOutfit, DTUserOutfit
        all_outfits = await database_api.db_get(DTOutfit, filters={})
        owned_outfits = await database_api.db_get(
            DTUserOutfit,
            filters={"user_id": user_id, "chat_id": chat_id}
        )
        owned_ids = {o["outfit_id"] for o in owned_outfits}

        # 使用图片输出
        try:
            from ...utils.help_image_generator import HelpImageGenerator

            # 按类别分组
            categories = {
                "已拥有": [],
                "可解锁": [],
                "未解锁": []
            }

            for outfit in all_outfits:
                unlock_cond = json.loads(outfit["unlock_condition"])
                is_owned = outfit["outfit_id"] in owned_ids
                is_unlockable = True

                # 检查解锁条件
                for attr, required in unlock_cond.items():
                    char_value = character.get(attr, 0)
                    if isinstance(required, str) and required.startswith("<"):
                        threshold = int(required[1:])
                        if char_value >= threshold:
                            is_unlockable = False
                    else:
                        threshold = int(required)
                        if char_value < threshold:
                            is_unlockable = False

                outfit_text = f"{outfit['outfit_name']} - {outfit['description']}"

                # 显示状态
                if is_owned:
                    categories["已拥有"].append(f"✅ {outfit_text}")
                elif is_unlockable or outfit["is_unlocked_by_default"]:
                    categories["可解锁"].append(f"🔓 {outfit_text}")
                else:
                    categories["未解锁"].append(f"🔒 {outfit_text}")

            # 构建sections
            sections = []
            if categories["已拥有"]:
                sections.append(("已拥有", categories["已拥有"]))
            if categories["可解锁"]:
                sections.append(("可解锁", categories["可解锁"]))
            if categories["未解锁"]:
                sections.append(("未解锁", categories["未解锁"]))

            img_bytes, img_base64 = HelpImageGenerator.generate_list_image(
                "服装列表", sections, width=800
            )

            await self.send_image(img_base64)
            return True, "服装列表", True

        except Exception as e:
            # 降级到文本模式
            lines = ["👗 【服装列表】\n"]

            for outfit in all_outfits:
                unlock_cond = json.loads(outfit["unlock_condition"])
                is_owned = outfit["outfit_id"] in owned_ids
                is_unlockable = True

                # 检查解锁条件
                for attr, required in unlock_cond.items():
                    char_value = character.get(attr, 0)
                    if isinstance(required, str) and required.startswith("<"):
                        threshold = int(required[1:])
                        if char_value >= threshold:
                            is_unlockable = False
                    else:
                        threshold = int(required)
                        if char_value < threshold:
                            is_unlockable = False

                # 显示状态
                if is_owned:
                    status = "✅ 已拥有"
                elif is_unlockable or outfit["is_unlocked_by_default"]:
                    status = "🔓 可解锁"
                else:
                    status = "🔒 未解锁"

                lines.append(f"{status} {outfit['outfit_name']} - {outfit['description']}")

            await self.send_text("\n".join(lines))
            return True, "服装列表", True


class DTWearOutfitCommand(BaseCommand):
    """穿服装"""

    command_name = "dt_wear_outfit"
    command_description = "穿上指定服装"
    command_pattern = r"^/穿\s+(.+)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("❌ 格式错误！使用: /穿 <服装名称>")
            return False, "格式错误", False

        outfit_name = match.group(1).strip()
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 查找服装
        from ...core.models import DTOutfit
        outfit = await database_api.db_get(
            DTOutfit,
            filters={"outfit_name": outfit_name},
            single_result=True
        )

        if not outfit:
            await self.send_text(f"❌ 未找到服装: {outfit_name}\n使用 /服装列表 查看所有服装")
            return False, "服装不存在", False

        # 获取角色数据(用于心理反应)
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        # 尝试穿上 (增强版 - 带心理反应)
        success, psychological_msg, instant_effects = await OutfitSystem.equip_outfit(
            user_id, chat_id, outfit["outfit_id"], character
        )

        if success:
            # 显示基本消息
            await self.send_text(f"✅ 已穿上 {outfit['outfit_name']}！\n{outfit['description']}")

            # 显示心理反应消息
            if psychological_msg:
                await self.send_text(f"\n{psychological_msg}")

            # 应用即时心理效果
            if instant_effects and character:
                updated = AttributeSystem.apply_changes(character, instant_effects)
                await database_api.db_save(
                    DTCharacter,
                    data=updated,
                    key_field="user_id",
                    key_value=user_id
                )

                # 显示属性变化反馈
                await self._send_effects_feedback(instant_effects)

            return True, f"穿上{outfit_name}", True
        else:
            await self.send_text(f"❌ 你还没有解锁 {outfit_name}")
            return False, "未解锁", False

    async def _send_effects_feedback(self, effects: dict):
        """显示属性变化反馈"""
        feedback_parts = []
        attr_names = {
            "affection": "好感", "intimacy": "亲密", "trust": "信任",
            "submission": "顺从", "desire": "欲望", "corruption": "堕落",
            "arousal": "兴奋", "resistance": "抵抗", "shame": "羞耻"
        }
        emoji_map = {
            "affection": "❤️", "intimacy": "💗", "trust": "🤝",
            "submission": "🙇", "desire": "🔥", "corruption": "😈",
            "arousal": "💓", "resistance": "🛡️", "shame": "😳"
        }

        for attr, change in effects.items():
            if change != 0:
                emoji = emoji_map.get(attr, "📊")
                name = attr_names.get(attr, attr)
                sign = "+" if change > 0 else ""
                feedback_parts.append(f"{emoji}{name}{sign}{change}")

        if feedback_parts:
            await self.send_text(f"〔{' '.join(feedback_parts)}〕")


class DTInventoryCommand(BaseCommand):
    """查看背包"""

    command_name = "dt_inventory"
    command_description = "查看道具背包"
    command_pattern = r"^/(背包|inventory|bag)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取背包
        from ...core.models import DTUserInventory, DTItem
        inventory = await database_api.db_get(
            DTUserInventory,
            filters={"user_id": user_id, "chat_id": chat_id}
        )

        if not inventory:
            await self.send_text("🎒 【背包】\n\n背包是空的！")
            return True, "背包为空", True

        # 使用图片输出
        try:
            from ...utils.help_image_generator import HelpImageGenerator

            sections = []
            for inv_item in inventory:
                item = await database_api.db_get(
                    DTItem,
                    filters={"item_id": inv_item["item_id"]},
                    single_result=True
                )

                if item:
                    item_info = [
                        f"{item['item_name']} x{inv_item['quantity']}",
                        f"  {item['description']}",
                        f"  效果: {item['effect_description']}"
                    ]
                    sections.append((item['item_name'], item_info))

            if sections:
                img_bytes, img_base64 = HelpImageGenerator.generate_list_image(
                    "道具背包", sections, width=800
                )

                await self.send_image(img_base64)
                return True, "查看背包", True

        except Exception as e:
            # 降级到文本模式
            pass

        # 文本模式
        lines = ["🎒 【背包】\n"]

        for inv_item in inventory:
            item = await database_api.db_get(
                DTItem,
                filters={"item_id": inv_item["item_id"]},
                single_result=True
            )

            if item:
                lines.append(
                    f"• {item['item_name']} x{inv_item['quantity']}\n"
                    f"  {item['description']}\n"
                    f"  效果: {item['effect_description']}"
                )

        await self.send_text("\n".join(lines))
        return True, "查看背包", True


# DTUseItemCommand 已移至 item_commands.py，使用带LLM回复的版本


class DTSceneListCommand(BaseCommand):
    """查看场景列表"""

    command_name = "dt_scene_list"
    command_description = "查看所有场景"
    command_pattern = r"^/(场景列表|scenes?)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not character:
            await self.send_text("❌ 你还没有开始游戏！使用 /开始 来开始")
            return False, "角色不存在", False

        # 获取已解锁场景
        unlocked = await SceneSystem.get_unlocked_scenes(user_id, chat_id, character)

        # 使用图片输出
        try:
            from ...utils.help_image_generator import HelpImageGenerator

            sections = [(
                "可用场景",
                [f"• {scene['scene_name']} - {scene['description']}" for scene in unlocked]
            )]

            img_bytes, img_base64 = HelpImageGenerator.generate_list_image(
                "场景列表", sections, width=800
            )

            await self.send_image(img_base64)
            return True, "场景列表", True

        except Exception as e:
            # 降级到文本模式
            lines = ["🌆 【可用场景】\n"]
            for scene in unlocked:
                lines.append(f"• {scene['scene_name']} - {scene['description']}")

            await self.send_text("\n".join(lines))
            return True, "场景列表", True


class DTGoSceneCommand(BaseCommand):
    """前往场景"""

    command_name = "dt_go_scene"
    command_description = "前往指定场景"
    command_pattern = r"^/(去|go|goto)\s+(.+)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("❌ 格式错误！使用: /去 <场景名称>")
            return False, "格式错误", False

        scene_name = match.group(2).strip()
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 查找场景
        from ...core.models import DTScene
        scene = await database_api.db_get(
            DTScene,
            filters={"scene_name": scene_name},
            single_result=True
        )

        if not scene:
            await self.send_text(f"❌ 未找到场景: {scene_name}\n使用 /场景列表 查看所有场景")
            return False, "场景不存在", False

        # 访问场景
        result = await SceneSystem.visit_scene(user_id, chat_id, scene["scene_id"])

        if result:
            await self.send_text(
                f"📍 来到了 {result['scene_name']}\n\n"
                f"{result['description']}\n\n"
                f"💡 在这里可以使用: {', '.join(result['available_actions'][:5])}"
            )
            return True, f"前往{scene_name}", True
        else:
            await self.send_text(f"❌ 无法前往 {scene_name}")
            return False, "访问失败", False


class DTTruthCommand(BaseCommand):
    """真心话游戏"""

    command_name = "dt_truth"
    command_description = "玩真心话游戏"
    command_pattern = r"^/真心话$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not character:
            await self.send_text("❌ 你还没有开始游戏！使用 /开始 来开始")
            return False, "角色不存在", False

        # 玩真心话
        success, question, effects = await GameSystem.play_truth_or_dare(
            user_id, chat_id, character, "truth"
        )

        if success:
            # 应用效果
            updated = AttributeSystem.apply_changes(character, effects)
            await database_api.db_save(
                DTCharacter,
                data=updated,
                key_field="user_id",
                key_value=user_id
            )

            await self.send_text(f"💬 【真心话】\n\n{question}")
            return True, "真心话游戏", True
        else:
            return False, "游戏失败", False


class DTDareCommand(BaseCommand):
    """大冒险游戏"""

    command_name = "dt_dare"
    command_description = "玩大冒险游戏"
    command_pattern = r"^/大冒险$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not character:
            await self.send_text("❌ 你还没有开始游戏！使用 /开始 来开始")
            return False, "角色不存在", False

        # 玩大冒险
        success, task, effects = await GameSystem.play_truth_or_dare(
            user_id, chat_id, character, "dare"
        )

        if success:
            # 应用效果
            updated = AttributeSystem.apply_changes(character, effects)
            await database_api.db_save(
                DTCharacter,
                data=updated,
                key_field="user_id",
                key_value=user_id
            )

            await self.send_text(f"🎯 【大冒险】\n\n{task}")
            return True, "大冒险游戏", True
        else:
            return False, "游戏失败", False


class DTDiceCommand(BaseCommand):
    """掷骰子游戏"""

    command_name = "dt_dice"
    command_description = "掷骰子"
    command_pattern = r"^/(骰子|dice|roll)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not character:
            await self.send_text("❌ 你还没有开始游戏！使用 /开始 来开始")
            return False, "角色不存在", False

        # 掷骰子
        result, desc, effects = await GameSystem.roll_dice(user_id, chat_id)

        # 应用效果
        updated = AttributeSystem.apply_changes(character, effects)
        await database_api.db_save(
            DTCharacter,
            data=updated,
            key_field="user_id",
            key_value=user_id
        )

        await self.send_text(f"🎲 【掷骰子】\n\n点数: {result}\n{desc}")
        return True, f"掷骰子={result}", True
