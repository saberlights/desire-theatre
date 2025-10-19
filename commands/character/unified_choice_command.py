"""
统一选择命令 - 智能识别事件类型并处理
"""

import re
import json
import time
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ...core.models import DTCharacter
from ...systems.events.random_event_system import RandomEventSystem
from ...systems.personality.dual_personality_system import DualPersonalitySystem
from ...systems.events.choice_dilemma_system import ChoiceDilemmaSystem

logger = get_logger("dt_unified_choice")


class DTUnifiedChoiceCommand(BaseCommand):
    """统一选择命令 - 自动识别是事件选择还是人格选择"""

    command_name = "dt_unified_choice"
    command_description = "在事件或人格战争中做出选择"
    command_pattern = r"^/(选择|choice)\s+(\d+)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 解析选择编号
        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("❌ 格式错误!使用: /选择 <数字>")
            return False, "格式错误", False

        choice_num = int(match.group(2))

        # 获取角色
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not character:
            await self.send_text("❌ 你还没有开始游戏!使用 /开始 来开始")
            return False, "角色不存在", False

        # 智能检测当前有哪种类型的待处理事件
        # 优先级: 随机事件 > 选择困境 > 人格战争

        # 1. 检查是否有活跃的随机事件
        active_event_str = character.get("active_event")
        if active_event_str:
            # 处理随机事件选择
            return await self._handle_random_event_choice(character, choice_num, user_id, chat_id)

        # 2. 检查是否有选择困境
        pending_dilemma = character.get("pending_dilemma")
        if pending_dilemma:
            # 处理选择困境
            return await self._handle_dilemma_choice(character, choice_num, user_id, chat_id)

        # 3. 检查是否有人格战争事件
        mask_strength = DualPersonalitySystem.calculate_mask_strength(character)
        core_desire = DualPersonalitySystem.calculate_core_desire(character)

        if mask_strength >= 70 and core_desire >= 70 and 1 <= choice_num <= 3:
            # 处理人格战争选择
            return await self._handle_personality_choice(character, choice_num, user_id, chat_id)

        # 4. 没有任何待处理的选择
        await self.send_text(
            "❌ 当前没有待处理的选择事件\n\n"
            "💡 选择事件会在以下情况触发:\n"
            "  • 使用 /明日 时可能触发随机事件\n"
            "  • 面具强度和真实欲望都≥70时触发人格战争\n"
            "  • 特定条件下触发选择困境"
        )
        return False, "无待处理选择", False

    async def _handle_random_event_choice(
        self,
        character: dict,
        choice_num: int,
        user_id: str,
        chat_id: str
    ) -> Tuple[bool, str, bool]:
        """处理随机事件选择"""
        # 解析事件数据
        try:
            active_event_str = character.get("active_event")
            active_event_data = json.loads(active_event_str) if isinstance(active_event_str, str) else active_event_str
            event_id = active_event_data.get("event_id")

            # 【修复】检查是否有完整的事件数据
            event_data = active_event_data.get("event_data")

            if not event_data:
                # 如果没有完整数据，尝试从预定义事件中获取
                event_data = RandomEventSystem.get_event_by_id(event_id)

                if not event_data:
                    await self.send_text("❌ 事件数据丢失")
                    return False, "事件数据丢失", False

        except Exception as e:
            logger.error(f"解析事件数据失败: {e}")
            await self.send_text("❌ 事件数据错误")
            return False, "事件数据错误", False

        # 验证选择编号
        if choice_num < 1 or choice_num > len(event_data["choices"]):
            await self.send_text(f"❌ 无效的选择!请选择 1-{len(event_data['choices'])} 之间的数字")
            return False, "无效选择", False

        # 获取选择
        choice = event_data["choices"][choice_num - 1]

        # 检查是否满足选择条件
        if not RandomEventSystem.check_choice_requirements(character, choice):
            requirements = choice.get("requirements", {})
            req_text = ", ".join(f"{k}≥{v}" for k, v in requirements.items())
            await self.send_text(f"❌ 不满足选择条件: {req_text}")
            return False, "条件不满足", False

        # 应用选择效果
        character, changes = RandomEventSystem.apply_choice_effects(character, choice)

        # 清除活跃事件
        character["active_event"] = None

        # 保存数据
        await database_api.db_save(
            DTCharacter,
            data=character,
            key_field="user_id",
            key_value=user_id
        )

        # 构建结果消息
        result_msg = f"""━━━━━━━━━━━━━━━━━━━
✨ 【选择结果】
━━━━━━━━━━━━━━━━━━━

你选择了: {choice['text']}

{choice.get('result_text', '')}

"""

        # 显示属性变化
        if changes:
            change_lines = []
            attr_display = {
                "affection": "❤️ 好感度",
                "intimacy": "💗 亲密度",
                "trust": "🤝 信任度",
                "corruption": "😈 堕落度",
                "submission": "🙇 顺从度",
                "arousal": "🔥 兴奋度",
                "desire": "💋 欲望值",
                "resistance": "🛡️ 抵抗度",
                "shame": "😳 羞耻心",
                "mood_gauge": "😊 心情",
                "coins": "💰 金币",
                "daily_interactions_used": "📊 互动次数"
            }

            for attr, change in changes.items():
                if change != 0:
                    sign = "+" if change > 0 else ""
                    attr_name = attr_display.get(attr, attr)
                    change_lines.append(f"  {attr_name} {sign}{change}")

            if change_lines:
                result_msg += f"""📊 属性变化:
{chr(10).join(change_lines)}

"""

        result_msg += "━━━━━━━━━━━━━━━━━━━"

        await self.send_text(result_msg)
        logger.info(f"完成随机事件选择: {user_id} - {event_id} - 选项{choice_num}")
        return True, "完成事件选择", True

    async def _handle_personality_choice(
        self,
        character: dict,
        choice_num: int,
        user_id: str,
        chat_id: str
    ) -> Tuple[bool, str, bool]:
        """处理人格战争选择"""
        choice_index = choice_num - 1  # 转换为索引

        # 应用选择结果
        updated_char, result_text = DualPersonalitySystem.apply_personality_choice_result(
            character, choice_index
        )

        # 保存角色
        await database_api.db_save(
            DTCharacter,
            data=updated_char,
            key_field="user_id",
            key_value=user_id
        )

        # 显示结果
        await self.send_text(result_text)

        # 显示属性变化
        from ...systems.attributes.attribute_system import AttributeSystem

        # 计算属性变化（通过对比）
        changes = {}
        for attr in ['affection', 'trust', 'intimacy', 'corruption', 'submission', 'shame', 'resistance', 'arousal']:
            old_val = character.get(attr, 0)
            new_val = updated_char.get(attr, 0)
            if old_val != new_val:
                changes[attr] = new_val - old_val

        if changes:
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

            for attr, change in changes.items():
                emoji = emoji_map.get(attr, "📊")
                name = attr_names.get(attr, attr)
                sign = "+" if change > 0 else ""
                feedback_parts.append(f"{emoji}{name}{sign}{change}")

            await self.send_text(f"〔{' '.join(feedback_parts)}〕")

        logger.info(f"人格战争选择: {user_id} - 选项{choice_num}")
        return True, f"人格选择-{choice_num}", True

    async def _handle_dilemma_choice(
        self,
        character: dict,
        choice_num: int,
        user_id: str,
        chat_id: str
    ) -> Tuple[bool, str, bool]:
        """处理选择困境"""
        # 【修复】解析困境数据（支持新旧格式）
        pending_dilemma_str = character.get("pending_dilemma")

        try:
            # 尝试解析为JSON（新格式：完整困境数据）
            if isinstance(pending_dilemma_str, str) and pending_dilemma_str.startswith("{"):
                pending_data = json.loads(pending_dilemma_str)
                dilemma_id = pending_data.get("dilemma_id")
                dilemma_def = pending_data.get("dilemma_data")

                if not dilemma_def:
                    # 没有完整数据，尝试从预定义中获取
                    dilemma_def = ChoiceDilemmaSystem.get_dilemma_by_id(dilemma_id)
            else:
                # 旧格式：只有ID
                dilemma_id = pending_dilemma_str
                dilemma_def = ChoiceDilemmaSystem.get_dilemma_by_id(dilemma_id)
        except Exception as e:
            logger.error(f"解析困境数据失败: {e}")
            dilemma_id = pending_dilemma_str
            dilemma_def = ChoiceDilemmaSystem.get_dilemma_by_id(dilemma_id)

        # 检查困境是否超时（5分钟）
        dilemma_time = character.get("dilemma_triggered_at", 0)
        if time.time() - dilemma_time > 300:
            # 清除过期困境
            character["pending_dilemma"] = None
            await database_api.db_save(
                DTCharacter,
                data=character,
                key_field="user_id",
                key_value=user_id
            )
            await self.send_text("❌ 困境选择已超时（5分钟）\n\n系统已自动取消该困境")
            return False, "困境超时", False

        if not dilemma_def:
            await self.send_text(f"❌ 困境不存在: {dilemma_id}")
            return False, "困境不存在", False

        # 验证选择编号
        if choice_num < 1 or choice_num > len(dilemma_def["choices"]):
            await self.send_text(f"❌ 选项无效\n\n该困境只有 {len(dilemma_def['choices'])} 个选项")
            return False, "选项无效", False

        choice_data = dilemma_def["choices"][choice_num - 1]
        choice_id = choice_data.get("id", f"choice_{choice_num}")

        # 应用选择后果
        updated_char, consequence_text, long_term = ChoiceDilemmaSystem.apply_choice_consequences(
            character, dilemma_id, choice_id
        )

        # 清除困境标记
        updated_char["pending_dilemma"] = None
        updated_char["dilemma_triggered_at"] = None

        # 保存角色
        await database_api.db_save(
            DTCharacter,
            data=updated_char,
            key_field="user_id",
            key_value=user_id
        )

        # 构建结果消息
        result_msg = f"""━━━━━━━━━━━━━━━━━━━
✨ 【选择结果】
━━━━━━━━━━━━━━━━━━━

你选择了: {choice_data['text']}

{consequence_text}
"""

        if long_term:
            result_msg += f"\n⏰ 延迟后果:\n{long_term}\n"

        result_msg += "\n━━━━━━━━━━━━━━━━━━━"

        await self.send_text(result_msg)

        # 显示属性变化
        from ...systems.attributes.attribute_system import AttributeSystem
        changes = {}
        for attr in ['affection', 'trust', 'intimacy', 'corruption', 'submission', 'shame', 'resistance', 'arousal']:
            old_val = character.get(attr, 0)
            new_val = updated_char.get(attr, 0)
            if old_val != new_val:
                changes[attr] = new_val - old_val

        if changes:
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

            for attr, change in changes.items():
                emoji = emoji_map.get(attr, "📊")
                name = attr_names.get(attr, attr)
                sign = "+" if change > 0 else ""
                feedback_parts.append(f"{emoji}{name}{sign}{change}")

            await self.send_text(f"〔{' '.join(feedback_parts)}〕")

        logger.info(f"困境选择: {user_id} - {dilemma_id}:{choice_id}")
        return True, f"困境选择-{choice_num}", True
