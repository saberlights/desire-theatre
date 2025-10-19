"""
动态情绪系统 - 基于当前状态实时计算情绪
每次互动都会重新计算，而非固定一天
"""

import random
import time
from typing import Dict, Optional, List, Tuple
from datetime import datetime


class DynamicMoodSystem:
    """动态情绪系统"""

    # NSFW情绪状态库
    MOOD_STATES = {
        # ========== 基础情绪 (所有阶段) ==========
        "平静": {
            "conditions": lambda c: c.get("arousal", 0) < 20 and c.get("shame", 100) > 70,
            "weight": 10,
            "effects": {
                "response_style": "平静温和",
                "resistance_modifier": 0,
                "arousal_gain_multiplier": 1.0
            },
            "description": "她看起来很平静，情绪稳定"
        },

        "害羞": {
            "conditions": lambda c: 20 <= c.get("arousal", 0) < 40 and c.get("shame", 100) > 50,
            "weight": 15,
            "effects": {
                "response_style": "害羞扭捏",
                "shame_decay_modifier": -5,
                "arousal_gain_multiplier": 1.2
            },
            "description": "她显得有些害羞，脸颊微红"
        },

        "紧张": {
            "conditions": lambda c: c.get("intimacy", 0) < 30 and c.get("arousal", 0) > 30,
            "weight": 12,
            "effects": {
                "response_style": "紧张不安",
                "resistance_modifier": 10,
                "trust_gain_multiplier": 0.8
            },
            "description": "她看起来有些紧张，不知所措"
        },

        "放松": {
            "conditions": lambda c: c.get("trust", 0) > 60 and c.get("arousal", 0) < 30,
            "weight": 8,
            "effects": {
                "response_style": "轻松自在",
                "resistance_modifier": -10,
                "intimacy_gain_multiplier": 1.3
            },
            "description": "她很放松，愿意敞开心扉"
        },

        # ========== NSFW情绪 (进阶阶段) ==========
        "发情期": {
            "conditions": lambda c: c.get("desire", 0) > 60 and c.get("arousal", 0) > 50,
            "weight": 20,
            "effects": {
                "response_style": "主动渴望",
                "arousal_gain_multiplier": 1.8,
                "resistance_modifier": -20,
                "shame_decay_modifier": -10,
                "desire_gain_multiplier": 1.5
            },
            "description": "她正处于发情期，身体异常敏感，眼神中充满渴望",
            "nsfw_level": 2,
            "triggers_extra_events": True
        },

        "敏感期": {
            "conditions": lambda c: c.get("arousal", 0) > 40 and c.get("intimacy", 0) > 50,
            "weight": 18,
            "effects": {
                "response_style": "极度敏感",
                "arousal_gain_multiplier": 2.0,
                "effect_multiplier": 1.5  # 所有动作效果x1.5
            },
            "description": "她的身体变得异常敏感，轻微的触碰都会引起强烈反应",
            "nsfw_level": 2
        },

        "余韵": {
            "conditions": lambda c: c.get("arousal", 0) > 70 and c.get("last_high_arousal_time", 0) > time.time() - 1800,  # 30分钟内
            "weight": 16,
            "effects": {
                "response_style": "意犹未尽",
                "arousal_decay_rate": 0.5,  # 兴奋度衰减减半
                "resistance_modifier": -15
            },
            "description": "她还沉浸在刚才的余韵中，身体微微颤抖",
            "nsfw_level": 3
        },

        "欲求不满": {
            "conditions": lambda c: c.get("desire", 0) > 70 and c.get("arousal", 0) < 40,
            "weight": 15,
            "effects": {
                "response_style": "焦躁不安",
                "arousal_gain_multiplier": 1.6,
                "initiative_probability": 0.3  # 30%主动请求
            },
            "description": "她显得焦躁不安，似乎在渴望些什么",
            "nsfw_level": 2,
            "triggers_extra_events": True
        },

        "顺从": {
            "conditions": lambda c: c.get("submission", 50) > 70 and c.get("resistance", 100) < 40,
            "weight": 14,
            "effects": {
                "response_style": "温顺听话",
                "resistance_modifier": -25,
                "submission_gain_multiplier": 1.3,
                "obedience_bonus": 20
            },
            "description": "她完全顺从你的意志，眼神中带着温顺",
            "nsfw_level": 2
        },

        "叛逆": {
            "conditions": lambda c: c.get("submission", 50) < 30 and c.get("corruption", 0) < 40,
            "weight": 12,
            "effects": {
                "response_style": "傲娇反抗",
                "resistance_modifier": 20,
                "failure_probability": 0.15  # 15%失败几率
            },
            "description": "她显得很叛逆，嘴上说着不要但身体很诚实",
            "nsfw_level": 1
        },

        "堕落": {
            "conditions": lambda c: c.get("corruption", 0) > 60 and c.get("shame", 100) < 30,
            "weight": 18,
            "effects": {
                "response_style": "堕落淫荡",
                "shame_decay_modifier": -15,
                "corruption_gain_multiplier": 1.4,
                "unlock_taboo_actions": True
            },
            "description": "她已经堕落了，不再掩饰自己的淫欲",
            "nsfw_level": 3,
            "triggers_extra_events": True
        },

        "羞耻崩溃": {
            "conditions": lambda c: c.get("shame", 100) < 20 and c.get("arousal", 0) > 60,
            "weight": 16,
            "effects": {
                "response_style": "羞耻全无",
                "shame_floor": 0,  # 羞耻可以降到0
                "arousal_gain_multiplier": 1.5,
                "extreme_actions_unlocked": True
            },
            "description": "她的羞耻心已经完全崩溃，什么都愿意做",
            "nsfw_level": 3
        },

        "高潮边缘": {
            "conditions": lambda c: c.get("arousal", 0) > 85,
            "weight": 25,
            "effects": {
                "response_style": "濒临高潮",
                "arousal_gain_multiplier": 2.5,
                "critical_probability": 0.4,  # 40%触发特殊事件
                "loss_of_control": True
            },
            "description": "她已经到了边缘，随时可能崩溃",
            "nsfw_level": 3,
            "triggers_extra_events": True
        },

        "贤者时间": {
            "conditions": lambda c: c.get("post_orgasm_time", 0) > time.time() - 3600,  # 1小时内
            "weight": 14,
            "effects": {
                "response_style": "疲惫满足",
                "arousal_gain_multiplier": 0.3,
                "resistance_modifier": -30,
                "intimacy_gain_multiplier": 1.5
            },
            "description": "她刚经历了高潮，现在很疲惫但很满足",
            "nsfw_level": 2
        },

        "醉酒": {
            "conditions": lambda c: c.get("drunk_level", 0) > 0,
            "weight": 12,
            "effects": {
                "response_style": "迷糊醉酒",
                "resistance_modifier": -10,  # 固定值，醉酒会降低抵抗力
                "shame_modifier": -5,  # 固定值，醉酒会降低羞耻心
                "random_response_probability": 0.3
            },
            "description": "她有些醉了，脸颊绯红，说话含糊",
            "nsfw_level": 2
        },

        "嫉妒": {
            "conditions": lambda c: c.get("jealousy_trigger", False),
            "weight": 10,
            "effects": {
                "response_style": "吃醋生气",
                "affection_demand": True,
                "special_dialogue": True
            },
            "description": "她在吃醋，需要你的关注",
            "nsfw_level": 0
        },

        "主动诱惑": {
            "conditions": lambda c: c.get("corruption", 0) > 50 and c.get("desire", 0) > 60 and random.random() < 0.2,
            "weight": 17,
            "effects": {
                "response_style": "主动诱惑",
                "initiative_seduction": True,
                "arousal_gain_multiplier": 1.4,
                "seduction_power": 20
            },
            "description": "她主动向你发起诱惑，眼神充满挑逗",
            "nsfw_level": 2,
            "triggers_extra_events": True
        },

        "恐惧兴奋": {
            "conditions": lambda c: c.get("arousal", 0) > 50 and c.get("resistance", 100) > 60 and c.get("shame", 100) > 50,
            "weight": 13,
            "effects": {
                "response_style": "害怕又兴奋",
                "arousal_gain_multiplier": 1.3,
                "resistance_modifier": 5,
                "shame_decay_modifier": -8,
                "conflicted_emotions": True
            },
            "description": "她既害怕又兴奋，矛盾的情绪让她不知所措",
            "nsfw_level": 2
        },

        "疲惫": {
            "conditions": lambda c: c.get("interaction_count", 0) % 15 == 14,  # 连续互动
            "weight": 8,
            "effects": {
                "response_style": "疲惫无力",
                "arousal_gain_multiplier": 0.7,
                "effect_multiplier": 0.8
            },
            "description": "她看起来有些累了，需要休息",
            "nsfw_level": 1
        },

        "兴奋期待": {
            "conditions": lambda c: c.get("affection", 0) > 50 and c.get("desire", 0) > 30 and c.get("arousal", 0) < 50,
            "weight": 11,
            "effects": {
                "response_style": "期待兴奋",
                "arousal_gain_multiplier": 1.4,
                "positive_feedback_boost": 10
            },
            "description": "她对接下来的互动充满期待",
            "nsfw_level": 1
        }
    }

    # 时间段影响
    TIME_MODIFIERS = {
        "deep_night": {  # 深夜 (0-4点)
            "hours": range(0, 5),
            "effects": {
                "arousal_multiplier": 1.3,
                "resistance_modifier": -10,
                "shame_modifier": -5,
                "special_dialogue_probability": 0.2
            },
            "description": "深夜的暧昧气氛"
        },
        "morning": {  # 清晨 (5-8点)
            "hours": range(5, 9),
            "effects": {
                "arousal_multiplier": 0.8,
                "affection_multiplier": 1.2
            },
            "description": "清晨的清新感觉"
        },
        "afternoon": {  # 下午 (14-17点)
            "hours": range(14, 18),
            "effects": {
                "arousal_multiplier": 1.0
            },
            "description": "平静的下午"
        },
        "evening": {  # 傍晚 (18-22点)
            "hours": range(18, 23),
            "effects": {
                "arousal_multiplier": 1.1,
                "intimacy_multiplier": 1.1
            },
            "description": "温馨的傍晚"
        },
        "late_night": {  # 深夜 (22-24点)
            "hours": range(22, 24),
            "effects": {
                "arousal_multiplier": 1.2,
                "resistance_modifier": -5
            },
            "description": "深夜的暧昧"
        }
    }

    @staticmethod
    def calculate_current_mood(character: Dict) -> Dict:
        """
        实时计算当前情绪
        返回: {
            "mood_name": str,
            "mood_description": str,
            "effects": dict,
            "nsfw_level": int,
            "triggers_events": bool
        }
        """
        # 获取所有满足条件的情绪
        possible_moods = []

        for mood_name, mood_data in DynamicMoodSystem.MOOD_STATES.items():
            try:
                if mood_data["conditions"](character):
                    possible_moods.append({
                        "name": mood_name,
                        "data": mood_data,
                        "weight": mood_data["weight"]
                    })
            except Exception:
                # 条件检查失败，跳过
                continue

        # 没有满足条件的情绪，返回默认平静
        if not possible_moods:
            return {
                "mood_name": "平静",
                "mood_description": "她看起来很平静",
                "effects": {},
                "nsfw_level": 0,
                "triggers_events": False
            }

        # 根据权重随机选择（权重越高越容易选中）
        total_weight = sum(m["weight"] for m in possible_moods)
        rand = random.uniform(0, total_weight)

        current_weight = 0
        selected_mood = possible_moods[0]

        for mood in possible_moods:
            current_weight += mood["weight"]
            if rand <= current_weight:
                selected_mood = mood
                break

        return {
            "mood_name": selected_mood["name"],
            "mood_description": selected_mood["data"]["description"],
            "effects": selected_mood["data"]["effects"],
            "nsfw_level": selected_mood["data"].get("nsfw_level", 0),
            "triggers_events": selected_mood["data"].get("triggers_extra_events", False)
        }

    @staticmethod
    def get_time_modifier() -> Dict:
        """获取当前时间段的修正"""
        current_hour = datetime.now().hour

        for period_name, period_data in DynamicMoodSystem.TIME_MODIFIERS.items():
            if current_hour in period_data["hours"]:
                return {
                    "period_name": period_name,
                    "effects": period_data["effects"],
                    "description": period_data["description"]
                }

        return {"period_name": "default", "effects": {}, "description": ""}

    @staticmethod
    def apply_mood_effects_to_action(
        base_effects: Dict[str, int],
        mood: Dict,
        time_modifier: Dict
    ) -> Tuple[Dict[str, int], List[str]]:
        """
        应用情绪效果到动作
        返回: (修改后的效果, 额外提示列表)
        """
        modified_effects = base_effects.copy()
        extra_hints = []

        mood_effects = mood.get("effects", {})

        # 应用各种倍率
        for attr, value in modified_effects.items():
            # 兴奋度倍率
            if attr == "arousal" and "arousal_gain_multiplier" in mood_effects:
                multiplier = mood_effects["arousal_gain_multiplier"]
                modified_effects[attr] = int(value * multiplier)
                if multiplier > 1.3:
                    extra_hints.append(f"【{mood['mood_name']}】她的身体异常敏感！(兴奋+{int((multiplier - 1) * 100)}%)")

            # 亲密度倍率
            if attr == "intimacy" and "intimacy_gain_multiplier" in mood_effects:
                multiplier = mood_effects["intimacy_gain_multiplier"]
                modified_effects[attr] = int(value * multiplier)

            # 其他属性倍率
            if "effect_multiplier" in mood_effects:
                multiplier = mood_effects["effect_multiplier"]
                modified_effects[attr] = int(value * multiplier)

        # 抵抗力修正
        if "resistance_modifier" in mood_effects:
            modified_effects["resistance"] = modified_effects.get("resistance", 0) + mood_effects["resistance_modifier"]

        # 羞耻心修正
        if "shame_decay_modifier" in mood_effects:
            modified_effects["shame"] = modified_effects.get("shame", 0) + mood_effects["shame_decay_modifier"]

        # 应用时间修正
        time_effects = time_modifier.get("effects", {})
        if "arousal_multiplier" in time_effects and "arousal" in modified_effects:
            modified_effects["arousal"] = int(modified_effects["arousal"] * time_effects["arousal_multiplier"])

        if "resistance_modifier" in time_effects:
            modified_effects["resistance"] = modified_effects.get("resistance", 0) + time_effects["resistance_modifier"]

        return modified_effects, extra_hints

    @staticmethod
    def check_special_mood_triggers(character: Dict, mood: Dict) -> Optional[Dict]:
        """
        检查情绪是否触发特殊事件
        返回: 事件信息或None
        """
        if not mood.get("triggers_events", False):
            return None

        mood_name = mood["mood_name"]
        effects = mood["effects"]

        # 发情期事件
        if mood_name == "发情期" and random.random() < 0.3:
            return {
                "event_type": "主动请求",
                "content": "她主动靠近你，眼神迷离：\"我...我想要...\"",
                "options": ["满足她", "继续调情", "故意忽视"],
                "arousal_bonus": 10
            }

        # 欲求不满事件
        if mood_name == "欲求不满" and "initiative_probability" in effects:
            if random.random() < effects["initiative_probability"]:
                return {
                    "event_type": "主动示好",
                    "content": "她不安地扭动着身体，小声说：\"能不能...再继续？\"",
                    "arousal_bonus": 5
                }

        # 堕落事件
        if mood_name == "堕落" and random.random() < 0.25:
            return {
                "event_type": "堕落宣言",
                "content": "她妩媚地看着你：\"我已经是你的东西了...想怎么样都可以...\"",
                "unlock_hint": "解锁了更多极端动作",
                "corruption_bonus": 5
            }

        # 高潮边缘事件
        if mood_name == "高潮边缘" and "critical_probability" in effects:
            if random.random() < effects["critical_probability"]:
                return {
                    "event_type": "临界点",
                    "content": "她已经到了极限，身体不受控制地颤抖...再一点点就...！",
                    "critical_moment": True,
                    "next_action_multiplier": 3.0
                }

        # 主动诱惑事件
        if mood_name == "主动诱惑" and random.random() < 0.4:
            seduction_lines = [
                "她故意露出雪白的肩膀，用诱人的眼神看着你...",
                "她轻咬嘴唇，手指在你身上游走...",
                "\"想要我吗？\"她贴在你耳边轻声低语...",
                "她慢慢解开纽扣，眼神充满挑逗..."
            ]
            return {
                "event_type": "主动诱惑",
                "content": random.choice(seduction_lines),
                "arousal_bonus": 15,
                "desire_bonus": 10
            }

        return None

    @staticmethod
    def get_mood_display(mood: Dict, time_modifier: Dict) -> str:
        """
        获取情绪的显示文本
        用于在状态面板中展示
        """
        mood_emoji = {
            0: "😊",  # 普通
            1: "😳",  # 轻度NSFW
            2: "💗",  # 中度NSFW
            3: "💦"   # 重度NSFW
        }

        nsfw_level = mood.get("nsfw_level", 0)
        emoji = mood_emoji.get(nsfw_level, "😊")

        time_desc = time_modifier.get("description", "")
        time_prefix = f"[{time_desc}] " if time_desc else ""

        display = f"{emoji} {time_prefix}{mood['mood_name']}\n"
        display += f"└─ {mood['mood_description']}"

        return display
