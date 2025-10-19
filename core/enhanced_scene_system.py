"""
增强场景系统 - NSFW向场景效果

核心理念:
- 不同场景影响羞耻度和效果倍率
- 公开场所刺激但高羞耻
- 私密场所安全但刺激度低
- 场景会动态影响互动效果
"""

from typing import Dict, Tuple, List
from src.common.logger import get_logger

logger = get_logger("dt_enhanced_scene")


class EnhancedSceneSystem:
    """增强场景系统"""

    # NSFW向场景定义（按羞耻度/刺激度排序）
    SCENE_EFFECTS = {
        # ===== 私密安全场景 =====
        "bedroom": {
            "name": "卧室",
            "category": "private",
            "shame_modifier": 0,           # 羞耻度修正
            "effect_multiplier": 1.0,      # 效果倍率
            "arousal_bonus": 0,            # 兴奋度加成
            "unlock_requirement": {},
            "description": "私密的个人空间，温馨而安全",
            "special": None
        },

        "living_room": {
            "name": "客厅",
            "category": "semi_private",
            "shame_modifier": 5,
            "effect_multiplier": 1.1,
            "arousal_bonus": 5,
            "unlock_requirement": {},
            "description": "半开放的空间，有被发现的风险",
            "special": "微弱的禁忌感"
        },

        # ===== 半私密刺激场景 =====
        "bathroom": {
            "name": "浴室",
            "category": "semi_private",
            "shame_modifier": 10,
            "effect_multiplier": 1.2,
            "arousal_bonus": 10,
            "unlock_requirement": {"intimacy": 30},
            "description": "水汽弥漫的空间，湿滑而刺激",
            "special": "羞耻降低加速×1.5"
        },

        "balcony": {
            "name": "阳台",
            "category": "semi_public",
            "shame_modifier": 20,
            "effect_multiplier": 1.4,
            "arousal_bonus": 15,
            "unlock_requirement": {"intimacy": 40, "corruption": 30},
            "description": "半开放的空间，邻居可能看到",
            "special": "刺激感显著增加"
        },

        "classroom": {
            "name": "空教室",
            "category": "semi_private",
            "shame_modifier": 15,
            "effect_multiplier": 1.3,
            "arousal_bonus": 12,
            "unlock_requirement": {"intimacy": 35},
            "description": "禁忌的场所，可能有人闯入",
            "special": "禁忌加成"
        },

        # ===== 情趣场所 =====
        "love_hotel": {
            "name": "情人旅馆",
            "category": "private",
            "shame_modifier": 15,
            "effect_multiplier": 1.5,
            "arousal_bonus": 20,
            "unlock_requirement": {"intimacy": 50, "corruption": 40},
            "description": "充满情色氛围的房间",
            "special": "堕落效果×1.5"
        },

        "car": {
            "name": "车内",
            "category": "semi_private",
            "shame_modifier": 18,
            "effect_multiplier": 1.35,
            "arousal_bonus": 15,
            "unlock_requirement": {"intimacy": 45, "corruption": 35},
            "description": "狭窄的密闭空间，窗外是路人",
            "special": "狭窄空间加成"
        },

        # ===== 公共刺激场景 =====
        "park": {
            "name": "公园",
            "category": "public",
            "shame_modifier": 25,
            "effect_multiplier": 1.5,
            "arousal_bonus": 20,
            "unlock_requirement": {"shame": "<40", "corruption": 50},
            "description": "人来人往的公园，随时可能被发现",
            "special": "公开羞耻×2.0"
        },

        "alley": {
            "name": "小巷",
            "category": "semi_public",
            "shame_modifier": 30,
            "effect_multiplier": 1.6,
            "arousal_bonus": 25,
            "unlock_requirement": {"shame": "<30", "corruption": 60},
            "description": "昏暗的小巷，危险而刺激",
            "special": "极限刺激"
        },

        "public_toilet": {
            "name": "公共厕所",
            "category": "semi_public",
            "shame_modifier": 35,
            "effect_multiplier": 1.7,
            "arousal_bonus": 30,
            "unlock_requirement": {"shame": "<25", "corruption": 70},
            "description": "肮脏而刺激的场所",
            "special": "羞耻崩坏加速"
        },

        # ===== 极限场景 =====
        "street": {
            "name": "繁华街道",
            "category": "public",
            "shame_modifier": 40,
            "effect_multiplier": 2.0,
            "arousal_bonus": 40,
            "unlock_requirement": {"shame": "<20", "corruption": 80},
            "description": "人群拥挤的街道，完全暴露",
            "special": "极限公开play"
        },

        "cinema": {
            "name": "电影院",
            "category": "semi_public",
            "shame_modifier": 28,
            "effect_multiplier": 1.6,
            "arousal_bonus": 25,
            "unlock_requirement": {"shame": "<35", "corruption": 55},
            "description": "黑暗的影厅，周围都是观众",
            "special": "黑暗掩护+公开刺激"
        },

        "elevator": {
            "name": "电梯",
            "category": "semi_public",
            "shame_modifier": 32,
            "effect_multiplier": 1.65,
            "arousal_bonus": 28,
            "unlock_requirement": {"shame": "<28", "corruption": 65},
            "description": "狭小的电梯，随时会停靠",
            "special": "紧张刺激"
        },
    }

    @staticmethod
    def get_scene_effect(scene_id: str) -> Dict:
        """获取场景效果"""
        return EnhancedSceneSystem.SCENE_EFFECTS.get(scene_id, EnhancedSceneSystem.SCENE_EFFECTS["bedroom"])

    @staticmethod
    def check_scene_unlocked(scene_id: str, character: Dict) -> Tuple[bool, str]:
        """
        检查场景是否已解锁

        返回: (是否解锁, 未解锁原因)
        """
        scene = EnhancedSceneSystem.SCENE_EFFECTS.get(scene_id)
        if not scene:
            return False, "场景不存在"

        requirements = scene["unlock_requirement"]
        if not requirements:
            return True, ""

        # 检查所有条件
        for attr, required in requirements.items():
            char_value = character.get(attr, 0)

            if isinstance(required, str) and required.startswith("<"):
                # 小于条件
                threshold = int(required[1:])
                if char_value >= threshold:
                    attr_names = {
                        "shame": "羞耻心",
                        "corruption": "堕落度",
                        "intimacy": "亲密度"
                    }
                    return False, f"{attr_names.get(attr, attr)}太高（需要<{threshold}，当前{char_value}）"
            else:
                # 大于等于条件
                threshold = int(required)
                if char_value < threshold:
                    attr_names = {
                        "shame": "羞耻心",
                        "corruption": "堕落度",
                        "intimacy": "亲密度"
                    }
                    return False, f"{attr_names.get(attr, attr)}不足（需要≥{threshold}，当前{char_value}）"

        return True, ""

    @staticmethod
    def apply_scene_effects(base_effects: Dict[str, int], scene_id: str) -> Tuple[Dict[str, int], str]:
        """
        应用场景效果修正

        返回: (修正后的效果, 场景提示消息)
        """
        scene = EnhancedSceneSystem.get_scene_effect(scene_id)

        modified_effects = base_effects.copy()

        # 应用效果倍率
        multiplier = scene["effect_multiplier"]
        for attr, value in modified_effects.items():
            if value > 0:  # 只对正向效果加成
                modified_effects[attr] = int(value * multiplier)

        # 应用羞耻度修正
        shame_mod = scene["shame_modifier"]
        if shame_mod != 0:
            modified_effects["shame"] = modified_effects.get("shame", 0) + shame_mod

        # 应用兴奋度加成
        arousal_bonus = scene["arousal_bonus"]
        if arousal_bonus > 0:
            modified_effects["arousal"] = modified_effects.get("arousal", 0) + arousal_bonus

        # 构建提示消息
        if scene_id == "bedroom":
            hint = ""
        else:
            hint = f"""🏛️ 【{scene['name']}】
{scene['description']}
{'✨ ' + scene['special'] if scene['special'] else ''}
效果倍率: ×{multiplier}"""

        return modified_effects, hint

    @staticmethod
    def get_unlocked_scenes_list(character: Dict) -> List[Tuple[str, str, bool]]:
        """
        获取所有场景列表（包括未解锁）

        返回: [(场景ID, 场景名, 是否解锁), ...]
        """
        scenes = []
        for scene_id, scene_data in EnhancedSceneSystem.SCENE_EFFECTS.items():
            is_unlocked, _ = EnhancedSceneSystem.check_scene_unlocked(scene_id, character)
            scenes.append((scene_id, scene_data["name"], is_unlocked))

        return scenes

    @staticmethod
    def get_scene_list_display(character: Dict) -> str:
        """获取场景列表显示"""
        scenes = EnhancedSceneSystem.get_unlocked_scenes_list(character)

        # 按类别分组
        categories = {
            "private": [],
            "semi_private": [],
            "semi_public": [],
            "public": []
        }

        for scene_id, scene_name, is_unlocked in scenes:
            scene_data = EnhancedSceneSystem.SCENE_EFFECTS[scene_id]
            category = scene_data["category"]

            if is_unlocked:
                status = f"✅ {scene_name}"
            else:
                status = f"🔒 {scene_name}"

            categories[category].append(status)

        # 构建显示文本
        lines = ["🏛️ 【场景列表】\n"]

        if categories["private"]:
            lines.append("【私密场所】")
            lines.extend(f"  {s}" for s in categories["private"])
            lines.append("")

        if categories["semi_private"]:
            lines.append("【半私密场所】")
            lines.extend(f"  {s}" for s in categories["semi_private"])
            lines.append("")

        if categories["semi_public"]:
            lines.append("【半公开场所】")
            lines.extend(f"  {s}" for s in categories["semi_public"])
            lines.append("")

        if categories["public"]:
            lines.append("【公开场所】")
            lines.extend(f"  {s}" for s in categories["public"])
            lines.append("")

        lines.append("💡 使用 /去 <场景名> 切换场景")

        return "\n".join(lines)
