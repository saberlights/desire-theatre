"""
约会活动系统 - 非互动型内容

核心理念:
- 借鉴《火山的女儿》的活动系统
- 消耗行动点，但不消耗每日互动次数
- 主要增加感情属性，较少NSFW内容
- 平衡正常活动和NSFW互动

活动类型:
- 约会活动：电影、餐厅、公园等
- 休闲活动：购物、逛街、游乐场等
- 特殊活动：温泉、海滩、旅行等
"""

from typing import Dict, Tuple, List, Optional
from src.common.logger import get_logger

logger = get_logger("dt_dating_activities")


class DatingActivitySystem:
    """约会活动系统"""

    # 活动定义
    ACTIVITIES = {
        # ===== 日常约会活动 =====
        "movie": {
            "name": "看电影",
            "category": "date",
            "action_cost": 3,          # 消耗行动点
            "coin_cost": 20,           # 消耗金币
            "effects": {
                "affection": 8,
                "intimacy": 5,
                "mood_gauge": 10,
            },
            "unlock_requirement": {},
            "description": "一起看一场浪漫的电影",
            "scene_text": "你们并肩坐在电影院里，她的手不经意间和你的手握在了一起...",
        },

        "restaurant": {
            "name": "高级餐厅",
            "category": "date",
            "action_cost": 4,
            "coin_cost": 30,
            "effects": {
                "affection": 12,
                "trust": 6,
                "mood_gauge": 15,
            },
            "unlock_requirement": {"affection": 30},
            "description": "在高级餐厅享用烛光晚餐",
            "scene_text": "烛光下，她的笑容格外迷人，你们聊了很多，关系更进一步...",
        },

        "park_walk": {
            "name": "公园散步",
            "category": "date",
            "action_cost": 2,
            "coin_cost": 0,
            "effects": {
                "affection": 5,
                "trust": 4,
                "mood_gauge": 8,
            },
            "unlock_requirement": {},
            "description": "在公园里悠闲地散步",
            "scene_text": "午后的阳光很温暖，你们牵着手在公园里散步，聊着日常的琐事...",
        },

        "cafe": {
            "name": "咖啡厅",
            "category": "date",
            "action_cost": 2,
            "coin_cost": 15,
            "effects": {
                "affection": 6,
                "intimacy": 3,
                "mood_gauge": 10,
            },
            "unlock_requirement": {},
            "description": "在咖啡厅里享受悠闲时光",
            "scene_text": "你们坐在咖啡厅的角落，品着咖啡，分享着彼此的故事...",
        },

        # ===== 休闲娱乐活动 =====
        "shopping": {
            "name": "逛街购物",
            "category": "leisure",
            "action_cost": 3,
            "coin_cost": 25,
            "effects": {
                "affection": 7,
                "mood_gauge": 12,
            },
            "unlock_requirement": {},
            "description": "陪她逛街买衣服",
            "scene_text": "她兴奋地试穿各种衣服，每一套都让你眼前一亮...",
        },

        "amusement_park": {
            "name": "游乐场",
            "category": "leisure",
            "action_cost": 5,
            "coin_cost": 40,
            "effects": {
                "affection": 15,
                "intimacy": 8,
                "mood_gauge": 20,
            },
            "unlock_requirement": {"affection": 40},
            "description": "在游乐场度过快乐的一天",
            "scene_text": "摩天轮上，她紧紧抓着你的手，夕阳下她的侧脸美得让人心动...",
        },

        "karaoke": {
            "name": "唱K",
            "category": "leisure",
            "action_cost": 3,
            "coin_cost": 25,
            "effects": {
                "affection": 8,
                "intimacy": 6,
                "mood_gauge": 15,
            },
            "unlock_requirement": {"intimacy": 30},
            "description": "在KTV包厢里唱歌",
            "scene_text": "包厢里只有你们两个人，她唱着情歌，眼神时不时看向你...",
        },

        # ===== 特殊约会活动 =====
        "hot_spring": {
            "name": "温泉旅行",
            "category": "special",
            "action_cost": 6,
            "coin_cost": 60,
            "effects": {
                "affection": 15,
                "intimacy": 15,
                "corruption": 10,
                "shame": -10,
                "mood_gauge": 25,
            },
            "unlock_requirement": {"intimacy": 50, "affection": 50},
            "description": "一起去温泉旅行",
            "scene_text": "在露天温泉里，水汽朦胧中，她的浴巾若隐若现...",
        },

        "beach": {
            "name": "海滩度假",
            "category": "special",
            "action_cost": 7,
            "coin_cost": 70,
            "effects": {
                "affection": 18,
                "intimacy": 12,
                "corruption": 8,
                "shame": -8,
                "mood_gauge": 30,
            },
            "unlock_requirement": {"intimacy": 55, "affection": 55},
            "description": "在海滩度假",
            "scene_text": "她穿着比基尼在沙滩上奔跑，夕阳下的身影美得让人窒息...",
        },

        "hotel_date": {
            "name": "酒店约会",
            "category": "special",
            "action_cost": 5,
            "coin_cost": 50,
            "effects": {
                "affection": 10,
                "intimacy": 20,
                "corruption": 15,
                "mood_gauge": 20,
            },
            "unlock_requirement": {"intimacy": 60, "corruption": 40},
            "description": "在酒店里度过一晚",
            "scene_text": "酒店房间里，气氛变得暧昧起来...",
        },

        # ===== 文化活动 =====
        "art_gallery": {
            "name": "美术馆",
            "category": "culture",
            "action_cost": 3,
            "coin_cost": 20,
            "effects": {
                "affection": 10,
                "trust": 8,
                "mood_gauge": 12,
            },
            "unlock_requirement": {"affection": 35},
            "description": "一起参观美术馆",
            "scene_text": "在艺术作品前，她认真地聆听你的解说，眼中满是崇拜...",
        },

        "concert": {
            "name": "音乐会",
            "category": "culture",
            "action_cost": 4,
            "coin_cost": 50,
            "effects": {
                "affection": 15,
                "intimacy": 8,
                "mood_gauge": 18,
            },
            "unlock_requirement": {"affection": 45},
            "description": "一起听音乐会",
            "scene_text": "美妙的音乐在耳边回荡，她靠在你的肩膀上，享受这份宁静...",
        },
    }

    @staticmethod
    def get_activity(activity_id: str) -> Optional[Dict]:
        """获取活动信息"""
        return DatingActivitySystem.ACTIVITIES.get(activity_id)

    @staticmethod
    def check_can_do_activity(
        character: Dict,
        activity_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        检查是否可以进行活动

        返回: (是否可以, 错误原因)
        """
        activity = DatingActivitySystem.get_activity(activity_id)
        if not activity:
            return False, "活动不存在"

        # 检查行动点
        from ..attributes.action_point_system import ActionPointSystem
        action_cost = activity["action_cost"]
        current_ap = ActionPointSystem.get_current_action_points(character)

        if current_ap < action_cost:
            return False, f"行动点不足（需要{action_cost}点，当前{current_ap}点）"

        # 检查金币
        coin_cost = activity["coin_cost"]
        current_coins = character.get("coins", 0)

        if current_coins < coin_cost:
            return False, f"爱心币不足（需要{coin_cost}币，当前{current_coins}币）"

        # 检查解锁条件
        requirements = activity["unlock_requirement"]
        for attr, required in requirements.items():
            char_value = character.get(attr, 0)
            if char_value < required:
                attr_names = {
                    "affection": "好感度",
                    "intimacy": "亲密度",
                    "corruption": "堕落度"
                }
                return False, f"{attr_names.get(attr, attr)}不足（需要{required}，当前{char_value}）"

        return True, None

    @staticmethod
    def execute_activity(
        character: Dict,
        activity_id: str
    ) -> Tuple[Dict[str, int], int, int, str]:
        """
        执行活动

        返回: (属性变化, 消耗行动点, 消耗金币, 场景文本)
        """
        activity = DatingActivitySystem.get_activity(activity_id)

        # 消耗行动点
        from ..attributes.action_point_system import ActionPointSystem
        action_cost = activity["action_cost"]
        ActionPointSystem.consume_action_points(character, action_cost)

        # 消耗金币
        coin_cost = activity["coin_cost"]
        character["coins"] = character.get("coins", 0) - coin_cost

        # 获取属性效果
        effects = activity["effects"].copy()

        # 返回结果
        scene_text = activity["scene_text"]

        logger.info(f"执行活动: {activity['name']}, 消耗AP:{action_cost}, 金币:{coin_cost}")

        return effects, action_cost, coin_cost, scene_text

    @staticmethod
    def get_available_activities(character: Dict) -> List[Tuple[str, Dict, bool]]:
        """
        获取所有活动列表

        返回: [(活动ID, 活动数据, 是否可用), ...]
        """
        activities = []

        for activity_id, activity_data in DatingActivitySystem.ACTIVITIES.items():
            can_do, _ = DatingActivitySystem.check_can_do_activity(character, activity_id)
            activities.append((activity_id, activity_data, can_do))

        return activities

    @staticmethod
    def get_activity_list_display(character: Dict) -> str:
        """获取活动列表显示"""
        activities = DatingActivitySystem.get_available_activities(character)

        # 按类别分组
        categories = {
            "date": ("💑 约会活动", []),
            "leisure": ("🎮 休闲娱乐", []),
            "special": ("✨ 特殊活动", []),
            "culture": ("🎨 文化活动", [])
        }

        for activity_id, activity_data, can_do in activities:
            category = activity_data["category"]
            name = activity_data["name"]
            action_cost = activity_data["action_cost"]
            coin_cost = activity_data["coin_cost"]

            if can_do:
                status = f"✅ {name} (AP:{action_cost}, 币:{coin_cost})"
            else:
                status = f"🔒 {name} (AP:{action_cost}, 币:{coin_cost})"

            if category in categories:
                categories[category][1].append(status)

        # 构建显示文本
        lines = ["💑 【约会活动列表】\n"]

        for category_name, items in categories.values():
            if items:
                lines.append(f"{category_name}")
                lines.extend(f"  {item}" for item in items)
                lines.append("")

        lines.append("💡 使用 /约会 <活动名> 进行活动")
        lines.append("   活动消耗行动点和金币，不消耗每日互动次数")

        return "\n".join(lines)
