"""
道具命令
"""

import re
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api

from ...core.models import DTCharacter, DTItem, DTUserInventory
from ...systems.attributes.attribute_system import AttributeSystem
from ...features.items.item_system import ItemSystem


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
            await self.send_text("🎒 背包是空的！\n\n💡 道具获取方式:\n  • 互动后有15%概率掉落\n  • 使用 /商店 购买道具")
            return True, "空背包", True

        # 只显示数量 > 0 的道具
        has_items = False
        message_parts = ["🎒 【道具背包】\n"]

        for inv in inventory:
            # 跳过数量为0的道具
            if inv["quantity"] <= 0:
                continue

            item = await database_api.db_get(
                DTItem,
                filters={"item_id": inv["item_id"]},
                single_result=True
            )

            if item:
                has_items = True
                message_parts.append(f"\n📦 {item['item_name']} x{inv['quantity']}")
                message_parts.append(f"\n   {item['description']}")
                message_parts.append(f"\n   效果: {item['effect_description']}\n")

        if not has_items:
            await self.send_text("🎒 背包是空的！\n\n💡 道具获取方式:\n  • 互动后有15%概率掉落\n  • 使用 /商店 购买道具")
            return True, "背包为空", True

        message_parts.append("\n使用 /用 <道具名> 来使用道具")

        await self.send_text("".join(message_parts))
        return True, "显示背包", True


class DTUseItemCommand(BaseCommand):
    """使用道具命令"""

    command_name = "dt_use_item"
    command_description = "使用道具"
    command_pattern = r"^/用\s+(.+)$"

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

        # 获取角色信息 (在使用前)
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            await self.send_text("❌ 还没有创建角色！")
            return False, "角色未创建", False

        # 使用道具 (传入角色信息以生成心理效果)
        success, result = await ItemSystem.use_item(user_id, chat_id, target_item["item_id"], character=char)

        if not success:
            await self.send_text("❌ 你没有这个道具或数量不足")
            return False, "使用失败", False

        # 应用效果到角色
        for attr, change in result["effects"].items():
            if attr in char:
                new_value = AttributeSystem.clamp(char[attr] + change)
                char[attr] = new_value

        # 应用额外心理效果 (如果有)
        if "extra_effects" in result and result["extra_effects"]:
            for attr, change in result["extra_effects"].items():
                if attr in char:
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
        from src.plugin_system.apis import llm_api
        from src.common.logger import get_logger

        logger = get_logger("dt_use_item")

        # 构建场景描述
        scenario_desc = f"你对她使用了{target_item['item_name']}。{target_item['description']}"

        # 如果有增强模块生成的场景描述，使用它
        if "scene_description" in result and result["scene_description"]:
            scenario_desc = result["scene_description"]

        # 获取当前情绪
        current_mood = DynamicMoodSystem.calculate_current_mood(char)

        # 获取最近历史
        history = await PromptBuilder.get_recent_history(user_id, chat_id, limit=2)

        # 构建 Prompt
        prompt = PromptBuilder.build_response_prompt(
            character=char,
            action_type="item_use",
            scenario_desc=scenario_desc,
            intensity=target_item.get("intensity_level", 3),
            effects=result["effects"],
            new_traits=[],
            triggered_scenarios=[],
            user_message=f"给她使用了{target_item['item_name']}",
            history=history,
            mood_info=current_mood
        )

        # 调用 LLM 生成回复
        models = llm_api.get_available_models()
        replyer_model = models.get("replyer")

        if not replyer_model:
            logger.error("未找到 'replyer' 模型配置")
            await self.send_text("❌ 系统错误：未找到回复模型配置")
            return False, "未找到回复模型", False

        success_llm, ai_response, reasoning, model_name = await llm_api.generate_with_model(
            prompt=prompt,
            model_config=replyer_model,
            request_type="desire_theatre.use_item"
        )

        if not success_llm or not ai_response:
            logger.error(f"LLM生成回复失败: {ai_response}")
            await self.send_text("❌ 生成回复失败，请稍后重试")
            return False, "生成回复失败", False

        # 构建完整消息
        duration_text = ""
        if result["duration_minutes"] > 0:
            duration_text = f"\n⏱️ 持续时间: {result['duration_minutes']}分钟"

        full_message = f"✨ 使用了 {target_item['item_name']}\n\n{ai_response}{duration_text}"

        await self.send_text(full_message)
        return True, f"使用{item_name}", True
