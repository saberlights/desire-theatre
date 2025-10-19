"""
小游戏系统
"""

import random
import time
from typing import Tuple, Dict, List

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ...core.models import DTGameRecord

logger = get_logger("dt_game_system")


class GameSystem:
    """小游戏管理系统"""

    # 真心话问题库
    TRUTH_QUESTIONS = [
        {"question": "你最喜欢我的哪一点？", "intimacy_gain": 5, "affection_gain": 3},
        {"question": "你有过什么羞耻的幻想吗？", "shame_loss": 5, "arousal_gain": 8, "min_intimacy": 30},
        {"question": "你愿意为我做什么程度的事情？", "submission_gain": 5, "desire_gain": 5, "min_corruption": 20},
        {"question": "你最敏感的地方在哪里？", "arousal_gain": 15, "shame_loss": 10, "min_intimacy": 50},
        {"question": "你想过和我...做那种事吗？", "corruption_gain": 10, "arousal_gain": 20, "min_corruption": 40},
    ]

    # 大冒险任务库
    DARE_TASKS = [
        {"task": "亲我一下", "intimacy_gain": 10, "affection_gain": 5, "arousal_gain": 8},
        {"task": "让我抱你10秒", "intimacy_gain": 8, "affection_gain": 8, "arousal_gain": 5},
        {"task": "说一句情话给我听", "affection_gain": 10, "intimacy_gain": 5},
        {"task": "让我摸摸你的头发", "intimacy_gain": 12, "arousal_gain": 10, "min_intimacy": 30},
        {"task": "坐到我腿上", "arousal_gain": 20, "shame_loss": 15, "intimacy_gain": 15, "min_intimacy": 50},
        {"task": "脱掉一件衣服", "arousal_gain": 25, "shame_loss": 20, "corruption_gain": 10, "min_corruption": 40},
        {"task": "让我亲你的脖子", "arousal_gain": 30, "intimacy_gain": 20, "corruption_gain": 8, "min_corruption": 50},
    ]

    # 骰子事件
    DICE_EVENTS = {
        1: {"desc": "最小点数！惩罚：羞耻值+10", "effects": {"shame": 10}},
        2: {"desc": "小点数，略显尴尬", "effects": {"shame": 5, "affection": -3}},
        3: {"desc": "普通点数，平平无奇", "effects": {"affection": 2}},
        4: {"desc": "不错的点数", "effects": {"affection": 5, "intimacy": 3}},
        5: {"desc": "很好的点数！", "effects": {"affection": 8, "intimacy": 5, "arousal": 5}},
        6: {"desc": "最大点数！大成功！", "effects": {"affection": 10, "intimacy": 8, "arousal": 10, "desire": 5}}
    }

    @staticmethod
    async def play_truth_or_dare(
        user_id: str,
        chat_id: str,
        character: Dict,
        game_type: str  # "truth" or "dare"
    ) -> Tuple[bool, str, Dict[str, int]]:
        """
        玩真心话大冒险
        返回: (是否成功, 问题/任务描述, 属性效果)
        """
        # 选择问题/任务库
        pool = GameSystem.TRUTH_QUESTIONS if game_type == "truth" else GameSystem.DARE_TASKS

        # 筛选可用的问题/任务（根据角色属性）
        available = []
        for item in pool:
            # 检查最低要求
            if "min_intimacy" in item and character.get("intimacy", 0) < item["min_intimacy"]:
                continue
            if "min_corruption" in item and character.get("corruption", 0) < item["min_corruption"]:
                continue
            available.append(item)

        if not available:
            # 如果没有可用的，使用基础的
            available = [pool[0]]

        # 随机选择一个
        selected = random.choice(available)

        # 提取效果
        effects = {k: v for k, v in selected.items() if k not in ["question", "task", "min_intimacy", "min_corruption"]}

        # 记录游戏
        await database_api.db_save(
            DTGameRecord,
            data={
                "user_id": user_id,
                "chat_id": chat_id,
                "game_type": game_type,
                "game_result": selected.get("question") or selected.get("task"),
                "timestamp": time.time()
            }
        )

        desc = selected.get("question") or selected.get("task")
        return True, desc, effects

    @staticmethod
    async def roll_dice(
        user_id: str,
        chat_id: str
    ) -> Tuple[int, str, Dict[str, int]]:
        """
        掷骰子
        返回: (点数, 描述, 属性效果)
        """
        # 掷骰子
        result = random.randint(1, 6)

        # 获取事件
        event = GameSystem.DICE_EVENTS[result]

        # 记录游戏
        await database_api.db_save(
            DTGameRecord,
            data={
                "user_id": user_id,
                "chat_id": chat_id,
                "game_type": "dice",
                "game_result": str(result),
                "timestamp": time.time()
            }
        )

        return result, event["desc"], event["effects"]

    @staticmethod
    async def get_game_statistics(user_id: str, chat_id: str) -> Dict:
        """获取游戏统计"""
        records = await database_api.db_get(
            DTGameRecord,
            filters={"user_id": user_id, "chat_id": chat_id}
        )

        stats = {
            "total_games": len(records),
            "truth_count": len([r for r in records if r["game_type"] == "truth"]),
            "dare_count": len([r for r in records if r["game_type"] == "dare"]),
            "dice_count": len([r for r in records if r["game_type"] == "dice"])
        }

        return stats

    @staticmethod
    async def initialize_games():
        """初始化游戏系统（当前无需初始化）"""
        logger.info("游戏系统初始化完成")
        pass

