"""
动作命令
"""

import re
import json
from typing import Tuple

from src.plugin_system import BaseCommand
from src.common.logger import get_logger

from ..core.action_handler import ActionHandler
from ..core.personality_system import PersonalitySystem
from ..core.action_growth_system import ActionGrowthSystem

logger = get_logger("dt_action_commands")


# 在模块级别构建动作pattern，确保在类定义前就生成好
def _build_action_pattern() -> str:
    """根据ActionGrowthSystem构建匹配所有动作命令的正则表达式"""
    all_commands = []

    # 从所有核心动作中提取命令
    for action_key, action_def in ActionGrowthSystem.CORE_ACTIONS.items():
        commands = action_def.get("command", [])
        all_commands.extend(commands)

    # 按长度降序排序，确保长命令优先匹配
    all_commands.sort(key=len, reverse=True)
    # 转义特殊字符并用|连接
    escaped_commands = [re.escape(cmd) for cmd in all_commands]
    commands_pattern = "|".join(escaped_commands)
    return rf"^/({commands_pattern})(?:\s+(.+))?$"


# 生成pattern字符串
_ACTION_PATTERN = _build_action_pattern()


class DTActionCommand(BaseCommand):
    """统一的动作命令处理器"""

    command_name = "dt_action"
    command_description = "执行互动动作"

    # 使用模块级别生成的pattern
    command_pattern = _ACTION_PATTERN

    async def execute(self) -> Tuple[bool, str, bool]:
        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            return False, "命令格式错误", False

        command_used = match.group(1)  # 用户输入的命令（如"早安"、"抱"等）
        action_params = match.group(2).strip() if match.group(2) else ""

        # 根据命令找到对应的动作key
        action_key = ActionGrowthSystem.find_action_by_command(command_used)
        if not action_key:
            await self.send_text(f"❌ 未找到命令: {command_used}")
            return False, "未知命令", False

        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 执行动作（使用action_key而不是命令名）
        success, result_msg, intercept = await ActionHandler.execute_action(
            action_name=action_key,
            action_params=action_params,
            user_id=user_id,
            chat_id=chat_id,
            message_obj=self.message
        )

        return success, result_msg, intercept


class DTStartGameCommand(BaseCommand):
    """开始游戏命令"""

    command_name = "dt_start_game"
    command_description = "开始欲望剧场游戏"
    command_pattern = r"^/(开始|start)(?:\s+(傲娇|天真|妖媚|害羞|高冷|tsundere|innocent|seductive|shy|cold))?$"

    async def execute(self) -> Tuple[bool, str, bool]:
        from src.plugin_system.apis import database_api
        from ..core.models import DTCharacter

        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            # 显示可用人格
            personalities = "\n".join([
                f"  • {val['name']} ({key}): {val['description']}"
                for key, val in PersonalitySystem.PERSONALITIES.items()
            ])
            await self.send_text(f"🎭 【选择人格开始游戏】\n\n{personalities}\n\n使用方法: /开始 <人格类型>")
            return False, "格式错误", False

        personality_input = match.group(2)
        personality_type = "tsundere"  # 默认

        if personality_input:
            # 支持中英文
            type_map = {
                "傲娇": "tsundere", "tsundere": "tsundere",
                "天真": "innocent", "innocent": "innocent",
                "妖媚": "seductive", "seductive": "seductive",
                "害羞": "shy", "shy": "shy",
                "高冷": "cold", "cold": "cold"
            }
            personality_type = type_map.get(personality_input, "tsundere")

        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 检查是否已有角色
        existing = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if existing:
            await self.send_text("❌ 你已经有角色了！\n使用 /重开 来重置游戏。")
            return False, "角色已存在", False

        # 创建新角色
        personality = PersonalitySystem.get_personality(personality_type)
        import time

        char = {
            "user_id": user_id,
            "chat_id": chat_id,
            "affection": 0,
            "intimacy": 0,
            "trust": 50,
            "submission": 50,
            "desire": 0,
            "corruption": 0,
            "arousal": 0,
            "resistance": personality["base_resistance"],
            "shame": personality["base_shame"],
            "personality_type": personality_type,
            "personality_traits": "[]",
            "evolution_stage": 1,
            "interaction_count": 0,
            "total_arousal_gained": 0,
            "challenges_completed": 0,
            "created_at": time.time(),
            "last_interaction": time.time(),
            "last_desire_decay": time.time(),
            # 虚拟时间系统
            "game_day": 1,
            "daily_interactions_used": 0,
            "last_daily_reset": time.time(),
            "last_interaction_time": time.time(),
        }

        await database_api.db_save(
            DTCharacter,
            data=char,
            key_field="user_id",
            key_value=user_id
        )

        # === v2.0新增：初始化职业系统 ===
        from ..core.career_system import CareerSystem
        char = CareerSystem.initialize_career(char)

        # 保存更新后的角色（包含职业信息）
        await database_api.db_save(
            DTCharacter,
            data=char,
            key_field="user_id",
            key_value=user_id
        )

        # === 构建增强的欢迎消息 ===
        welcome_msg = f"""
━━━━━━━━━━━━━━━━━━━
🎭 【欲望剧场 v2.0】
━━━━━━━━━━━━━━━━━━━

欢迎来到欲望剧场！

你选择的人格: {personality['name']}
{personality['description']}

━━━ 🎮 游戏核心 ━━━
📊 九维属性系统
  • 显性: 好感/亲密/信任
  • 隐性: 顺从/堕落/欲望
  • 状态: 兴奋/抵抗/羞耻

⭐ 五个进化阶段
  初识 → 熟悉 → 亲密 → 沦陷 → 完全堕落

━━━ ✨ v2.0新内容 ━━━
⏰ 42天时间周期
  • 每日互动次数限制
  • 第42天游戏自动结束
  • 合理规划时间很重要

🌸 四季系统
  • 春夏秋冬不同属性加成
  • 8个固定节日额外+20%效果

💼 职业养成
  • 12种职业成长路线
  • 每日自动获得收入
  • 影响最终结局类型

🎲 随机事件
  • 13种事件随机触发
  • 每个事件多个选择分支

🎬 32个结局
  • 完美/好/普通/坏 四个等级
  • 职业和季节相关特殊结局

━━━ 💡 快速上手 ━━━
第一步 - 查看状态:
  /快看 - 快速查看核心属性
  /看 - 查看完整状态和进度

第二步 - 开始互动:
  /早安 - 温柔问候(好感+5)
  /牵手 - 身体接触(亲密+3)
  /摸头 - 温柔抚摸(好感+4)

第三步 - 了解系统:
  /帮助 - 查看所有命令
  /帮助 v2 - v2.0新功能详解
  /说明 - 完整游戏指南

辅助功能:
  /推荐 - AI推荐下一步
  /快速互动 - 随机执行动作

━━━ 🌅 第1天 ━━━
今天是春天，万物复苏的季节...
你面前站着一位{personality['name']}的少女。

你们的故事，从这里开始。

💡 提示: 使用 /明日 推进到下一天
"""
        await self.send_text(welcome_msg.strip())

        # === 发送职业初始化提示 ===
        career_name = char.get("career", "高中生")
        await self.send_text(f"💼 【职业】你的当前职业是: {career_name}\n每日自动获得收入，使用 /职业 查看详情")

        return True, f"游戏开始 - {personality_type}", True


