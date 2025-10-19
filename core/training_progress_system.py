"""
调教进度系统 - NSFW向成长机制

核心理念:
- 某些极端/羞耻度高的玩法需要多次训练才能接受
- 0-20%: 强烈抵抗，可能失败，效果差
- 20-60%: 逐渐适应，效果正常
- 60-100%: 完全接受，开始享受，效果加成
- 100%+: 解锁变种玩法

与《火山的女儿》课程进度的区别:
- 火山: 学习课程有进度条
- 这里: 调教/训练某些玩法的接受度
"""

import json
from typing import Dict, Tuple, List, Optional
from src.common.logger import get_logger

logger = get_logger("dt_training_progress")


class TrainingProgressSystem:
    """调教进度系统"""

    # 需要训练的动作定义
    TRAINABLE_ACTIONS = {
        # 动作名: {需要训练次数, 初始抵抗度, 解锁变种}
        "舔": {
            "max_progress": 100,
            "training_needed": 8,          # 需要8次才能完全接受
            "base_resistance": 60,          # 初始抵抗度
            "unlock_variants": ["深度舔舐", "互相舔"],
            "category": "进阶",
        },
        "口": {
            "max_progress": 100,
            "training_needed": 10,
            "base_resistance": 70,
            "unlock_variants": ["深喉", "吞咽"],
            "category": "进阶",
        },
        "肛交": {
            "max_progress": 100,
            "training_needed": 15,
            "base_resistance": 90,
            "unlock_variants": ["无套肛交", "肛门扩张"],
            "category": "极限",
        },
        "SM玩法": {
            "max_progress": 100,
            "training_needed": 12,
            "base_resistance": 80,
            "unlock_variants": ["完全支配", "束缚调教"],
            "category": "极限",
        },
        "户外play": {
            "max_progress": 100,
            "training_needed": 10,
            "base_resistance": 85,
            "unlock_variants": ["公共场所", "露出"],
            "category": "极限",
        },
        "多人": {
            "max_progress": 100,
            "training_needed": 20,
            "base_resistance": 95,
            "unlock_variants": ["3P", "群交"],
            "category": "禁忌",
        },
        "道具play": {
            "max_progress": 100,
            "training_needed": 8,
            "base_resistance": 65,
            "unlock_variants": ["多道具组合", "极限道具"],
            "category": "进阶",
        },
        "角色扮演": {
            "max_progress": 100,
            "training_needed": 6,
            "base_resistance": 50,
            "unlock_variants": ["主奴play", "师生play"],
            "category": "进阶",
        },
    }

    @staticmethod
    def get_training_progress(character: Dict, action_name: str) -> int:
        """
        获取某个动作的训练进度

        返回: 0-100的进度值
        """
        progress_data = character.get("training_progress", "{}")

        if isinstance(progress_data, str):
            progress_dict = json.loads(progress_data)
        else:
            progress_dict = progress_data

        return progress_dict.get(action_name, 0)

    @staticmethod
    def add_training_progress(character: Dict, action_name: str) -> Tuple[int, int, bool, List[str]]:
        """
        增加训练进度

        返回: (旧进度, 新进度, 是否解锁变种, 解锁的变种列表)
        """
        if action_name not in TrainingProgressSystem.TRAINABLE_ACTIONS:
            return 0, 0, False, []

        action_config = TrainingProgressSystem.TRAINABLE_ACTIONS[action_name]

        # 获取当前进度
        progress_data = character.get("training_progress", "{}")
        if isinstance(progress_data, str):
            progress_dict = json.loads(progress_data)
        else:
            progress_dict = progress_data

        old_progress = progress_dict.get(action_name, 0)

        # 计算增加量（每次训练增加固定值）
        max_progress = action_config["max_progress"]
        training_needed = action_config["training_needed"]
        increment = max_progress // training_needed

        new_progress = min(max_progress, old_progress + increment)

        # 更新进度
        progress_dict[action_name] = new_progress
        character["training_progress"] = json.dumps(progress_dict, ensure_ascii=False)

        # 检查是否解锁变种（达到100%时）
        unlocked_variants = []
        if new_progress >= 100 and old_progress < 100:
            unlocked_variants = action_config.get("unlock_variants", [])

        logger.info(f"训练进度更新: {action_name} {old_progress}% → {new_progress}%")

        return old_progress, new_progress, (new_progress >= 100 and old_progress < 100), unlocked_variants

    @staticmethod
    def calculate_resistance_modifier(character: Dict, action_name: str) -> Tuple[float, str]:
        """
        根据训练进度计算抵抗修正

        返回: (效果倍率, 阶段描述)
        """
        if action_name not in TrainingProgressSystem.TRAINABLE_ACTIONS:
            return 1.0, "正常"

        action_config = TrainingProgressSystem.TRAINABLE_ACTIONS[action_name]
        progress = TrainingProgressSystem.get_training_progress(character, action_name)

        # 根据进度计算效果倍率和抵抗
        if progress < 20:
            # 强烈抵抗阶段
            effect_multiplier = 0.5
            stage_desc = "强烈抵抗"
        elif progress < 40:
            # 初步适应阶段
            effect_multiplier = 0.7
            stage_desc = "初步适应"
        elif progress < 60:
            # 逐渐接受阶段
            effect_multiplier = 1.0
            stage_desc = "逐渐接受"
        elif progress < 80:
            # 开始享受阶段
            effect_multiplier = 1.3
            stage_desc = "开始享受"
        elif progress < 100:
            # 完全沉溺阶段
            effect_multiplier = 1.5
            stage_desc = "完全沉溺"
        else:
            # 精通阶段（100%）
            effect_multiplier = 2.0
            stage_desc = "完全精通"

        return effect_multiplier, stage_desc

    @staticmethod
    def get_training_status(character: Dict, action_name: str) -> str:
        """获取训练状态显示文本"""
        if action_name not in TrainingProgressSystem.TRAINABLE_ACTIONS:
            return ""

        action_config = TrainingProgressSystem.TRAINABLE_ACTIONS[action_name]
        progress = TrainingProgressSystem.get_training_progress(character, action_name)
        _, stage_desc = TrainingProgressSystem.calculate_resistance_modifier(character, action_name)

        # 进度条
        bar_length = 10
        filled = int(progress / 10)
        empty = bar_length - filled
        bar = "█" * filled + "░" * empty

        status = f"""📊 【{action_name} - 训练进度】

{bar} {progress}%
阶段: {stage_desc}
"""

        # 显示解锁变种（如果已达到100%）
        if progress >= 100:
            variants = action_config.get("unlock_variants", [])
            if variants:
                status += f"\n🔓 已解锁变种: {', '.join(variants)}"

        return status

    @staticmethod
    def get_all_trainable_actions() -> Dict[str, Dict]:
        """获取所有可训练动作"""
        return TrainingProgressSystem.TRAINABLE_ACTIONS

    @staticmethod
    def is_trainable(action_name: str) -> bool:
        """检查动作是否需要训练"""
        return action_name in TrainingProgressSystem.TRAINABLE_ACTIONS

    @staticmethod
    def get_category_actions(category: str) -> List[str]:
        """获取某个类别的所有可训练动作"""
        return [
            name for name, config in TrainingProgressSystem.TRAINABLE_ACTIONS.items()
            if config.get("category") == category
        ]

    @staticmethod
    def get_training_summary(character: Dict) -> str:
        """获取所有训练进度总结"""
        progress_data = character.get("training_progress", "{}")
        if isinstance(progress_data, str):
            progress_dict = json.loads(progress_data)
        else:
            progress_dict = progress_data

        if not progress_dict:
            return "暂无训练进度"

        # 按类别分组
        categories = {"进阶": [], "极限": [], "禁忌": []}

        for action_name, progress in progress_dict.items():
            if action_name in TrainingProgressSystem.TRAINABLE_ACTIONS:
                category = TrainingProgressSystem.TRAINABLE_ACTIONS[action_name].get("category", "进阶")
                if progress > 0:
                    categories[category].append((action_name, progress))

        # 构建显示文本
        lines = ["📊 【训练进度总结】\n"]

        for category, actions in categories.items():
            if actions:
                lines.append(f"\n【{category}】")
                for action_name, progress in sorted(actions, key=lambda x: x[1], reverse=True):
                    filled = "█" * (progress // 10)
                    empty = "░" * (10 - progress // 10)
                    bar = filled + empty
                    lines.append(f"  {action_name}: {bar} {progress}%")

        return "\n".join(lines)
