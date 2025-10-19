"""
四季时间和节日系统 - 借鉴《火山女儿》的时间流逝感

核心理念:
- 42天游戏周期按季节划分
- 每个季节有独特的氛围和活动
- 节日触发特殊事件和互动加成
- 增加时间流逝的仪式感
"""

from typing import Dict, Tuple, Optional, List
from datetime import datetime
from src.common.logger import get_logger

logger = get_logger("dt_seasonal")


class SeasonalSystem:
    """四季时间和节日系统"""

    # 季节定义（42天 = 每季10.5天，实际划分为4个季节）
    SEASONS = {
        "spring": {
            "name": "春",
            "emoji": "🌸",
            "day_range": (1, 10),
            "description": "万物复苏的季节，樱花盛开",
            "atmosphere": "温暖、清新、充满希望",
            "bonus": {
                "affection": 1.1,  # 好感度获得+10%
            },
            "special_activities": ["赏樱", "春游", "放风筝"],
            "weather": ["晴天", "微风", "小雨"],
        },
        "summer": {
            "name": "夏",
            "emoji": "☀️",
            "day_range": (11, 21),
            "description": "炎热的季节，阳光灿烂",
            "atmosphere": "热情、活力、激情四射",
            "bonus": {
                "arousal": 1.15,  # 兴奋度获得+15%
                "corruption": 1.1,  # 堕落度获得+10%
            },
            "special_activities": ["海滩", "泳池", "夏日祭", "烟火大会"],
            "weather": ["晴天", "高温", "雷雨"],
        },
        "autumn": {
            "name": "秋",
            "emoji": "🍂",
            "day_range": (22, 32),
            "description": "收获的季节，枫叶染红",
            "atmosphere": "成熟、浪漫、略带感伤",
            "bonus": {
                "intimacy": 1.15,  # 亲密度获得+15%
                "trust": 1.1,  # 信任度获得+10%
            },
            "special_activities": ["赏枫", "温泉", "文化祭"],
            "weather": ["晴天", "凉爽", "秋雨"],
        },
        "winter": {
            "name": "冬",
            "emoji": "❄️",
            "day_range": (33, 42),
            "description": "寒冷的季节，白雪皑皑",
            "atmosphere": "宁静、温馨、依偎取暖",
            "bonus": {
                "intimacy": 1.2,  # 亲密度获得+20%
                "affection": 1.15,  # 好感度获得+15%
            },
            "special_activities": ["滑雪", "温泉", "圣诞约会", "跨年"],
            "weather": ["晴天", "雪天", "寒冷"],
        }
    }

    # 节日定义
    FESTIVALS = {
        # 春季节日
        3: {
            "name": "樱花祭",
            "season": "spring",
            "emoji": "🌸",
            "description": "一年一度的樱花盛开节日",
            "special_dialogue": "樱花树下，她的笑容比花还美...",
            "bonus_effects": {
                "affection": 15,
                "intimacy": 10,
                "mood_gauge": 20,
            },
            "special_activities": ["一起赏樱", "樱花树下告白", "拍樱花照"],
            "festival_type": "romantic",  # 浪漫型节日
        },

        7: {
            "name": "春日野餐",
            "season": "spring",
            "emoji": "🧺",
            "description": "在草地上享受春日阳光",
            "special_dialogue": "她躺在草地上，阳光洒在她脸上...",
            "bonus_effects": {
                "affection": 10,
                "trust": 8,
                "mood_gauge": 15,
            },
            "special_activities": ["野餐", "晒太阳", "放风筝"],
            "festival_type": "casual",
        },

        # 夏季节日
        14: {
            "name": "海滩日",
            "season": "summer",
            "emoji": "🏖️",
            "description": "在海滩度过炎热的一天",
            "special_dialogue": "她穿着泳衣，海风吹拂着她的长发...",
            "bonus_effects": {
                "intimacy": 15,
                "arousal": 12,
                "corruption": 10,
                "shame": -10,
            },
            "special_activities": ["游泳", "沙滩排球", "晒日光浴"],
            "festival_type": "sexy",  # 性感型节日
        },

        17: {
            "name": "夏日祭",
            "season": "summer",
            "emoji": "🎆",
            "description": "传统的夏日庆典，烟火璀璨",
            "special_dialogue": "她穿着浴衣，在烟火下回头看你...",
            "bonus_effects": {
                "affection": 20,
                "intimacy": 15,
                "mood_gauge": 25,
            },
            "special_activities": ["穿浴衣", "逛祭典", "看烟火"],
            "festival_type": "romantic",
        },

        # 秋季节日
        25: {
            "name": "赏月夜",
            "season": "autumn",
            "emoji": "🌕",
            "description": "中秋月圆之夜",
            "special_dialogue": "月光下，你们坐在一起赏月...",
            "bonus_effects": {
                "intimacy": 18,
                "trust": 12,
                "affection": 15,
            },
            "special_activities": ["赏月", "吃月饼", "许愿"],
            "festival_type": "romantic",
        },

        29: {
            "name": "万圣节",
            "season": "autumn",
            "emoji": "🎃",
            "description": "神秘而有趣的万圣节",
            "special_dialogue": "她穿着魔女装扮，对你露出调皮的笑容...",
            "bonus_effects": {
                "intimacy": 12,
                "corruption": 15,
                "shame": -8,
                "mood_gauge": 18,
            },
            "special_activities": ["cosplay", "trick or treat", "鬼屋约会"],
            "festival_type": "playful",  # 俏皮型节日
        },

        # 冬季节日
        36: {
            "name": "圣诞节",
            "season": "winter",
            "emoji": "🎄",
            "description": "温馨的圣诞节",
            "special_dialogue": "圣诞树下，她期待地看着你手中的礼物...",
            "bonus_effects": {
                "affection": 25,
                "intimacy": 20,
                "trust": 15,
                "mood_gauge": 30,
            },
            "special_activities": ["交换礼物", "圣诞约会", "平安夜共度"],
            "festival_type": "romantic",
        },

        42: {
            "name": "跨年夜",
            "season": "winter",
            "emoji": "🎆",
            "description": "游戏的最后一天，新年钟声即将敲响",
            "special_dialogue": "倒数时刻，你们紧紧相拥...",
            "bonus_effects": {
                "affection": 30,
                "intimacy": 25,
                "trust": 20,
            },
            "special_activities": ["跨年倒数", "新年钟声下接吻", "许下愿望"],
            "festival_type": "finale",  # 终章型节日
        },
    }

    @staticmethod
    def get_season_by_day(game_day: int) -> str:
        """根据游戏日获取当前季节"""
        for season_id, season_data in SeasonalSystem.SEASONS.items():
            day_range = season_data["day_range"]
            if day_range[0] <= game_day <= day_range[1]:
                return season_id
        return "spring"  # 默认春季

    @staticmethod
    def get_season_info(game_day: int) -> Dict:
        """获取季节详细信息"""
        season_id = SeasonalSystem.get_season_by_day(game_day)
        return SeasonalSystem.SEASONS.get(season_id, SeasonalSystem.SEASONS["spring"])

    @staticmethod
    def get_festival_by_day(game_day: int) -> Optional[Dict]:
        """检查当天是否有节日"""
        if game_day in SeasonalSystem.FESTIVALS:
            return SeasonalSystem.FESTIVALS[game_day]
        return None

    @staticmethod
    def is_festival_today(game_day: int) -> bool:
        """检查今天是否是节日"""
        return game_day in SeasonalSystem.FESTIVALS

    @staticmethod
    def apply_seasonal_bonus(
        character: Dict,
        attribute_changes: Dict[str, int],
        game_day: int
    ) -> Dict[str, int]:
        """
        应用季节加成到属性变化

        Args:
            character: 角色数据
            attribute_changes: 原始属性变化 {"affection": 10, ...}
            game_day: 游戏日

        Returns:
            应用加成后的属性变化
        """
        season_info = SeasonalSystem.get_season_info(game_day)
        season_bonus = season_info.get("bonus", {})

        modified_changes = attribute_changes.copy()

        for attr, change in attribute_changes.items():
            if attr in season_bonus:
                multiplier = season_bonus[attr]
                modified_changes[attr] = int(change * multiplier)
                logger.info(f"季节加成: {attr} {change} -> {modified_changes[attr]} (x{multiplier})")

        return modified_changes

    @staticmethod
    def get_seasonal_display(game_day: int) -> str:
        """获取季节显示信息"""
        season_info = SeasonalSystem.get_season_info(game_day)
        festival_info = SeasonalSystem.get_festival_by_day(game_day)

        season_text = f"{season_info['emoji']} {season_info['name']}天 - {season_info['description']}"

        if festival_info:
            festival_text = f"\n🎉 【{festival_info['emoji']} {festival_info['name']}】"
            return season_text + festival_text
        else:
            return season_text

    @staticmethod
    def get_festival_notification(game_day: int) -> Optional[str]:
        """
        获取节日通知（在节日当天显示）

        Returns:
            节日通知文本，如果不是节日则返回None
        """
        festival_info = SeasonalSystem.get_festival_by_day(game_day)

        if not festival_info:
            return None

        return f"""
━━━━━━━━━━━━━━━━━━━
🎉 【{festival_info['emoji']} {festival_info['name']}】
━━━━━━━━━━━━━━━━━━━

{festival_info['description']}

{festival_info['special_dialogue']}

✨ 节日加成:
{'  '.join(f'{k}+{v}' for k, v in festival_info['bonus_effects'].items())}

💡 特殊活动:
{'  '.join(f'• {activity}' for activity in festival_info['special_activities'])}

🎁 今天的互动会获得额外加成！
━━━━━━━━━━━━━━━━━━━
""".strip()

    @staticmethod
    def apply_festival_bonus(
        character: Dict,
        attribute_changes: Dict[str, int],
        game_day: int
    ) -> Tuple[Dict[str, int], bool, str]:
        """
        应用节日加成

        Returns:
            (应用加成后的属性变化, 是否是节日, 节日名称)
        """
        festival_info = SeasonalSystem.get_festival_by_day(game_day)

        if not festival_info:
            return attribute_changes, False, ""

        # 节日额外加成（在原有基础上叠加）
        modified_changes = attribute_changes.copy()
        bonus_effects = festival_info.get("bonus_effects", {})

        for attr, bonus in bonus_effects.items():
            if attr in modified_changes:
                # 如果属性已有变化，增加节日加成（取20%）
                modified_changes[attr] += int(bonus * 0.2)
            else:
                # 如果属性没有变化，直接添加节日加成（取全额）
                modified_changes[attr] = bonus

        logger.info(f"节日加成: {festival_info['name']}")

        return modified_changes, True, festival_info['name']

    @staticmethod
    def get_weather(game_day: int) -> Dict:
        """
        获取天气信息（返回包含emoji和描述的字典）

        Returns:
            {"emoji": "☀️", "description": "天气晴朗", "type": "晴天"}
        """
        import random

        season_info = SeasonalSystem.get_season_info(game_day)
        weather_options = season_info.get("weather", ["晴天"])

        # 使用游戏日作为随机种子，确保同一天天气一致
        random.seed(game_day)
        weather_type = random.choice(weather_options)
        random.seed()  # 重置种子

        weather_map = {
            "晴天": {"emoji": "☀️", "description": "天气晴朗"},
            "微风": {"emoji": "🌬️", "description": "微风拂面"},
            "小雨": {"emoji": "🌧️", "description": "淅淅沥沥的小雨"},
            "高温": {"emoji": "🌡️", "description": "天气炎热"},
            "雷雨": {"emoji": "⛈️", "description": "雷雨天气"},
            "凉爽": {"emoji": "🍃", "description": "秋高气爽"},
            "秋雨": {"emoji": "🌧️", "description": "秋雨绵绵"},
            "雪天": {"emoji": "❄️", "description": "漫天飞雪"},
            "寒冷": {"emoji": "🥶", "description": "寒风刺骨"},
        }

        weather_data = weather_map.get(weather_type, {"emoji": "☀️", "description": weather_type})
        weather_data["type"] = weather_type

        return weather_data

    @staticmethod
    def get_weather_description(game_day: int) -> str:
        """
        获取天气描述（根据季节随机）

        Returns:
            天气描述文本
        """
        weather_data = SeasonalSystem.get_weather(game_day)
        return f"{weather_data['emoji']} {weather_data['description']}"

    @staticmethod
    def get_season_transition_message(old_day: int, new_day: int) -> Optional[str]:
        """
        检查是否发生季节转换，返回转换消息

        Returns:
            季节转换消息，如果没有转换则返回None
        """
        old_season = SeasonalSystem.get_season_by_day(old_day)
        new_season = SeasonalSystem.get_season_by_day(new_day)

        if old_season != new_season:
            new_season_info = SeasonalSystem.SEASONS[new_season]
            return f"""
━━━━━━━━━━━━━━━━━━━
🍃 【季节更替】
━━━━━━━━━━━━━━━━━━━

{new_season_info['emoji']} {new_season_info['name']}天到来了

{new_season_info['description']}
{new_season_info['atmosphere']}

✨ 季节加成:
{'  '.join(f'{k}: x{v}' for k, v in new_season_info.get('bonus', {}).items())}

💡 特殊活动:
{'  '.join(f'• {activity}' for activity in new_season_info['special_activities'])}

━━━━━━━━━━━━━━━━━━━
""".strip()

        return None

    @staticmethod
    def get_all_festivals() -> List[Tuple[int, Dict]]:
        """
        获取所有节日列表

        Returns:
            [(游戏日, 节日信息), ...]
        """
        return sorted(SeasonalSystem.FESTIVALS.items())

    @staticmethod
    def get_upcoming_festivals(current_day: int, look_ahead: int = 7) -> List[Tuple[int, Dict]]:
        """
        获取即将到来的节日（未来N天内）

        Args:
            current_day: 当前游戏日
            look_ahead: 查找未来多少天

        Returns:
            [(游戏日, 节日信息), ...]
        """
        upcoming = []

        for festival_day, festival_info in SeasonalSystem.FESTIVALS.items():
            if current_day < festival_day <= current_day + look_ahead:
                upcoming.append((festival_day, festival_info))

        return sorted(upcoming)
