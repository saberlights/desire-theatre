"""
心情槽系统 - 借鉴《火山的女儿》的简洁设计

核心理念:
- 心情是每日资源，影响互动效果
- 玩家需要考虑何时互动（心情好时效果更好）
- 失败会影响心情，需要谨慎选择
- 每天重置，保持新鲜感

心情等级（5个等级代替18种复杂情绪）:
- 😞 低落 (0-20) - 互动效果-30%
- 😐 平静 (21-40) - 互动效果正常
- 😊 愉快 (41-60) - 互动效果+20%
- 😍 兴奋 (61-80) - 互动效果+50%
- 💕 极佳 (81-100) - 互动效果+100%，触发特殊对话
"""

from typing import Dict, Tuple, Optional
from src.common.logger import get_logger

logger = get_logger("dt_mood_gauge")


class MoodGaugeSystem:
    """心情槽系统"""

    # 心情等级定义
    MOOD_LEVELS = {
        "低落": {
            "range": (0, 20),
            "emoji": "😞",
            "effect_multiplier": 0.7,  # 互动效果-30%
            "description": "她情绪低落，似乎不太想互动...",
            "hint": "💡 建议：先用温柔动作提升心情"
        },
        "平静": {
            "range": (21, 40),
            "emoji": "😐",
            "effect_multiplier": 1.0,  # 正常效果
            "description": "她心情平静，可以正常互动",
            "hint": ""
        },
        "愉快": {
            "range": (41, 60),
            "emoji": "😊",
            "effect_multiplier": 1.2,  # 效果+20%
            "description": "她心情不错，互动效果更好",
            "hint": "💡 现在是互动的好时机！"
        },
        "兴奋": {
            "range": (61, 80),
            "emoji": "😍",
            "effect_multiplier": 1.5,  # 效果+50%
            "description": "她非常兴奋，期待你的互动！",
            "hint": "✨ 绝佳时机！此时互动效果大幅提升"
        },
        "极佳": {
            "range": (81, 100),
            "emoji": "💕",
            "effect_multiplier": 2.0,  # 效果+100%
            "description": "她的心情好到极点，对你充满期待！",
            "hint": "🌟 完美时刻！效果翻倍，可能触发特殊对话",
            "special_dialogue": True
        }
    }

    # 不同人格的基础心情值
    PERSONALITY_BASE_MOOD = {
        "tsundere": 45,   # 傲娇：稍低但不会太差
        "innocent": 55,   # 天真：偏高
        "seductive": 50,  # 妖媚：中等
        "shy": 40,        # 害羞：偏低
        "cold": 35        # 高冷：低
    }

    @staticmethod
    def get_base_mood(character: Dict) -> int:
        """获取角色的基础心情值（每日重置时使用）"""
        personality = character.get("personality_type", "tsundere")
        base = MoodGaugeSystem.PERSONALITY_BASE_MOOD.get(personality, 50)

        # 好感度影响基础心情
        affection = character.get("affection", 0)
        if affection >= 80:
            base += 15
        elif affection >= 60:
            base += 10
        elif affection >= 40:
            base += 5
        elif affection < 20:
            base -= 10

        # 限制在0-100范围
        return max(0, min(100, base))

    @staticmethod
    def get_current_mood_level(mood_value: int) -> Tuple[str, Dict]:
        """
        根据心情值获取心情等级
        返回: (等级名称, 等级数据)
        """
        for level_name, level_data in MoodGaugeSystem.MOOD_LEVELS.items():
            min_val, max_val = level_data["range"]
            if min_val <= mood_value <= max_val:
                return level_name, level_data

        # 默认返回平静
        return "平静", MoodGaugeSystem.MOOD_LEVELS["平静"]

    @staticmethod
    def apply_mood_to_effects(
        base_effects: Dict[str, int],
        mood_value: int
    ) -> Tuple[Dict[str, int], str, bool]:
        """
        应用心情效果到互动
        返回: (修改后的效果, 心情提示, 是否触发特殊对话)
        """
        level_name, level_data = MoodGaugeSystem.get_current_mood_level(mood_value)

        multiplier = level_data["effect_multiplier"]
        modified_effects = {}

        # 应用倍率（只影响正向效果）
        for attr, value in base_effects.items():
            if value > 0:  # 正向效果
                modified_effects[attr] = int(value * multiplier)
            else:  # 负向效果不受心情影响
                modified_effects[attr] = value

        # 构建心情提示
        hint = f"{level_data['emoji']} 【心情: {level_name}】({mood_value}/100)"
        if level_data.get("hint"):
            hint += f"\n{level_data['hint']}"

        # 检查是否触发特殊对话
        has_special = level_data.get("special_dialogue", False)

        return modified_effects, hint, has_special

    @staticmethod
    def update_mood(
        character: Dict,
        change: int,
        reason: str = ""
    ) -> Tuple[int, str]:
        """
        更新心情值
        返回: (新心情值, 变化消息)
        """
        current_mood = character.get("mood_gauge", 50)
        new_mood = max(0, min(100, current_mood + change))

        character["mood_gauge"] = new_mood

        # 构建变化消息
        old_level, _ = MoodGaugeSystem.get_current_mood_level(current_mood)
        new_level, new_data = MoodGaugeSystem.get_current_mood_level(new_mood)

        change_msg = ""
        if change > 0:
            change_msg = f"💗 心情上升 +{change}"
        elif change < 0:
            change_msg = f"💔 心情下降 {change}"

        if reason:
            change_msg += f" ({reason})"

        # 等级变化提示
        if old_level != new_level:
            change_msg += f"\n{new_data['emoji']} 心情变为: {new_level}"

        return new_mood, change_msg

    @staticmethod
    def calculate_mood_change(
        action_success: bool,
        is_combo: bool = False,
        is_first_today: bool = False,
        interactions_used_up: bool = False
    ) -> int:
        """
        计算心情变化值

        参数:
        - action_success: 动作是否成功
        - is_combo: 是否连续互动
        - is_first_today: 是否今日首次
        - interactions_used_up: 是否用完互动次数
        """
        change = 0

        # 基础变化
        if action_success:
            change += 10  # 成功+10
        else:
            change -= 15  # 失败-15（惩罚更重）

        # Combo加成
        if is_combo and action_success:
            change += 5

        # 首次互动加成
        if is_first_today:
            change += 5

        # 用完互动次数惩罚
        if interactions_used_up:
            change -= 10

        return change

    @staticmethod
    def reset_daily_mood(character: Dict):
        """
        每日重置心情值
        在 advance_to_next_day 中调用
        """
        base_mood = MoodGaugeSystem.get_base_mood(character)
        character["mood_gauge"] = base_mood

        logger.info(f"重置心情值: {base_mood}")

    @staticmethod
    def get_mood_display(character: Dict) -> str:
        """获取心情显示（用于状态查询）"""
        mood_value = character.get("mood_gauge", 50)
        level_name, level_data = MoodGaugeSystem.get_current_mood_level(mood_value)

        # 进度条
        bar_length = 10
        filled = int((mood_value / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        display = f"""{level_data['emoji']} 【心情: {level_name}】
{bar} {mood_value}/100

{level_data['description']}"""

        if level_data.get("hint"):
            display += f"\n\n{level_data['hint']}"

        # 效果说明
        multiplier_percent = int((level_data['effect_multiplier'] - 1) * 100)
        if multiplier_percent > 0:
            display += f"\n📈 当前互动效果: +{multiplier_percent}%"
        elif multiplier_percent < 0:
            display += f"\n📉 当前互动效果: {multiplier_percent}%"

        return display

    @staticmethod
    def get_special_dialogue(mood_value: int, character: Dict) -> Optional[str]:
        """
        根据心情获取特殊对话
        仅在心情极佳时触发
        """
        level_name, level_data = MoodGaugeSystem.get_current_mood_level(mood_value)

        if not level_data.get("special_dialogue", False):
            return None

        # 根据关系阶段返回不同的特殊对话
        from ..time.daily_limit_system import DailyInteractionSystem
        stage = DailyInteractionSystem.get_relationship_stage(character)

        dialogues = {
            "stranger": [
                "\"今天和你在一起真开心...\" 她露出了难得的笑容。",
                "\"我觉得...我们能成为很好的朋友。\" 她的眼神很温柔。"
            ],
            "friend": [
                "\"能认识你真好...\" 她主动牵住了你的手。",
                "\"和你在一起的时候，总是特别放松。\" 她靠在你肩上。",
                "\"今天的你...特别有魅力呢。\" 她脸红着看着你。"
            ],
            "close": [
                "\"我想...一直这样和你在一起...\" 她深情地望着你。",
                "\"你知道吗...我已经离不开你了。\" 她主动拥抱你。",
                "\"只要和你在一起，做什么都开心。\" 她亲了亲你的脸颊。"
            ],
            "lover": [
                "\"我爱你...\" 她第一次说出这三个字。",
                "\"想要你...一直想要...\" 她主动吻上你的嘴唇。",
                "\"今晚...我是你的...\" 她眼神迷离地看着你。"
            ]
        }

        import random
        stage_dialogues = dialogues.get(stage, dialogues["stranger"])
        return random.choice(stage_dialogues)
