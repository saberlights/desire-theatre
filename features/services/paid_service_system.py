"""
付费服务系统 - 援助交际等付费互动
"""

import random
from typing import Tuple, Dict

from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ...core.models import DTCharacter
from ...systems.attributes.attribute_system import AttributeSystem

logger = get_logger("dt_paid_service")


class PaidServiceSystem:
    """付费服务系统"""

    # 援助交际服务配置
    PAPA_KATSU_SERVICES = {
        "约会": {
            "price": 100,
            "description": "和她外出约会，去餐厅、电影院或购物",
            "requirements": {"corruption": 50, "shame": "<60"},
            "effects": {
                "affection": 5,
                "intimacy": 8,
                "desire": 3,
                "shame": -2,
                "corruption": 1
            },
            "intensity": 3,
            "success_messages": [
                "她有些犹豫，但还是接受了你的提议...",
                "虽然有点不好意思，但约会的氛围很好...",
                "她似乎很享受这次约会，虽然心里有点复杂..."
            ]
        },
        "私人摄影": {
            "price": 200,
            "description": "为她拍摄私房照，可以选择服装和姿势",
            "requirements": {"corruption": 60, "shame": "<50", "intimacy": 30},
            "effects": {
                "intimacy": 6,
                "desire": 8,
                "arousal": 10,
                "shame": -5,
                "corruption": 3
            },
            "intensity": 5,
            "success_messages": [
                "她换上了你选的衣服，害羞地摆出姿势...",
                "虽然很不好意思，但她还是配合了拍摄...",
                "镜头下的她格外诱人，她自己也意识到了这一点..."
            ]
        },
        "亲密接触": {
            "price": 300,
            "description": "更进一步的身体接触，抚摸和爱抚",
            "requirements": {"corruption": 70, "shame": "<40", "intimacy": 50},
            "effects": {
                "intimacy": 10,
                "desire": 15,
                "arousal": 20,
                "shame": -8,
                "corruption": 5,
                "submission": 5
            },
            "intensity": 7,
            "success_messages": [
                "她的身体微微颤抖，但没有拒绝...",
                "虽然很害羞，但她的身体很诚实...",
                "她闭上眼睛，任由你抚摸..."
            ]
        },
        "特殊服务": {
            "price": 500,
            "description": "提供更亲密的特殊服务...",
            "requirements": {"corruption": 80, "shame": "<30", "intimacy": 70, "desire": 50},
            "effects": {
                "intimacy": 15,
                "desire": 20,
                "arousal": 30,
                "shame": -12,
                "corruption": 8,
                "submission": 10
            },
            "intensity": 9,
            "arrest_risk": 0.10,  # 10%被抓风险
            "success_messages": [
                "她咬着嘴唇，缓缓配合着...",
                "虽然心里充满罪恶感，但她还是做了...",
                "她的眼神复杂，但身体却很配合..."
            ],
            "arrest_messages": [
                "突然传来敲门声——是警察！",
                "糟了...有人举报了，警察破门而入！",
                "警笛声响起，这下麻烦了..."
            ]
        }
    }

    @staticmethod
    async def request_service(
        user_id: str,
        chat_id: str,
        service_type: str
    ) -> Tuple[bool, str, Dict]:
        """
        请求付费服务

        Returns:
            (是否成功, 消息, 效果字典)
        """
        # 检查服务类型
        if service_type not in PaidServiceSystem.PAPA_KATSU_SERVICES:
            return False, f"未知的服务类型: {service_type}", {}

        service_config = PaidServiceSystem.PAPA_KATSU_SERVICES[service_type]

        # 获取角色
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            return False, "角色不存在", {}

        # 检查金币是否足够
        price = service_config["price"]
        if char.get("coins", 0) < price:
            return False, f"爱心币不足！需要{price}币，当前只有{char.get('coins', 0)}币", {}

        # 检查属性需求
        requirements = service_config.get("requirements", {})
        for attr, value in requirements.items():
            char_value = char.get(attr, 0)

            if isinstance(value, str) and value.startswith("<"):
                threshold = int(value[1:])
                if char_value >= threshold:
                    attr_names = {
                        "corruption": "堕落度", "shame": "羞耻心",
                        "intimacy": "亲密度", "desire": "欲望值"
                    }
                    return False, f"她的{attr_names.get(attr, attr)}太高了，拒绝了你的请求（需要<{threshold}，当前{char_value}）", {}
            else:
                threshold = int(value)
                if char_value < threshold:
                    attr_names = {
                        "corruption": "堕落度", "shame": "羞耻心",
                        "intimacy": "亲密度", "desire": "欲望值"
                    }
                    return False, f"你们的关系还不够，她拒绝了（{attr_names.get(attr, attr)}需要≥{threshold}，当前{char_value}）", {}

        # 检查逮捕风险
        arrest_risk = service_config.get("arrest_risk", 0)
        is_arrested = False

        if arrest_risk > 0 and random.random() < arrest_risk:
            # 被抓了！
            is_arrested = True

            # 扣除罚款和金币（双重损失）
            penalty_coins = price + 300  # 服务费损失 + 300罚款
            char["coins"] = max(0, char.get("coins", 0) - penalty_coins)

            # 属性惩罚
            char["affection"] = AttributeSystem.clamp(char.get("affection", 0) - 30)
            char["trust"] = AttributeSystem.clamp(char.get("trust", 0) - 20)
            char["shame"] = AttributeSystem.clamp(char.get("shame", 0) + 50)

            await database_api.db_save(
                DTCharacter,
                data=char,
                key_field="user_id",
                key_value=user_id
            )

            arrest_message = random.choice(service_config["arrest_messages"])

            result_msg = f"""🚨 【援交被捕】

{arrest_message}

⚠️ 严重后果:
  爱心币 -{penalty_coins} (服务费{price} + 罚款300)
  好感 -30
  信任 -20
  羞耻 +50

💵 当前余额: {char['coins']}

她哭着被带走了...你们的关系受到了严重损害。"""

            logger.warning(f"援交被捕: {user_id} - {service_type}")
            return False, result_msg, {}

        # 成功完成服务
        # 扣除金币
        char["coins"] = char.get("coins", 0) - price

        # 应用效果
        effects = service_config["effects"].copy()
        for attr, change in effects.items():
            char[attr] = AttributeSystem.clamp(char.get(attr, 0) + change)

        await database_api.db_save(
            DTCharacter,
            data=char,
            key_field="user_id",
            key_value=user_id
        )

        # 构建效果文本
        effect_parts = []
        attr_names = {
            "affection": "好感", "intimacy": "亲密", "trust": "信任",
            "submission": "顺从", "desire": "欲望", "corruption": "堕落",
            "arousal": "兴奋", "resistance": "抵抗", "shame": "羞耻"
        }
        for attr, change in effects.items():
            name = attr_names.get(attr, attr)
            sign = "+" if change > 0 else ""
            effect_parts.append(f"{name}{sign}{change}")

        success_message = random.choice(service_config["success_messages"])

        result_msg = f"""💰 【{service_type}】

{success_message}

💸 花费: {price}爱心币
💵 剩余余额: {char['coins']}

📊 效果: {', '.join(effect_parts)}"""

        if arrest_risk > 0:
            result_msg += f"\n\n⚠️ 注意: 此服务有{int(arrest_risk*100)}%被警察逮捕的风险！"

        logger.info(f"付费服务: {user_id} - {service_type}, 花费{price}币")
        return True, result_msg, effects
