"""
进化阶段系统
"""

from typing import Dict, Optional, List, Tuple
import json

from src.common.logger import get_logger

logger = get_logger("dt_evolution_system")


class EvolutionSystem:
    """进化阶段管理系统"""

    # 定义5个进化阶段及其要求和奖励
    EVOLUTION_STAGES = {
        1: {
            "name": "初识",
            "requirements": {},  # 初始阶段，无需求
            "description": "你们刚刚认识，一切都是新鲜的",
            "unlocks": ["基础互动命令"],
            "rewards": {}
        },
        2: {
            "name": "熟悉",
            "requirements": {
                "affection": 30,
                "intimacy": 20,
                "interaction_count": 20
            },
            "description": "你们已经熟悉起来，她开始对你放下戒备",
            "unlocks": ["亲密互动", "部分服装"],
            "rewards": {
                "outfit_unlocks": ["school_uniform", "maid_outfit"],
                "arousal_gain_bonus": 1.1
            }
        },
        3: {
            "name": "亲密",
            "requirements": {
                "affection": 60,
                "intimacy": 50,
                "trust": 60,
                "interaction_count": 50
            },
            "description": "你们的关系变得亲密，她愿意为你做更多",
            "unlocks": ["高级互动", "性感服装", "场景解锁"],
            "rewards": {
                "outfit_unlocks": ["sexy_dress"],
                "scene_unlocks": ["bathroom", "classroom"],
                "intimacy_gain_bonus": 1.2,
                "item_drop": "love_potion"
            }
        },
        4: {
            "name": "沦陷",
            "requirements": {
                "affection": 80,
                "intimacy": 70,
                "corruption": 40,
                "submission": 60,
                "shame": "<50"
            },
            "description": "她已经深深沦陷，开始接受更多禁忌的事",
            "unlocks": ["堕落互动", "情趣服装", "特殊场景"],
            "rewards": {
                "outfit_unlocks": ["bunny_suit", "lingerie_set"],
                "scene_unlocks": ["love_hotel", "street"],
                "corruption_gain_bonus": 1.3,
                "item_drop": "aphrodisiac"
            }
        },
        5: {
            "name": "完全堕落",
            "requirements": {
                "corruption": 80,
                "submission": 80,
                "shame": "<20",
                "intimacy": 90,
                "interaction_count": 100
            },
            "description": "她已经完全属于你，愿意做任何事情",
            "unlocks": ["所有互动", "所有服装", "所有场景", "终极事件"],
            "rewards": {
                "outfit_unlocks": ["nothing"],
                "all_modifiers_bonus": 1.5
            }
        }
    }

    @staticmethod
    def check_evolution(character: Dict) -> Tuple[bool, Optional[int], Optional[Dict]]:
        """
        检查角色是否可以进化
        返回: (是否可以进化, 新阶段, 阶段信息)
        """
        current_stage = character.get("evolution_stage", 1)

        # 检查下一个阶段
        next_stage = current_stage + 1
        if next_stage > 5:
            return False, None, None  # 已达最高阶段

        stage_info = EvolutionSystem.EVOLUTION_STAGES[next_stage]
        requirements = stage_info["requirements"]

        # 检查是否满足所有要求
        for attr, required in requirements.items():
            char_value = character.get(attr, 0)

            if isinstance(required, str) and required.startswith("<"):
                # 小于条件
                threshold = int(required[1:])
                if char_value >= threshold:
                    return False, None, None
            else:
                # 大于等于条件
                threshold = int(required)
                if char_value < threshold:
                    return False, None, None

        # 满足所有条件
        return True, next_stage, stage_info

    @staticmethod
    def apply_evolution_rewards(character: Dict, stage_info: Dict) -> Dict:
        """
        应用进化奖励到角色
        返回: 更新后的角色数据
        """
        rewards = stage_info.get("rewards", {})
        updated = character.copy()

        # 应用属性加成（存储在角色数据中，供后续使用）
        if "arousal_gain_bonus" in rewards:
            updated["arousal_bonus"] = updated.get("arousal_bonus", 1.0) * rewards["arousal_gain_bonus"]

        if "intimacy_gain_bonus" in rewards:
            updated["intimacy_bonus"] = updated.get("intimacy_bonus", 1.0) * rewards["intimacy_gain_bonus"]

        if "corruption_gain_bonus" in rewards:
            updated["corruption_bonus"] = updated.get("corruption_bonus", 1.0) * rewards["corruption_gain_bonus"]

        if "all_modifiers_bonus" in rewards:
            updated["all_bonus"] = updated.get("all_bonus", 1.0) * rewards["all_modifiers_bonus"]

        return updated

    @staticmethod
    async def unlock_evolution_rewards(user_id: str, chat_id: str, rewards: Dict):
        """
        解锁进化奖励（服装、道具等）
        """
        from src.plugin_system.apis import database_api

        # 解锁服装
        if "outfit_unlocks" in rewards:
            from ..extensions import OutfitSystem
            for outfit_id in rewards["outfit_unlocks"]:
                await OutfitSystem.unlock_outfit(user_id, chat_id, outfit_id)
                logger.info(f"进化奖励: 解锁服装 {outfit_id}")

        # 掉落道具
        if "item_drop" in rewards:
            from ..extensions import ItemSystem
            await ItemSystem.add_item(user_id, chat_id, rewards["item_drop"], quantity=1)
            logger.info(f"进化奖励: 获得道具 {rewards['item_drop']}")

    @staticmethod
    def get_stage_name(stage: int) -> str:
        """获取阶段名称"""
        if stage in EvolutionSystem.EVOLUTION_STAGES:
            return EvolutionSystem.EVOLUTION_STAGES[stage]["name"]
        return f"阶段{stage}"

    @staticmethod
    def get_evolution_progress(character: Dict) -> Tuple[float, str]:
        """
        计算进化进度百分比和可视化进度条
        返回: (进度百分比, 可视化进度条)
        """
        current_stage = character.get("evolution_stage", 1)
        next_stage = current_stage + 1

        if next_stage > 5:
            return 1.0, "████████████ 100%"

        requirements = EvolutionSystem.EVOLUTION_STAGES[next_stage]["requirements"]

        # 计算满足的条件数
        met_count = 0
        total_count = len(requirements)

        for attr, required in requirements.items():
            char_value = character.get(attr, 0)
            if isinstance(required, str) and required.startswith("<"):
                if char_value < int(required[1:]):
                    met_count += 1
            else:
                if char_value >= int(required):
                    met_count += 1

        progress = met_count / total_count if total_count > 0 else 1.0
        bar_length = 12
        filled = int(progress * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        return progress, f"{bar} {int(progress * 100)}%"

    @staticmethod
    def get_next_stage_hint(character: Dict) -> str:
        """获取下一阶段的提示"""
        current_stage = character.get("evolution_stage", 1)
        next_stage = current_stage + 1

        if next_stage > 5:
            return "✨ 你已达到最高进化阶段！"

        stage_info = EvolutionSystem.EVOLUTION_STAGES[next_stage]
        requirements = stage_info["requirements"]

        # 获取进度可视化
        progress, progress_bar = EvolutionSystem.get_evolution_progress(character)

        hints = []
        for attr, required in requirements.items():
            char_value = character.get(attr, 0)

            # 属性中文名
            attr_names = {
                "affection": "好感",
                "intimacy": "亲密",
                "trust": "信任",
                "submission": "顺从",
                "corruption": "堕落",
                "shame": "羞耻",
                "interaction_count": "互动次数"
            }

            attr_name = attr_names.get(attr, attr)

            if isinstance(required, str) and required.startswith("<"):
                threshold = int(required[1:])
                if char_value >= threshold:
                    hints.append(f"❌ {attr_name} 需要<{threshold} (当前{char_value})")
                else:
                    hints.append(f"✅ {attr_name}<{threshold}")
            else:
                threshold = int(required)
                if char_value < threshold:
                    hints.append(f"❌ {attr_name} 需要≥{threshold} (当前{char_value})")
                else:
                    hints.append(f"✅ {attr_name}≥{threshold}")

        hint_text = f"\n📈 【下一阶段: {stage_info['name']}】\n"
        hint_text += f"进度: {progress_bar}\n\n"
        hint_text += "\n".join(hints)
        hint_text += f"\n\n解锁内容: {', '.join(stage_info['unlocks'])}"

        return hint_text
