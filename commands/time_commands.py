"""
时间推进命令 - /明日, /状态
"""

import re
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ..core.models import DTCharacter
from ..core.daily_limit_system import DailyInteractionSystem

logger = get_logger("dt_time_commands")


class DTNextDayCommand(BaseCommand):
    """推进到下一天"""

    command_name = "dt_next_day"
    command_description = "进入下一天,重置互动次数"
    command_pattern = r"^/(明日|明天|nextday)$"

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
            await self.send_text("❌ 你还没有开始游戏!使用 /开始 来开始")
            return False, "角色不存在", False

        # 检查是否已用完今日互动
        used = character.get("daily_interactions_used", 0)
        limit = DailyInteractionSystem.get_daily_limit(character)

        if used < limit:
            remaining = limit - used
            await self.send_text(
                f"⚠️ 今天还有 {remaining} 次互动机会\n"
                f"确定要跳过吗?\n\n"
                f"💡 建议用完互动次数后再进入下一天"
            )
            # 仍然允许推进,但给出提示

        # 记录当前天数
        old_day = character.get("game_day", 1)

        # 推进到下一天
        DailyInteractionSystem.advance_to_next_day(character)

        # 保存数据
        await database_api.db_save(
            DTCharacter,
            data=character,
            key_field="user_id",
            key_value=user_id
        )

        new_day = character.get("game_day", 1)

        # === 【新增】检查是否到达游戏结束（第42天） ===
        if new_day > 42:
            # 游戏已经结束，不允许继续推进
            await self.send_text(
                f"⏰ 【游戏已结束】\n\n"
                f"第42天已经过去，游戏已经结束了\n\n"
                f"💡 使用 /结局 查看最终结局\n"
                f"   或使用 /重开 开始新的故事"
            )
            return False, "游戏已结束", False

        # 检查是否触发周期总结
        if new_day % 7 == 1 and new_day > 1:
            # 触发周总结
            week_num = (new_day - 1) // 7
            summary_msg = await self._generate_week_summary(character, week_num)
            await self.send_text(summary_msg)

        # === 【修改】42天时自动触发结局 ===
        if new_day == 42:
            await self.send_text(
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"🎬 【最后一天】\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"这是你们在一起的第 {new_day} 天。\n\n"
                f"时光飞逝，42天的时间转瞬即逝...\n"
                f"你们的关系也将在今天定格。\n\n"
                f"💡 今天过完后，游戏将自动结束\n"
                f"   使用 /结局 查看你们的最终结局"
            )
        elif new_day >= 35:
            # 最后一周的时间压力提示
            remaining = 42 - new_day
            await self.send_text(
                f"⏰ 【倒计时 {remaining} 天】\n\n"
                f"距离第42天只剩 {remaining} 天了...\n"
                f"抓紧时间培养关系吧！"
            )
        elif new_day >= 30:
            await self.send_text(
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"⏰ 【时光飞逝】\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"不知不觉，已经过去了 {new_day} 天。\n\n"
                f"你们的关系...会走向何方呢？\n\n"
                f"💡 可以使用 /结局 提前查看当前结局\n"
                f"   游戏将在第42天自动结束"
            )

        # === 【v2.0新增】职业系统 - 发放每日收入和增加职业天数 ===
        from ..core.career_system import CareerSystem

        # 初始化职业(如果还没有)
        if "career" not in character or not character.get("career"):
            character = CareerSystem.initialize_career(character)

        # 发放每日收入
        daily_income = CareerSystem.daily_income(character)
        character["coins"] = character.get("coins", 100) + daily_income
        character["career_day"] = character.get("career_day", 0) + 1

        await self.send_text(f"💰 【每日收入】+{daily_income}币 (余额: {character['coins']})")

        # 检查是否可以晋升
        can_promote, next_career, promotion_text = CareerSystem.check_promotion(character)
        if can_promote:
            await self.send_text(f"\n✨ 可以晋升了！使用 /晋升 查看详情")

        # === 【v2.0新增】随机事件系统 - 检查并触发随机事件 ===
        from ..core.random_event_system import RandomEventSystem
        import json

        event_tuple = RandomEventSystem.check_and_trigger_event(character)

        if event_tuple:
            event_id, event_data = event_tuple

            # 存储活跃事件到角色数据
            character["active_event"] = json.dumps({"event_id": event_id}, ensure_ascii=False)

            # 【修复】立即保存,确保用户使用 /选择 时能读取到
            await database_api.db_save(
                DTCharacter,
                data=character,
                key_field="user_id",
                key_value=user_id
            )

            # 显示事件消息
            event_message = RandomEventSystem.format_event_message(event_data, character)
            await self.send_text(event_message)

            logger.info(f"触发随机事件: {event_id}")

        # === 【v2.0新增】季节系统 - 显示季节和节日信息 ===
        from ..core.seasonal_system import SeasonalSystem

        season_info = SeasonalSystem.get_season_info(new_day)
        weather = SeasonalSystem.get_weather(new_day)
        festival = SeasonalSystem.get_festival_by_day(new_day)

        season_msg = f"{season_info['emoji']} {season_info['name']}天 | {weather['emoji']} {weather['description']}"
        if festival:
            season_msg += f"\n🎉 今天是【{festival['name']}】！"

        # 保存更新后的角色数据
        await database_api.db_save(
            DTCharacter,
            data=character,
            key_field="user_id",
            key_value=user_id
        )

        # 发送推进消息
        await self.send_text(
            f"🌅 【新的一天】\n\n"
            f"第 {old_day} 天 → 第 {new_day} 天\n"
            f"{season_msg}\n\n"
            f"互动次数已重置: {limit} 次\n"
            f"当前阶段: {DailyInteractionSystem.get_stage_display(character)}\n\n"
            f"💭 新的一天,新的开始..."
        )

        return True, f"推进到第{new_day}天", True

    async def _generate_week_summary(self, character: dict, week_num: int) -> str:
        """生成周总结"""
        from ..core.action_growth_system import ActionGrowthSystem
        import json

        # 获取当前属性
        intimacy = character.get("intimacy", 0)
        affection = character.get("affection", 0)
        corruption = character.get("corruption", 0)
        trust = character.get("trust", 0)
        submission = character.get("submission", 0)

        # 获取关系阶段
        stage = DailyInteractionSystem.get_relationship_stage(character)
        stage_emoji = {
            "stranger": "🤝",
            "friend": "😊",
            "close": "💕",
            "lover": "❤️"
        }

        # 对比上周快照
        last_snapshot_str = character.get("last_week_snapshot", "{}")
        changes = {}
        if last_snapshot_str and last_snapshot_str != "{}":
            last_snapshot = json.loads(last_snapshot_str) if isinstance(last_snapshot_str, str) else last_snapshot_str
            changes["intimacy"] = intimacy - last_snapshot.get("intimacy", 0)
            changes["affection"] = affection - last_snapshot.get("affection", 0)
            changes["corruption"] = corruption - last_snapshot.get("corruption", 0)
            changes["trust"] = trust - last_snapshot.get("trust", 0)
            changes["submission"] = submission - last_snapshot.get("submission", 0)

        # 构建变化文本
        change_text = []
        attr_display = {
            "intimacy": "亲密度",
            "affection": "好感度",
            "corruption": "堕落度",
            "trust": "信任度",
            "submission": "顺从度"
        }

        for attr, change in changes.items():
            if change != 0:
                sign = "+" if change > 0 else ""
                emoji = "📈" if change > 0 else "📉"
                change_text.append(f"  {emoji} {attr_display[attr]}: {sign}{change}")

        # 获取可用动作数量
        available_actions = ActionGrowthSystem.get_all_available_actions(character)
        action_count = len(available_actions)

        # 关系发展评价
        if intimacy >= 80:
            progress_comment = "你们已经成为恋人，关系发展完美！"
        elif intimacy >= 50:
            progress_comment = "关系发展顺利，继续保持！"
        elif intimacy >= 20:
            progress_comment = "友谊正在逐渐加深..."
        else:
            progress_comment = "关系还需要时间慢慢培养。"

        # 下周建议
        next_week_advice = []
        if stage == "stranger":
            next_week_advice.append("💡 建议：专注于提升好感和信任")
            next_week_advice.append("   多使用温柔系动作（问候、聊天、牵手）")
        elif stage == "friend":
            next_week_advice.append("💡 建议：增加亲密互动")
            next_week_advice.append("   尝试拥抱和亲吻等动作")
        elif stage == "close":
            next_week_advice.append("💡 建议：尝试更进一步")
            next_week_advice.append("   可以开始挑逗和诱惑")
        elif stage == "lover":
            next_week_advice.append("💡 恭喜！已解锁所有内容")
            next_week_advice.append("   尽情探索吧！")

        summary = f"""━━━━━━━━━━━━━━━━━━━
📊 【第 {week_num} 周总结】
━━━━━━━━━━━━━━━━━━━

{stage_emoji.get(stage, '📊')} 关系阶段:
  {DailyInteractionSystem.get_stage_display(character)}

📈 本周成长:
{chr(10).join(change_text) if change_text else "  （暂无对比数据）"}

💫 当前状态:
  亲密度: {intimacy}/100
  好感度: {affection}/100
  堕落度: {corruption}/100
  可用动作: {action_count}个

💭 评价:
  {progress_comment}

{chr(10).join(next_week_advice)}

━━━━━━━━━━━━━━━━━━━
"""

        return summary


class DTStatusCommand(BaseCommand):
    """查看当前状态"""

    command_name = "dt_status"
    command_description = "查看游戏进度和当前状态"
    command_pattern = r"^/(状态|status|info)$"

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
            await self.send_text("❌ 你还没有开始游戏!使用 /开始 来开始")
            return False, "角色不存在", False

        # 获取状态信息
        status_msg = DailyInteractionSystem.get_day_summary(character)

        await self.send_text(status_msg)
        return True, "查看状态", True
