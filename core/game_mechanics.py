"""
游戏机制 - 解锁、Buff/Debuff系统
"""

from typing import Dict, List


class GameMechanics:
    """游戏机制"""

    # 关系等级门槛
    RELATIONSHIP_LEVELS = {
        0: {
            "level_name": "陌生人",
            "available_actions": ["问候", "夸", "送礼", "牵手"],
            "description": "她对你很警惕"
        },
        20: {
            "level_name": "认识",
            "description": "她开始接受你的靠近"
        },
        40: {
            "level_name": "朋友",
            "description": "你们成为了朋友"
        },
        60: {
            "level_name": "好感",
            "description": "她对你有好感"
        },
        80: {
            "level_name": "恋人",
            "description": "你们已是恋人"
        },
        100: {
            "level_name": "深爱",
            "description": "她深深爱着你"
        }
    }

    # Debuff系统
    DEBUFFS = {
        "疲劳": {
            "trigger": "连续互动5次以上不休息",
            "effect": "所有收益-30%",
            "duration": 3600,  # 1小时
            "cure": "休息或使用恢复道具"
        },
        "戒备": {
            "trigger": "推进太快，亲密度不足但强行高强度互动",
            "effect": "抵抗+20, 信任-10",
            "duration": 7200,  # 2小时
            "cure": "做温柔的日常互动恢复信任"
        },
        "厌倦": {
            "trigger": "重复同一动作3次以上",
            "effect": "该动作效果-50%",
            "duration": 1800,  # 30分钟
            "cure": "尝试不同的动作"
        },
    }

    @staticmethod
    def get_relationship_level(affection: int) -> Dict:
        """获取关系等级"""
        for threshold in sorted(GameMechanics.RELATIONSHIP_LEVELS.keys(), reverse=True):
            if affection >= threshold:
                return GameMechanics.RELATIONSHIP_LEVELS[threshold]
        return GameMechanics.RELATIONSHIP_LEVELS[0]

    @staticmethod
    def check_hidden_action_unlock(character: Dict, action_name: str) -> bool:
        """检查隐藏动作是否解锁"""
        # 隐藏动作解锁条件
        HIDDEN_ACTIONS = {
            "支配": {
                "corruption": 90,
                "submission": 90,
                "resistance": "<10",
            },
            "契约": {
                "affection": 100,
                "trust": 100,
                "intimacy": 100
            },
        }

        if action_name not in HIDDEN_ACTIONS:
            return True  # 不是隐藏动作，直接返回True

        conditions = HIDDEN_ACTIONS[action_name]
        for attr, required in conditions.items():
            char_value = character.get(attr, 0)
            if isinstance(required, str) and required.startswith("<"):
                threshold = int(required[1:])
                if char_value >= threshold:
                    return False
            else:
                threshold = int(required)
                if char_value < threshold:
                    return False

        return True
