"""
付费服务命令 - 援助交际(爸爸活)
"""

import re
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api

from ..core.models import DTCharacter
from ..extensions.paid_service_system import PaidServiceSystem


class DTPapaKatsuCommand(BaseCommand):
    """援助交际命令"""

    command_name = "dt_papa_katsu"
    command_description = "援助交际服务"
    command_pattern = r"^/(援交|爸爸活|包养)(?:\s+(.+))?$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色数据
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            await self.send_text("❌ 还没有创建角色！\n使用 /开始 <人格> 来开始游戏")
            return True, "角色未创建", True

        match = re.match(self.command_pattern, self.message.processed_plain_text)
        service_type = match.group(2).strip() if match and match.group(2) else None

        if not service_type:
            # 显示服务列表
            service_list = f"""💰 【援助交际服务】

💵 当前爱心币: {char['coins']}

━━━ 可选服务 ━━━
"""

            for name, config in PaidServiceSystem.PAPA_KATSU_SERVICES.items():
                price = config["price"]
                service_list += f"\n💸 {name} - {price}💰"
                service_list += f"\n   {config['description']}"

                # 显示需求
                if "requirements" in config:
                    reqs = []
                    for attr, value in config["requirements"].items():
                        attr_names = {
                            "intimacy": "亲密", "corruption": "堕落",
                            "shame": "羞耻", "desire": "欲望"
                        }
                        attr_name = attr_names.get(attr, attr)

                        if isinstance(value, str) and value.startswith("<"):
                            reqs.append(f"{attr_name}<{value[1:]}")
                        else:
                            reqs.append(f"{attr_name}≥{value}")

                    service_list += f"\n   📋 需求: {', '.join(reqs)}"

                # 显示风险
                if "arrest_risk" in config:
                    risk_percent = int(config["arrest_risk"] * 100)
                    service_list += f"\n   ⚠️ 逮捕风险: {risk_percent}%"

                service_list += "\n"

            service_list += """
━━━ 使用方法 ━━━
/援交 <服务名称>
/爸爸活 <服务名称>

例如: /援交 约会

⚠️ 警告:
  • 需要花费爱心币
  • 高级服务有被警察逮捕的风险
  • 被捕后会被罚款并严重损害关系
  • 请谨慎选择！"""

            await self.send_text(service_list.strip())
            return True, "显示服务列表", True

        # 请求服务
        success, message, effects = await PaidServiceSystem.request_service(
            user_id, chat_id, service_type
        )

        if success:
            await self.send_text(f"✅ {message}")
            # 服务成功后，返回效果供LLM生成回复
            return True, message, True
        else:
            await self.send_text(f"❌ {message}")
            return False, message, False
