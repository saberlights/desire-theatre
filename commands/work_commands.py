"""
打工命令
"""

import re
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api

from ..core.models import DTCharacter
from ..extensions.earning_system import EarningSystem


class DTWorkCommand(BaseCommand):
    """打工赚钱命令"""

    command_name = "dt_work"
    command_description = "打工赚取爱心币"
    command_pattern = r"^/(打工|work|赚钱)(?:\s+(.+))?$"

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
        work_type = match.group(2).strip() if match and match.group(2) else None

        if not work_type:
            # 显示打工列表
            work_list = f"""💼 【打工赚钱】

💰 当前爱心币: {char['coins']}

━━━ 可选工作 ━━━
"""

            for name, config in EarningSystem.WORK_TYPES.items():
                min_r, max_r = config["base_reward"]
                work_list += f"\n💼 {name}"
                work_list += f"\n   {config['description']}"
                work_list += f"\n   ⏰ {config['duration_hours']}小时 | 💰 {min_r}-{max_r}币"

                # 显示需求
                if "requirements" in config:
                    reqs = []
                    for attr, value in config["requirements"].items():
                        attr_names = {
                            "intimacy": "亲密", "corruption": "堕落",
                            "shame": "羞耻", "affection": "好感"
                        }
                        attr_name = attr_names.get(attr, attr)

                        if isinstance(value, str) and value.startswith("<"):
                            reqs.append(f"{attr_name}<{value[1:]}")
                        else:
                            reqs.append(f"{attr_name}≥{value}")

                    work_list += f"\n   📋 需求: {', '.join(reqs)}"

                work_list += "\n"

            work_list += """
━━━ 使用方法 ━━━
/打工 <工作名称>

例如: /打工 咖啡店

💡 Tip:
  • 每种工作6小时只能做一次
  • 好感度和魅力会影响收入
  • 完成动作也能获得爱心币！"""

            await self.send_text(work_list.strip())
            return True, "显示打工列表", True

        # 执行打工
        success, message, reward = await EarningSystem.work(user_id, chat_id, work_type)

        if success:
            await self.send_text(f"✅ {message}")
        else:
            await self.send_text(f"❌ {message}")

        return success, message, success
