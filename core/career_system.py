"""
职业养成系统 - 借鉴《火山女儿》的职业成长路线

核心理念:
- 角色有职业身份和成长路线
- 职业影响收入、属性和剧情
- 职业发展影响结局
- 增加养成深度和长期目标
"""

from typing import Dict, Tuple, Optional, List
from src.common.logger import get_logger

logger = get_logger("dt_career")


class CareerSystem:
    """职业养成系统"""

    # 职业路线定义
    CAREERS = {
        # ========== 学生系 ==========
        "high_school_student": {
            "name": "高中生",
            "category": "student",
            "emoji": "🎓",
            "description": "正在读高中的学生",
            "base_income": 10,  # 每天基础收入（零用钱）
            "attribute_effects": {
                "shame": 5,  # 学生身份羞耻感较高
            },
            "next_stages": ["college_student", "part_time_worker"],
            "stage_requirements": {
                "college_student": {"game_day": 15, "intelligence": 60},
                "part_time_worker": {"game_day": 10},
            },
            "special_interactions": ["课后补习", "放学后约会", "体育祭"],
        },

        "college_student": {
            "name": "大学生",
            "category": "student",
            "emoji": "🎓",
            "description": "正在读大学",
            "base_income": 15,
            "attribute_effects": {
                "shame": 0,  # 大学生更开放
                "corruption": -5,  # 基础堕落降低
            },
            "next_stages": ["office_worker", "freelancer", "graduate_student"],
            "stage_requirements": {
                "office_worker": {"game_day": 25},
                "freelancer": {"game_day": 25, "creativity": 50},
                "graduate_student": {"game_day": 25, "intelligence": 70},
            },
            "special_interactions": ["社团活动", "打工", "宿舍", "图书馆约会"],
        },

        # ========== 职场系 ==========
        "office_worker": {
            "name": "普通职员",
            "category": "career",
            "emoji": "💼",
            "description": "朝九晚五的上班族",
            "base_income": 40,
            "attribute_effects": {},
            "next_stages": ["senior_staff", "manager"],
            "stage_requirements": {
                "senior_staff": {"game_day": 30, "professionalism": 60},
                "manager": {"game_day": 35, "professionalism": 80, "leadership": 60},
            },
            "special_interactions": ["加班", "出差", "公司聚会", "办公室恋情"],
        },

        "senior_staff": {
            "name": "资深职员",
            "category": "career",
            "emoji": "💼",
            "description": "经验丰富的职场人",
            "base_income": 60,
            "attribute_effects": {},
            "next_stages": ["manager", "specialist"],
            "stage_requirements": {
                "manager": {"game_day": 38, "leadership": 70},
                "specialist": {"game_day": 38, "professionalism": 90},
            },
            "special_interactions": ["项目主导", "带新人", "商务谈判"],
        },

        "manager": {
            "name": "部门经理",
            "category": "career",
            "emoji": "👔",
            "description": "管理团队的中层领导",
            "base_income": 100,
            "attribute_effects": {
                "confidence": 10,
            },
            "next_stages": [],  # 终点职业
            "stage_requirements": {},
            "special_interactions": ["管理团队", "高层会议", "决策权"],
        },

        # ========== 自由职业系 ==========
        "freelancer": {
            "name": "自由职业者",
            "category": "freelance",
            "emoji": "💻",
            "description": "时间自由的创作者",
            "base_income": 30,  # 收入不稳定
            "attribute_effects": {
                "freedom": 10,
            },
            "next_stages": ["successful_freelancer", "entrepreneur"],
            "stage_requirements": {
                "successful_freelancer": {"game_day": 30, "creativity": 70},
                "entrepreneur": {"game_day": 35, "creativity": 60, "leadership": 60},
            },
            "special_interactions": ["接外包", "咖啡厅创作", "灵活时间"],
        },

        "successful_freelancer": {
            "name": "成功自由职业者",
            "category": "freelance",
            "emoji": "✨",
            "description": "有固定客户的知名创作者",
            "base_income": 80,
            "attribute_effects": {
                "confidence": 8,
                "freedom": 15,
            },
            "next_stages": ["entrepreneur"],
            "stage_requirements": {
                "entrepreneur": {"game_day": 40, "leadership": 70},
            },
            "special_interactions": ["大项目", "展览/发布会", "采访"],
        },

        # ========== 特殊职业系 ==========
        "idol": {
            "name": "偶像",
            "category": "entertainment",
            "emoji": "🌟",
            "description": "光鲜亮丽的娱乐圈偶像",
            "base_income": 70,
            "attribute_effects": {
                "shame": -10,  # 需要在众人面前表演
                "corruption": 5,  # 娱乐圈诱惑多
            },
            "next_stages": ["top_idol"],
            "stage_requirements": {
                "top_idol": {"game_day": 35, "charm": 90, "performance": 80},
            },
            "special_interactions": ["演出", "握手会", "拍摄", "粉丝见面"],
        },

        "model": {
            "name": "模特",
            "category": "entertainment",
            "emoji": "📸",
            "description": "时尚界的宠儿",
            "base_income": 50,
            "attribute_effects": {
                "shame": -15,  # 需要穿各种服装拍照
                "confidence": 5,
            },
            "next_stages": ["top_model"],
            "stage_requirements": {
                "top_model": {"game_day": 32, "charm": 85, "confidence": 70},
            },
            "special_interactions": ["拍摄", "走秀", "试镜", "时装周"],
        },

        "streamer": {
            "name": "主播",
            "category": "entertainment",
            "emoji": "🎥",
            "description": "直播赚钱的网红",
            "base_income": 35,
            "attribute_effects": {
                "shame": -8,
            },
            "next_stages": ["top_streamer"],
            "stage_requirements": {
                "top_streamer": {"game_day": 28, "charm": 70, "popularity": 80},
            },
            "special_interactions": ["直播", "打赏", "粉丝互动", "联动"],
        },

        # ========== 成人向职业系 ==========
        "part_time_worker": {
            "name": "兼职工",
            "category": "service",
            "emoji": "👗",
            "description": "在服务行业打工",
            "base_income": 25,
            "attribute_effects": {},
            "next_stages": ["hostess", "office_worker"],
            "stage_requirements": {
                "hostess": {"game_day": 15, "charm": 50, "corruption": 30},
                "office_worker": {"game_day": 20},
            },
            "special_interactions": ["上班", "顾客骚扰", "加班"],
        },

        "hostess": {
            "name": "陪酒女郎",
            "category": "adult",
            "emoji": "🍷",
            "description": "在夜店陪酒的女孩",
            "base_income": 60,
            "attribute_effects": {
                "corruption": 10,
                "shame": -10,
            },
            "next_stages": ["high_class_escort"],
            "stage_requirements": {
                "high_class_escort": {"game_day": 25, "charm": 80, "corruption": 60},
            },
            "special_interactions": ["陪酒", "被骚扰", "潜规则", "包养提议"],
        },

        "high_class_escort": {
            "name": "高级陪侍",
            "category": "adult",
            "emoji": "💎",
            "description": "服务富豪的高级陪侍",
            "base_income": 120,
            "attribute_effects": {
                "corruption": 20,
                "shame": -20,
                "submission": 5,
            },
            "next_stages": [],  # 终点职业
            "stage_requirements": {},
            "special_interactions": ["高端派对", "私人服务", "奢华生活"],
        },
    }

    # 职业属性定义（影响职业发展）
    CAREER_ATTRIBUTES = {
        "intelligence": "智力",
        "creativity": "创造力",
        "charm": "魅力",
        "professionalism": "专业度",
        "leadership": "领导力",
        "performance": "表演力",
        "confidence": "自信",
        "freedom": "自由度",
        "popularity": "人气",
    }

    @staticmethod
    def get_career_info(career_id: str) -> Optional[Dict]:
        """获取职业信息"""
        return CareerSystem.CAREERS.get(career_id)

    @staticmethod
    def initialize_career(character: Dict, career_id: str = "high_school_student") -> Dict:
        """初始化职业"""
        character["career"] = career_id
        character["career_day"] = 0  # 从事该职业的天数

        # 初始化职业属性
        for attr in CareerSystem.CAREER_ATTRIBUTES.keys():
            if attr not in character:
                character[attr] = 0

        logger.info(f"初始化职业: {career_id}")
        return character

    @staticmethod
    def daily_income(character: Dict) -> int:
        """获取每日收入"""
        career_id = character.get("career", "high_school_student")
        career_info = CareerSystem.get_career_info(career_id)

        if not career_info:
            return 0

        base_income = career_info["base_income"]

        # 根据职业属性调整收入
        category = career_info["category"]
        bonus_multiplier = 1.0

        if category == "freelance":
            # 自由职业收入受创造力影响
            creativity = character.get("creativity", 0)
            bonus_multiplier = 1.0 + (creativity / 100) * 0.5

        elif category == "entertainment":
            # 娱乐行业收入受魅力和人气影响
            charm = character.get("charm", 0)
            popularity = character.get("popularity", 0)
            bonus_multiplier = 1.0 + ((charm + popularity) / 200) * 0.8

        elif category == "career":
            # 职场收入受专业度影响
            professionalism = character.get("professionalism", 0)
            bonus_multiplier = 1.0 + (professionalism / 100) * 0.3

        final_income = int(base_income * bonus_multiplier)
        logger.info(f"每日收入: {final_income} (基础{base_income} x {bonus_multiplier:.2f})")

        return final_income

    @staticmethod
    def check_promotion(character: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        检查是否可以晋升

        Returns:
            (是否可以晋升, 新职业ID, 晋升描述)
        """
        current_career = character.get("career", "")
        career_info = CareerSystem.get_career_info(current_career)

        if not career_info:
            return False, None, None

        next_stages = career_info.get("next_stages", [])
        if not next_stages:
            return False, None, None  # 已经是终点职业

        # 检查所有可能的晋升路线
        for next_career_id in next_stages:
            requirements = career_info["stage_requirements"].get(next_career_id, {})

            # 检查是否满足所有要求
            all_met = True
            for attr, required in requirements.items():
                char_value = character.get(attr, 0)
                if char_value < required:
                    all_met = False
                    break

            if all_met:
                next_career_info = CareerSystem.get_career_info(next_career_id)
                promotion_text = f"""
🎉 【职业晋升】

{career_info['emoji']} {career_info['name']}
    ↓
{next_career_info['emoji']} {next_career_info['name']}

{next_career_info['description']}

💰 每日收入: {career_info['base_income']} → {next_career_info['base_income']}

✨ 解锁新互动: {', '.join(next_career_info['special_interactions'])}
""".strip()

                return True, next_career_id, promotion_text

        return False, None, None

    @staticmethod
    def promote(character: Dict, new_career_id: str) -> Dict:
        """执行晋升"""
        character["career"] = new_career_id
        character["career_day"] = 0
        logger.info(f"晋升到: {new_career_id}")
        return character

    @staticmethod
    def get_career_display(character: Dict) -> str:
        """获取职业显示信息"""
        career_id = character.get("career", "high_school_student")
        career_info = CareerSystem.get_career_info(career_id)

        if not career_info:
            return "无职业"

        career_day = character.get("career_day", 0)
        daily_income = CareerSystem.daily_income(character)

        # 检查晋升条件
        can_promote, next_career, _ = CareerSystem.check_promotion(character)

        promotion_hint = ""
        if can_promote:
            promotion_hint = f"\n✨ 可以晋升！使用 /晋升 查看详情"
        elif career_info.get("next_stages"):
            # 显示晋升进度
            next_career_id = career_info["next_stages"][0]
            requirements = career_info["stage_requirements"].get(next_career_id, {})

            progress_lines = []
            for attr, required in requirements.items():
                char_value = character.get(attr, 0)
                if char_value < required:
                    progress_lines.append(f"  {CareerSystem.CAREER_ATTRIBUTES.get(attr, attr)}: {char_value}/{required}")

            if progress_lines:
                promotion_hint = f"\n💡 晋升条件:\n" + "\n".join(progress_lines)

        return f"""
💼 【职业信息】

{career_info['emoji']} {career_info['name']}
{career_info['description']}

💰 每日收入: {daily_income}币
📅 从业天数: {career_day}天
{promotion_hint}
""".strip()

    @staticmethod
    def train_attribute(character: Dict, attribute: str, amount: int) -> Tuple[Dict, str]:
        """
        训练职业属性

        Returns:
            (更新后的角色, 训练结果消息)
        """
        if attribute not in CareerSystem.CAREER_ATTRIBUTES:
            return character, "❌ 无效的属性"

        current_value = character.get(attribute, 0)
        new_value = min(100, current_value + amount)
        character[attribute] = new_value

        attr_name = CareerSystem.CAREER_ATTRIBUTES[attribute]
        message = f"✨ {attr_name} +{amount} ({current_value} → {new_value})"

        logger.info(f"训练属性: {attribute} +{amount}")

        return character, message

    @staticmethod
    def get_career_endings(character: Dict) -> List[str]:
        """
        根据职业获取相关结局

        Returns:
            可能的结局ID列表
        """
        career_id = character.get("career", "")
        career_info = CareerSystem.get_career_info(career_id)

        if not career_info:
            return []

        category = career_info["category"]

        # 根据职业类别返回相关结局
        career_endings = {
            "student": ["student_love", "campus_romance"],
            "career": ["successful_career_woman", "office_romance"],
            "freelance": ["creative_freedom", "independent_woman"],
            "entertainment": ["celebrity_couple", "spotlight_life"],
            "adult": ["fallen_angel", "sugar_baby", "redemption"],
        }

        return career_endings.get(category, [])
