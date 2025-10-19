"""
道具系统心理效果增强模块
"""

import random
import time
import json
from typing import Dict, Tuple, Optional

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ..core.models import DTMemory

logger = get_logger("dt_item_enhanced")


class ItemPsychologySystem:
    """道具心理效果系统"""

    @staticmethod
    def generate_item_use_scene(item: Dict, character: Dict) -> Tuple[Optional[str], Optional[Dict]]:
        """
        生成使用道具时的场景描述和心理反应

        返回: (场景描述消息, 额外心理效果)
        """
        item_name = item["item_name"]
        item_id = item["item_id"]
        category = item["item_category"]

        shame = character.get("shame", 50)
        corruption = character.get("corruption", 0)
        resistance = character.get("resistance", 50)

        message_parts = []
        extra_effects = {}

        # === 根据道具类型生成不同的场景 ===
        if item_id == "aphrodisiac":  # 催情剂
            message_parts.append("🍷 你递给她一杯水...")
            if resistance > 60:
                message_parts.append("\"...这水有点奇怪...你在里面加了什么？\"")
                message_parts.append("她警惕地看着你，但还是喝了下去...")
                extra_effects["trust"] = -5
            elif corruption > 50:
                message_parts.append("她心知肚明，但没有拒绝...")
                message_parts.append("\"...又是这个...你真坏...\"")
                extra_effects["submission"] = 5
            else:
                message_parts.append("她不疑有他，一饮而尽...")
                message_parts.append("\"...怎么...身体突然好热...\"")
                extra_effects["shock"] = 10

            message_parts.append("\n几分钟后，她的身体开始起反应...")
            message_parts.append("她的呼吸变得急促，脸颊泛起不自然的红晕...")

        elif item_id == "collar":  # 项圈
            message_parts.append("🎀 你拿出了项圈...")
            if shame > 70:
                message_parts.append("\"不...不要...这太羞耻了...\"")
                message_parts.append("她的眼泪在眼眶里打转，但没有逃开")
                extra_effects["shame"] = 10
                extra_effects["resistance"] = -8
            elif corruption > 60:
                message_parts.append("\"...这是要给我的吗？\"")
                message_parts.append("她主动低下头，等待你为她戴上...")
                extra_effects["submission"] = 10
            else:
                message_parts.append("她犹豫了一下，最终还是接受了...")
                extra_effects["corruption"] = 5

            message_parts.append("\n你为她扣上项圈的那一刻...")
            message_parts.append("仿佛某种无形的契约被建立了")

        elif item_id == "handcuffs":  # 手铐
            message_parts.append("⛓️ 你拿出了手铐...")
            if resistance > 70:
                message_parts.append("\"等等...你想做什么？！\"")
                message_parts.append("她下意识地后退了一步")
                extra_effects["resistance"] = 5
                extra_effects["fear"] = 10
            elif submission > 60:
                message_parts.append("她乖巧地伸出双手...")
                message_parts.append("\"...请温柔一点...\"")
                extra_effects["submission"] = 12
            else:
                message_parts.append("她的身体微微颤抖，但还是允许了...")
                extra_effects["corruption"] = 8

            message_parts.append("\n'咔嚓'一声，手铐扣上了...")
            message_parts.append("她现在完全无法抵抗你了")

        elif item_id == "chocolate":  # 巧克力
            if corruption < 30:
                message_parts.append("🍫 你递给她一块巧克力...")
                message_parts.append("\"谢谢你...\" 她微笑着接过")
                message_parts.append("这样的温柔让她感到安心")
                extra_effects["trust"] = 3
            else:
                message_parts.append("🍫 巧克力...在这种时候？")
                message_parts.append("她有些意外，但也有些欣慰")
                extra_effects["affection"] = 5

        elif item_id == "massage_oil":  # 按摩油
            message_parts.append("💧 你拿出了按摩油...")
            if intimacy := character.get("intimacy", 0) > 60:
                message_parts.append("\"又要...按摩吗...\"")
                message_parts.append("她已经知道'按摩'意味着什么了...")
                extra_effects["arousal"] = 10
                extra_effects["anticipation"] = 15
            else:
                message_parts.append("\"按摩？好啊...\"")
                message_parts.append("她还不知道接下来会发生什么...")
                extra_effects["trust"] = 5

            message_parts.append("\n你在手心倒出油液...")
            message_parts.append("滑腻的触感让她的身体不自觉地颤抖")

        elif item_id == "red_wine":  # 红酒
            message_parts.append("🍷 你们一起喝了红酒...")
            if corruption < 40:
                message_parts.append("微醺的感觉让她放松了警惕...")
                extra_effects["resistance"] = -8
            else:
                message_parts.append("酒精让她变得更加大胆...")
                extra_effects["desire"] = 8

        # 组合消息
        if message_parts:
            return "\n".join(message_parts), extra_effects

        return None, None

    @staticmethod
    async def create_item_memory(user_id: str, chat_id: str, item: Dict, character: Dict):
        """
        为重要道具使用创建记忆
        """
        item_name = item["item_name"]
        item_id = item["item_id"]
        intensity = item.get("intensity_level", 1)

        # 只为高强度道具创建记忆
        if intensity < 5:
            return

        # 构建记忆内容
        if item_id == "aphrodisiac":
            memory_content = f"那次你在她的水里加了催情剂，她失去了控制..."
            emotional_tag = "betrayal"
            importance = 9
        elif item_id == "collar":
            memory_content = f"你为她戴上项圈的那一刻，她接受了从属地位"
            emotional_tag = "submission"
            importance = 8
        elif item_id == "handcuffs":
            memory_content = f"她被手铐锁住时，完全失去了抵抗能力"
            emotional_tag = "helplessness"
            importance = 9
        elif item_id == "blindfold":
            memory_content = f"蒙上眼睛后，她的其他感官变得异常敏锐"
            emotional_tag = "vulnerability"
            importance = 6
        else:
            return  # 其他道具不创建记忆

        # 保存记忆
        memory_id = f"item_{item_id}_{int(time.time())}"

        await database_api.db_save(
            DTMemory,
            data={
                "memory_id": memory_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "memory_type": "item_use",
                "memory_content": memory_content,
                "emotional_tags": json.dumps([emotional_tag]),
                "importance": importance,
                "created_at": time.time(),
                "last_referenced": time.time(),
                "decay_rate": 0.08  # 道具记忆衰减中等
            },
            key_field="memory_id",
            key_value=memory_id
        )

        logger.info(f"创建道具记忆: {memory_content}")
