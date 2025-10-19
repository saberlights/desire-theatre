"""
惊喜机制系统 - 随机波动、暴击、失败
让每次互动都有不确定性和惊喜感
"""

import random
from typing import Dict, Tuple, Optional, List


class SurpriseSystem:
    """惊喜机制系统"""

    # 暴击等级配置
    CRITICAL_LEVELS = {
        "普通暴击": {
            "probability": 0.15,  # 15%概率
            "multiplier": 2.0,
            "messages": [
                "✨【暴击！】她的反应比平时更加强烈！",
                "💫【超级有效！】这次的效果格外好！",
                "⚡【会心一击！】你似乎找到了最佳时机！"
            ]
        },
        "大暴击": {
            "probability": 0.05,  # 5%概率
            "multiplier": 3.0,
            "messages": [
                "🌟【大暴击！！】她完全无法抵抗这种刺激！",
                "💥【超级暴击！】效果惊人！她的身体剧烈反应！",
                "✨【完美触碰！】你精准地找到了她的弱点！"
            ],
            "extra_arousal": 15
        },
        "史诗暴击": {
            "probability": 0.01,  # 1%概率
            "multiplier": 5.0,
            "messages": [
                "🌈【史诗级暴击！！！】不可思议的效果！她几乎要当场崩溃！",
                "💖【神级触碰！！！】这是绝对的致命一击！",
                "🎆【超越极限！！！】她从未体验过如此强烈的感觉！"
            ],
            "extra_arousal": 30,
            "bonus_effects": {
                "resistance": -20,
                "shame": -15,
                "corruption": 10
            }
        }
    }

    # 失败等级配置
    FAILURE_LEVELS = {
        "轻微失误": {
            "probability": 0.1,  # 10%概率（正常情况）
            "multiplier": 0.5,
            "messages": [
                "😅【失误】时机似乎不太对...她的反应有些冷淡",
                "🤔【效果欠佳】这次似乎没什么感觉...",
                "😐【不在状态】她看起来心不在焉"
            ]
        },
        "明显失败": {
            "probability": 0.05,  # 5%概率（叛逆/抵抗高时）
            "multiplier": 0.2,
            "messages": [
                "❌【失败】她推开了你，\"不是现在...\"",
                "😤【抵抗】\"我不想...\"她明确拒绝了",
                "🙅【拒绝】她转过身去，显然不愿意"
            ],
            "resistance_gain": 10
        },
        "适得其反": {
            "probability": 0.02,  # 2%概率
            "multiplier": 0,  # 无效果
            "messages": [
                "💢【适得其反】她生气了！\"你在想什么！\"",
                "😠【惹怒】这让她很不高兴...",
                "🚫【严重失误】她推开你，看起来很失望"
            ],
            "negative_effects": {
                "affection": -5,
                "trust": -3,
                "resistance": 15
            }
        }
    }

    @staticmethod
    def calculate_synergy(
        character: Dict,
        action_name: str,
        mood: Optional[Dict] = None
    ) -> Tuple[float, List[str]]:
        """
        计算状态契合度（替代纯随机暴击）
        返回: (效果倍率, 契合提示列表)
        """
        synergy = 1.0
        synergy_hints = []

        # === 情绪-动作匹配 ===
        if mood:
            mood_name = mood.get("mood_name", "")

            # 敏感期 + 触碰类动作
            if mood_name == "敏感期" and action_name in ["摸", "亲", "舔", "抱", "壁咚"]:
                synergy += 0.5
                synergy_hints.append("💫【敏感期加成】她的身体异常敏感！")

            # 发情期 + 高强度动作
            if mood_name == "发情期" and action_name in ["推倒", "侵犯", "调教", "舔"]:
                synergy += 0.8
                synergy_hints.append("🔥【发情期高度契合】她正渴望这种刺激！")

            # 欲求不满 + 满足需求
            if mood_name == "欲求不满" and action_name in ["推倒", "侵犯", "舔", "诱惑"]:
                synergy += 0.6
                synergy_hints.append("💗【满足渴望】正是她所需要的！")

            # 顺从 + 命令/调教
            if mood_name == "顺从" and action_name in ["命令", "调教", "羞辱"]:
                synergy += 0.4
                synergy_hints.append("🙇【完美顺从】她乖巧地接受了一切")

            # 堕落 + 羞耻/堕落类动作
            if mood_name == "堕落" and action_name in ["羞辱", "侵犯", "调教"]:
                synergy += 0.5
                synergy_hints.append("😈【堕落共鸣】她已经完全沉沦")

            # 高潮边缘 + 任何刺激
            if mood_name == "高潮边缘":
                synergy += 1.0  # 翻倍！
                synergy_hints.append("✨【临界状态】她已经到了极限！")

            # 贤者时间 + 高强度动作（负面契合）
            if mood_name == "贤者时间" and action_name in ["推倒", "侵犯", "舔"]:
                synergy -= 0.4
                synergy_hints.append("😴【疲惫不堪】她现在对这些提不起兴趣...")

            # 害羞 + 温柔动作
            if mood_name == "害羞" and action_name in ["牵手", "摸头", "亲 额头", "抱"]:
                synergy += 0.3
                synergy_hints.append("😊【温柔契合】她害羞但很享受")

            # 叛逆 + 强制动作（冲突但刺激）
            if mood_name == "叛逆" and action_name in ["命令", "壁咚", "调教"]:
                synergy += 0.2  # 小加成，因为有抵抗但也兴奋
                synergy_hints.append("😤【叛逆刺激】虽然嘴上不愿，但身体很诚实")

        # === 属性阈值奖励 ===
        arousal = character.get("arousal", 0)
        shame = character.get("shame", 100)
        corruption = character.get("corruption", 0)
        resistance = character.get("resistance", 100)

        # 高兴奋 + 推倒/侵犯（恰到好处的时机）
        if arousal > 80 and action_name in ["推倒", "侵犯"]:
            synergy += 0.3
            synergy_hints.append("⚡【完美时机】她的身体已经准备好了")

        # 低羞耻 + 大胆动作
        if shame < 30 and action_name in ["羞辱", "侵犯", "脱"]:
            synergy += 0.25
            synergy_hints.append("💋【毫无羞耻】她已经不在乎了")

        # 高堕落 + 极端动作
        if corruption > 70 and action_name in ["侵犯", "羞辱"]:
            synergy += 0.3
            synergy_hints.append("😈【深度堕落】她完全接受了")

        # 低抵抗 + 任何动作
        if resistance < 30:
            synergy += 0.2
            synergy_hints.append("🌊【意志崩溃】她已经无法抵抗")

        # === 连续动作Combo ===
        last_action = character.get("last_action", "")

        combo_chains = {
            ("诱惑", "推倒"): (0.4, "🎯【行云流水】完美的进攻节奏！"),
            ("壁咚", "亲"): (0.3, "💕【乘胜追击】趁她慌乱时..."),
            ("抱", "亲"): (0.25, "💗【情到深处】自然而然的进展"),
            ("摸", "亲"): (0.2, "💫【逐步升温】气氛正好"),
            ("亲", "推倒"): (0.35, "🔥【水到渠成】时机已到！"),
            ("调教", "命令"): (0.3, "👑【持续支配】巩固主导地位"),
            ("羞辱", "调教"): (0.4, "😈【步步深入】让她更加顺从")
        }

        for (prev, curr), (bonus, hint) in combo_chains.items():
            if last_action == prev and action_name == curr:
                synergy += bonus
                synergy_hints.append(hint)
                break

        # 保存当前动作供下次combo检查
        character["last_action"] = action_name

        # === 特殊状态加成 ===
        if character.get("sensitivity_increased", False):
            synergy += 0.2
            synergy_hints.append("💡【敏感点刺激】她的弱点被精准攻击")

        # 限制倍率范围 0.5-2.5
        final_synergy = max(0.5, min(2.5, synergy))

        return final_synergy, synergy_hints

    @staticmethod
    def calculate_action_result(
        base_effects: Dict[str, int],
        character: Dict,
        action_name: str,
        mood: Optional[Dict] = None
    ) -> Tuple[Dict[str, int], Optional[str], str]:
        """
        计算动作结果（包含契合度和随机性）
        返回: (最终效果, 特殊消息, 结果类型)
        """
        # === 1. 计算契合度 ===
        synergy, synergy_hints = SurpriseSystem.calculate_synergy(character, action_name, mood)

        # === 2. 应用小幅随机波动（±10%，降低了之前的±20%）===
        effects = {}
        for attr, value in base_effects.items():
            if value != 0:
                fluctuation = random.uniform(0.9, 1.1)  # 减少波动
                effects[attr] = int(value * fluctuation)
            else:
                effects[attr] = value

        # === 3. 应用契合度倍率 ===
        for attr, value in effects.items():
            effects[attr] = int(value * synergy)

        # === 4. 低概率额外暴击（在契合度基础上）===
        extra_critical = None
        if synergy >= 1.5:  # 契合度高时才有机会额外暴击
            if random.random() < 0.05:  # 5%超级暴击
                effects = {k: int(v * 1.5) for k, v in effects.items()}
                extra_critical = "🌟【超级暴击】完美契合 + 幸运加成！"

        # === 5. 检查失败（只在契合度低时）===
        failure_result = None
        if synergy < 0.8:  # 契合度低才可能失败
            failure_result = SurpriseSystem._check_failure(character, action_name, mood)

        if failure_result:
            effects = SurpriseSystem._apply_failure(effects, failure_result)
            return effects, failure_result["message"], "failure"

        # === 6. 构建最终消息 ===
        if extra_critical:
            final_message = extra_critical
            if synergy_hints:
                final_message += "\n" + "\n".join(synergy_hints)
            return effects, final_message, "super_critical"

        if synergy >= 1.8:  # 高契合度
            message = "✨【完美契合】" + (synergy_hints[0] if synergy_hints else "效果拔群！")
            if len(synergy_hints) > 1:
                message += "\n" + "\n".join(synergy_hints[1:])
            return effects, message, "high_synergy"

        if synergy >= 1.3:  # 中等契合
            message = synergy_hints[0] if synergy_hints else None
            return effects, message, "normal_synergy"

        # 普通结果
        return effects, None, "normal"

    @staticmethod
    def _apply_random_fluctuation(base_effects: Dict[str, int]) -> Dict[str, int]:
        """
        应用随机波动 (±20%)
        """
        fluctuated = {}
        for attr, value in base_effects.items():
            if value != 0:
                # ±20%波动
                fluctuation = random.uniform(0.8, 1.2)
                fluctuated[attr] = int(value * fluctuation)
            else:
                fluctuated[attr] = value
        return fluctuated

    @staticmethod
    def _check_critical(character: Dict, mood: Optional[Dict]) -> Optional[Dict]:
        """
        检查是否触发暴击
        """
        # 基础暴击概率
        base_crit_chance = 0.15

        # 情绪加成
        if mood and "critical_probability" in mood.get("effects", {}):
            base_crit_chance += mood["effects"]["critical_probability"]

        # 特定状态加成
        if character.get("sensitivity_increased", False):
            base_crit_chance += 0.1  # 敏感状态+10%

        if character.get("arousal", 0) > 70:
            base_crit_chance += 0.05  # 高兴奋+5%

        # 随机判定
        rand = random.random()

        # 检查史诗暴击 (最稀有)
        if rand < SurpriseSystem.CRITICAL_LEVELS["史诗暴击"]["probability"]:
            level = SurpriseSystem.CRITICAL_LEVELS["史诗暴击"]
            return {
                "level": "史诗暴击",
                "multiplier": level["multiplier"],
                "message": random.choice(level["messages"]),
                "extra_arousal": level.get("extra_arousal", 0),
                "bonus_effects": level.get("bonus_effects", {})
            }

        # 检查大暴击
        if rand < SurpriseSystem.CRITICAL_LEVELS["大暴击"]["probability"]:
            level = SurpriseSystem.CRITICAL_LEVELS["大暴击"]
            return {
                "level": "大暴击",
                "multiplier": level["multiplier"],
                "message": random.choice(level["messages"]),
                "extra_arousal": level.get("extra_arousal", 0),
                "bonus_effects": level.get("bonus_effects", {})
            }

        # 检查普通暴击
        if rand < base_crit_chance:
            level = SurpriseSystem.CRITICAL_LEVELS["普通暴击"]
            return {
                "level": "普通暴击",
                "multiplier": level["multiplier"],
                "message": random.choice(level["messages"]),
                "extra_arousal": level.get("extra_arousal", 0),
                "bonus_effects": level.get("bonus_effects", {})
            }

        return None

    @staticmethod
    def _check_failure(character: Dict, action_name: str, mood: Optional[Dict]) -> Optional[Dict]:
        """
        检查是否触发失败
        """
        # 基础失败概率
        base_fail_chance = 0.05

        # 抵抗力高增加失败率
        if character.get("resistance", 100) > 70:
            base_fail_chance += 0.1

        # 顺从度低增加失败率
        if character.get("submission", 50) < 30:
            base_fail_chance += 0.08

        # 情绪影响
        if mood and "failure_probability" in mood.get("effects", {}):
            base_fail_chance += mood["effects"]["failure_probability"]

        # 亲密度低的高强度动作更容易失败
        high_intensity_actions = ["推倒", "侵犯", "羞辱", "调教"]
        if action_name in high_intensity_actions and character.get("intimacy", 0) < 40:
            base_fail_chance += 0.15

        # 随机判定
        rand = random.random()

        # 检查适得其反 (最严重)
        if rand < SurpriseSystem.FAILURE_LEVELS["适得其反"]["probability"] * base_fail_chance:
            level = SurpriseSystem.FAILURE_LEVELS["适得其反"]
            return {
                "level": "适得其反",
                "multiplier": level["multiplier"],
                "message": random.choice(level["messages"]),
                "negative_effects": level.get("negative_effects", {})
            }

        # 检查明显失败
        if rand < SurpriseSystem.FAILURE_LEVELS["明显失败"]["probability"] * base_fail_chance:
            level = SurpriseSystem.FAILURE_LEVELS["明显失败"]
            return {
                "level": "明显失败",
                "multiplier": level["multiplier"],
                "message": random.choice(level["messages"]),
                "resistance_gain": level.get("resistance_gain", 0)
            }

        # 检查轻微失误
        if rand < base_fail_chance:
            level = SurpriseSystem.FAILURE_LEVELS["轻微失误"]
            return {
                "level": "轻微失误",
                "multiplier": level["multiplier"],
                "message": random.choice(level["messages"])
            }

        return None

    @staticmethod
    def _apply_critical(effects: Dict[str, int], critical_data: Dict) -> Dict[str, int]:
        """应用暴击效果"""
        multiplier = critical_data["multiplier"]
        result = {}

        # 所有正面效果乘以倍率
        for attr, value in effects.items():
            if value > 0:
                result[attr] = int(value * multiplier)
            else:
                # 负面效果也放大（如羞耻心降低更多）
                result[attr] = int(value * multiplier)

        # 额外兴奋度
        if critical_data.get("extra_arousal"):
            result["arousal"] = result.get("arousal", 0) + critical_data["extra_arousal"]

        # 额外奖励效果
        if critical_data.get("bonus_effects"):
            for attr, value in critical_data["bonus_effects"].items():
                result[attr] = result.get(attr, 0) + value

        return result

    @staticmethod
    def _apply_failure(effects: Dict[str, int], failure_data: Dict) -> Dict[str, int]:
        """应用失败效果"""
        multiplier = failure_data["multiplier"]
        result = {}

        # 所有效果乘以失败倍率
        for attr, value in effects.items():
            result[attr] = int(value * multiplier)

        # 抵抗力增加
        if failure_data.get("resistance_gain"):
            result["resistance"] = result.get("resistance", 0) + failure_data["resistance_gain"]

        # 负面效果
        if failure_data.get("negative_effects"):
            for attr, value in failure_data["negative_effects"].items():
                result[attr] = result.get(attr, 0) + value

        return result

    @staticmethod
    def add_random_surprises(character: Dict) -> Optional[str]:
        """
        添加完全随机的惊喜事件（低概率）
        """
        surprises = [
            {
                "probability": 0.03,
                "message": "🎁【意外惊喜】她今天心情特别好，对你格外温柔",
                "effects": {"affection": 10, "trust": 5}
            },
            {
                "probability": 0.02,
                "message": "💝【特殊礼物】她害羞地塞给你一个小礼物",
                "effects": {"affection": 15, "intimacy": 10}
            },
            {
                "probability": 0.02,
                "message": "🌙【月夜效应】今晚的月光格外撩人，她看起来更加迷人",
                "effects": {"arousal": 10, "shame": -5}
            },
            {
                "probability": 0.01,
                "message": "💫【命运邂逅】你们之间的化学反应达到了顶峰",
                "effects": {"intimacy": 20, "arousal": 15, "affection": 15}
            },
            {
                "probability": 0.02,
                "message": "🎵【音乐效果】背景音乐恰好播放到最适合的旋律",
                "effects": {"arousal": 8, "intimacy": 5}
            },
            {
                "probability": 0.015,
                "message": "❄️【心情不佳】她今天似乎有些心事，对你有些冷淡",
                "effects": {"resistance": 10, "arousal": -5}
            },
            {
                "probability": 0.01,
                "message": "🔥【欲火焚身】不知为何，她今天特别容易兴奋",
                "effects": {"arousal": 20, "desire": 15, "resistance": -10}
            }
        ]

        for surprise in surprises:
            if random.random() < surprise["probability"]:
                # 应用效果到角色
                from .attribute_system import AttributeSystem
                for attr, change in surprise["effects"].items():
                    current = character.get(attr, 0)
                    character[attr] = AttributeSystem.clamp(current + change)

                return surprise["message"]

        return None

    @staticmethod
    def calculate_luck_factor(character: Dict) -> float:
        """
        计算幸运因子（影响暴击和失败概率）
        某些状态下更容易暴击/失败
        """
        luck = 1.0

        # 高好感度提升暴击率
        if character.get("affection", 0) > 70:
            luck += 0.2

        # 高抵抗降低暴击率
        if character.get("resistance", 100) > 80:
            luck -= 0.3

        # 特殊状态
        if character.get("sensitivity_increased", False):
            luck += 0.3

        return max(0.5, min(2.0, luck))  # 限制在0.5-2.0倍

    @staticmethod
    def get_combo_bonus(character: Dict) -> Tuple[int, Optional[str]]:
        """
        连续互动奖励（但不会太夸张，避免刷连击）
        """
        interaction_count = character.get("interaction_count", 0)

        # 每10次互动给一次小奖励
        if interaction_count > 0 and interaction_count % 10 == 0:
            return 5, f"🎯【里程碑 {interaction_count} 次互动】你们的关系更进一步！"

        # 每50次大奖励
        if interaction_count > 0 and interaction_count % 50 == 0:
            return 20, f"🏆【重要里程碑 {interaction_count} 次互动！】你们已经非常亲密了！"

        return 0, None

    @staticmethod
    def format_result_message(result_type: str, message: Optional[str], effects: Dict[str, int]) -> str:
        """
        格式化结果消息
        """
        if not message:
            return ""

        # 添加效果预览
        preview_parts = []
        attr_names = {
            "affection": "好感", "intimacy": "亲密", "trust": "信任",
            "submission": "顺从", "desire": "欲望", "corruption": "堕落",
            "arousal": "兴奋", "resistance": "抵抗", "shame": "羞耻"
        }

        for attr, value in effects.items():
            if attr in attr_names and abs(value) >= 5:  # 只显示显著变化
                name = attr_names[attr]
                sign = "+" if value > 0 else ""
                preview_parts.append(f"{name}{sign}{value}")

        if preview_parts:
            message += f"\n[{' | '.join(preview_parts)}]"

        return message
