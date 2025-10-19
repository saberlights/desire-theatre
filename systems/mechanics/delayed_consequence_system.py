"""
延迟后果系统 - 行为的后果会在未来爆发

核心机制：某些行为的负面后果不会立刻显现，而是在几天后突然爆发
"""

import time
import json
import random
from typing import Dict, List, Tuple, Optional

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ...core.models import DTEvent

logger = get_logger("dt_delayed_consequence")


class DelayedConsequenceSystem:
    """延迟后果系统"""

    # 延迟后果类型定义
    CONSEQUENCE_TYPES = {
        "forced_action": {
            "name": "强迫行为后遗症",
            "delay_days": 2,
            "trigger_actions": ["强迫", "命令", "调教"],
            "consequence": {
                "trust": -20,
                "affection": -15,
                "resistance": 20,
            },
            "messages": [
                "这几天她一直在回避你...\n\n今天她终于开口了：\n\"那天的事...我一直在想...你为什么要那样对我？\"",
                "她最近总是心不在焉，今天她突然说：\n\"我...我不知道该怎么面对你了...\"",
            ]
        },
        "promise_broken": {
            "name": "违背承诺的余波",
            "delay_days": 3,
            "consequence": {
                "trust": -30,
                "affection": -20,
            },
            "messages": [
                "她突然提起了你之前的承诺：\n\"你还记得你说过什么吗...？我一直在等...\"",
                "\"我真的很想相信你...但是...\"她的眼神满是失望",
            ]
        },
        "rough_treatment": {
            "name": "粗暴对待的心理创伤",
            "delay_days": 1,
            "trigger_actions": ["粗暴", "打", "惩罚"],
            "consequence": {
                "trust": -25,
                "affection": -10,
                "resistance": 25,
                "fear": 15,  # 新增恐惧属性
            },
            "messages": [
                "她做噩梦了...\n\n她颤抖着说：\"我...我有点怕你了...\"",
                "她看到你就会下意识地后退一步...\n这让她自己也很困惑",
            ]
        },
        "emotional_neglect": {
            "name": "情感忽视的累积",
            "delay_days": 5,
            "consequence": {
                "affection": -20,
                "trust": -15,
            },
            "messages": [
                "\"你是不是...不在乎我了？\"她突然问道，眼神黯淡",
                "她变得越来越沉默，今天她说：\"算了...反正说了你也不会听...\"",
            ]
        }
    }

    @staticmethod
    async def schedule_delayed_consequence(
        user_id: str,
        chat_id: str,
        consequence_type: str,
        trigger_action: str,
        context: Dict = None
    ):
        """
        安排一个延迟后果

        Args:
            user_id: 用户ID
            chat_id: 聊天ID
            consequence_type: 后果类型
            trigger_action: 触发行为
            context: 额外上下文
        """
        if consequence_type not in DelayedConsequenceSystem.CONSEQUENCE_TYPES:
            logger.warning(f"未知的延迟后果类型: {consequence_type}")
            return

        consequence_def = DelayedConsequenceSystem.CONSEQUENCE_TYPES[consequence_type]
        delay_days = consequence_def["delay_days"]

        # 计算触发时间
        trigger_time = time.time() + (delay_days * 86400)

        # 创建事件记录
        event_id = f"delayed_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        await database_api.db_save(
            DTEvent,
            data={
                "event_id": event_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "event_type": "delayed_consequence",
                "event_name": consequence_type,
                "timestamp": trigger_time,  # 使用未来时间
                "event_data": json.dumps({
                    "trigger_action": trigger_action,
                    "context": context or {},
                    "consequence": consequence_def["consequence"]
                }, ensure_ascii=False),
                "user_choice": None,
                "outcome": "pending",
                "attribute_changes": "{}"
            },
            key_field="event_id",
            key_value=event_id
        )

        logger.info(f"安排延迟后果: {consequence_type}, {delay_days}天后触发")

    @staticmethod
    async def check_pending_consequences(
        user_id: str,
        chat_id: str
    ) -> List[Dict]:
        """
        检查待触发的延迟后果

        返回: 应该触发的后果列表
        """
        # 获取所有pending的延迟后果事件
        pending_events = await database_api.db_get(
            DTEvent,
            filters={
                "user_id": user_id,
                "chat_id": chat_id,
                "event_type": "delayed_consequence",
                "outcome": "pending"
            }
        )

        if not pending_events:
            return []

        # 筛选出时间已到的事件
        current_time = time.time()
        triggered_consequences = []

        for event in pending_events:
            if event["timestamp"] <= current_time:
                # 解析事件数据
                event_data = json.loads(event.get("event_data", "{}"))
                consequence_type = event["event_name"]

                if consequence_type in DelayedConsequenceSystem.CONSEQUENCE_TYPES:
                    consequence_def = DelayedConsequenceSystem.CONSEQUENCE_TYPES[consequence_type]

                    triggered_consequences.append({
                        "event_id": event["event_id"],
                        "type": consequence_type,
                        "name": consequence_def["name"],
                        "message": random.choice(consequence_def["messages"]),
                        "consequence": event_data.get("consequence", {}),
                        "trigger_action": event_data.get("trigger_action", ""),
                    })

                    # 标记为已触发
                    event["outcome"] = "triggered"
                    await database_api.db_save(
                        DTEvent,
                        data=event,
                        key_field="event_id",
                        key_value=event["event_id"]
                    )

        return triggered_consequences

    @staticmethod
    async def trigger_consequence(
        user_id: str,
        chat_id: str,
        consequence: Dict,
        character: Dict
    ) -> Tuple[Dict, str]:
        """
        触发延迟后果

        返回: (更新后的角色数据, 显示消息)
        """
        from ..attributes.attribute_system import AttributeSystem

        # 应用后果
        updated_char = AttributeSystem.apply_changes(character, consequence["consequence"])

        # 构建消息
        message = f"""⏰ 【延迟后果】{consequence['name']}

{consequence['message']}

━━━━━━━━━━━━━━━━━━━

这是{consequence['trigger_action']}行为的后果...
"""

        logger.info(f"触发延迟后果: {user_id} - {consequence['type']}")

        return updated_char, message

    @staticmethod
    def should_schedule_consequence(action_name: str, action_type: str, character: Dict) -> Optional[str]:
        """
        判断是否应该安排延迟后果

        返回: 后果类型（如果应该安排）
        """
        # 检查是否匹配触发条件
        for consequence_type, definition in DelayedConsequenceSystem.CONSEQUENCE_TYPES.items():
            trigger_actions = definition.get("trigger_actions", [])

            if action_name in trigger_actions:
                # 根据角色状态决定是否触发
                trust = character.get("trust", 50)

                # 信任度越低，越容易产生延迟后果
                trigger_chance = 0.3 if trust < 40 else 0.15 if trust < 60 else 0.05

                if random.random() < trigger_chance:
                    return consequence_type

        # 检查强迫类行为
        if action_type in ["dominant", "risky", "corrupting"]:
            resistance = character.get("resistance", 50)

            # 抵抗力高时更容易产生后遗症
            if resistance > 60 and random.random() < 0.2:
                return "forced_action"

        return None
