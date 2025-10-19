"""
行动点系统 - 借鉴《火山的女儿》的资源管理机制

核心理念:
- 每天有限的行动点，需要策略规划
- 不同动作消耗不同点数
- 可以通过休息、饮食恢复
- 制造资源稀缺性和决策权重
"""

from typing import Dict, Tuple, Optional
from src.common.logger import get_logger

logger = get_logger("dt_action_points")


class ActionPointSystem:
    """行动点系统"""

    # 每日初始行动点
    DAILY_ACTION_POINTS = 10

    # 动作消耗定义（根据动作类型）
    ACTION_COST = {
        # 温柔系动作 - 1-2点
        "gentle": 1,

        # 亲密系动作 - 2-3点
        "intimate": 2,

        # 诱惑系动作 - 3-4点
        "seductive": 3,

        # 挑逗系动作 - 3-4点
        "teasing": 3,

        # 强势系动作 - 4-5点
        "dominant": 4,

        # 调教系动作 - 5点
        "training": 5,

        # 风险系动作 - 2-4点（根据成功率动态调整）
        "risky": 3,
    }

    # 恢复行动点的方法（NSFW向）
    RECOVERY_METHODS = {
        "rest": 3,              # 休息恢复3点
        "together_meal": 5,     # 一起用餐恢复5点（增加好感+3）
        "drink_together": 3,    # 一起喝酒恢复3点（降低羞耻-5）
        "massage": 4,           # 按摩放松恢复4点（增加亲密+2）
        "bath_together": 6,     # 一起洗澡恢复6点（增加亲密+5，羞耻-10）
        "aftercare": 4,         # 善后照顾恢复4点（增加好感+5，信任+3）
    }

    @staticmethod
    def get_daily_action_points(character: Dict) -> int:
        """
        获取每日行动点上限

        可能的扩展：根据关系阶段或某些天赋增加上限
        """
        base_points = ActionPointSystem.DAILY_ACTION_POINTS

        # 检查是否有增加行动点的天赋（未来实现）
        # talent_bonus = character.get("action_point_talent", 0)

        return base_points

    @staticmethod
    def get_current_action_points(character: Dict) -> int:
        """获取当前剩余行动点"""
        return character.get("current_action_points", ActionPointSystem.DAILY_ACTION_POINTS)

    @staticmethod
    def get_action_cost(action_type: str, action_name: str = "") -> int:
        """
        获取动作消耗的行动点

        参数:
            action_type: 动作类型（gentle, intimate等）
            action_name: 动作名称（用于特殊动作的自定义消耗）
        """
        # 基础消耗
        base_cost = ActionPointSystem.ACTION_COST.get(action_type, 2)

        # 特殊动作的自定义消耗（可扩展）
        special_costs = {
            "睡在一起": 6,  # 特殊高消耗动作
            "约会": 4,
            "送礼物": 1,
        }

        if action_name in special_costs:
            return special_costs[action_name]

        return base_cost

    @staticmethod
    def can_afford_action(character: Dict, cost: int) -> Tuple[bool, Optional[str]]:
        """
        检查是否有足够行动点执行动作

        返回: (能否执行, 错误提示)
        """
        current = ActionPointSystem.get_current_action_points(character)

        if current < cost:
            shortage = cost - current
            return False, f"""❌ 【行动点不足】

今天的精力已经不够了...

💫 当前行动点: {current}/10
💰 需要: {cost}点
📉 还差: {shortage}点

💡 建议:
  • 使用 /休息 恢复3点行动点
  • 使用 /吃饭 恢复5点行动点
  • 或等待明天（/明日 进入下一天）
"""

        return True, None

    @staticmethod
    def consume_action_points(character: Dict, cost: int):
        """消耗行动点"""
        current = ActionPointSystem.get_current_action_points(character)
        character["current_action_points"] = max(0, current - cost)

        logger.info(f"消耗行动点: {cost}, 剩余: {character['current_action_points']}")

    @staticmethod
    def recover_action_points(character: Dict, method: str) -> Tuple[int, str, Dict[str, int]]:
        """
        恢复行动点（NSFW向，带属性加成）

        返回: (恢复量, 提示消息, 属性变化)
        """
        recovery = ActionPointSystem.RECOVERY_METHODS.get(method, 0)
        current = ActionPointSystem.get_current_action_points(character)
        max_points = ActionPointSystem.get_daily_action_points(character)

        # 计算实际恢复量（不超过上限）
        actual_recovery = min(recovery, max_points - current)
        new_points = min(max_points, current + recovery)

        character["current_action_points"] = new_points

        # 【NSFW向】不同恢复方式的属性加成
        attribute_bonus = {}
        bonus_desc = []

        if method == "together_meal":
            attribute_bonus = {"affection": 3}
            bonus_desc.append("好感+3")
        elif method == "drink_together":
            attribute_bonus = {"shame": -5}
            bonus_desc.append("羞耻-5")
        elif method == "massage":
            attribute_bonus = {"intimacy": 2}
            bonus_desc.append("亲密+2")
        elif method == "bath_together":
            attribute_bonus = {"intimacy": 5, "shame": -10}
            bonus_desc.append("亲密+5")
            bonus_desc.append("羞耻-10")
        elif method == "aftercare":
            attribute_bonus = {"affection": 5, "trust": 3}
            bonus_desc.append("好感+5")
            bonus_desc.append("信任+3")

        # 构建提示消息
        method_names = {
            "rest": "休息",
            "together_meal": "一起用餐",
            "drink_together": "一起喝酒",
            "massage": "按摩放松",
            "bath_together": "一起洗澡",
            "aftercare": "善后照顾"
        }

        method_descriptions = {
            "rest": "她在床上休息了一会儿...",
            "together_meal": "你们一起享用了美味的餐点",
            "drink_together": "你们一起喝了点小酒，气氛变得轻松",
            "massage": "你温柔地为她按摩，她逐渐放松",
            "bath_together": "你们一起洗澡...亲密的氛围让她放下了防备",
            "aftercare": "你温柔地照顾她，让她感到被珍视"
        }

        method_name = method_names.get(method, method)
        description = method_descriptions.get(method, "")

        bonus_text = " ".join(f"💕{desc}" for desc in bonus_desc) if bonus_desc else ""

        if actual_recovery > 0:
            message = f"""💫 【{method_name}】

{description}

恢复了 {actual_recovery} 点行动点
{bonus_text}

当前行动点: {new_points}/{max_points}
"""
        else:
            message = f"""💫 【行动点已满】

当前行动点: {current}/{max_points}
不需要恢复了
"""

        return actual_recovery, message, attribute_bonus

    @staticmethod
    def reset_daily_action_points(character: Dict):
        """重置每日行动点（进入新的一天时调用）"""
        max_points = ActionPointSystem.get_daily_action_points(character)
        character["current_action_points"] = max_points

        logger.info(f"重置每日行动点: {max_points}")

    @staticmethod
    def get_action_point_display(character: Dict) -> str:
        """获取行动点显示文本"""
        current = ActionPointSystem.get_current_action_points(character)
        max_points = ActionPointSystem.get_daily_action_points(character)

        # 根据剩余行动点显示不同提示
        if current >= 8:
            status = "精力充沛✨"
        elif current >= 5:
            status = "状态良好💫"
        elif current >= 3:
            status = "有些疲惫😮‍💨"
        elif current >= 1:
            status = "非常疲惫😓"
        else:
            status = "精疲力竭💤"

        # 进度条
        filled = "█" * current
        empty = "░" * (max_points - current)
        bar = filled + empty

        return f"""💫 行动点: {bar} {current}/{max_points}
状态: {status}"""

    @staticmethod
    def get_cost_preview(action_type: str, action_name: str = "") -> str:
        """获取动作消耗预览"""
        cost = ActionPointSystem.get_action_cost(action_type, action_name)

        if cost == 1:
            level = "💚 轻松"
        elif cost <= 2:
            level = "💙 普通"
        elif cost <= 3:
            level = "💛 中等"
        elif cost <= 4:
            level = "🧡 较累"
        else:
            level = "❤️ 很累"

        return f"{level} ({cost}点行动点)"
