"""
选择困境系统 - 强迫二选一的关键时刻

核心机制：在关键时刻强迫玩家做出艰难的选择
- 每个选择都有代价
- 无完美答案，只有权衡
- 选择影响后续发展
"""

import random
from typing import Dict, Tuple, Optional, List

from src.common.logger import get_logger

logger = get_logger("dt_choice_dilemma")


class ChoiceDilemmaSystem:
    """选择困境系统"""

    # 困境事件定义
    DILEMMA_EVENTS = {
        "moral_conflict": {
            "name": "道德困境",
            "trigger_conditions": {
                "desire": (">", 80),
                "corruption": (">", 60),
                "shame": (">", 50),
            },
            "title": "💔 【道德的十字路口】",
            "description": """她颤抖着，眼神里充满矛盾...

"我...我不知道该怎么办..."

她的身体在渴望，但理智在抗拒。
她的欲望在膨胀，但羞耻在煎熬。

你可以看到她内心的挣扎...

现在，你必须做出选择：""",
            "choices": [
                {
                    "id": "satisfy_desire",
                    "text": "满足她的欲望（推进关系）",
                    "description": "顺应她身体的需求，哪怕她理智上还没准备好",
                    "effects": {
                        "desire": 20,
                        "arousal": 15,
                        "corruption": 10,
                        "shame": -20,
                        "trust": -15,
                    },
                    "consequence_text": "你选择了满足她的欲望...她的身体得到了释放，但眼神更加复杂了...",
                    "long_term": "她可能会质疑你是否真的在乎她的感受"
                },
                {
                    "id": "protect_dignity",
                    "text": "保护她的尊严（停下来）",
                    "description": "尊重她的矛盾，即使这意味着压抑欲望",
                    "effects": {
                        "trust": 25,
                        "affection": 15,
                        "desire": -10,
                        "arousal": -20,
                        "frustration": 30,  # 新增：挫败感
                    },
                    "consequence_text": "你选择了保护她的尊严...她感激地看着你，但身体的渴望没有得到满足...",
                    "long_term": "她会更信任你，但可能会因欲望得不到满足而更加焦虑"
                }
            ]
        },

        "trust_crisis": {
            "name": "信任危机",
            "trigger_conditions": {
                "trust": ("<", 30),
                "affection": (">", 50),
            },
            "title": "😢 【她的质问】",
            "description": """她突然停下，眼眶泛红...

"我...我想问你一个问题..."

"你对我...是真心的吗？"

"还是说...我只是你的玩物...？"

她的眼神期待又害怕，等待你的回答：""",
            "choices": [
                {
                    "id": "confess_truth",
                    "text": "坦诚真相（诚实但残酷）",
                    "description": "告诉她真实的想法，无论多么伤人",
                    "effects": {
                        "trust": 30,
                        "affection": -25,
                        "resistance": 20,
                        "corruption": -15,
                    },
                    "consequence_text": "你说出了真相...她的泪水滑落，但眼神变得坚定了...",
                    "long_term": "她知道了真相，虽然痛苦，但至少不是谎言"
                },
                {
                    "id": "comfort_lie",
                    "text": "温柔安抚（善意的谎言）",
                    "description": "告诉她你爱她，即使这可能不完全真实",
                    "effects": {
                        "affection": 20,
                        "trust": -10,
                        "submission": 10,
                        "hidden_doubt": 25,  # 新增：隐藏的怀疑
                    },
                    "consequence_text": "你温柔地安抚她...她靠在你怀里，但眼神里有一丝不确定...",
                    "long_term": "她暂时被安抚了，但内心深处的怀疑会慢慢积累"
                }
            ]
        },

        "promise_deadline": {
            "name": "承诺期限",
            "trigger_conditions": {
                # 需要从记忆系统检查是否有未履行的承诺
            },
            "title": "⏰ 【她在等待】",
            "description": """她看着窗外，轻声说：

"你还记得...你答应过我的事吗？"

"我一直在等..."

她没有转过头，但你能感受到她的期待和失望。

现在你必须决定：""",
            "choices": [
                {
                    "id": "fulfill_promise",
                    "text": "履行承诺（付出巨大代价）",
                    "description": "不管代价多大，兑现你的承诺",
                    "effects": {
                        "trust": 40,
                        "affection": 30,
                        "coins": -200,  # 金币代价
                    },
                    "consequence_text": "你兑现了承诺...虽然付出了很多，但她的眼睛亮了...",
                    "long_term": "她会完全信任你，知道你说到做到"
                },
                {
                    "id": "break_promise",
                    "text": "违背承诺（保留资源）",
                    "description": "找个理由推迟或拒绝，保留你的资源",
                    "effects": {
                        "trust": -40,
                        "affection": -25,
                        "resistance": 25,
                        "coins": 0,
                    },
                    "consequence_text": "你选择了违背承诺...她的眼神暗淡下去，转过身不再看你...",
                    "long_term": "她会记住这次背叛，以后很难再相信你的话"
                }
            ]
        },

        "relationship_fork": {
            "name": "关系分岔点",
            "trigger_conditions": {
                "affection": (">", 70),
                "desire": (">", 70),
                "submission": (">", 60),
            },
            "title": "🌙 【深夜的告白】",
            "description": """深夜，她躺在你身边，突然开口：

"如果...我是说如果..."

"你会娶我吗...？"

空气凝固了。

这不是玩笑，她是认真的。

你该如何回答？""",
            "choices": [
                {
                    "id": "commit_relationship",
                    "text": "承诺关系（认真发展）",
                    "description": "答应她，准备建立真正的关系",
                    "effects": {
                        "affection": 50,
                        "trust": 45,
                        "submission": -20,  # 她不再只是顺从，而是平等伴侣
                        "relationship_status": "committed",
                    },
                    "consequence_text": "你认真地回答了她...她紧紧抱住你，流下了幸福的眼泪...",
                    "long_term": "关系进入新阶段，她不再只是玩伴，而是认真的伴侣"
                },
                {
                    "id": "keep_casual",
                    "text": "保持现状（维持暧昧）",
                    "description": "回避问题，维持现在的暧昧关系",
                    "effects": {
                        "affection": -30,
                        "trust": -25,
                        "resistance": 20,
                        "emotional_distance": 40,  # 新增：情感距离
                    },
                    "consequence_text": "你选择了回避...她沉默了很久，然后轻声说'我知道了'...",
                    "long_term": "她会在心里筑起一道墙，不再对你完全敞开心扉"
                }
            ]
        },

        "sacrifice_demand": {
            "name": "牺牲要求",
            "trigger_conditions": {
                "trust": (">", 80),
                "affection": (">", 75),
            },
            "title": "💐 【她的请求】",
            "description": """她认真地看着你：

"我想...让你为我做一件事..."

"这对你来说可能很困难..."

"但如果你真的爱我，你会答应的，对吗？"

她提出了一个需要你巨大牺牲的请求。

你会如何选择？""",
            "choices": [
                {
                    "id": "make_sacrifice",
                    "text": "做出牺牲（证明爱意）",
                    "description": "答应她的要求，即使代价巨大",
                    "effects": {
                        "affection": 40,
                        "trust": 35,
                        "devotion": 50,  # 新增：献身度
                        "all_attributes": -10,  # 全属性短期下降（疲惫）
                    },
                    "consequence_text": "你为她做出了牺牲...她感动得说不出话，紧紧拥抱着你...",
                    "long_term": "她会永远记住你的牺牲，你在她心中的地位无可替代"
                },
                {
                    "id": "refuse_sacrifice",
                    "text": "拒绝牺牲（保护自己）",
                    "description": "温和地拒绝，保护自己的利益",
                    "effects": {
                        "affection": -20,
                        "trust": -15,
                        "disappointment": 30,  # 新增：失望值
                    },
                    "consequence_text": "你拒绝了她...她试图理解，但眼神里的失望无法掩饰...",
                    "long_term": "她会明白你也有底线，但可能会怀疑你的爱意深度"
                }
            ]
        }
    }

    @staticmethod
    def get_dilemma_by_id(dilemma_id: str) -> Optional[Dict]:
        """
        根据ID获取困境定义

        Args:
            dilemma_id: 困境ID

        Returns:
            困境定义字典，如果不存在则返回None
        """
        return ChoiceDilemmaSystem.DILEMMA_EVENTS.get(dilemma_id)

    @staticmethod
    def check_dilemma_trigger(character: Dict, recent_events: List[Dict] = None) -> Tuple[bool, Optional[Dict]]:
        """
        检查是否触发选择困境

        Args:
            character: 角色数据
            recent_events: 最近的事件列表（用于上下文判断）

        Returns:
            (是否触发, 困境数据)
        """
        # 遍历所有困境类型
        for dilemma_id, dilemma_def in ChoiceDilemmaSystem.DILEMMA_EVENTS.items():
            # 检查触发条件
            if ChoiceDilemmaSystem._check_conditions(character, dilemma_def.get("trigger_conditions", {})):
                # 随机触发（避免过于频繁）
                if random.random() < 0.3:  # 30%概率触发
                    return True, {
                        "dilemma_id": dilemma_id,
                        "title": dilemma_def["title"],
                        "description": dilemma_def["description"],
                        "choices": dilemma_def["choices"],
                        "name": dilemma_def["name"]
                    }

        return False, None

    @staticmethod
    def _check_conditions(character: Dict, conditions: Dict) -> bool:
        """检查触发条件是否满足"""
        for attr, (operator, threshold) in conditions.items():
            char_value = character.get(attr, 0)

            if operator == ">":
                if char_value <= threshold:
                    return False
            elif operator == "<":
                if char_value >= threshold:
                    return False
            elif operator == "==":
                if char_value != threshold:
                    return False
            elif operator == ">=":
                if char_value < threshold:
                    return False
            elif operator == "<=":
                if char_value > threshold:
                    return False

        return True

    @staticmethod
    def apply_choice_consequences(character: Dict, dilemma_id: str, choice_id: str) -> Tuple[Dict, str, str]:
        """
        应用选择的后果

        Args:
            character: 角色数据
            dilemma_id: 困境ID
            choice_id: 选择ID

        Returns:
            (更新后的角色, 后果文本, 长期影响描述)
        """
        dilemma = ChoiceDilemmaSystem.DILEMMA_EVENTS.get(dilemma_id)
        if not dilemma:
            logger.error(f"未知困境: {dilemma_id}")
            return character, "发生错误", ""

        # 找到对应的选择
        choice = None
        for c in dilemma["choices"]:
            if c["id"] == choice_id:
                choice = c
                break

        if not choice:
            logger.error(f"未知选择: {choice_id}")
            return character, "发生错误", ""

        # 应用效果
        from .attribute_system import AttributeSystem

        updated_char = AttributeSystem.apply_changes(character, choice["effects"])

        logger.info(f"应用困境选择: {dilemma_id} -> {choice_id}")

        return updated_char, choice["consequence_text"], choice["long_term"]

    @staticmethod
    def get_dilemma_hint(character: Dict) -> Optional[str]:
        """
        获取困境提示（玩家可以预感即将到来的选择）

        Returns:
            提示文本（如果有潜在困境）
        """
        for dilemma_id, dilemma_def in ChoiceDilemmaSystem.DILEMMA_EVENTS.items():
            conditions = dilemma_def.get("trigger_conditions", {})

            # 检查是否接近触发条件（允许20%的容差）
            close_to_trigger = True
            for attr, (operator, threshold) in conditions.items():
                char_value = character.get(attr, 0)

                if operator == ">":
                    if char_value < threshold * 0.8:  # 达到80%就提示
                        close_to_trigger = False
                        break
                elif operator == "<":
                    if char_value > threshold * 1.2:
                        close_to_trigger = False
                        break

            if close_to_trigger:
                return f"💭 你隐约感觉...一个重要的时刻正在靠近...（{dilemma_def['name']}）"

        return None
