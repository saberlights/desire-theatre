"""
服装系统心理效果增强模块
"""

import random
import time
import json
from typing import Dict, Tuple, Optional

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ...core.models import DTMemory

logger = get_logger("dt_outfit_enhanced")


class OutfitPsychologySystem:
    """服装心理效果系统"""

    @staticmethod
    def generate_outfit_reaction(outfit: Dict, character: Dict, is_first_time: bool) -> Tuple[Optional[str], Optional[Dict]]:
        """
        生成换装后的心理反应

        返回: (心理反应消息, 即时属性效果)
        """
        outfit_name = outfit["outfit_name"]
        category = outfit["outfit_category"]
        shame = character.get("shame", 50)
        corruption = character.get("corruption", 0)

        # 计算羞耻反应强度
        shame_impact = outfit.get("shame_modifier", 0)

        # 构建心理反应消息
        message_parts = []
        instant_effects = {}

        # === 首次穿着特殊反应 ===
        if is_first_time:
            message_parts.append(f"👗 【第一次穿{outfit_name}】\n")

            if category == "lingerie":
                if shame > 60:
                    message_parts.append("她的脸瞬间涨红，手指颤抖着...")
                    message_parts.append("\"这...这也太...\"")
                    message_parts.append("她几乎不敢看镜子里的自己")
                    instant_effects["shame"] = 10
                    instant_effects["resistance"] = 5
                elif shame > 30:
                    message_parts.append("她咬着嘴唇，在镜子前转了一圈...")
                    message_parts.append("\"好羞耻...但是...\"")
                    instant_effects["arousal"] = 8
                else:
                    message_parts.append("她在镜子前摆出诱人的姿态...")
                    message_parts.append("\"...你喜欢吗？\"")
                    instant_effects["arousal"] = 15
                    instant_effects["desire"] = 10

            elif category == "cosplay":
                if corruption < 30:
                    message_parts.append("\"让我穿成这样...你是认真的吗？\"")
                    message_parts.append("她的眼神既羞涩又期待")
                    instant_effects["shame"] = -5
                    instant_effects["submission"] = 5
                else:
                    message_parts.append("她摆出角色扮演的姿势...")
                    message_parts.append("\"主人，请尽情使用我吧...\"")
                    instant_effects["submission"] = 12
                    instant_effects["arousal"] = 10

            elif category == "sexy":
                message_parts.append("她穿上紧身裙，身体曲线一览无余...")
                message_parts.append("\"...这样真的可以吗？\"")
                instant_effects["arousal"] = 6
                instant_effects["shame"] = -3

            elif category == "normal":
                message_parts.append("她换上了日常的服装，稍微放松了一些")
                instant_effects["shame"] = 5
                instant_effects["resistance"] = 3

        # === 习惯性换装反应（非首次）===
        else:
            # 根据属性给出不同反应
            if category == "lingerie" and corruption > 60:
                reactions = [
                    "她熟练地换上了情趣内衣，已经习惯了这种暴露...",
                    "\"又是这件...\" 她叹了口气，但没有抗拒",
                    "她的动作变得自然了，甚至有些主动..."
                ]
                message_parts.append(random.choice(reactions))
                instant_effects["corruption"] = 2  # 继续堕落

            elif category == "cosplay" and shame < 20:
                message_parts.append("她已经完全适应了角色扮演，甚至开始享受...")
                instant_effects["arousal"] = 5

        # 组合消息
        if message_parts:
            return "\n".join(message_parts), instant_effects

        return None, None

    @staticmethod
    async def create_outfit_memory(user_id: str, chat_id: str, outfit: Dict, character: Dict):
        """
        为首次穿着创建记忆

        这个记忆会影响后续的对话和反应
        """
        outfit_name = outfit["outfit_name"]
        category = outfit["outfit_category"]
        shame = character.get("shame", 50)

        # 构建记忆内容
        if category == "lingerie":
            if shame > 60:
                memory_content = f"第一次穿{outfit_name}的时候，她羞耻到几乎哭了出来"
                emotional_tag = "humiliation"
            elif shame > 30:
                memory_content = f"她第一次穿{outfit_name}时，内心矛盾地既羞耻又兴奋"
                emotional_tag = "conflicted"
            else:
                memory_content = f"她穿上{outfit_name}时，眼神中充满了诱惑"
                emotional_tag = "seductive"
        elif category == "cosplay":
            memory_content = f"她第一次穿{outfit_name}进行角色扮演，标志着顺从度的提升"
            emotional_tag = "submission"
        elif category == "sexy":
            memory_content = f"她穿上{outfit_name}，意识到自己的身体对你有吸引力"
            emotional_tag = "awareness"
        else:
            return  # 普通服装不创建记忆

        # 保存记忆
        memory_id = f"outfit_{outfit['outfit_id']}_{int(time.time())}"

        await database_api.db_save(
            DTMemory,
            data={
                "memory_id": memory_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "memory_type": "outfit_first_wear",
                "memory_content": memory_content,
                "emotional_tags": json.dumps([emotional_tag]),
                "importance": 7 if category == "lingerie" else 5,
                "created_at": time.time(),
                "last_referenced": time.time(),
                "decay_rate": 0.05  # 衣服记忆衰减较慢
            },
            key_field="memory_id",
            key_value=memory_id
        )

        logger.info(f"创建服装记忆: {memory_content}")


