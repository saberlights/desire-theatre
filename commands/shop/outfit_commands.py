"""
服装命令
"""

import re
import json
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api

from ...core.models import DTCharacter, DTOutfit, DTUserOutfit
from ...features.outfits.outfit_system import OutfitSystem


class DTOutfitListCommand(BaseCommand):
    """查看服装列表命令"""

    command_name = "dt_outfit_list"
    command_description = "查看拥有的服装"
    command_pattern = r"^/(衣柜|outfits?)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色信息 (用于显示进度)
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            await self.send_text("❌ 还没有创建角色！")
            return False, "角色未创建", False

        # 获取拥有的服装
        owned = await database_api.db_get(
            DTUserOutfit,
            filters={"user_id": user_id, "chat_id": chat_id}
        )

        # 获取当前穿着
        current = await OutfitSystem.get_current_outfit(user_id, chat_id)
        current_id = current["outfit_id"] if current else None

        # 获取所有服装
        all_outfits = await database_api.db_get(DTOutfit, filters={})
        owned_ids = {o["outfit_id"] for o in owned} if owned else set()

        # 已拥有服装
        message = "👗 【服装列表】\n\n✅ 已拥有:\n"
        owned_count = 0

        for outfit in all_outfits:
            if outfit["outfit_id"] in owned_ids:
                owned_count += 1
                is_current = "✨" if outfit["outfit_id"] == current_id else "  "
                message += f"{is_current} {outfit['outfit_name']}\n"
                message += f"   {outfit['description']}\n"

                # 查找使用次数
                own_data = next((o for o in owned if o["outfit_id"] == outfit["outfit_id"]), None)
                times = own_data["times_worn"] if own_data else 0
                message += f"   穿着次数: {times}次\n\n"

        # 未解锁服装
        locked_outfits = [o for o in all_outfits if o["outfit_id"] not in owned_ids]

        if locked_outfits:
            message += f"\n🔒 未解锁 ({len(locked_outfits)}/{len(all_outfits)}):\n"

            for outfit in locked_outfits:
                message += f"\n  • {outfit['outfit_name']}\n"
                message += f"    {outfit['description']}\n"

                # 解析解锁条件
                unlock_cond = json.loads(outfit.get("unlock_condition", "{}"))

                if unlock_cond:
                    message += "    解锁条件:\n"
                    all_met = True

                    attr_names = {
                        "affection": "好感度",
                        "intimacy": "亲密度",
                        "trust": "信任度",
                        "corruption": "堕落度",
                        "submission": "顺从度",
                        "shame": "羞耻心"
                    }

                    for attr, required in unlock_cond.items():
                        attr_name = attr_names.get(attr, attr)
                        current_val = char.get(attr, 0)

                        if isinstance(required, str) and required.startswith("<"):
                            # 小于条件
                            threshold = int(required[1:])
                            if current_val >= threshold:
                                message += f"      ❌ {attr_name} 需要 <{threshold} (当前{current_val})\n"
                                all_met = False
                            else:
                                message += f"      ✅ {attr_name} <{threshold}\n"
                        else:
                            # 大于等于条件
                            threshold = int(required)
                            diff = threshold - current_val
                            if diff > 0:
                                message += f"      ❌ {attr_name} ≥{threshold} (当前{current_val}, 还差{diff})\n"
                                all_met = False
                            else:
                                message += f"      ✅ {attr_name} ≥{threshold}\n"

                    if all_met:
                        message += "    💡 条件已满足！可以通过商店购买解锁\n"
                else:
                    message += "    💡 默认可用，可通过商店购买\n"

        message += f"\n✨ 当前穿着: {current['outfit_name'] if current else '日常便装'}\n"
        message += "\n使用 /穿 <服装名> 来更换\n"
        message += "使用 /商店 购买服装"

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

        # 获取角色信息 (在装备前)
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            await self.send_text("❌ 还没有创建角色！")
            return False, "角色未创建", False

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

        # 装备服装 (传入角色信息以生成心理反应)
        success, psychological_message, instant_effects = await OutfitSystem.equip_outfit(
            user_id, chat_id, target_outfit["outfit_id"], character=char
        )

        if not success:
            await self.send_text(f"❌ 你还没有解锁这件服装")
            return False, "未解锁", False

        # 应用即时属性效果 (如果有)
        if instant_effects:
            for attr, change in instant_effects.items():
                if attr in char:
                    from ...systems.attributes.attribute_system import AttributeSystem
                    new_value = AttributeSystem.clamp(char[attr] + change)
                    char[attr] = new_value

            # 保存角色状态
            await database_api.db_save(
                DTCharacter,
                data=char,
                key_field="user_id",
                key_value=user_id
            )

        # === 使用 LLM 生成详细回复 ===
        from ...utils.prompt_builder import PromptBuilder
        from ...systems.personality.dynamic_mood_system import DynamicMoodSystem
        from src.llm_models.utils_model import get_model_by_task

        # 构建场景描述
        scenario_desc = f"你让她换上了{target_outfit['outfit_name']}。{target_outfit['description']}"

        # 如果有增强模块生成的心理反应描述，使用它
        if psychological_message:
            scenario_desc = psychological_message

        # 获取当前情绪
        current_mood = DynamicMoodSystem.calculate_current_mood(char)

        # 获取最近历史
        history = await PromptBuilder.get_recent_history(user_id, chat_id, limit=2)

        # 构建效果字典（服装主要提供被动加成，这里显示即时效果）
        effects = instant_effects if instant_effects else {}

        # 构建 Prompt
        prompt = PromptBuilder.build_response_prompt(
            character=char,
            action_type="outfit_change",
            scenario_desc=scenario_desc,
            intensity=target_outfit.get("arousal_bonus", 0) // 10,  # 使用 arousal_bonus 估算强度
            effects=effects,
            new_traits=[],
            triggered_scenarios=[],
            user_message=f"让她换上了{target_outfit['outfit_name']}",
            history=history,
            mood_info=current_mood
        )

        # 调用 LLM 生成回复
        model = get_model_by_task("replyer")
        ai_response = await model.get_response(prompt)

        # 构建完整消息
        modifiers_text = ""
        if "attribute_modifiers" in target_outfit and target_outfit["attribute_modifiers"]:
            modifiers = json.loads(target_outfit["attribute_modifiers"])
            if modifiers:
                modifiers_text = "\n📊 被动效果: " + ", ".join([f"{k}×{v}" for k, v in modifiers.items()])

        full_message = f"✨ 换上了 {target_outfit['outfit_name']}\n\n{ai_response}{modifiers_text}"

        await self.send_text(full_message)
        return True, f"穿上{outfit_name}", True
