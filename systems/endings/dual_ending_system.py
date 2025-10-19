"""
双重结局系统 - 感情路线 + 性向路线

核心理念:
- 借鉴《火山的女儿》的双重结局设计
- 感情路线：描述关系的情感深度（纯爱/禁忌/依赖等）
- 性向路线：描述关系的性倾向（纯洁/开放/SM等）
- 玩家可以同时达成两种结局
- 满足多个结局时可以自主选择

结局组合示例:
- 纯爱至上 + 纯洁天使 = 最完美的纯爱结局
- 禁忌之爱 + SM女王 = 禁忌而刺激的关系
- 依赖之爱 + 完全服从 = 支配与被支配的关系
"""

from typing import Dict, Tuple, Optional, List
from src.common.logger import get_logger

logger = get_logger("dt_dual_ending")


class DualEndingSystem:
    """双重结局系统"""

    # ========== 感情路线结局 ==========
    EMOTION_ENDINGS = {
        "perfect_love": {
            "name": "💕 完美恋人",
            "tier": "完美",
            "priority": 100,
            "conditions": {
                "affection": (80, 100),
                "intimacy": (80, 100),
                "trust": (70, 100),
                "resistance": (0, 40),
            },
            "description": "你们的关系达到了理想的平衡，互相尊重，彼此信任。",
        },
        "pure_love": {
            "name": "💗 纯爱至上",
            "tier": "完美",
            "priority": 95,
            "conditions": {
                "affection": (85, 100),
                "intimacy": (75, 100),
                "trust": (80, 100),
                "corruption": (0, 30),
            },
            "description": "最纯粹的爱情，不掺杂任何杂质，只有彼此的心意。",
        },
        "forbidden_love": {
            "name": "🔥 禁忌之爱",
            "tier": "好",
            "priority": 90,
            "conditions": {
                "affection": (70, 100),
                "intimacy": (80, 100),
                "corruption": (70, 100),
                "trust": (60, 100),
            },
            "description": "你们跨越了所有的禁忌，这是危险而炙热的爱情。",
        },
        "dependent_love": {
            "name": "💞 依赖之爱",
            "tier": "好",
            "priority": 85,
            "conditions": {
                "affection": (70, 100),
                "submission": (70, 100),
                "trust": (60, 100),
            },
            "description": "她已经完全依赖你了，这是一种不平等却又真实的关系。",
        },
        "gentle_daily": {
            "name": "🌸 温柔日常",
            "tier": "好",
            "priority": 80,
            "conditions": {
                "affection": (75, 100),
                "trust": (70, 100),
                "intimacy": (40, 70),
            },
            "description": "温馨而平淡的感情，细水长流的陪伴。",
        },
        "best_friend": {
            "name": "🤝 挚友情深",
            "tier": "好",
            "priority": 75,
            "conditions": {
                "trust": (80, 100),
                "affection": (60, 85),
                "intimacy": (0, 40),
            },
            "description": "你们成为了最好的朋友，这份友谊同样珍贵。",
        },
        "secret_lover": {
            "name": "🌙 秘密恋人",
            "tier": "普通",
            "priority": 70,
            "conditions": {
                "intimacy": (70, 100),
                "corruption": (50, 80),
                "affection": (50, 75),
            },
            "description": "暧昧而隐秘的关系，白天是朋友，夜晚是恋人。",
        },
        "ordinary_love": {
            "name": "😊 平凡恋人",
            "tier": "普通",
            "priority": 60,
            "conditions": {
                "affection": (50, 75),
                "intimacy": (40, 70),
            },
            "description": "平平淡淡的关系，没有特别突出，也没有大问题。",
        },
        "broken_relationship": {
            "name": "💔 破碎关系",
            "tier": "坏",
            "priority": 30,
            "conditions": {
                "affection": (0, 30),
                "resistance": (70, 100),
            },
            "description": "你们的关系已经破碎，她恨你入骨。",
        },
    }

    # ========== 性向路线结局 ==========
    SEXUAL_ENDINGS = {
        "pure_angel": {
            "name": "👼 纯洁天使",
            "tier": "纯洁",
            "priority": 100,
            "conditions": {
                "corruption": (0, 20),
                "shame": (60, 100),
                "intimacy": (60, 100),
            },
            "description": "她保持着纯洁，羞耻心让她更加可爱。",
        },
        "innocent_seduction": {
            "name": "😊 清纯诱惑",
            "tier": "纯洁",
            "priority": 95,
            "conditions": {
                "corruption": (20, 40),
                "shame": (50, 80),
                "affection": (70, 100),
            },
            "description": "她有些开放，但仍然保持着羞涩和纯真。",
        },
        "open_lover": {
            "name": "🌹 开放情人",
            "tier": "开放",
            "priority": 90,
            "conditions": {
                "corruption": (40, 70),
                "shame": (20, 50),
                "intimacy": (70, 100),
            },
            "description": "她接受了很多玩法，但仍有底线和自我。",
        },
        "passionate_fire": {
            "name": "🔥 欲火焚身",
            "tier": "开放",
            "priority": 85,
            "conditions": {
                "corruption": (60, 85),
                "desire": (80, 100),
                "arousal": (70, 100),
            },
            "description": "她沉溺在欲望之中，每次都渴望更多。",
        },
        "sm_queen": {
            "name": "👑 SM女王",
            "tier": "极限",
            "priority": 80,
            "conditions": {
                "corruption": (70, 100),
                "submission": (0, 30),
                "resistance": (60, 100),
                "affection": (50, 100),
            },
            "description": "她反客为主，成为了支配你的女王。",
        },
        "perfect_slave": {
            "name": "🙇 完全服从",
            "tier": "极限",
            "priority": 75,
            "conditions": {
                "submission": (85, 100),
                "corruption": (70, 100),
                "resistance": (0, 20),
            },
            "description": "她完全服从你的一切命令，没有自我。",
        },
        "corruption_fall": {
            "name": "😈 堕落深渊",
            "tier": "极限",
            "priority": 70,
            "conditions": {
                "corruption": (90, 100),
                "shame": (0, 15),
                "resistance": (0, 15),
            },
            "description": "她已经彻底堕落，所有底线都被打破。",
        },
        "exhibitionist": {
            "name": "🎭 暴露癖",
            "tier": "极限",
            "priority": 65,
            "conditions": {
                "corruption": (75, 100),
                "shame": (0, 20),
                # 需要有户外play的训练进度
            },
            "description": "她迷恋上了公开场合的刺激感。",
        },
        "masochist": {
            "name": "💔 受虐狂",
            "tier": "极限",
            "priority": 60,
            "conditions": {
                "corruption": (70, 100),
                "submission": (80, 100),
                # 需要有SM玩法的训练进度
            },
            "description": "她从痛苦中获得快感，完全沉溺。",
        },
        "nymphomaniac": {
            "name": "💗 性瘾者",
            "tier": "极限",
            "priority": 55,
            "conditions": {
                "corruption": (85, 100),
                "desire": (90, 100),
                "total_arousal_gained": (5000, 999999),
            },
            "description": "她对性上瘾，无法自拔。",
        },
    }

    @staticmethod
    def check_emotion_ending(character: Dict) -> Optional[Tuple[str, Dict]]:
        """检查感情路线结局"""
        sorted_endings = sorted(
            DualEndingSystem.EMOTION_ENDINGS.items(),
            key=lambda x: x[1]["priority"],
            reverse=True
        )

        for ending_id, ending_data in sorted_endings:
            if DualEndingSystem._check_conditions(character, ending_data["conditions"]):
                return ending_id, ending_data

        return None

    @staticmethod
    def check_sexual_ending(character: Dict) -> Optional[Tuple[str, Dict]]:
        """检查性向路线结局"""
        sorted_endings = sorted(
            DualEndingSystem.SEXUAL_ENDINGS.items(),
            key=lambda x: x[1]["priority"],
            reverse=True
        )

        for ending_id, ending_data in sorted_endings:
            if DualEndingSystem._check_conditions(character, ending_data["conditions"]):
                return ending_id, ending_data

        return None

    @staticmethod
    def _check_conditions(character: Dict, conditions: Dict) -> bool:
        """检查是否满足条件"""
        for attr, required in conditions.items():
            if isinstance(required, tuple):
                min_val, max_val = required
                char_value = character.get(attr, 0)
                if not (min_val <= char_value <= max_val):
                    return False
            else:
                # 单个数值条件（大于等于）
                char_value = character.get(attr, 0)
                if char_value < required:
                    return False
        return True

    @staticmethod
    def get_all_possible_emotion_endings(character: Dict) -> List[Tuple[str, Dict]]:
        """获取所有可能的感情结局"""
        possible = []
        for ending_id, ending_data in DualEndingSystem.EMOTION_ENDINGS.items():
            if DualEndingSystem._check_conditions(character, ending_data["conditions"]):
                possible.append((ending_id, ending_data))

        possible.sort(key=lambda x: x[1]["priority"], reverse=True)
        return possible

    @staticmethod
    def get_all_possible_sexual_endings(character: Dict) -> List[Tuple[str, Dict]]:
        """获取所有可能的性向结局"""
        possible = []
        for ending_id, ending_data in DualEndingSystem.SEXUAL_ENDINGS.items():
            if DualEndingSystem._check_conditions(character, ending_data["conditions"]):
                possible.append((ending_id, ending_data))

        possible.sort(key=lambda x: x[1]["priority"], reverse=True)
        return possible

    @staticmethod
    def format_dual_ending_message(
        emotion_ending: Tuple[str, Dict],
        sexual_ending: Tuple[str, Dict],
        character: Dict
    ) -> str:
        """格式化双重结局消息"""
        emotion_id, emotion_data = emotion_ending
        sexual_id, sexual_data = sexual_ending

        game_day = character.get("game_day", 1)
        interaction_count = character.get("interaction_count", 0)

        message = f"""
━━━━━━━━━━━━━━━━━━━
🎬 【游戏结束 - 第{game_day}天】
━━━━━━━━━━━━━━━━━━━

【感情路线】
{emotion_data['name']}
{emotion_data['description']}

【性向路线】
{sexual_data['name']}
{sexual_data['description']}

━━━━━━━━━━━━━━━━━━━
📊 最终数据:
  游戏天数: {game_day}天
  互动次数: {interaction_count}次

  ❤️ 好感度: {character.get('affection', 0)}
  💗 亲密度: {character.get('intimacy', 0)}
  🤝 信任度: {character.get('trust', 0)}
  😈 堕落度: {character.get('corruption', 0)}
  🙇 顺从度: {character.get('submission', 0)}

━━━━━━━━━━━━━━━━━━━
感谢游玩！

使用 /重开 可以重新开始，尝试其他结局组合。
━━━━━━━━━━━━━━━━━━━
"""

        return message.strip()