class DTRestartCommand(BaseCommand):
    """重开游戏命令"""

    command_name = "dt_restart"
    command_description = "重置游戏并重新开始"
    command_pattern = r"^/(重开|restart|reset|确认重开)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        from src.plugin_system.apis import database_api
        from ..core.models import DTCharacter, DTEvent
        from ..core.confirmation_manager import ConfirmationManager

        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id
        command_text = self.message.processed_plain_text

        # 检查是否有角色
        existing = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not existing:
            await self.send_text("❌ 你还没有开始游戏！\n使用 /开始 <人格> 来开始")
            return False, "角色不存在", False

        # 检查是否是确认命令
        if "确认" in command_text:
            # 验证确认状态
            is_confirmed, _ = ConfirmationManager.check_confirmation(user_id, chat_id, "restart")

            if not is_confirmed:
                await self.send_text("❌ 没有待确认的重开操作，或确认已超时\n\n重新输入 /重开 开始重置流程")
                return False, "无待确认操作", False

            # 执行重置
            # 删除角色数据
            await database_api.db_query(
                DTCharacter,
                query_type="delete",
                filters={"user_id": user_id, "chat_id": chat_id}
            )

            # 删除事件记录
            await database_api.db_query(
                DTEvent,
                query_type="delete",
                filters={"user_id": user_id, "chat_id": chat_id}
            )

            # 清理其他相关数据
            from ..core.models import (DTMemory, DTPreference, DTUserOutfit,
                                      DTCurrentOutfit, DTUserInventory, DTUserAchievement)

            for model in [DTMemory, DTPreference, DTUserOutfit, DTCurrentOutfit,
                         DTUserInventory, DTUserAchievement]:
                await database_api.db_query(
                    model,
                    query_type="delete",
                    filters={"user_id": user_id, "chat_id": chat_id}
                )

            await self.send_text("""
✅ 游戏已完全重置！

所有数据已清空（包括记忆、偏好、服装、道具、成就），你可以重新开始。
使用 /开始 <人格> 来选择新的人格开始游戏

可用人格：傲娇、天真、妖媚、害羞、高冷
""".strip())

            return True, "游戏重置", True
        else:
            # 首次请求，创建确认状态
            ConfirmationManager.create_confirmation(user_id, chat_id, "restart")

            # 显示当前进度信息
            stage_name = ["初识", "熟悉", "亲密", "沦陷", "完全堕落"][min(existing.get("evolution_stage", 1) - 1, 4)]

            await self.send_text(f"""
⚠️ 【重置确认】

你当前的进度:
  🎭 人格: {existing.get('personality_type', '未知')}
  ⭐ 阶段: {stage_name}
  💕 好感度: {existing.get('affection', 0)}/100
  📈 互动次数: {existing.get('interaction_count', 0)}

⚠️ 重置将删除所有数据，包括：
  • 角色属性和进化进度
  • 所有记忆和偏好
  • 已解锁的服装、道具、成就
  • 所有互动记录

此操作不可撤销！

确定要重置吗？
  • 输入 /确认重开 继续
  • 60秒内不确认将自动取消
""".strip())

            return True, "等待确认", False


