"""
每日互动限制系统 - 借鉴《火山的女儿》的时间推进机制

核心理念:
- 关系需要时间培养,不能一天刷完
- 每次互动都有价值,玩家需要思考
- 制造稀缺性和期待感

⏰ 时间机制说明:
- **固定42天游戏周期**（借鉴火山的女儿）
- 每次互动消耗互动次数
- 用完后可通过 /明日 命令进入下一天
- 或自动推进(闲置一段时间后自动进入明日)
- **第42天结束时强制触发结局**
"""

import time
from typing import Dict, Tuple, Optional

from src.common.logger import get_logger

logger = get_logger("dt_daily_limit")


class DailyInteractionSystem:
    """每日互动限制系统 - 虚拟时间版本"""

    # 游戏总天数（借鉴火山的女儿）
    TOTAL_GAME_DAYS = 42

    # 根据关系阶段的每日互动次数
    DAILY_LIMITS = {
        "stranger": 2,      # 陌生人阶段 (intimacy < 20)
        "friend": 3,        # 朋友阶段 (intimacy 20-50)
        "close": 4,         # 亲密阶段 (intimacy 50-80)
        "lover": 5,         # 恋人阶段 (intimacy >= 80)
    }

    # 自动推进时间(秒) - 闲置此时间后自动进入下一天
    AUTO_ADVANCE_THRESHOLD = 3600  # 1小时

    @staticmethod
    def get_relationship_stage(character: Dict) -> str:
        """根据亲密度判断关系阶段"""
        intimacy = character.get("intimacy", 0)

        if intimacy < 20:
            return "stranger"
        elif intimacy < 50:
            return "friend"
        elif intimacy < 80:
            return "close"
        else:
            return "lover"

    @staticmethod
    def get_daily_limit(character: Dict) -> int:
        """获取当前的每日互动次数上限"""
        stage = DailyInteractionSystem.get_relationship_stage(character)
        return DailyInteractionSystem.DAILY_LIMITS[stage]

    @staticmethod
    def check_auto_advance(character: Dict) -> bool:
        """
        检查是否应该自动推进到明天

        条件:
        1. 今日互动次数已用完
        2. 距离最后一次互动超过阈值时间
        """
        # 获取今日已用次数和上限
        used = character.get("daily_interactions_used", 0)
        limit = DailyInteractionSystem.get_daily_limit(character)

        # 如果还有剩余次数,不自动推进
        if used < limit:
            return False

        # 获取最后一次互动时间
        last_interaction = character.get("last_interaction_time", 0)
        now = time.time()

        # 如果超过阈值,自动推进
        if (now - last_interaction) > DailyInteractionSystem.AUTO_ADVANCE_THRESHOLD:
            return True

        return False

    @staticmethod
    def check_can_interact(character: Dict) -> Tuple[bool, Optional[str], int, int]:
        """
        检查是否还能互动

        返回: (能否互动, 拒绝原因, 剩余次数, 总次数)
        """
        # 检查是否应该自动推进
        if DailyInteractionSystem.check_auto_advance(character):
            # 自动推进到明天
            DailyInteractionSystem.advance_to_next_day(character)
            logger.info(f"自动推进到第 {character.get('game_day', 1)} 天")

        # 获取今日已用次数和上限
        used = character.get("daily_interactions_used", 0)
        limit = DailyInteractionSystem.get_daily_limit(character)

        remaining = limit - used

        if remaining <= 0:
            game_day = character.get("game_day", 1)

            reason = f"""❌ 【她累了】

她今天已经陪你很久了...
让她休息一下吧

📊 今日互动: {used}/{limit}
📅 当前: 第 {game_day} 天

💡 提示:
  使用 /明日 进入下一天
  随着关系加深,每日互动次数会增加
  当前阶段: {DailyInteractionSystem.get_stage_display(character)}
"""
            return False, reason, 0, limit

        return True, None, remaining, limit

    @staticmethod
    def consume_interaction(character: Dict):
        """消耗一次互动次数"""
        character["daily_interactions_used"] = character.get("daily_interactions_used", 0) + 1
        character["last_interaction_time"] = time.time()

    @staticmethod
    def advance_to_next_day(character: Dict):
        """
        推进到下一天

        重置:
        - 每日互动次数
        - 行动点
        - 心情槽
        - 记录新的游戏日
        """
        # 重置互动次数
        character["daily_interactions_used"] = 0

        # 重置行动点
        from ..attributes.action_point_system import ActionPointSystem
        ActionPointSystem.reset_daily_action_points(character)

        # 重置心情槽
        from ..personality.mood_gauge_system import MoodGaugeSystem
        MoodGaugeSystem.reset_daily_mood(character)

        # 增加游戏日
        current_day = character.get("game_day", 1)
        character["game_day"] = current_day + 1

        # 记录推进时间
        character["last_day_advance"] = time.time()

        # 检查是否是新的一周（每7天）
        new_day = character["game_day"]
        if new_day % 7 == 1 and new_day > 1:
            # 记录上周的属性快照（用于周总结对比）
            import json
            character["last_week_snapshot"] = json.dumps({
                "intimacy": character.get("intimacy", 0),
                "affection": character.get("affection", 0),
                "corruption": character.get("corruption", 0),
                "trust": character.get("trust", 0),
                "submission": character.get("submission", 0),
            }, ensure_ascii=False)

        logger.info(f"推进到第 {character['game_day']} 天")

    @staticmethod
    def get_stage_display(character: Dict) -> str:
        """获取阶段显示文本"""
        stage = DailyInteractionSystem.get_relationship_stage(character)
        intimacy = character.get("intimacy", 0)

        stage_names = {
            "stranger": f"陌生人 (亲密度 {intimacy}/20)",
            "friend": f"朋友 (亲密度 {intimacy}/50)",
            "close": f"亲密 (亲密度 {intimacy}/80)",
            "lover": f"恋人 (亲密度 {intimacy}+)",
        }

        return stage_names.get(stage, "未知")

    @staticmethod
    def is_game_ended(character: Dict) -> bool:
        """
        检查游戏是否已结束（到达第42天）

        返回: True=游戏已结束, False=游戏继续
        """
        game_day = character.get("game_day", 1)
        return game_day >= DailyInteractionSystem.TOTAL_GAME_DAYS

    @staticmethod
    def get_remaining_days(character: Dict) -> int:
        """
        获取剩余天数

        返回: 剩余天数（0表示已结束）
        """
        game_day = character.get("game_day", 1)
        remaining = max(0, DailyInteractionSystem.TOTAL_GAME_DAYS - game_day)
        return remaining

    @staticmethod
    def get_time_pressure_message(character: Dict) -> str:
        """
        获取时间压力提示消息（在关键节点提示玩家）

        返回: 提示消息（如果需要提示的话）
        """
        game_day = character.get("game_day", 1)
        remaining = DailyInteractionSystem.get_remaining_days(character)

        # 关键节点提示
        if game_day == 1:
            return None  # 第一天不提示
        elif game_day == 7:
            return f"💡 已过去一周，还有 {remaining} 天"
        elif game_day == 14:
            return f"⏰ 已过去两周，还有 {remaining} 天"
        elif game_day == 21:
            return f"⚠️ 已过去三周，还有 {remaining} 天！"
        elif game_day == 28:
            return f"🚨 只剩两周了！还有 {remaining} 天"
        elif game_day == 35:
            return f"⏰ 【最后一周】还有 {remaining} 天！"
        elif game_day == 38:
            return f"🚨 【倒计时】还有 {remaining} 天！"
        elif game_day == 40:
            return f"⚠️ 【最后3天】关系即将定格..."
        elif game_day == 41:
            return f"💔 【最后2天】明天就是最后一天了！"
        elif game_day == 42:
            return f"🎬 【最后一天】今天结束后，游戏将迎来结局"

        return None

    @staticmethod
    def get_interaction_feedback(character: Dict) -> str:
        """获取互动后的反馈信息"""
        used = character.get("daily_interactions_used", 0)
        limit = DailyInteractionSystem.get_daily_limit(character)
        remaining = limit - used

        if remaining == 0:
            return f"""💤 【今日互动已用完】

她看起来有些疲惫...
"今天就到这里吧..."

💡 使用 /明日 进入下一天
"""
        elif remaining == 1:
            return f"💭 她看起来有点累了... (剩余互动: 1次)"
        else:
            return f"📊 今日剩余互动: {remaining}/{limit}次"

    @staticmethod
    def get_day_summary(character: Dict) -> str:
        """获取当前游戏日总结"""
        game_day = character.get("game_day", 1)
        stage = DailyInteractionSystem.get_relationship_stage(character)
        intimacy = character.get("intimacy", 0)
        used = character.get("daily_interactions_used", 0)
        limit = DailyInteractionSystem.get_daily_limit(character)

        # 计算剩余天数
        remaining_days = DailyInteractionSystem.get_remaining_days(character)

        stage_emoji = {
            "stranger": "🤝",
            "friend": "😊",
            "close": "💕",
            "lover": "❤️"
        }

        # 倒计时显示
        if remaining_days == 0:
            countdown_text = "⏰ 【游戏已结束】"
        elif remaining_days <= 3:
            countdown_text = f"🚨 【倒计时 {remaining_days} 天】"
        elif remaining_days <= 7:
            countdown_text = f"⚠️ 【剩余 {remaining_days} 天】"
        elif remaining_days <= 14:
            countdown_text = f"⏰ 剩余 {remaining_days} 天"
        else:
            countdown_text = f"📅 剩余 {remaining_days} 天"

        return f"""📅 【第 {game_day} 天 / 共 42 天】
{countdown_text}

{stage_emoji.get(stage, '📊')} 关系阶段: {DailyInteractionSystem.get_stage_display(character)}
📊 今日互动: {used}/{limit}

💡 每周(7天)会触发阶段总结
"""