# 为了兼容性，添加 OutfitSystem 别名和初始化方法
class OutfitSystem:
    """服装系统（兼容类）"""

    @staticmethod
    async def initialize_outfits():
        """初始化服装系统（当前无需初始化）"""
        logger.info("服装系统初始化完成")
        pass

    @staticmethod
    async def unlock_outfit(user_id: str, chat_id: str, outfit_id: str):
        """解锁服装"""
        from ...core.models import DTUserOutfit

        # 检查是否已解锁
        existing = await database_api.db_get(
            DTUserOutfit,
            filters={"user_id": user_id, "chat_id": chat_id, "outfit_id": outfit_id},
            single_result=True
        )

        if existing:
            logger.warning(f"服装已解锁: {user_id} - {outfit_id}")
            return

        # 解锁服装
        await database_api.db_save(
            DTUserOutfit,
            data={
                "user_id": user_id,
                "chat_id": chat_id,
                "outfit_id": outfit_id,
                "unlocked_at": time.time()
            },
            key_field="user_id",
            key_value=user_id
        )

        logger.info(f"解锁服装: {user_id} - {outfit_id}")

    @staticmethod
    async def equip_outfit(user_id: str, chat_id: str, outfit_id: str, character: Dict):
        """穿上服装（带心理反应）"""
        from ...core.models import DTUserOutfit, DTOutfit

        # 检查是否已解锁
        owned = await database_api.db_get(
            DTUserOutfit,
            filters={"user_id": user_id, "chat_id": chat_id, "outfit_id": outfit_id},
            single_result=True
        )

        if not owned:
            return False, None, None

        # 获取服装信息
        outfit = await database_api.db_get(
            DTOutfit,
            filters={"outfit_id": outfit_id},
            single_result=True
        )

        if not outfit:
            return False, None, None

        # 更新角色当前穿着
        character["current_outfit"] = outfit_id
        await database_api.db_save(
            character.__class__,
            data=character,
            key_field="user_id",
            key_value=user_id
        )

        # 检查是否第一次穿着
        is_first_time = not owned.get("first_worn", False)
        if is_first_time:
            owned["first_worn"] = True
            await database_api.db_save(
                DTUserOutfit,
                data=owned,
                key_field="user_id",
                key_value=user_id
            )

        # 生成心理反应
        psychological_msg, instant_effects = OutfitPsychologySystem.generate_outfit_reaction(
            outfit, character, is_first_time
        )

        # 创建记忆（如果是第一次）
        if is_first_time:
            await OutfitPsychologySystem.create_outfit_memory(user_id, chat_id, outfit, character)

        return True, psychological_msg, instant_effects or {}

