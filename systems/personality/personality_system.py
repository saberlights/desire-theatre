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
        },
        "gentle": {
            "name": "温柔",
            "description": "温柔体贴，善解人意，容易心软，喜欢照顾他人",
            "base_resistance": 60,
            "base_shame": 70,
            "corruption_rate": 0.7,
            "dialogue_traits": ["温柔", "体贴", "善解人意", "容易心软"],
            "unlockable_traits": [
                {"name": "奉献之心", "condition": {"trust": 60}},
                {"name": "温柔献身", "condition": {"intimacy": 70}},
                {"name": "全心全意", "condition": {"affection": 80, "trust": 70}}
            ]
        },
        "lively": {
            "name": "活泼",
            "description": "开朗活泼，精力充沛，喜欢热闹，容易兴奋",
            "base_resistance": 50,
            "base_shame": 60,
            "corruption_rate": 0.9,
            "dialogue_traits": ["活泼", "开朗", "精力充沛", "容易兴奋"],
            "unlockable_traits": [
                {"name": "好奇心旺盛", "condition": {"desire": 50}},
                {"name": "玩心大发", "condition": {"arousal": 60}},
                {"name": "放飞自我", "condition": {"shame": "<30", "corruption": 60}}
            ]
        },
        "intellectual": {
            "name": "知性",
            "description": "知识渊博，理性冷静，喜欢思考，但内心敏感",
            "base_resistance": 85,
            "base_shame": 85,
            "corruption_rate": 0.6,
            "dialogue_traits": ["知性", "理性", "冷静", "内心敏感"],
            "unlockable_traits": [
                {"name": "理性崩塌", "condition": {"arousal": 70}},
                {"name": "本能觉醒", "condition": {"desire": 75}},
                {"name": "知性沦陷", "condition": {"corruption": 75, "resistance": "<40"}}
            ]
        },
        "yandere": {
            "name": "病娇",
            "description": "表面温柔可爱，但对你有病态的占有欲和依赖",
            "base_resistance": 40,
            "base_shame": 50,
            "corruption_rate": 1.0,
            "dialogue_traits": ["病态", "占有欲强", "极端", "粘人"],
            "unlockable_traits": [
                {"name": "病态依赖", "condition": {"affection": 70}},
                {"name": "独占欲", "condition": {"intimacy": 60, "submission": 50}},
                {"name": "完全疯狂", "condition": {"corruption": 80, "desire": 80}}
            ]
        },
        "kuudere": {
            "name": "无口",
            "description": "沉默寡言，面无表情，但会用行动表达感情",
            "base_resistance": 95,
            "base_shame": 75,
            "corruption_rate": 0.5,
            "dialogue_traits": ["沉默", "面无表情", "行动派", "慢热"],
            "unlockable_traits": [
                {"name": "微笑绽放", "condition": {"affection": 60}},
                {"name": "心防崩溃", "condition": {"trust": 70, "resistance": "<40"}},
                {"name": "情感爆发", "condition": {"intimacy": 80, "arousal": 70}}
            ]
        },
        "oneesan": {
            "name": "姐姐系",
            "description": "成熟温柔，喜欢照顾人，有时会主动诱惑",
            "base_resistance": 50,
            "base_shame": 45,
            "corruption_rate": 0.7,
            "dialogue_traits": ["成熟", "温柔", "主动", "包容"],
            "unlockable_traits": [
                {"name": "母性本能", "condition": {"trust": 60}},
                {"name": "诱惑觉醒", "condition": {"desire": 60, "shame": "<50"}},
                {"name": "反差魅惑", "condition": {"corruption": 70, "submission": "<30"}}
            ]
        },
        "genki": {
            "name": "元气",
            "description": "超级活泼开朗，精力无限，对什么都充满好奇",
            "base_resistance": 30,
            "base_shame": 40,
            "corruption_rate": 1.1,
            "dialogue_traits": ["元气满满", "好奇心强", "天真", "精力充沛"],
            "unlockable_traits": [
                {"name": "好奇探索", "condition": {"desire": 50}},
                {"name": "快乐堕落", "condition": {"corruption": 60, "shame": "<40"}},
                {"name": "玩心失控", "condition": {"arousal": 80, "submission": 60}}
            ]
        },
        "mesugaki": {
            "name": "小恶魔",
            "description": "喜欢挑逗和捉弄人，但其实很容易害羞",
            "base_resistance": 70,
            "base_shame": 80,
            "corruption_rate": 0.8,
            "dialogue_traits": ["挑衅", "傲慢", "捉弄", "嘴硬"],
            "unlockable_traits": [
                {"name": "反被调教", "condition": {"submission": 60}},
                {"name": "傲慢崩坏", "condition": {"resistance": "<30", "arousal": 70}},
                {"name": "彻底驯服", "condition": {"corruption": 75, "shame": "<25"}}
            ]
        },
        "dandere": {
            "name": "文静",
            "description": "极度内向害羞，说话很小声，但对信任的人很依赖",
            "base_resistance": 90,
            "base_shame": 100,
            "corruption_rate": 0.9,
            "dialogue_traits": ["害羞", "内向", "胆小", "依赖性强"],
            "unlockable_traits": [
                {"name": "心扉打开", "condition": {"trust": 70}},
                {"name": "情欲觉醒", "condition": {"desire": 70, "arousal": 60}},
                {"name": "完全献身", "condition": {"intimacy": 85, "submission": 80}}
            ]
        },
        "sadistic": {
            "name": "女王",
            "description": "高傲强势，喜欢支配和控制，享受征服的快感",
            "base_resistance": 20,
            "base_shame": 20,
            "corruption_rate": 0.3,
            "dialogue_traits": ["高傲", "强势", "支配欲", "施虐"],
            "unlockable_traits": [
                {"name": "女王降临", "condition": {"submission": "<20"}},
                {"name": "立场逆转", "condition": {"submission": 50, "corruption": 60}},
                {"name": "调教失败", "condition": {"submission": 80, "resistance": "<20"}}
            ]
        },
        "masochistic": {
            "name": "受虐",
            "description": "喜欢被支配和虐待，从痛苦中获得快感",
            "base_resistance": 10,
            "base_shame": 30,
            "corruption_rate": 1.3,
            "dialogue_traits": ["受虐", "顺从", "渴望痛苦", "易兴奋"],
            "unlockable_traits": [
                {"name": "痛苦快感", "condition": {"arousal": 60, "submission": 60}},
                {"name": "完全臣服", "condition": {"submission": 85}},
                {"name": "堕落深渊", "condition": {"corruption": 90, "shame": "<15"}}
            ]
        },
        "bitch": {
            "name": "淫乱",
            "description": "性欲强烈，主动勾引，享受肉体快感",
            "base_resistance": 5,
            "base_shame": 10,
            "corruption_rate": 1.5,
            "dialogue_traits": ["淫荡", "主动", "饥渴", "无耻"],
            "unlockable_traits": [
                {"name": "欲望失控", "condition": {"desire": 80}},
                {"name": "肉便器化", "condition": {"corruption": 85, "shame": "<10"}},
                {"name": "性爱成瘾", "condition": {"arousal": 90, "corruption": 95}}
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
