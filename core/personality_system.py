"""
人格系统
"""

import json
from typing import Dict, List


class PersonalitySystem:
    """人格系统"""

    # 人格模板定义
    PERSONALITIES = {
        "tsundere": {
            "name": "傲娇",
            "description": "表面高傲但内心害羞，容易脸红，嘴硬心软",
            "base_resistance": 80,
            "base_shame": 90,
            "corruption_rate": 0.5,
            "dialogue_traits": ["傲娇", "嘴硬", "容易脸红", "反差萌"],
            "unlockable_traits": [
                {"name": "口嫌体正直", "condition": {"submission": 60}},
                {"name": "身体很诚实", "condition": {"corruption": 40}},
                {"name": "完全沦陷", "condition": {"corruption": 80, "submission": 80}}
            ]
        },
        "innocent": {
            "name": "天真无邪",
            "description": "纯洁天真，对一切都充满好奇，容易被引导",
            "base_resistance": 90,
            "base_shame": 95,
            "corruption_rate": 1.2,
            "dialogue_traits": ["天真", "好奇", "不懂装懂", "容易被骗"],
            "unlockable_traits": [
                {"name": "懵懂觉醒", "condition": {"corruption": 30}},
                {"name": "堕落反差", "condition": {"corruption": 60}},
                {"name": "彻底染色", "condition": {"corruption": 90}}
            ]
        },
        "seductive": {
            "name": "妖媚",
            "description": "主动诱惑，懂得如何挑逗，享受掌控感",
            "base_resistance": 30,
            "base_shame": 40,
            "corruption_rate": 0.3,
            "dialogue_traits": ["主动", "挑逗", "魅惑", "懂得诱惑"],
            "unlockable_traits": [
                {"name": "反客为主", "condition": {"submission": "<30"}},
                {"name": "女王范", "condition": {"submission": "<20", "corruption": 60}},
                {"name": "完全主导", "condition": {"submission": "<10"}}
            ]
        },
        "shy": {
            "name": "害羞内向",
            "description": "极度害羞，说话小声，容易紧张，但内心渴望",
            "base_resistance": 95,
            "base_shame": 100,
            "corruption_rate": 0.8,
            "dialogue_traits": ["害羞", "小声说话", "容易紧张", "内心渴望"],
            "unlockable_traits": [
                {"name": "小鹿乱撞", "condition": {"arousal": 60}},
                {"name": "压抑爆发", "condition": {"desire": 80}},
                {"name": "沉迷快乐", "condition": {"corruption": 70}}
            ]
        },
        "cold": {
            "name": "冷淡高冷",
            "description": "表面冷漠，难以接近，但一旦突破防线会产生巨大反差",
            "base_resistance": 100,
            "base_shame": 80,
            "corruption_rate": 0.4,
            "dialogue_traits": ["冷淡", "不苟言笑", "难以接近", "反差巨大"],
            "unlockable_traits": [
                {"name": "冰山融化", "condition": {"affection": 70}},
                {"name": "克制崩塌", "condition": {"resistance": "<30"}},
                {"name": "彻底臣服", "condition": {"submission": 90}}
            ]
        }
    }

    @staticmethod
    def get_personality(personality_type: str) -> Dict:
        """获取人格模板"""
        return PersonalitySystem.PERSONALITIES.get(
            personality_type,
            PersonalitySystem.PERSONALITIES["tsundere"]
        )

    @staticmethod
    def check_trait_unlocks(character: Dict) -> List[str]:
        """检查可解锁的特质"""
        personality_type = character.get("personality_type", "tsundere")
        personality = PersonalitySystem.get_personality(personality_type)

        current_traits = json.loads(character.get("personality_traits", "[]"))
        newly_unlocked = []

        for trait_def in personality.get("unlockable_traits", []):
            trait_name = trait_def["name"]

            # 如果已解锁，跳过
            if trait_name in current_traits:
                continue

            # 检查解锁条件
            conditions = trait_def["condition"]
            all_met = True

            for attr, required in conditions.items():
                if isinstance(required, str) and required.startswith("<"):
                    # 小于条件
                    threshold = int(required[1:])
                    if character.get(attr, 0) >= threshold:
                        all_met = False
                        break
                else:
                    # 大于等于条件
                    threshold = int(required)
                    if character.get(attr, 0) < threshold:
                        all_met = False
                        break

            if all_met:
                newly_unlocked.append(trait_name)

        return newly_unlocked

    @staticmethod
    def get_evolution_stage(character: Dict) -> int:
        """根据属性判断进化阶段"""
        corruption = character.get("corruption", 0)
        submission = character.get("submission", 50)
        intimacy = character.get("intimacy", 0)

        # 阶段判定
        if corruption >= 80 and submission >= 70:
            return 5  # 完全堕落
        elif corruption >= 60 or submission >= 60:
            return 4  # 深度开发
        elif corruption >= 40 or intimacy >= 60:
            return 3  # 关系深化
        elif intimacy >= 30:
            return 2  # 初步接触
        else:
            return 1  # 初识