class DTQuickInteractCommand(BaseCommand):
    """快速互动命令 - 随机选择一个可用动作"""

    command_name = "dt_quick_interact"
    command_description = "随机选择一个可用动作进行互动"
    command_pattern = r"^/(快速互动|quick)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        from src.plugin_system.apis import database_api
        from ..core.models import DTCharacter
        import random

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

        # 使用新系统获取所有可用动作
        available_actions = ActionGrowthSystem.get_all_available_actions(char)

        # 过滤掉需要参数的动作
        simple_actions = []
        for action_info in available_actions:
            action_key = action_info["key"]
            action_def = ActionGrowthSystem.CORE_ACTIONS[action_key]
            # 只保留不需要部位选择的动作
            if not action_def.get("has_targets", False):
                simple_actions.append(action_key)

        if not simple_actions:
            await self.send_text("❌ 没有可用的简单动作\n\n可能需要提升关系才能解锁更多动作")
            return False, "无可用动作", False

        # 随机选择一个动作
        chosen_action = random.choice(simple_actions)
        # 获取该动作的第一个命令作为显示
        commands = ActionGrowthSystem.get_commands_for_action(chosen_action)
        display_cmd = commands[0] if commands else chosen_action

        await self.send_text(f"🎲 随机选择动作: /{display_cmd}\n\n执行中...")

        # 执行该动作
        success, result_msg, intercept = await ActionHandler.execute_action(
            action_name=chosen_action,
            action_params="",
            user_id=user_id,
            chat_id=chat_id,
            message_obj=self.message
        )

        return success, result_msg, intercept


class DTRecommendCommand(BaseCommand):
    """推荐命令 - AI推荐下一步应该做什么"""

    command_name = "dt_recommend"
    command_description = "获取AI推荐的下一步行动"
    command_pattern = r"^/(推荐|recommend)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        from src.plugin_system.apis import database_api
        from ..core.models import DTCharacter
        from ..core.daily_limit_system import DailyInteractionSystem

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

        # 分析当前状态
        stage = DailyInteractionSystem.get_relationship_stage(char)
        affection = char.get("affection", 0)
        intimacy = char.get("intimacy", 0)
        corruption = char.get("corruption", 0)
        trust = char.get("trust", 0)

        recommendations = []

        # 根据关系阶段推荐
        if stage == "stranger":
            recommendations.append("🤝 【陌生人阶段】")
            recommendations.append("  重点：建立基础好感和信任")
            recommendations.append("  • /早安 /晚安 - 提升好感")
            recommendations.append("  • /聊天 - 提升信任")
            if intimacy >= 10:
                recommendations.append("  • /牵手 - 尝试身体接触")
            recommendations.append("\n📊 目标：亲密度达到20进入朋友阶段")

        elif stage == "friend":
            recommendations.append("😊 【朋友阶段】")
            recommendations.append("  重点：深化关系，增加亲密互动")
            recommendations.append("  • /牵手 - 增进亲密")
            recommendations.append("  • /拥抱 - 友好的拥抱")
            if intimacy >= 30:
                recommendations.append("  • /亲 额头 - 温柔的亲吻")
                recommendations.append("  • /抚摸 头/脸 - 温柔抚摸")
            recommendations.append("\n📊 目标：亲密度达到50进入亲密阶段")

        elif stage == "close":
            recommendations.append("💕 【亲密阶段】")
            recommendations.append("  重点：尝试更进一步的互动")
            recommendations.append("  • /亲 嘴唇 - 深情的亲吻")
            recommendations.append("  • /抚摸 腰 - 大胆的抚摸")
            if corruption < 30:
                recommendations.append("  • /诱惑 - 提升堕落度")
                recommendations.append("  • /挑逗 - 增加欲望")
            recommendations.append("\n📊 目标：亲密度达到80进入恋人阶段")

        elif stage == "lover":
            recommendations.append("❤️ 【恋人阶段】")
            recommendations.append("  恭喜！已达最高关系阶段")
            recommendations.append("  • 所有动作全部解锁")
            recommendations.append("  • 尽情探索各种互动")
            if corruption < 50:
                recommendations.append("  • 可以尝试更深入的内容")

        # 获取当前可用动作
        available_actions = ActionGrowthSystem.get_all_available_actions(char)
        action_count = len(available_actions)

        recommendations.append(f"\n💡 【当前状态】")
        recommendations.append(f"  关系阶段: {DailyInteractionSystem.get_stage_display(char)}")
        recommendations.append(f"  可用动作: {action_count}个")
        recommendations.append(f"\n使用 /看 查看详细状态")
        recommendations.append(f"使用 /快速互动 随机执行动作")

        recommend_text = "\n".join(recommendations)
        await self.send_text(f"🤖 【AI推荐】\n\n{recommend_text}")

        return True, "显示推荐", True
