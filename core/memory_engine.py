"""
记忆引擎 - 深化版
让角色真正记住玩家的承诺、矛盾行为、习惯模式
"""

import time
import random
import json
from typing import List, Dict, Tuple, Optional
import re

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from .models import DTMemory, DTEvent

logger = get_logger("dt_memory_engine")


class MemoryEngine:
    """深化的记忆引擎"""

    # 记忆类型定义
    MEMORY_TYPES = {
        "promise": {"name": "承诺", "importance": 8, "decay_rate": 0.1},
        "contradiction": {"name": "矛盾", "importance": 9, "decay_rate": 0.05},
        "habit": {"name": "习惯", "importance": 6, "decay_rate": 0.3},
        "milestone": {"name": "里程碑", "importance": 10, "decay_rate": 0.0},
        "trauma": {"name": "创伤", "importance": 10, "decay_rate": 0.0},
        "preference": {"name": "偏好", "importance": 5, "decay_rate": 0.4},
        "event": {"name": "事件", "importance": 6, "decay_rate": 0.2},
        "dialogue": {"name": "对话", "importance": 4, "decay_rate": 0.5},
    }

    # 承诺关键词检测
    PROMISE_KEYWORDS = [
        "我保证", "我答应", "我发誓", "我一定", "我承诺",
        "相信我", "我不会", "我只", "永远", "以后",
    ]

    # 矛盾行为检测模式
    CONTRADICTION_PATTERNS = {
        "承诺违背": {
            "pattern": "之前说了{promise}，但现在做了{action}",
            "trust_penalty": -15,
            "message": "你之前明明说过{promise}...为什么现在..."
        },
        "反复无常": {
            "pattern": "频繁改变决定",
            "trust_penalty": -10,
            "message": "你到底是怎么想的...？"
        },
        "言行不一": {
            "pattern": "说一套做一套",
            "trust_penalty": -20,
            "message": "我还以为你是真心的..."
        }
    }

    @staticmethod
    async def create_memory(
        user_id: str,
        chat_id: str,
        memory_type: str,
        content: str,
        importance: int = None,
        emotional_impact: int = 0,
        tags: List[str] = None,
        context: Dict = None,
        related_attributes: Dict = None
    ) -> str:
        """创建新记忆（强化版）"""

        # 自动设置重要性
        if importance is None:
            importance = MemoryEngine.MEMORY_TYPES.get(memory_type, {}).get("importance", 5)

        memory_id = f"mem_{int(time.time() * 1000000)}_{random.randint(1000, 9999)}"

        await database_api.db_save(
            DTMemory,
            data={
                "memory_id": memory_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "timestamp": time.time(),
                "memory_type": memory_type,
                "content": content,
                "context": json.dumps(context or {}, ensure_ascii=False),
                "importance": importance,
                "emotional_impact": emotional_impact,
                "tags": json.dumps(tags or [], ensure_ascii=False),
                "related_attributes": json.dumps(related_attributes or {}, ensure_ascii=False),
                "recall_count": 0,
                "last_recalled": None
            },
            key_field="memory_id",
            key_value=memory_id
        )

        logger.info(f"创建{memory_type}记忆: {content[:50]}...")
        return memory_id

    @staticmethod
    async def detect_promise(user_message: str, user_id: str, chat_id: str) -> Optional[str]:
        """
        检测玩家是否做出了承诺

        返回: 承诺内容（如果检测到）
        """
        for keyword in MemoryEngine.PROMISE_KEYWORDS:
            if keyword in user_message:
                # 提取承诺内容
                promise_content = user_message.strip()

                # 记录承诺
                await MemoryEngine.create_memory(
                    user_id=user_id,
                    chat_id=chat_id,
                    memory_type="promise",
                    content=promise_content,
                    tags=["承诺", keyword],
                    context={"raw_message": user_message},
                    emotional_impact=10
                )

                logger.info(f"检测到承诺: {promise_content}")
                return promise_content

        return None

    @staticmethod
    async def check_promise_consistency(
        user_id: str,
        chat_id: str,
        current_action: str,
        action_type: str
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        检查当前行为是否违背了之前的承诺

        返回: (是否违背, 违背的承诺, 惩罚效果)
        """
        # 获取所有承诺记忆
        promises = await database_api.db_get(
            DTMemory,
            filters={"user_id": user_id, "chat_id": chat_id, "memory_type": "promise"},
            order_by="-timestamp",
            limit=10
        )

        if not promises:
            return False, None, None

        # 检测矛盾规则
        contradiction_rules = {
            ("我只爱你", ["挑逗", "诱惑", "亲"]): "你说过只爱我，为什么还要对别人...",
            ("我不会强迫你", ["强迫", "命令", "调教"]): "你明明说不会强迫我的...",
            ("我会温柔对你", ["粗暴", "打", "惩罚"]): "你不是说会温柔的吗？",
            ("我会保护你", ["无视", "冷落"]): "你说过会保护我...现在呢？",
        }

        for promise_mem in promises:
            promise_content = promise_mem["content"]

            # 检查是否有矛盾
            for (promise_key, conflicting_actions), message in contradiction_rules.items():
                if promise_key in promise_content and current_action in conflicting_actions:
                    # 记录矛盾
                    await MemoryEngine.create_memory(
                        user_id=user_id,
                        chat_id=chat_id,
                        memory_type="contradiction",
                        content=f"承诺「{promise_content}」与行为「{current_action}」矛盾",
                        tags=["矛盾", "承诺违背"],
                        context={
                            "promise": promise_content,
                            "action": current_action,
                            "timestamp": time.time()
                        },
                        emotional_impact=-20
                    )

                    # 返回惩罚效果
                    penalty = {
                        "trust": -20,
                        "affection": -15,
                        "resistance": 10,
                    }

                    return True, promise_content, penalty

        return False, None, None

    @staticmethod
    async def track_habit(
        user_id: str,
        chat_id: str,
        action_name: str
    ):
        """
        追踪玩家的行为习惯

        连续3次同样的行为 = 形成习惯
        """
        # 获取最近的行为记录
        recent_actions = await database_api.db_get(
            DTEvent,
            filters={"user_id": user_id, "chat_id": chat_id, "event_type": "interaction"},
            order_by="-timestamp",
            limit=10
        )

        if not recent_actions:
            return

        # 统计action_name出现次数
        action_count = sum(1 for evt in recent_actions if evt["event_name"] == action_name)

        # 形成习惯
        if action_count >= 3:
            # 检查是否已经记录过这个习惯
            existing_habit = await database_api.db_get(
                DTMemory,
                filters={
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "memory_type": "habit"
                },
                single_result=True
            )

            habit_content = f"你总是喜欢{action_name}"

            # 检查习惯是否已存在
            if existing_habit and action_name in existing_habit.get("content", ""):
                # 更新习惯强度
                existing_habit["importance"] = min(10, existing_habit.get("importance", 5) + 1)
                await database_api.db_save(
                    DTMemory,
                    data=existing_habit,
                    key_field="memory_id",
                    key_value=existing_habit["memory_id"]
                )
                logger.debug(f"强化习惯: {action_name}")
            else:
                # 创建新习惯记忆
                await MemoryEngine.create_memory(
                    user_id=user_id,
                    chat_id=chat_id,
                    memory_type="habit",
                    content=habit_content,
                    tags=["习惯", action_name],
                    context={"action": action_name, "count": action_count}
                )
                logger.info(f"形成新习惯: {action_name}")

    @staticmethod
    async def check_habit_expectation(
        user_id: str,
        chat_id: str,
        current_action: str
    ) -> Tuple[bool, Optional[str]]:
        """
        检查是否违背了她的期待（基于习惯）

        例如：你一直摸头，她已经习惯了，今天你没摸，她会失落

        返回: (是否期待落空, 期待内容)
        """
        # 获取习惯记忆
        habits = await database_api.db_get(
            DTMemory,
            filters={"user_id": user_id, "chat_id": chat_id, "memory_type": "habit"},
            order_by="-importance",
            limit=3
        )

        if not habits:
            return False, None

        # 获取最近的互动
        recent_events = await database_api.db_get(
            DTEvent,
            filters={"user_id": user_id, "chat_id": chat_id, "event_type": "interaction"},
            order_by="-timestamp",
            limit=5
        )

        # 检查习惯是否被打破
        for habit in habits:
            context = json.loads(habit.get("context", "{}"))
            habit_action = context.get("action")

            if not habit_action:
                continue

            # 检查最近5次互动中是否有这个习惯动作
            recent_has_habit = any(evt["event_name"] == habit_action for evt in recent_events)

            # 如果习惯动作消失了，她会期待落空
            if not recent_has_habit and current_action != habit_action:
                expectation_message = f"你今天...没有{habit_action}呢..."
                return True, expectation_message

        return False, None

    @staticmethod
    async def get_relevant_memories(
        user_id: str,
        chat_id: str,
        limit: int = 5,
        memory_types: List[str] = None,
        recent_hours: int = None
    ) -> List[Dict]:
        """获取相关记忆（强化版）"""
        filters = {"user_id": user_id, "chat_id": chat_id}

        memories = await database_api.db_get(
            DTMemory,
            filters=filters,
            limit=limit * 3,  # 获取更多候选
            order_by="-importance"
        )

        if not memories:
            return []

        # 筛选记忆类型
        if memory_types:
            memories = [m for m in memories if m["memory_type"] in memory_types]

        # 筛选时间范围
        if recent_hours:
            cutoff_time = time.time() - (recent_hours * 3600)
            memories = [m for m in memories if m["timestamp"] > cutoff_time]

        # 综合排序（重要性 + 情感冲击 + 时间新鲜度）
        def score_memory(mem):
            importance = mem.get("importance", 5)
            emotional_impact = abs(mem.get("emotional_impact", 0))
            time_factor = (time.time() - mem["timestamp"]) / 86400  # 天数
            freshness = max(0, 10 - time_factor)  # 越新鲜越高分

            return importance * 1.5 + emotional_impact * 1.2 + freshness * 0.8

        sorted_memories = sorted(memories, key=score_memory, reverse=True)

        return sorted_memories[:limit]

    @staticmethod
    async def recall_memory(memory_id: str):
        """回忆记忆（更新统计）"""
        memory = await database_api.db_get(
            DTMemory,
            filters={"memory_id": memory_id},
            single_result=True
        )

        if memory:
            memory["recall_count"] = memory.get("recall_count", 0) + 1
            memory["last_recalled"] = time.time()

            await database_api.db_save(
                DTMemory,
                data=memory,
                key_field="memory_id",
                key_value=memory_id
            )

    @staticmethod
    async def get_memory_summary(user_id: str, chat_id: str) -> str:
        """
        获取记忆摘要（用于添加到Prompt）

        返回: 格式化的记忆摘要字符串
        """
        # 获取不同类型的关键记忆
        promises = await database_api.db_get(
            DTMemory,
            filters={"user_id": user_id, "chat_id": chat_id, "memory_type": "promise"},
            order_by="-timestamp",
            limit=3
        )

        contradictions = await database_api.db_get(
            DTMemory,
            filters={"user_id": user_id, "chat_id": chat_id, "memory_type": "contradiction"},
            order_by="-timestamp",
            limit=2
        )

        habits = await database_api.db_get(
            DTMemory,
            filters={"user_id": user_id, "chat_id": chat_id, "memory_type": "habit"},
            order_by="-importance",
            limit=2
        )

        traumas = await database_api.db_get(
            DTMemory,
            filters={"user_id": user_id, "chat_id": chat_id, "memory_type": "trauma"},
            order_by="-timestamp",
            limit=2
        )

        summary_parts = []

        if promises:
            summary_parts.append("【你记得的承诺】")
            for p in promises:
                summary_parts.append(f"  • {p['content']}")

        if contradictions:
            summary_parts.append("\n【你注意到的矛盾】")
            for c in contradictions:
                summary_parts.append(f"  • {c['content']}")

        if habits:
            summary_parts.append("\n【你发现的习惯】")
            for h in habits:
                summary_parts.append(f"  • {h['content']}")

        if traumas:
            summary_parts.append("\n【你心里的伤痕】")
            for t in traumas:
                summary_parts.append(f"  • {t['content']}")

        return "\n".join(summary_parts) if summary_parts else ""

    @staticmethod
    async def create_milestone(
        user_id: str,
        chat_id: str,
        milestone_name: str,
        description: str,
        related_attributes: Dict = None
    ):
        """创建里程碑记忆"""
        await MemoryEngine.create_memory(
            user_id=user_id,
            chat_id=chat_id,
            memory_type="milestone",
            content=f"{milestone_name}: {description}",
            tags=["里程碑", milestone_name],
            related_attributes=related_attributes,
            emotional_impact=15
        )

        logger.info(f"创建里程碑: {milestone_name}")

    @staticmethod
    async def create_trauma(
        user_id: str,
        chat_id: str,
        trauma_content: str,
        severity: int = 5
    ):
        """创建创伤记忆（负面重要事件）"""
        await MemoryEngine.create_memory(
            user_id=user_id,
            chat_id=chat_id,
            memory_type="trauma",
            content=trauma_content,
            importance=10,
            emotional_impact=-severity * 3,
            tags=["创伤", "负面"]
        )

        logger.warning(f"创建创伤记忆: {trauma_content}")
