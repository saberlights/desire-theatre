"""
聊天命令 - 自然语言对话
"""

import re
import json
import time
import random
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api, llm_api, send_api
from src.common.logger import get_logger

from ..core.models import DTCharacter, DTEvent
from ..core.prompt_builder import PromptBuilder
from ..core.attribute_system import AttributeSystem

logger = get_logger("dt_chat_command")


class DTChatCommand(BaseCommand):
    """自然语言聊天命令"""

    command_name = "dt_chat"
    command_description = "与角色进行自然语言对话"
    command_pattern = r"^/聊天\s+(.+)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("💬 使用方法: /聊天 <你想说的话>\n\n例如:\n  /聊天 你今天在干嘛\n  /聊天 最近心情怎么样")
            return False, "格式错误", False

        user_message = match.group(1).strip()
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not character:
            await self.send_text("❌ 还没有创建角色！\n使用 /开始 <人格> 来开始游戏")
            return False, "角色未创建", False

        # 应用属性衰减
        character = await self._apply_decay(character)

        # 获取历史记忆（最近3次互动）
        history = await PromptBuilder.get_recent_history(user_id, chat_id, 3)

        # 直接复用现有的 PromptBuilder，传入聊天场景的参数
        prompt = PromptBuilder.build_response_prompt(
            character=character,
            action_type="gentle",  # 聊天属于温柔类型
            scenario_desc=f"用户对你说：{user_message}",
            intensity=1,  # 聊天强度很低
            effects={"affection": 2, "trust": 1},  # 轻微的好感和信任提升
            new_traits=[],
            triggered_scenarios=[],
            user_message=user_message,
            history=history
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
            request_type="desire_theatre.chat"
        )

        if success_llm and ai_response:
            # 【优化】合并AI回复和属性变化为一条消息
            chat_effects = {
                "affection": 2,
                "trust": 1
            }

            # 合并输出
            output = f"{ai_response}\n\n〔❤️好感+2 🤝信任+1〕"

            await send_api.text_to_stream(
                text=output,
                stream_id=self.message.chat_stream.stream_id,
                storage_message=True
            )

            # 应用属性变化
            character = AttributeSystem.apply_changes(character, chat_effects)

            # 保存角色状态
            await self._save_character(user_id, chat_id, character)

            # 记录聊天事件
            await self._record_chat_event(user_id, chat_id, user_message, ai_response, chat_effects)

            return True, "聊天成功", True
        else:
            logger.error(f"LLM生成聊天回复失败: {ai_response}")
            await self.send_text("❌ 生成回复失败，请稍后重试")
            return False, "生成回复失败", False

    async def _apply_decay(self, character: dict) -> dict:
        """应用属性衰减"""
        last_decay = character.get("last_desire_decay", time.time())
        hours_passed = (time.time() - last_decay) / 3600

        if hours_passed >= 1:
            decay_changes = AttributeSystem.calculate_decay(character, hours_passed)
            character = AttributeSystem.apply_changes(character, decay_changes)
            character["last_desire_decay"] = time.time()

        return character

    async def _save_character(self, user_id: str, chat_id: str, character: dict):
        """保存角色状态"""
        character["last_interaction"] = time.time()
        character["interaction_count"] = character.get("interaction_count", 0) + 1

        await database_api.db_save(
            DTCharacter,
            data=character,
            key_field="user_id",
            key_value=user_id
        )

    async def _record_chat_event(self, user_id: str, chat_id: str, user_message: str, ai_response: str, effects: dict):
        """记录聊天事件"""
        event_id = f"evt_{int(time.time() * 1000000)}_{random.randint(1000, 9999)}"

        await database_api.db_save(
            DTEvent,
            data={
                "event_id": event_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "event_type": "interaction",
                "event_name": "聊天",
                "timestamp": time.time(),
                "event_data": json.dumps({
                    "user_message": user_message,
                    "ai_response": ai_response
                }, ensure_ascii=False),
                "attribute_changes": json.dumps(effects, ensure_ascii=False)
            },
            key_field="event_id",
            key_value=event_id
        )
