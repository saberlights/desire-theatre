"""
属性冲突系统 - 处理属性之间的制约和协同关系
让属性不再是独立增长，而是相互影响
"""

from typing import Dict, List, Tuple


class AttributeConflictSystem:
    """属性冲突与协同系统"""

    # 属性制约规则 - 某些属性会抑制其他属性的增长
    CONFLICT_RULES = {
        # 羞耻心制约堕落度和欲望
        "shame": {
            "suppresses": {
                "corruption": {
                    "threshold": 60,  # 羞耻心>60时开始抑制
                    "reduction_rate": 0.3,  # 减少30%堕落度增长
                    "description": "💫 羞耻心抑制了堕落的进展"
                },
                "desire": {
                    "threshold": 70,
                    "reduction_rate": 0.25,
                    "description": "😳 羞耻心压抑了欲望的增长"
                }
            }
        },

        # 抵抗力制约顺从度和堕落度
        "resistance": {
            "suppresses": {
                "submission": {
                    "threshold": 70,
                    "reduction_rate": 0.4,
                    "description": "🛡️ 强烈的抵抗意志减缓了顺从"
                },
                "corruption": {
                    "threshold": 65,
                    "reduction_rate": 0.3,
                    "description": "⚔️ 抵抗力阻碍了堕落"
                }
            }
        },

        # 信任度制约抵抗力（信任高则抵抗低）
        "trust": {
            "suppresses": {
                "resistance": {
                    "threshold": 70,
                    "reduction_rate": 0.5,  # 高信任大幅降低抵抗增长
                    "description": "🤝 深厚的信任瓦解了抵抗",
                    "reverse": True  # 反向制约：信任高时，抵抗增长被抑制
                }
            }
        },

        # 堕落度制约羞耻心（堕落后羞耻心难以恢复）
        "corruption": {
            "suppresses": {
                "shame": {
                    "threshold": 50,
                    "reduction_rate": 0.6,  # 大幅减少羞耻心恢复
                    "description": "😈 堕落侵蚀了羞耻心",
                    "reverse": True  # 只抑制羞耻心的增长（恢复）
                }
            }
        },

        # 顺从度制约抵抗力
        "submission": {
            "suppresses": {
                "resistance": {
                    "threshold": 60,
                    "reduction_rate": 0.45,
                    "description": "🙇 顺从削弱了反抗的意志",
                    "reverse": True
                }
            }
        }
    }

    # 属性协同规则 - 某些属性组合会增强效果
    SYNERGY_RULES = {
        # 好感+信任 = 亲密度加成
        ("affection", "trust"): {
            "target": "intimacy",
            "condition": lambda char: char.get("affection", 0) > 60 and char.get("trust", 0) > 60,
            "bonus_multiplier": 1.3,
            "description": "💕【情投意合】好感与信任的结合加速了亲密"
        },

        # 欲望+兴奋 = 堕落度加成
        ("desire", "arousal"): {
            "target": "corruption",
            "condition": lambda char: char.get("desire", 0) > 50 and char.get("arousal", 0) > 60,
            "bonus_multiplier": 1.4,
            "description": "🔥【欲火焚身】欲望与兴奋共同推动堕落"
        },

        # 顺从+堕落 = 羞耻心大幅下降加成
        ("submission", "corruption"): {
            "target": "shame",
            "condition": lambda char: char.get("submission", 0) > 55 and char.get("corruption", 0) > 50,
            "bonus_multiplier": 1.5,
            "description": "😈【完全沉沦】顺从与堕落加速了羞耻心的崩溃",
            "only_negative": True  # 只增强负向变化
        },

        # 亲密+好感 = 信任度加成
        ("intimacy", "affection"): {
            "target": "trust",
            "condition": lambda char: char.get("intimacy", 0) > 50 and char.get("affection", 0) > 60,
            "bonus_multiplier": 1.25,
            "description": "💗【深厚情感】亲密与好感强化了信任"
        },

        # 堕落+顺从 = 抵抗力大幅下降加成
        ("corruption", "submission"): {
            "target": "resistance",
            "condition": lambda char: char.get("corruption", 0) > 50 and char.get("submission", 0) > 60,
            "bonus_multiplier": 1.6,
            "description": "🌊【意志崩溃】堕落与顺从摧毁了最后的抵抗",
            "only_negative": True
        }
    }

    # 属性阈值触发的被动效果
    THRESHOLD_EFFECTS = {
        # 极高羞耻心会降低所有负面属性的增长
        "shame": [
            {
                "threshold": 85,
                "effects": {
                    "corruption_growth": -0.3,
                    "desire_growth": -0.2,
                    "arousal_growth": -0.15
                },
                "description": "💫【纯洁之心】极高的羞耻心保护着她"
            }
        ],

        # 极低羞耻心会加速堕落
        "shame_low": [
            {
                "threshold": 20,
                "effects": {
                    "corruption_growth": 0.3,
                    "desire_growth": 0.2
                },
                "description": "😈【羞耻全失】失去羞耻心后变得更加放纵"
            }
        ],

        # 极高抵抗力会降低所有负面影响
        "resistance": [
            {
                "threshold": 85,
                "effects": {
                    "submission_growth": -0.4,
                    "corruption_growth": -0.25,
                    "shame_decay": -0.3
                },
                "description": "⚔️【钢铁意志】强大的抵抗力保护着她的心智"
            }
        ],

        # 极高信任会降低抵抗增长
        "trust": [
            {
                "threshold": 80,
                "effects": {
                    "resistance_growth": -0.5
                },
                "description": "🤝【完全信任】深厚的信任让她不再设防"
            }
        ],

        # 极高堕落度会自动降低羞耻心
        "corruption": [
            {
                "threshold": 75,
                "effects": {
                    "shame_decay": 0.3,
                    "resistance_decay": 0.2
                },
                "description": "😈【深度堕落】堕落正在侵蚀她的理智"
            }
        ]
    }

    @staticmethod
    def apply_conflict_modifiers(
        character: Dict,
        effects: Dict[str, int]
    ) -> Tuple[Dict[str, int], List[str]]:
        """
        应用属性冲突修正
        返回: (修正后的效果, 提示消息列表)
        """
        modified_effects = effects.copy()
        messages = []

        # === 1. 应用制约规则 ===
        for suppressor_attr, rules in AttributeConflictSystem.CONFLICT_RULES.items():
            suppressor_value = character.get(suppressor_attr, 0)

            for target_attr, rule in rules["suppresses"].items():
                if suppressor_value > rule["threshold"]:
                    # 检查是否有该属性的变化
                    if target_attr in modified_effects:
                        change = modified_effects[target_attr]
                        is_reverse = rule.get("reverse", False)

                        # 正常制约：抑制目标属性的正向增长
                        # 反向制约：抑制目标属性的负向增长（即恢复）
                        if (not is_reverse and change > 0) or (is_reverse and change > 0):
                            # 应用减少率
                            reduction = int(change * rule["reduction_rate"])
                            modified_effects[target_attr] = change - reduction

                            if reduction > 0:
                                messages.append(rule["description"] + f" ({target_attr} -{reduction})")

        # === 2. 应用协同规则 ===
        for (attr1, attr2), synergy in AttributeConflictSystem.SYNERGY_RULES.items():
            if synergy["condition"](character):
                target_attr = synergy["target"]

                if target_attr in modified_effects:
                    change = modified_effects[target_attr]
                    only_negative = synergy.get("only_negative", False)

                    # 只增强负向变化 或 增强所有变化
                    if (only_negative and change < 0) or (not only_negative and change != 0):
                        bonus_multiplier = synergy["bonus_multiplier"]
                        bonus = int(change * (bonus_multiplier - 1.0))

                        modified_effects[target_attr] = change + bonus

                        if abs(bonus) > 0:
                            messages.append(synergy["description"] + f" ({target_attr} {'+' if bonus > 0 else ''}{bonus})")

        # === 3. 应用阈值被动效果 ===
        threshold_messages = AttributeConflictSystem._apply_threshold_effects(character, modified_effects)
        messages.extend(threshold_messages)

        return modified_effects, messages

    @staticmethod
    def _apply_threshold_effects(
        character: Dict,
        effects: Dict[str, int]
    ) -> List[str]:
        """应用属性阈值触发的被动效果"""
        messages = []

        # 检查普通属性阈值
        for attr, threshold_list in AttributeConflictSystem.THRESHOLD_EFFECTS.items():
            if attr.endswith("_low"):
                # 低阈值检查（羞耻心过低等）
                base_attr = attr.replace("_low", "")
                char_value = character.get(base_attr, 100)

                for threshold_data in threshold_list:
                    if char_value < threshold_data["threshold"]:
                        messages.append(threshold_data["description"])
                        # 应用效果修正
                        AttributeConflictSystem._apply_growth_modifiers(
                            effects, threshold_data["effects"]
                        )
                        break  # 只触发第一个满足的阈值
            else:
                # 高阈值检查
                char_value = character.get(attr, 0)

                for threshold_data in threshold_list:
                    if char_value > threshold_data["threshold"]:
                        messages.append(threshold_data["description"])
                        AttributeConflictSystem._apply_growth_modifiers(
                            effects, threshold_data["effects"]
                        )
                        break

        return messages

    @staticmethod
    def _apply_growth_modifiers(effects: Dict[str, int], modifiers: Dict[str, float]):
        """应用成长修正器"""
        for modifier_key, modifier_value in modifiers.items():
            if modifier_key.endswith("_growth"):
                # 例如 "corruption_growth": -0.3 表示减少30%堕落度增长
                target_attr = modifier_key.replace("_growth", "")
                if target_attr in effects and effects[target_attr] > 0:
                    reduction = int(effects[target_attr] * abs(modifier_value))
                    if modifier_value < 0:
                        effects[target_attr] -= reduction
                    else:
                        effects[target_attr] += reduction

            elif modifier_key.endswith("_decay"):
                # 例如 "shame_decay": 0.3 表示增加30%羞耻心衰减（下降更快）
                target_attr = modifier_key.replace("_decay", "")
                if target_attr in effects and effects[target_attr] < 0:
                    increase = int(abs(effects[target_attr]) * abs(modifier_value))
                    if modifier_value > 0:
                        effects[target_attr] -= increase  # 更负
                    else:
                        effects[target_attr] += increase  # 不那么负

    @staticmethod
    def check_conflict_warnings(character: Dict) -> List[str]:
        """
        检查并返回属性冲突警告
        例如：高羞耻心+高堕落度会产生矛盾
        """
        warnings = []

        shame = character.get("shame", 100)
        corruption = character.get("corruption", 0)
        resistance = character.get("resistance", 100)
        submission = character.get("submission", 50)
        trust = character.get("trust", 50)

        # 高羞耻心 + 高堕落度 = 内心矛盾
        if shame > 60 and corruption > 50:
            warnings.append("⚠️【内心矛盾】她在羞耻与堕落之间挣扎，心理压力很大")

        # 高抵抗 + 高顺从 = 人格分裂倾向
        if resistance > 70 and submission > 60:
            warnings.append("⚠️【人格撕裂】抵抗与顺从的冲突正在撕裂她的意志")

        # 低信任 + 高亲密 = 不健康关系
        if trust < 40 and character.get("intimacy", 0) > 60:
            warnings.append("⚠️【扭曲关系】缺乏信任的亲密关系可能导致不良后果")

        # 极低羞耻心 + 极高堕落 = 完全沉沦警告
        if shame < 20 and corruption > 80:
            warnings.append("🚨【完全沉沦】她已经彻底堕落，几乎不再抗拒任何事")

        return warnings

    @staticmethod
    def suggest_balanced_actions(character: Dict) -> List[str]:
        """
        根据当前属性冲突，建议平衡性动作
        """
        suggestions = []

        shame = character.get("shame", 100)
        corruption = character.get("corruption", 0)
        resistance = character.get("resistance", 100)
        trust = character.get("trust", 50)

        # 高羞耻心阻碍进展 -> 建议降羞耻
        if shame > 70 and corruption < 30:
            suggestions.append("💡 建议：羞耻心过高，尝试 /诱惑 /挑逗 来降低羞耻心")

        # 高抵抗阻碍进展 -> 建议降抵抗
        if resistance > 75:
            suggestions.append("💡 建议：抵抗力过高，尝试 /抱 /亲 等温柔动作降低抵抗")

        # 低信任阻碍深度互动 -> 建议提升信任
        if trust < 40 and character.get("intimacy", 0) > 40:
            suggestions.append("💡 建议：信任度不足，尝试 /聊天 /帮助 /送礼 建立信任")

        return suggestions
