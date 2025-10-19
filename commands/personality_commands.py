"""
双重人格相关命令 + 选择困境命令
"""

import re
import time
from typing import Tuple

from src.plugin_system import BaseCommand
from src.common.logger import get_logger
from src.plugin_system.apis import database_api

from ..core.models import DTCharacter
from ..core.dual_personality_system import DualPersonalitySystem
from ..core.choice_dilemma_system import ChoiceDilemmaSystem

logger = get_logger("dt_personality_commands")


class DTPersonalityStatusCommand(BaseCommand):
    """查看人格状态命令"""

    command_name = "dt_personality_status"
    command_description = "查看双重人格状态"
    command_pattern = r"^/(人格|personality)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            await self.send_text("❌ 还没有创建角色！\n使用 /开始 <人格> 来开始游戏")
            return False, "角色未创建", False

        # 获取人格状态
        status = DualPersonalitySystem.get_personality_status(char)

        # 构建状态显示
        status_msg = f"""
🎭 【双重人格状态】

━━━━━━━━━━━━━━━━━━━
😇 【表层人格 - Mask】
   状态: {status['mask_emoji']} {status['mask_status']}
   强度: {status['mask_strength']}/100

🔥 【真实人格 - Core】
   状态: {status['core_emoji']} {status['core_status']}
   强度: {status['core_desire']}/100

{status['conflict_emoji']} 【人格冲突】
   等级: {status['conflict_status']}
   冲突值: {status['conflict']}/100

━━━━━━━━━━━━━━━━━━━

💡 说明:
• 面具强度 = 她对外伪装的能力
• 真实欲望 = 她内心真正的渴求
• 冲突值 = 两者之间的撕裂程度

"""

        if status['warning']:
            status_msg += f"\n{status['warning']}"

        status_msg = status_msg.strip()

        await self.send_text(status_msg)
        return True, "显示人格状态", True


class DTPersonalityChoiceCommand(BaseCommand):
    """处理人格战争选择"""

    command_name = "dt_personality_choice"
    command_description = "在人格战争中做出选择"
    command_pattern = r"^/(选择|choice)\s+([123])$"

    async def execute(self) -> Tuple[bool, str, bool]:
        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("❌ 格式错误\n\n使用方法: /选择 <1/2/3>")
            return False, "格式错误", False

        choice_num = int(match.group(2))
        choice_index = choice_num - 1  # 转换为索引

        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            await self.send_text("❌ 还没有创建角色！")
            return False, "角色未创建", False

        # 检查是否有待处理的人格战争
        # （简化处理：只要人格冲突>70就允许选择）
        mask_strength = DualPersonalitySystem.calculate_mask_strength(char)
        core_desire = DualPersonalitySystem.calculate_core_desire(char)

        if mask_strength < 70 or core_desire < 70:
            await self.send_text("❌ 当前没有人格战争事件\n\n💡 当面具强度和真实欲望都>70时会触发")
            return False, "未触发事件", False

        # 应用选择结果
        updated_char, result_text = DualPersonalitySystem.apply_personality_choice_result(
            char, choice_index
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
        from ..core.attribute_system import AttributeSystem

        # 计算属性变化（通过对比）
        changes = {}
        for attr in ['affection', 'trust', 'intimacy', 'corruption', 'submission', 'shame', 'resistance', 'arousal']:
            old_val = char.get(attr, 0)
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


class DTDilemmaChoiceCommand(BaseCommand):
    """处理选择困境命令"""

    command_name = "dt_dilemma_choice"
    command_description = "在选择困境中做出抉择"
    command_pattern = r"^/(抉择|dilemma)\s+(\w+)\s+([12])$"

    async def execute(self) -> Tuple[bool, str, bool]:
        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("❌ 格式错误\n\n使用方法: /抉择 <困境ID> <1/2>\n\n困境ID会在事件触发时显示")
            return False, "格式错误", False

        dilemma_id = match.group(2)
        choice_num = int(match.group(3))

        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            await self.send_text("❌ 还没有创建角色！")
            return False, "角色未创建", False

        # 检查是否有待处理的困境
        pending_dilemma = char.get("pending_dilemma")
        if not pending_dilemma:
            await self.send_text("❌ 当前没有待处理的选择困境\n\n💡 困境会在特定条件下自动触发")
            return False, "无待处理困境", False

        # 验证困境ID
        if pending_dilemma != dilemma_id:
            await self.send_text(f"❌ 困境ID不匹配\n\n当前困境: {pending_dilemma}\n你输入的: {dilemma_id}")
            return False, "困境ID不匹配", False

        # 检查困境是否超时（5分钟）
        dilemma_time = char.get("dilemma_triggered_at", 0)
        if time.time() - dilemma_time > 300:
            # 清除过期困境
            char["pending_dilemma"] = None
            await database_api.db_save(
                DTCharacter,
                data=char,
                key_field="user_id",
                key_value=user_id
            )
            await self.send_text("❌ 困境选择已超时（5分钟）\n\n系统已自动取消该困境")
            return False, "困境超时", False

        # 获取选择ID
        dilemma_def = ChoiceDilemmaSystem.DILEMMA_EVENTS.get(dilemma_id)
        if not dilemma_def:
            await self.send_text(f"❌ 未知的困境类型: {dilemma_id}")
            return False, "未知困境", False

        if choice_num < 1 or choice_num > len(dilemma_def["choices"]):
            await self.send_text(f"❌ 选项无效\n\n该困境只有 {len(dilemma_def['choices'])} 个选项")
            return False, "选项无效", False

        choice_data = dilemma_def["choices"][choice_num - 1]
        choice_id = choice_data["id"]

        # 应用选择后果
        updated_char, consequence_text, long_term = ChoiceDilemmaSystem.apply_choice_consequences(
            char, dilemma_id, choice_id
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

        # 显示结果
        result_msg = f"""⚖️ 【你做出了选择】

你选择了: {choice_data['text']}

━━━━━━━━━━━━━━━━━━━

{consequence_text}

━━━━━━━━━━━━━━━━━━━
💭 【长期影响】
{long_term}
"""

        await self.send_text(result_msg.strip())

        # 显示属性变化
        changes = {}
        for attr in ['affection', 'trust', 'intimacy', 'corruption', 'submission', 'shame', 'resistance', 'arousal', 'desire', 'coins']:
            old_val = char.get(attr, 0)
            new_val = updated_char.get(attr, 0)
            if old_val != new_val:
                changes[attr] = new_val - old_val

        if changes:
            feedback_parts = []
            attr_names = {
                "affection": "好感", "intimacy": "亲密", "trust": "信任",
                "submission": "顺从", "desire": "欲望", "corruption": "堕落",
                "arousal": "兴奋", "resistance": "抵抗", "shame": "羞耻",
                "coins": "爱心币"
            }
            emoji_map = {
                "affection": "❤️", "intimacy": "💗", "trust": "🤝",
                "submission": "🙇", "desire": "🔥", "corruption": "😈",
                "arousal": "💓", "resistance": "🛡️", "shame": "😳",
                "coins": "💰"
            }

            for attr, change in changes.items():
                emoji = emoji_map.get(attr, "📊")
                name = attr_names.get(attr, attr)
                sign = "+" if change > 0 else ""
                feedback_parts.append(f"{emoji}{name}{sign}{change}")

            await self.send_text(f"〔{' '.join(feedback_parts)}〕")

        logger.info(f"困境选择: {user_id} - {dilemma_id}:{choice_id}")
        return True, f"困境选择-{dilemma_id}", True
