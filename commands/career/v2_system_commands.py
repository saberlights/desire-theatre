"""
v2.0 新增系统命令 - 季节、职业、事件
"""

import re
import json
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ...core.models import DTCharacter
from ...systems.time.seasonal_system import SeasonalSystem
from ...systems.career.career_system import CareerSystem
from ...systems.events.random_event_system import RandomEventSystem

logger = get_logger("dt_v2_commands")


class DTSeasonCommand(BaseCommand):
    """查看当前季节和节日"""

    command_name = "dt_season"
    command_description = "查看当前季节、天气和即将到来的节日"
    command_pattern = r"^/(季节|season)$"

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

        game_day = character.get("game_day", 1)

        # 获取季节信息
        season_info = SeasonalSystem.get_season_info(game_day)

        # 获取当前天气
        weather = SeasonalSystem.get_weather(game_day)

        # 检查今天是否是节日
        festival = SeasonalSystem.get_festival_by_day(game_day)

        # 查找下一个节日
        next_festival = None
        for day in sorted(SeasonalSystem.FESTIVALS.keys()):
            if day > game_day:
                next_festival = SeasonalSystem.FESTIVALS[day]
                next_festival_day = day
                break

        # 构建消息
        message = f"""━━━━━━━━━━━━━━━━━━━
{season_info['emoji']} 【{season_info['name']}天】
━━━━━━━━━━━━━━━━━━━

📅 第 {game_day} 天 / 42天
{weather['emoji']} 天气: {weather['description']}

"""

        # 如果今天是节日
        if festival:
            message += f"""🎉 【今天是{festival['name']}！】

{festival['story']}

✨ 节日加成: 所有互动效果+20%
{festival['special_hint']}

"""

        # 显示下一个节日
        if next_festival:
            days_until = next_festival_day - game_day
            message += f"""🎯 下一个节日:
{next_festival['emoji']} {next_festival['name']} (第{next_festival_day}天)
⏰ 还有 {days_until} 天

"""

        # 显示季节加成
        bonus_text = []
        for attr, multiplier in season_info.get("bonus", {}).items():
            bonus_pct = int((multiplier - 1) * 100)
            attr_name = {
                "affection": "好感度",
                "intimacy": "亲密度",
                "trust": "信任度",
                "arousal": "兴奋度",
                "corruption": "堕落度"
            }.get(attr, attr)
            bonus_text.append(f"  • {attr_name} +{bonus_pct}%")

        if bonus_text:
            message += f"""💫 季节加成:
{chr(10).join(bonus_text)}

"""

        message += f"""━━━━━━━━━━━━━━━━━━━
💡 在节日当天互动获得额外加成！
"""

        await self.send_text(message)
        return True, "查看季节", True


class DTCareerCommand(BaseCommand):
    """查看职业信息"""

    command_name = "dt_career"
    command_description = "查看当前职业、收入和晋升条件"
    command_pattern = r"^/(职业|career|work)$"

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

        # 如果角色还没有职业,初始化职业
        if "career" not in character or not character.get("career"):
            character = CareerSystem.initialize_career(character)
            await database_api.db_save(
                DTCharacter,
                data=character,
                key_field="user_id",
                key_value=user_id
            )

        # 获取职业显示信息
        career_display = CareerSystem.get_career_display(character)

        await self.send_text(career_display)
        return True, "查看职业", True


class DTPromotionCommand(BaseCommand):
    """执行职业晋升"""

    command_name = "dt_promotion"
    command_description = "执行职业晋升(如果满足条件)"
    command_pattern = r"^/(晋升|promote|升职)$"

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

        # 检查是否可以晋升
        can_promote, next_career, promotion_text = CareerSystem.check_promotion(character)

        if not can_promote:
            # 获取当前职业信息
            career_id = character.get("career", "high_school_student")
            career_info = CareerSystem.get_career_info(career_id)

            if not career_info.get("next_stages"):
                await self.send_text(
                    f"✨ 你已经达到了职业的巅峰！\n\n"
                    f"{career_info['emoji']} {career_info['name']}\n"
                    f"这已经是最高职业了,无法继续晋升。"
                )
            else:
                await self.send_text(
                    f"❌ 暂时无法晋升\n\n"
                    f"还不满足晋升条件。\n"
                    f"使用 /职业 查看详细的晋升要求。"
                )
            return False, "无法晋升", False

        # 执行晋升
        character = CareerSystem.promote(character, next_career)

        # 保存数据
        await database_api.db_save(
            DTCharacter,
            data=character,
            key_field="user_id",
            key_value=user_id
        )

        await self.send_text(promotion_text)
        return True, f"晋升到{next_career}", True


class DTEventChoiceCommand(BaseCommand):
    """在随机事件中做出选择"""

    command_name = "dt_event_choice"
    command_description = "在随机事件中选择一个选项"
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

        # 获取当前活跃事件
        active_event_str = character.get("active_event")
        if not active_event_str:
            await self.send_text("❌ 当前没有正在进行的事件")
            return False, "没有活跃事件", False

        # 解析事件数据
        try:
            active_event_data = json.loads(active_event_str) if isinstance(active_event_str, str) else active_event_data
            event_id = active_event_data.get("event_id")
        except:
            await self.send_text("❌ 事件数据错误")
            return False, "事件数据错误", False

        # 获取事件定义
        event_data = RandomEventSystem.get_event_by_id(event_id)
        if not event_data:
            await self.send_text("❌ 事件不存在")
            return False, "事件不存在", False

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
        return True, "完成事件选择", True
