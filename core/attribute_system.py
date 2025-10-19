"""
属性计算系统
"""

from typing import Dict


class AttributeSystem:
    """属性计算系统"""

    @staticmethod
    def clamp(value: int, min_val: int = 0, max_val: int = 100) -> int:
        """限制数值范围"""
        return max(min_val, min(max_val, value))

    @staticmethod
    def calculate_decay(character: Dict, hours_passed: float) -> Dict[str, int]:
        """计算属性衰减

        改进后的衰减机制：
        - 24小时内：不衰减（保护期）
        - 24-48小时：每小时-1%
        - 48-72小时：每小时-2%
        - 72小时+：每小时-3%
        - 最低保底：20%
        """
        decay = {}

        # 24小时保护期
        if hours_passed < 24:
            return decay

        # 计算衰减率
        if hours_passed < 48:
            decay_rate = 0.01  # 1%/小时
        elif hours_passed < 72:
            decay_rate = 0.02  # 2%/小时
        else:
            decay_rate = 0.03  # 3%/小时

        # 超过24小时的时长
        effective_hours = hours_passed - 24

        # 应用衰减到特定属性
        decayable_attrs = {
            "affection": 0.7,    # 好感衰减较慢（70%速率）
            "intimacy": 0.8,     # 亲密度衰减中等（80%速率）
            "desire": 1.0,       # 欲望衰减正常（100%速率）
            "arousal": 1.5,      # 兴奋度衰减最快（150%速率）
        }

        for attr, attr_decay_multiplier in decayable_attrs.items():
            current = character.get(attr, 0)
            if current > 20:  # 保底20
                # 计算衰减量
                max_value = 100
                decayed = int(max_value * decay_rate * effective_hours * attr_decay_multiplier)
                # 不低于保底值
                actual_decay = min(decayed, current - 20)
                if actual_decay > 0:
                    decay[attr] = -actual_decay

        return decay

    @staticmethod
    def calculate_interaction_effects(
        character: Dict,
        action_type: str,
        intensity: int = 5
    ) -> Dict[str, int]:
        """计算互动对属性的影响"""
        changes = {}

        current_submission = character.get("submission", 50)
        current_shame = character.get("shame", 100)
        current_corruption = character.get("corruption", 0)

        if action_type == "gentle":
            # 温柔攻势
            changes["affection"] = intensity * 3
            changes["trust"] = intensity * 2
            changes["arousal"] = intensity * 2
            changes["resistance"] = -intensity * 2

        elif action_type == "dominant":
            # 强势主导
            if current_submission > 70:
                changes["arousal"] = intensity * 5
                changes["resistance"] = -intensity * 4
                changes["submission"] = intensity * 2
            else:
                changes["arousal"] = intensity * 3
                changes["resistance"] = -intensity * 2
                changes["trust"] = -intensity
                changes["shame"] = intensity

        elif action_type == "seductive":
            # 诱惑挑逗
            changes["arousal"] = intensity * 4
            changes["desire"] = intensity * 3
            changes["shame"] = -intensity * 2

        elif action_type == "intimate":
            # 亲密互动
            changes["intimacy"] = intensity * 3
            changes["affection"] = intensity * 2
            changes["arousal"] = intensity * 4
            changes["shame"] = -intensity * 2
            changes["corruption"] = intensity

        elif action_type == "corrupting":
            # 堕落引导
            corruption_multiplier = 1 + (100 - current_shame) / 100
            changes["corruption"] = int(intensity * corruption_multiplier * 3)
            changes["shame"] = -intensity * 4
            changes["resistance"] = -intensity * 3
            changes["arousal"] = intensity * 3

        # 转换为整数并限制范围
        return {k: int(v) for k, v in changes.items()}

    @staticmethod
    def apply_changes(character: Dict, changes: Dict[str, int]) -> Dict:
        """应用属性变化"""
        updated = character.copy()

        for attr, change in changes.items():
            if attr in updated:
                current = updated[attr]
                new_value = AttributeSystem.clamp(current + change)
                updated[attr] = new_value

        return updated
