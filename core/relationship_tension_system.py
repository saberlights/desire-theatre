"""
关系张力系统 - 检测爱意与欲望的平衡

核心机制：爱意和欲望必须保持平衡，失衡会触发危机事件
"""

from typing import Dict, Tuple, Optional
from src.common.logger import get_logger

logger = get_logger("dt_relationship_tension")


class RelationshipTensionSystem:
    """关系张力系统"""

    # 张力等级阈值
    TENSION_THRESHOLDS = {
        "和谐": 20,        # 差距<20
        "轻微失衡": 35,    # 差距20-35
        "显著失衡": 50,    # 差距35-50
        "严重失衡": 70,    # 差距50-70
        "危机": 100,       # 差距>70
    }

    @staticmethod
    def calculate_tension(character: Dict) -> Tuple[int, str, Optional[str]]:
        """
        计算关系张力

        返回: (张力值, 张力等级, 警告信息)
        """
        affection = character.get("affection", 0)
        desire = character.get("desire", 0)

        # 计算差距
        gap = abs(affection - desire)

        # 判断等级
        if gap < 20:
            level = "和谐"
            warning = None
        elif gap < 35:
            level = "轻微失衡"
            warning = None
        elif gap < 50:
            level = "显著失衡"
            warning = "⚠️ 关系开始不稳定"
        elif gap < 70:
            level = "严重失衡"
            warning = "⚠️ 关系严重失衡，需要调整"
        else:
            level = "危机"
            warning = "🚨 关系危机！"

        return gap, level, warning

    @staticmethod
    def check_relationship_crisis(character: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        检查是否触发关系危机事件

        返回: (是否触发, 事件数据)
        """
        affection = character.get("affection", 0)
        desire = character.get("desire", 0)
        trust = character.get("trust", 50)

        gap = abs(affection - desire)

        # 情况1: 欲望远高于爱意 (欲望>爱意+40)
        if desire > affection + 40:
            event = {
                "title": "💔 【她的质问】",
                "desc": f"""她突然安静下来，眼神复杂地看着你。

"我对你来说...只是发泄欲望的对象吗？"

她的声音在颤抖，眼眶有些泛红。

现在的情况:
  💕 爱意: {affection}/100
  🔥 欲望: {desire}/100
  ❓ 她开始怀疑你的真心

""",
                "crisis_type": "lust_over_love",
                "penalty": {"trust": -25, "affection": -15, "resistance": 15}
            }
            return True, event

        # 情况2: 爱意远高于欲望 (爱意>欲望+40)
        elif affection > desire + 40:
            event = {
                "title": "😔 【她的不安】",
                "desc": f"""她低着头，小声说：

"你...是不是不喜欢我的身体...？"

"还是说...我对你没有吸引力...？"

她看起来很受伤。

现在的情况:
  💕 爱意: {affection}/100
  🔥 欲望: {desire}/100
  ❓ 她开始怀疑自己的魅力

""",
                "crisis_type": "love_over_lust",
                "penalty": {"affection": -10, "shame": 20, "corruption": -10}
            }
            return True, event

        # 情况3: 信任很低且失衡严重
        elif trust < 30 and gap > 50:
            event = {
                "title": "💥 【关系崩溃】",
                "desc": """她突然推开你，眼神里满是失望和痛苦。

"我受够了...我不知道你到底想要什么..."

"也许...我们不应该继续下去了..."

⚠️ 这是严重的关系危机！
""",
                "crisis_type": "relationship_breakdown",
                "penalty": {"trust": -30, "affection": -25, "resistance": 30}
            }
            return True, event

        return False, None

    @staticmethod
    def get_balance_suggestion(character: Dict) -> str:
        """
        获取平衡建议

        返回: 建议文本
        """
        affection = character.get("affection", 0)
        desire = character.get("desire", 0)

        if desire > affection + 20:
            return """💡 【平衡建议】

她需要感受到你的爱意，而不只是欲望。

建议行动:
  • /牵手 - 提升好感和信任
  • /聊天 - 增进了解
  • /送礼 - 表达心意
  • 减少高欲望的互动

目标: 让爱意接近欲望值"""

        elif affection > desire + 20:
            return """💡 【平衡建议】

她需要感受到你的渴望，而不只是精神恋爱。

建议行动:
  • /诱惑 - 提升欲望和吸引力
  • /挑逗 - 增加暧昧氛围
  • /亲 - 适度的亲密接触

目标: 让欲望接近爱意值"""

        else:
            return "✅ 关系平衡良好！继续保持"
