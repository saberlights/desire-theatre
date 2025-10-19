"""
赚钱系统 - 各种获取爱心币的方式
"""

import random
import time
from typing import Tuple, Dict

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ...core.models import DTCharacter

logger = get_logger("dt_earning_system")


class EarningSystem:
    """赚钱系统"""

    # 打工类型配置
    WORK_TYPES = {
        "咖啡店": {
            "base_reward": (15, 30),  # 最小和最大奖励
            "duration_hours": 2,
            "description": "在咖啡店打工，为客人服务",
            "success_messages": [
                "你在咖啡店辛勤工作了2小时，老板很满意！",
                "今天生意不错，老板夸奖了你的服务！",
                "虽然有点累，但工作完成得很好！"
            ]
        },
        "便利店": {
            "base_reward": (12, 25),
            "duration_hours": 2,
            "description": "在便利店值班，整理货架和收银",
            "success_messages": [
                "你认真整理了货架，老板很满意！",
                "今天工作很顺利，没有出什么差错！",
                "虽然有点单调，但工作完成得很好！"
            ]
        },
        "家教": {
            "base_reward": (30, 50),
            "duration_hours": 3,
            "description": "给学生补习功课",
            "success_messages": [
                "学生听得很认真，家长很满意你的教学！",
                "今天的课程进展顺利，学生理解得很快！",
                "虽然有点费脑，但看到学生进步很有成就感！"
            ]
        },
        "餐厅": {
            "base_reward": (20, 40),
            "duration_hours": 3,
            "description": "在餐厅当服务员",
            "success_messages": [
                "你热情地为客人服务，收到了不少小费！",
                "今天生意很好，虽然很忙但收入不错！",
                "客人们都很友善，工作氛围很愉快！"
            ]
        },
        "搬运工": {
            "base_reward": (40, 60),
            "duration_hours": 4,
            "description": "做搬运工，搬运货物和杂物",
            "success_messages": [
                "虽然很累，但总算完成了今天的搬运任务！",
                "体力活虽然辛苦，但报酬还不错！",
                "汗流浃背地干了一下午，拿到了工资！"
            ]
        },
        "夜班保安": {
            "base_reward": (50, 80),
            "duration_hours": 5,
            "description": "当夜班保安，巡逻和守卫",
            "success_messages": [
                "平安度过了夜班，虽然困但工资不错！",
                "夜班很安静，顺利完成了巡逻工作！",
                "熬了一夜，但夜班津贴很高！"
            ]
        },
        "牛郎": {
            "base_reward": (80, 150),
            "duration_hours": 4,
            "description": "在牛郎店工作，陪女性客人聊天喝酒",
            "requirements": {"affection": 40},
            "success_messages": [
                "今晚的客人都很满意你的陪伴，给了很多小费！",
                "虽然要说些甜言蜜语，但收入确实不错...",
                "客人们都很喜欢你，今晚赚了不少！"
            ],
            "side_effects": {"affection": -2}  # 对很多人好，对她的专一度下降
        },
        "男公关": {
            "base_reward": (100, 200),
            "duration_hours": 4,
            "description": "高级会所的男公关，提供陪伴服务",
            "requirements": {"affection": 50, "intimacy": 30},
            "success_messages": [
                "今晚接待了几位贵妇，她们很满意你的服务...",
                "虽然有些暧昧的互动，但只是陪聊而已...",
                "高级会所的小费果然丰厚！"
            ],
            "side_effects": {"affection": -3, "intimacy": -2}
        },
        "情趣用品推销": {
            "base_reward": (60, 120),
            "duration_hours": 3,
            "description": "推销情趣用品，需要演示和讲解",
            "requirements": {"corruption": 40},
            "success_messages": [
                "成功推销了几件商品，虽然有点尴尬...",
                "客户对你的讲解很满意，买了不少东西！",
                "虽然是情趣用品，但推销得很专业！"
            ],
            "side_effects": {"corruption": 1, "shame": -1}
        },
        "私人健身教练": {
            "base_reward": (70, 140),
            "duration_hours": 3,
            "description": "为女性客户提供一对一健身指导",
            "requirements": {"intimacy": 35},
            "success_messages": [
                "客户对你的指导很满意，还预约了下次！",
                "虽然有些身体接触，但都是专业的指导...",
                "今天的训练课程很成功，获得了好评！"
            ],
            "side_effects": {"intimacy": -1}
        },
        "AV男优试镜": {
            "base_reward": (150, 300),
            "duration_hours": 4,
            "description": "参加AV男优试镜，可能需要实际演出",
            "requirements": {"corruption": 70, "shame": "<30", "desire": 40},
            "success_messages": [
                "试镜通过了...虽然过程很尴尬，但报酬很高...",
                "导演很满意你的表现，给了高额的出演费！",
                "这份工作真的很羞耻，但钱确实来得快..."
            ],
            "side_effects": {"corruption": 3, "shame": -5, "desire": 5}
        }
    }

    # 上次打工时间记录（避免刷钱）
    _last_work_time = {}

    @staticmethod
    async def work(user_id: str, chat_id: str, work_type: str) -> Tuple[bool, str, int]:
        """打工赚钱

        Returns:
            (是否成功, 消息, 获得金币数)
        """
        # 检查工作类型是否存在
        if work_type not in EarningSystem.WORK_TYPES:
            return False, f"未知的工作类型: {work_type}", 0

        work_config = EarningSystem.WORK_TYPES[work_type]

        # 获取角色
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            return False, "角色不存在", 0

        # 检查职业需求
        if "requirements" in work_config:
            for attr, value in work_config["requirements"].items():
                char_value = char.get(attr, 0)

                if isinstance(value, str) and value.startswith("<"):
                    threshold = int(value[1:])
                    if char_value >= threshold:
                        return False, f"你的{attr}太高了，不适合这份工作", 0
                else:
                    threshold = int(value)
                    if char_value < threshold:
                        return False, f"你的{attr}不足，无法胜任这份工作（需要≥{threshold}）", 0

        # 检查冷却时间（每种工作每6小时只能做一次）
        work_key = f"{user_id}_{chat_id}_{work_type}"
        current_time = time.time()

        if work_key in EarningSystem._last_work_time:
            last_time = EarningSystem._last_work_time[work_key]
            cooldown_hours = 6
            time_passed = (current_time - last_time) / 3600

            if time_passed < cooldown_hours:
                remaining = cooldown_hours - time_passed
                hours = int(remaining)
                minutes = int((remaining - hours) * 60)
                return False, f"你刚刚做过{work_type}了，请休息一下！还需等待{hours}小时{minutes}分钟", 0

        # 计算奖励（随机）
        min_reward, max_reward = work_config["base_reward"]
        base_reward = random.randint(min_reward, max_reward)

        # 根据属性给予奖励加成
        bonus_multiplier = 1.0

        # 好感度高 -> 人缘好 -> 更多小费
        if char.get("affection", 0) > 70:
            bonus_multiplier += 0.2

        # 魅力高（根据堕落度和羞耻心）-> 更受欢迎
        if char.get("corruption", 0) > 50 and char.get("shame", 100) < 50:
            bonus_multiplier += 0.15

        final_reward = int(base_reward * bonus_multiplier)

        # 成功完成工作
        # 给予奖励
        char["coins"] = char.get("coins", 100) + final_reward

        # 应用副作用（如果有）
        side_effects = work_config.get("side_effects", {})
        if side_effects:
            from ...systems.attributes.attribute_system import AttributeSystem
            for attr, change in side_effects.items():
                char[attr] = AttributeSystem.clamp(char.get(attr, 0) + change)

        await database_api.db_save(
            DTCharacter,
            data=char,
            key_field="user_id",
            key_value=user_id
        )

        # 记录打工时间
        EarningSystem._last_work_time[work_key] = current_time

        # 随机选择成功消息
        success_message = random.choice(work_config["success_messages"])

        # 构建副作用信息（如果有）
        side_effects_text = ""
        if side_effects:
            effect_parts = []
            attr_names = {
                "shame": "羞耻", "corruption": "堕落", "intimacy": "亲密",
                "desire": "欲望", "arousal": "兴奋"
            }
            for attr, change in side_effects.items():
                name = attr_names.get(attr, attr)
                sign = "+" if change > 0 else ""
                effect_parts.append(f"{name}{sign}{change}")

            side_effects_text = f"\n\n⚠️ 副作用: {', '.join(effect_parts)}"

        result_message = f"""💼 【{work_type}】

{success_message}

⏰ 工作时长: {work_config["duration_hours"]}小时
💰 获得爱心币: {final_reward}
💵 当前余额: {char['coins']}{side_effects_text}

💡 每种工作6小时只能做一次，记得休息哦！"""

        logger.info(f"打工: {user_id} - {work_type}, 获得{final_reward}币")
        return True, result_message, final_reward

    @staticmethod
    def calculate_action_reward(action_config: Dict) -> int:
        """根据动作配置计算金币奖励"""
        action_type = action_config.get("type", "gentle")
        intensity = action_config.get("base_intensity", 1)

        # 基础奖励表
        type_rewards = {
            "gentle": (1, 3),      # 温柔 1-3币
            "intimate": (3, 5),    # 亲密 3-5币
            "seductive": (5, 8),   # 诱惑 5-8币
            "dominant": (8, 12),   # 支配 8-12币
            "corrupting": (12, 20), # 极限 12-20币
            "risky": (10, 25),     # 风险 10-25币（高风险高回报）
            "mood_locked": (15, 30) # 情绪专属 15-30币
        }

        min_reward, max_reward = type_rewards.get(action_type, (1, 5))

        # 根据强度调整
        reward = min_reward + (max_reward - min_reward) * (intensity / 10)

        # 添加随机波动 (±20%)
        reward = int(reward * random.uniform(0.8, 1.2))

        return max(1, reward)  # 至少1币
