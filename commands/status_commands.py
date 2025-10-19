"""
状态查询命令
"""

import re
import json
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api

from ..core.models import DTCharacter
from ..core.personality_system import PersonalitySystem


class DTQuickStatusCommand(BaseCommand):
    """快速查看状态命令"""

    command_name = "dt_quick_status"
    command_description = "快速查看核心状态"
    command_pattern = r"^/(快看|quick)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            await self.send_text("❌ 还没有创建角色！\n使用 /开始 <人格> 来开始游戏")
            return True, "角色未创建", True

        from ..core.evolution_system import EvolutionSystem
        from ..core.career_system import CareerSystem
        from ..core.seasonal_system import SeasonalSystem
        from ..core.daily_limit_system import DailyInteractionSystem

        evolution_stage = char.get("evolution_stage", 1)
        stage_name = EvolutionSystem.get_stage_name(evolution_stage)

        # 获取职业和时间信息
        career_id = char.get("career", "high_school_student")
        career_info = CareerSystem.get_career_info(career_id)
        game_day = char.get("game_day", 1)
        season_info = SeasonalSystem.get_season_info(game_day)
        festival_info = SeasonalSystem.get_festival_by_day(game_day)
        _, _, remaining, limit = DailyInteractionSystem.check_can_interact(char)

        # 使用图片输出
        try:
            from ..utils.help_image_generator import HelpImageGenerator

            content = {
                "基础信息": {
                    "⭐ 阶段": f"{stage_name} ({evolution_stage}/5)",
                    "💰 爱心币": f"{char.get('coins', 0)}",
                    "📅 游戏日": f"第{game_day}天/42天",
                    f"{season_info['emoji']} 季节": season_info['name'],
                    f"{career_info['emoji']} 职业": career_info['name'],
                    "💬 今日互动": f"{remaining}/{limit}次"
                },
                "核心属性": {
                    "💕 好感": f"{char['affection']}/100 {'❤️'*(char['affection']//20)}",
                    "💗 亲密": f"{char['intimacy']}/100 {'💓'*(char['intimacy']//20)}",
                    "😈 堕落": f"{char['corruption']}/100 {'🔥'*(char['corruption']//20)}",
                    "💓 兴奋": f"{char['arousal']}/100 {'⚡'*(char['arousal']//20)}",
                    "😳 羞耻": f"{char['shame']}/100 {'💫'*(char['shame']//20)}"
                }
            }

            # 如果是节日,添加提示
            if festival_info:
                content["节日"] = {
                    f"{festival_info['emoji']} 今日": festival_info['name']
                }

            img_bytes, img_base64 = HelpImageGenerator.generate_status_image(
                "快速状态", content, width=1920
            )

            await self.send_image(img_base64)
            return True, "显示快速状态", True

        except Exception as e:
            # 降级到文本模式
            festival_text = ""
            if festival_info:
                festival_text = f"\n🎉 节日: {festival_info['emoji']} {festival_info['name']}"

            quick_status = f"""📊 【快速状态】

⭐ 阶段: {stage_name} ({evolution_stage}/5)
💰 爱心币: {char.get('coins', 0)}
📅 游戏日: 第{game_day}天/42天
{season_info['emoji']} 季节: {season_info['name']}
{career_info['emoji']} 职业: {career_info['name']}
💬 今日互动: {remaining}/{limit}次{festival_text}

💕 好感: {char['affection']}/100 {'❤️'*(char['affection']//20)}
💗 亲密: {char['intimacy']}/100 {'💓'*(char['intimacy']//20)}
😈 堕落: {char['corruption']}/100 {'🔥'*(char['corruption']//20)}
💓 兴奋: {char['arousal']}/100 {'⚡'*(char['arousal']//20)}
😳 羞耻: {char['shame']}/100 {'💫'*(char['shame']//20)}

💡 输入 /看 查看详细状态"""

            await self.send_text(quick_status.strip())
            return True, "显示快速状态", True


class DTStatusCommand(BaseCommand):
    """查看状态命令"""

    command_name = "dt_status"
    command_description = "查看角色状态"
    command_pattern = r"^/(看|status|状态)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            await self.send_text("❌ 还没有创建角色！\n使用 /开始 <人格> 来开始游戏")
            return True, "角色未创建", True

        personality = PersonalitySystem.get_personality(char["personality_type"])
        evolution_stage = char.get("evolution_stage", 1)
        traits = json.loads(char.get("personality_traits", "[]"))

        # 获取进化阶段信息
        from ..core.evolution_system import EvolutionSystem
        stage_name = EvolutionSystem.get_stage_name(evolution_stage)
        next_stage_hint = EvolutionSystem.get_next_stage_hint(char)

        # 获取职业信息
        from ..core.career_system import CareerSystem
        career_id = char.get("career", "high_school_student")
        career_info = CareerSystem.get_career_info(career_id)
        daily_income = CareerSystem.daily_income(char)

        # 获取季节和时间信息
        from ..core.seasonal_system import SeasonalSystem
        game_day = char.get("game_day", 1)
        season_info = SeasonalSystem.get_season_info(game_day)
        festival_info = SeasonalSystem.get_festival_by_day(game_day)
        weather = SeasonalSystem.get_weather(game_day)

        # 获取每日互动信息
        from ..core.daily_limit_system import DailyInteractionSystem
        _, _, remaining, limit = DailyInteractionSystem.check_can_interact(char)

        # 使用图片输出
        try:
            from ..utils.help_image_generator import HelpImageGenerator

            content = {
                "角色信息": {
                    "🎭 人格": personality['name'],
                    "⭐ 进化阶段": f"{stage_name} (阶段{evolution_stage}/5)",
                    "🎯 已解锁特质": ', '.join(traits) if traits else '无',
                    "💰 爱心币": str(char.get('coins', 0))
                },
                "时间与职业": {
                    "📅 游戏日": f"第{game_day}天 / 42天",
                    f"{season_info['emoji']} 季节": f"{season_info['name']}天 - {season_info['description']}",
                    f"{weather['emoji']} 天气": weather['description'],
                    f"{career_info['emoji']} 职业": f"{career_info['name']} (日薪{daily_income}币)",
                    "💬 今日互动": f"{remaining}/{limit}次"
                },
                "显性属性": {
                    "💕 好感度": f"{char['affection']}/100 {'❤️'*(char['affection']//20)}",
                    "💗 亲密度": f"{char['intimacy']}/100 {'💓'*(char['intimacy']//20)}",
                    "🤝 信任度": f"{char['trust']}/100 {'🤝'*(char['trust']//20)}"
                },
                "隐性属性": {
                    "👑 顺从度": f"{char['submission']}/100",
                    "😈 堕落度": f"{char['corruption']}/100",
                    "🔥 欲望值": f"{char['desire']}/100"
                },
                "当前状态": {
                    "💓 兴奋度": f"{char['arousal']}/100",
                    "🛡️ 抵抗力": f"{char['resistance']}/100",
                    "😳 羞耻心": f"{char['shame']}/100",
                    "😊 心情值": f"{char.get('mood_gauge', 50)}/100"
                },
                "统计数据": {
                    "📈 互动次数": str(char['interaction_count']),
                    "🏆 完成挑战": str(char['challenges_completed'])
                }
            }

            # 如果是节日,添加节日信息
            if festival_info:
                content["节日特别"] = {
                    f"{festival_info['emoji']} 节日": festival_info['name'],
                    "✨ 描述": festival_info['description']
                }

            # 如果有进化提示，添加到最后
            if next_stage_hint and next_stage_hint.strip():
                content["进化提示"] = {"💡 提示": next_stage_hint.replace("💡 ", "")}

            img_bytes, img_base64 = HelpImageGenerator.generate_status_image(
                "角色状态", content, width=1920
            )

            await self.send_image(img_base64)
            return True, "显示状态", True

        except Exception as e:
            # 降级到文本模式
            festival_text = ""
            if festival_info:
                festival_text = f"\n🎉 节日: {festival_info['emoji']} {festival_info['name']}"

            status_text = f"""
📊 【欲望剧场 - 角色状态】

🎭 人格: {personality['name']}
⭐ 进化阶段: {stage_name} (阶段{evolution_stage}/5)
🎯 已解锁特质: {', '.join(traits) if traits else '无'}
💰 爱心币: {char.get('coins', 0)}

⏰ 时间与职业:
  📅 游戏日: 第{game_day}天 / 42天
  {season_info['emoji']} 季节: {season_info['name']}天 - {season_info['description']}
  {weather['emoji']} 天气: {weather['description']}{festival_text}
  {career_info['emoji']} 职业: {career_info['name']} (日薪{daily_income}币)
  💬 今日互动: {remaining}/{limit}次

💕 显性属性:
  好感度: {char['affection']}/100 {'❤️'*(char['affection']//20)}
  亲密度: {char['intimacy']}/100 {'💗'*(char['intimacy']//20)}
  信任度: {char['trust']}/100 {'🤝'*(char['trust']//20)}

🔥 隐性属性:
  顺从度: {char['submission']}/100
  堕落度: {char['corruption']}/100
  欲望值: {char['desire']}/100

💫 当前状态:
  兴奋度: {char['arousal']}/100
  抵抗力: {char['resistance']}/100
  羞耻心: {char['shame']}/100
  心情值: {char.get('mood_gauge', 50)}/100

📈 统计:
  互动次数: {char['interaction_count']}
  完成挑战: {char['challenges_completed']}

{next_stage_hint}
"""

            await self.send_text(status_text.strip())
            return True, "显示状态", True


class DTHelpCommand(BaseCommand):
    """帮助命令"""

    command_name = "dt_help"
    command_description = "显示欲望剧场帮助信息"
    command_pattern = r"^/(dt|帮助|help)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        await self._show_main_help()
        return True, "显示帮助", True

    async def _show_main_help(self):
        """显示主帮助页面 - 包含所有实际可用命令"""
        try:
            from ..utils.help_image_generator import HelpImageGenerator

            sections = [
                ("🎮 核心", [
                    "/开始 傲娇 - 创建角色 (傲娇/天真/妖媚/害羞/高冷)",
                    "/看 - 详细状态 | /快看 - 快速状态",
                    "/重开 - 重置游戏 (需二次确认)",
                    "/聊天 内容 - 自由对话"
                ]),
                ("💕 互动 (50+)", [
                    "温柔: /早安 /晚安 /牵手 /摸头 /抱",
                    "亲密: /亲 嘴唇 /摸 腰 /表白 /凝视",
                    "诱惑: /挑逗 /舔 /脱 /耳语",
                    "支配: /壁咚 /命令 /调教 /推倒",
                    "极限: /进入 /开发 /羞辱",
                    "风险: /强吻 /突然袭击 (有失败风险)",
                    "查看所有: /快速参考"
                ]),
                ("⏰ 时间系统", [
                    "/明日 - 推进到下一天",
                    "/季节 - 查看季节和节日信息",
                    "• 42天周期，每日3-6次互动",
                    "• 春夏秋冬，8个节日+20%加成"
                ]),
                ("💼 职业养成", [
                    "/职业 - 查看职业信息",
                    "/晋升 - 职业晋升",
                    "/打工 咖啡店 - 打工赚钱",
                    "• 12种职业路线",
                    "• 每日自动发放工资"
                ]),
                ("🎬 事件 & 结局", [
                    "/选择 1 - 事件/人格选择",
                    "/结局 - 查看当前结局",
                    "/结局预览 - 预览所有可能结局",
                    "• 13种随机事件",
                    "• 32种结局"
                ]),
                ("🎁 物品系统", [
                    "/背包 - 查看道具",
                    "/用 道具名 - 使用道具",
                    "/服装列表 - 查看服装",
                    "/穿 服装名 - 穿上服装",
                    "/场景列表 - 查看场景",
                    "/去 场景名 - 切换场景"
                ]),
                ("💰 商店经济", [
                    "/商店 - 查看商店",
                    "/买道具 名称 - 购买道具",
                    "/买服装 名称 - 购买服装",
                    "/打工 工作名 - 打工赚钱",
                    "/援交 服务 - 付费服务(高风险)"
                ]),
                ("🎲 小游戏", [
                    "/真心话 - 问答游戏",
                    "/大冒险 - 任务游戏",
                    "/骰子 - 掷骰子"
                ]),
                ("🆘 辅助", [
                    "/快速参考 - 所有动作速查",
                    "/快速互动 - 随机选择动作",
                    "/推荐 - AI推荐下一步",
                    "/说明 - 完整游戏指南",
                    "/导出 - 导出存档",
                    "/导入 码 - 导入存档",
                    "/人格 - 双重人格状态"
                ])
            ]

            img_bytes, img_base64 = HelpImageGenerator.generate_help_image(
                "欲望剧场 v2.0 - 命令大全", sections, width=1400
            )

            await self.send_image(img_base64)
            return
        except Exception as e:
            import traceback
            traceback.print_exc()
            pass

        # 文本模式
        help_text = """
🎭 【欲望剧场 v2.0 - 命令大全】

🎮 核心
/开始 傲娇 - 创建角色 (傲娇/天真/妖媚/害羞/高冷)
/看 - 详细状态 | /快看 - 快速状态
/重开 - 重置游戏 (需二次确认)
/聊天 内容 - 自由对话

💕 互动 (50+)
温柔: /早安 /晚安 /牵手 /摸头 /抱
亲密: /亲 嘴唇 /摸 腰 /表白 /凝视
诱惑: /挑逗 /舔 /脱 /耳语
支配: /壁咚 /命令 /调教 /推倒
极限: /进入 /开发 /羞辱
风险: /强吻 /突然袭击 (有失败风险)
查看所有: /快速参考

⏰ 时间系统
/明日 - 推进到下一天
/季节 - 查看季节和节日信息
• 42天周期，每日3-6次互动
• 春夏秋冬，8个节日+20%加成

💼 职业养成
/职业 - 查看职业信息
/晋升 - 职业晋升
/打工 咖啡店 - 打工赚钱
• 12种职业路线
• 每日自动发放工资

🎬 事件 & 结局
/选择 1 - 事件/人格选择
/结局 - 查看当前结局
/结局预览 - 预览所有可能结局
• 13种随机事件
• 32种结局

🎁 物品系统
/背包 - 查看道具
/用 道具名 - 使用道具
/服装列表 - 查看服装
/穿 服装名 - 穿上服装
/场景列表 - 查看场景
/去 场景名 - 切换场景

💰 商店经济
/商店 - 查看商店
/买道具 名称 - 购买道具
/买服装 名称 - 购买服装
/打工 工作名 - 打工赚钱
/援交 服务 - 付费服务(高风险)

🎲 小游戏
/真心话 - 问答游戏
/大冒险 - 任务游戏
/骰子 - 掷骰子

🆘 辅助
/快速参考 - 所有动作速查
/快速互动 - 随机选择动作
/推荐 - AI推荐下一步
/说明 - 完整游戏指南
/导出 - 导出存档
/导入 码 - 导入存档
/人格 - 双重人格状态
"""
        await self.send_text(help_text.strip())

    async def _show_commands_help(self):
        """显示所有核心命令的详细列表"""
        try:
            from ..utils.help_image_generator import HelpImageGenerator

            sections = [
                ("核心管理命令", [
                    "/开始 <人格> - 创建新角色",
                    "  可选人格: 傲娇/天真/妖媚/害羞/高冷",
                    "  示例: /开始 傲娇",
                    "/看 - 查看角色详细状态",
                    "/快看 - 快速查看核心属性",
                    "/重开 - 重置游戏(需二次确认)",
                    "/导出 - 导出存档(Base64)",
                    "/导入 <码> - 导入存档",
                    "/快速互动 - 随机选择可用动作",
                    "/推荐 - AI推荐下一步行动"
                ]),
                ("服装系统命令", [
                    "/服装列表 - 查看所有服装",
                    "/穿 <服装> - 让她穿上服装",
                    "  示例: /穿 女仆装"
                ]),
                ("道具系统命令", [
                    "/背包 - 查看道具背包",
                    "/用 <道具> - 使用道具",
                    "/喂 <道具> - 喂她吃/喝道具",
                    "/戴 <道具> - 给她戴上道具(需顺从≥20)"
                ]),
                ("场景系统命令", [
                    "/场景列表 - 查看所有场景",
                    "/去 <场景> - 切换场景",
                    "  示例: /去 卧室"
                ]),
                ("小游戏命令", [
                    "/真心话 - 真心话游戏",
                    "/大冒险 - 大冒险游戏",
                    "/骰子 - 掷骰子"
                ]),
                ("经济系统命令", [
                    "/商店 - 查看商店",
                    "/买道具 <名> - 购买道具",
                    "/买服装 <名> - 购买服装",
                    "/打工 <工作> - 打工赚钱",
                    "/援交 <服务> - 付费援交服务"
                ]),
                ("帮助命令", [
                    "/dt - 显示主帮助",
                    "/帮助 <类别> - 查看分类帮助",
                    "  可用类别: 命令/游戏/动作/服装/道具/场景/小游戏/进化/经济"
                ])
            ]

            img_bytes, img_base64 = HelpImageGenerator.generate_help_image(
                "命令大全", sections, width=900
            )

            await self.send_image(img_base64)
            return

        except Exception as e:
            # 降级到文本模式
            pass

        help_text = """
📋 【命令大全】

━━━ 核心管理命令 ━━━
/开始 <人格>   创建新角色
  • 可选人格: 傲娇/天真/妖媚/害羞/高冷
  • 示例: /开始 傲娇

/看            查看角色详细状态
  • 显示所有属性、进化阶段、解锁特质
  • 包含进化进度提示

/快看          快速查看核心属性
  • 仅显示关键属性
  • 适合快速确认状态

/重开          重置游戏
  • 需二次确认
  • 删除所有数据(角色/记忆/道具/成就)
  • 输入 /确认重开 完成重置

/导出          导出存档
  • 生成存档码(Base64)
  • 可备份当前进度

/导入 <码>     导入存档
  • 恢复之前的存档
  • 会覆盖当前数据
  • 示例: /导入 ABC123XYZ...

/快速互动      随机选择可用动作
  • 自动筛选满足条件的动作
  • 适合新手体验

/推荐          AI推荐下一步行动
  • 根据当前阶段给出建议
  • 帮助规划进化路径

━━━ 服装系统命令 ━━━
/服装列表      查看所有服装
  • 显示已解锁和未解锁服装
  • 含解锁条件和属性加成

/穿 <服装>     让她穿上服装
  • 示例: /穿 女仆装
  • 需要先解锁该服装
  • 不同服装有不同加成

━━━ 道具系统命令 ━━━
/背包          查看道具背包
  • 显示拥有的所有道具
  • 道具数量和效果说明

/用 <道具>     使用道具
  • 示例: /用 爱情药水
  • 消耗品使用后消失
  • 部分道具有持续效果

/喂 <道具>     喂她吃/喝道具
  • 与 /用 类似
  • 更有互动感的描述

/戴 <道具>     给她戴上道具
  • 用于饰品类道具
  • 需顺从度≥20

━━━ 场景系统命令 ━━━
/场景列表      查看所有场景
  • 显示已解锁场景
  • 场景效果说明

/去 <场景>     切换场景
  • 示例: /去 卧室
  • 不同场景有属性加成
  • 影响互动效果

━━━ 小游戏命令 ━━━
/真心话        真心话游戏
  • 问她问题
  • 根据属性解锁不同问题
  • 奖励好感和信任

/大冒险        大冒险游戏
  • 让她完成任务
  • 高难度任务高奖励
  • 可快速提升属性

/骰子          掷骰子
  • 1-6点随机效果
  • 趣味性玩法

━━━ 经济系统命令 ━━━
/商店          查看商店
  • 道具和服装商品
  • 价格和效果一览

/买道具 <名>   购买道具
  • 示例: /买道具 爱情药水
  • 消耗爱心币

/买服装 <名>   购买服装
  • 示例: /买服装 女仆装
  • 需满足解锁条件

/打工 <工作>   打工赚钱
  • 12种工作可选
  • 普通工作: 咖啡店/便利店/家教/餐厅/搬运工/夜班保安
  • NSFW工作: 牛郎/男公关/情趣推销/健身教练/AV男优
  • 示例: /打工 咖啡店
  • 有冷却时间

/援交 <服务>   付费援交服务
/爸爸活 <服务> (同上)
  • 花钱享受服务
  • 可选: 约会/私人摄影/亲密接触/特殊服务
  • 示例: /援交 约会
  • 特殊服务有风险

━━━ 帮助命令 ━━━
/dt            显示主帮助
/帮助 <类别>   查看分类帮助
  • 可用类别: 命令/游戏/动作/服装/道具/场景/小游戏/进化/经济

💡 所有命令都以 / 开头
💡 命令不区分中英文(部分支持)
💡 带 <> 的参数为必需，带 [] 的为可选
"""
        await self.send_text(help_text.strip())

    async def _show_game_help(self):
        """显示游戏管理帮助"""
        # 尝试使用图片模式
        try:
            from ..utils.help_image_generator import HelpImageGenerator

            sections = [
                ("基础命令", [
                    "/开始 <人格> - 开始游戏",
                    "/看 - 查看详细状态",
                    "/快看 - 快速查看",
                    "/重开 - 重置游戏",
                    "/导出 - 导出存档",
                    "/导入 <码> - 导入存档"
                ]),
                ("九维属性系统", [
                    "💕 显性属性 (AI可见)",
                    "  好感 - 喜欢程度",
                    "  亲密 - 关系深度",
                    "  信任 - 信任度",
                    "",
                    "🔥 隐性属性 (影响AI)",
                    "  顺从 - 服从意愿",
                    "  堕落 - 调教程度",
                    "  欲望 - 欲望强度",
                    "",
                    "💫 状态属性 (波动)",
                    "  兴奋 - 当前兴奋度",
                    "  抵抗 - 反抗意志",
                    "  羞耻 - 羞耻感"
                ]),
                ("属性冲突系统", [
                    "⚖️ 属性相互影响",
                    "• 高羞耻(>60) → 抑制堕落30%",
                    "• 高抵抗(>70) → 抑制顺从40%",
                    "• 高信任(>70) → 抑制抵抗50%",
                    "• 高堕落(>50) → 抑制羞耻恢复60%"
                ]),
                ("属性协同系统", [
                    "⚡ 属性配合加成",
                    "• 好感+信任 → 亲密+30%",
                    "• 欲望+兴奋 → 堕落+40%",
                    "• 顺从+堕落 → 羞耻崩溃+50%"
                ]),
                ("契合度系统", [
                    "🎯 状态匹配触发暴击",
                    "• 情绪匹配 → 效果0.5x~2.5x",
                    "• 连续Combo → 额外加成",
                    "• 状态配合 → 完美时机"
                ]),
                ("动态情绪系统", [
                    "💭 18种情绪状态",
                    "平静/害羞/敏感期/发情期/欲求不满",
                    "高潮边缘/贤者时间/顺从/堕落...",
                    "每次互动实时计算，不同情绪不同效果"
                ]),
                ("随机事件", [
                    "🎲 30+种动作后事件",
                    "主动亲吻/身体颤抖/进入高潮/",
                    "意外惊喜/情绪波动等",
                    "随机触发增加真实感"
                ])
            ]

            img_bytes, img_base64 = HelpImageGenerator.generate_help_image(
                "游戏系统", sections, width=900
            )

            await self.send_image(img_base64)
            return

        except Exception as e:
            # 降级到文本模式
            import traceback
            traceback.print_exc()
            pass

        # 文本模式 (降级方案)
        help_text = """
🎮 【游戏系统】

━━━ 基础命令 ━━━
/开始 <人格>   开始游戏
/看           查看详细状态
/快看         快速查看
/重开         重置游戏
/导出         导出存档
/导入 <码>    导入存档

━━━ 9维属性 ━━━
💕 显性（AI可见）
  好感 - 喜欢程度
  亲密 - 关系深度
  信任 - 信任度

🔥 隐性（影响AI）
  顺从 - 服从意愿
  堕落 - 调教程度
  欲望 - 欲望强度

💫 状态（波动）
  兴奋 - 当前兴奋
  抵抗 - 反抗意志
  羞耻 - 羞耻感

━━━ 新系统 ━━━
⚖️ 属性冲突
  • 高羞耻(>60) → 抑制堕落30%
  • 高抵抗(>70) → 抑制顺从40%
  • 高信任(>70) → 抑制抵抗50%
  • 高堕落(>50) → 抑制羞耻恢复60%

⚡ 属性协同
  • 好感+信任 → 亲密+30%
  • 欲望+兴奋 → 堕落+40%
  • 顺从+堕落 → 羞耻崩溃+50%

🎯 契合度系统
  • 情绪匹配 → 效果0.5x~2.5x
  • 连续Combo → 额外加成
  • 状态配合 → 完美时机

💭 18种动态情绪
  平静/害羞/敏感期/发情期/欲求不满
  高潮边缘/贤者时间/顺从/堕落...
  每次互动实时计算，不同情绪不同效果

🎲 随机事件
  30+种动作后事件随机触发
  主动亲吻/身体颤抖/进入高潮等
"""
        await self.send_text(help_text.strip())

    async def _show_actions_help(self):
        """显示所有动作的分类帮助"""
        try:
            from ..utils.help_image_generator import HelpImageGenerator

            sections = [
                ("温柔互动 (1-3)", [
                    "/早安 /晚安 /牵手 /摸头 /聊天 /帮助 /安慰"
                ]),
                ("亲密互动 (4-6)", [
                    "/抱 [紧紧/轻轻/从背后]",
                    "/亲 [额头/脸颊/嘴唇/脖子/耳朵]",
                    "/摸 [头/脸/手/肩/背/腰/腿]",
                    "/诱惑 [耳语/眼神/肢体]",
                    "/凝视 [深情/炙热/挑逗]",
                    "/表白 /送礼 /吹气 /咬"
                ]),
                ("诱惑互动 (6-8)", [
                    "/挑逗 [语言/动作/眼神]",
                    "/舔 [手指/耳朵/脖子/嘴唇]",
                    "/吸 [手指/耳垂/脖子/锁骨]",
                    "/揉 [肩膀/腰/背/腿]",
                    "/耳语 [甜言蜜语/下流话/命令]",
                    "/脱 [上衣/裙子/全部]"
                ]),
                ("支配互动 (7-9)", [
                    "/壁咚 /命令 /调教 [温柔/严厉/惩罚]",
                    "/玩弄 /标记 /折磨 /品尝"
                ]),
                ("极限互动 (8-10)", [
                    "/推倒 /羞辱 /侵犯 /深入 /开发",
                    "/进入 [温柔/粗暴/缓慢]"
                ]),
                ("⚡ 风险动作", [
                    "/强吻 - 成功率60% 失败→好感-10",
                    "/突然袭击 - 成功率65% 失败→好感-8",
                    "/强行 - 成功率50% 失败→关系受损",
                    "/挑衅 - 成功率70% 失败→叛逆",
                    "/禁锢 - 成功率55% 失败→信任-12",
                    "/威胁 - 成功率50% 失败→坏结局警告",
                    "/放纵 - 成功率70% 失败→贤者时间",
                    "/睡觉时 - 成功率50% 失败→信任-15",
                    "/洗澡时 - 成功率55% 失败→好感-12"
                ]),
                ("🔒 情绪专属动作", [
                    "💕 发情期 → /索求",
                    "💤 贤者时间 → /温存",
                    "💫 敏感期 → /挑逗敏感点",
                    "😈 堕落 → /羞辱play",
                    "🙇 顺从 → /支配",
                    "🔥 欲求不满 → /满足她",
                    "✨ 高潮边缘 → /边缘控制",
                    "😊 害羞 → /安抚",
                    "😤 叛逆 → /突破防线"
                ]),
                ("其他命令", [
                    "/穿 /用 /去 /真心话 /大冒险 /骰子",
                    "",
                    "💡 括号内容为可选参数，如: /亲 嘴唇"
                ])
            ]

            img_bytes, img_base64 = HelpImageGenerator.generate_help_image(
                "动作命令速查", sections, width=900
            )

            await self.send_image(img_base64)
            return

        except Exception as e:
            import traceback
            traceback.print_exc()
            pass

        # 降级文本模式
        help_text = """
🎭 【动作命令速查】

━━━ 温柔互动(1-3) ━━━
/早安 /晚安 /牵手 /摸头 /聊天 /帮助 /安慰

━━━ 亲密互动(4-6) ━━━
/抱 [紧紧/轻轻/从背后]
/亲 [额头/脸颊/嘴唇/脖子/耳朵]
/摸 [头/脸/手/肩/背/腰/腿]
/诱惑 [耳语/眼神/肢体]
/凝视 [深情/炙热/挑逗]
/表白 /送礼 /吹气 /咬

━━━ 诱惑互动(6-8) ━━━
/挑逗 [语言/动作/眼神]
/舔 [手指/耳朵/脖子/嘴唇]
/吸 [手指/耳垂/脖子/锁骨]
/揉 [肩膀/腰/背/腿]
/耳语 [甜言蜜语/下流话/命令]
/脱 [上衣/裙子/全部]

━━━ 支配互动(7-9) ━━━
/壁咚 /命令 /调教 [温柔/严厉/惩罚]
/玩弄 /标记 /折磨 /品尝

━━━ 极限互动(8-10) ━━━
/推倒 /羞辱 /侵犯 /深入 /开发
/进入 [温柔/粗暴/缓慢]

━━━ ⚡风险动作 ━━━
/强吻      成功率60% 失败→好感-10
/突然袭击  成功率65% 失败→好感-8
/强行      成功率50% 失败→关系受损
/挑衅      成功率70% 失败→叛逆
/禁锢      成功率55% 失败→信任-12
/威胁      成功率50% 失败→坏结局警告
/放纵      成功率70% 失败→贤者时间
/睡觉时    成功率50% 失败→信任-15
/洗澡时    成功率55% 失败→好感-12

━━━ 🔒情绪专属动作 ━━━
💕 发情期      → /索求
💤 贤者时间    → /温存
💫 敏感期      → /挑逗敏感点
😈 堕落        → /羞辱play
🙇 顺从        → /支配
🔥 欲求不满    → /满足她
✨ 高潮边缘    → /边缘控制
😊 害羞        → /安抚
😤 叛逆        → /突破防线

━━━ 其他 ━━━
/穿 /用 /去 /真心话 /大冒险 /骰子

💡 括号内容为可选参数，如: /亲 嘴唇
"""
        await self.send_text(help_text.strip())

    async def _show_outfit_help(self):
        """显示服装系统帮助"""
        try:
            from ..utils.help_image_generator import HelpImageGenerator

            sections = [
                ("命令", [
                    "/服装列表 - 查看所有服装",
                    "/穿 <名称> - 让她穿上"
                ]),
                ("服装列表", [
                    "🎀 日常 (阶段1-2)",
                    "  日常便装 学生制服 女仆装",
                    "",
                    "💃 性感 (阶段3)",
                    "  性感连衣裙",
                    "",
                    "🔥 情趣 (阶段4-5)",
                    "  兔女郎装 情趣内衣 一丝不挂"
                ]),
                ("解锁机制", [
                    "💡 随进化阶段自动解锁"
                ])
            ]

            img_bytes, img_base64 = HelpImageGenerator.generate_help_image(
                "服装系统", sections, width=800
            )

            await self.send_image(img_base64)
            return

        except Exception as e:
            import traceback
            traceback.print_exc()
            pass

        # 降级文本模式
        help_text = """
👗 【服装系统】

━━━ 命令 ━━━
/服装列表    查看所有服装
/穿 <名称>   让她穿上

━━━ 服装列表 ━━━
🎀 日常(阶段1-2)
  日常便装 学生制服 女仆装

💃 性感(阶段3)
  性感连衣裙

🔥 情趣(阶段4-5)
  兔女郎装 情趣内衣 一丝不挂

💡 随进化阶段自动解锁
"""
        await self.send_text(help_text.strip())

    async def _show_item_help(self):
        """显示道具系统帮助"""
        help_text = """
🎁 【道具系统】

━━━ 命令 ━━━
/背包        查看道具
/用 <名称>   使用道具

━━━ 道具示例 ━━━
💊 消耗品
  爱情药水 - 兴奋+20 欲望+15
  催情剂 - 兴奋+30 抵抗-20 羞耻-15

━━━ 获取方式 ━━━
• 互动随机掉落(15%)
• 进化阶段奖励
• 特殊事件获得
"""
        await self.send_text(help_text.strip())

    async def _show_scene_help(self):
        """显示场景系统帮助"""
        help_text = """
🌆 【场景系统】

━━━ 命令 ━━━
/场景列表    查看场景
/去 <场景>   切换场景

━━━ 场景列表 ━━━
🏠 私密
  卧室 - 亲密效果↑
  浴室 - 羞耻↓加速

🌳 公共
  公园 - 羞耻↑
  街道 - 公开play

🏫 半私密
  教室 - 禁忌感↑

💕 特殊
  情人旅馆 - 堕落效果极强

💡 不同场景有属性加成
"""
        await self.send_text(help_text.strip())

    async def _show_minigame_help(self):
        """显示小游戏帮助"""
        help_text = """
🎲 【小游戏】

━━━ 游戏 ━━━
/真心话    问答获得奖励
/大冒险    完成任务获得奖励
/骰子      1-6点随机效果

━━━ 真心话示例 ━━━
• 你最喜欢我的哪一点？
• 你有过什么羞耻的幻想吗？(亲密≥30)
• 你想过和我...做那种事吗？(堕落≥40)

━━━ 大冒险示例 ━━━
• 亲我一下 - 基础
• 让我抱你10秒 - 基础
• 坐到我腿上 - 亲密≥50
• 脱掉一件衣服 - 堕落≥40

💡 小游戏是快速提升属性的好方法
"""
        await self.send_text(help_text.strip())

    async def _show_evolution_help(self):
        """显示进化阶段帮助"""
        help_text = """
✨【进化阶段】

━━━ 5个阶段 ━━━
🌱 1.初识
  无需求
  刚刚认识，一切都是新鲜的

🌸 2.熟悉
  好感≥30 亲密≥20 互动≥20
  解锁学生制服、女仆装

💕 3.亲密
  好感≥60 亲密≥50 信任≥60 互动≥50
  解锁性感连衣裙、浴室、教室

🔥 4.沦陷
  好感≥80 亲密≥70 堕落≥40
  顺从≥60 羞耻<50
  解锁兔女郎装、情趣内衣、旅馆

😈 5.完全堕落
  堕落≥80 顺从≥80 羞耻<20
  亲密≥90 互动≥100
  解锁所有内容、终极事件

━━━ 进化机制 ━━━
• 满足条件自动升级
• 每次互动后检查
• 自动解锁奖励
• 属性加成提升

💡 用 /看 查看进化进度
"""
        await self.send_text(help_text.strip())

    async def _show_economy_help(self):
        """显示经济系统帮助"""
        help_text = """
💰 【经济系统】

━━━ 基础货币 ━━━
💵 爱心币 - 游戏货币
  • 初始赠送: 100币
  • 每次动作: 1-30币
  • 道具掉落: 15%概率

━━━ 赚钱途径 ━━━
🔨 打工 (/打工 <工作>)
  普通工作 (6种):
  • 咖啡店 15-30币/2h
  • 便利店 12-25币/2h
  • 家教 30-50币/3h
  • 餐厅 20-40币/3h
  • 搬运工 40-60币/4h
  • 夜班保安 50-80币/5h

  NSFW工作 (6种):
  • 牛郎 80-150币/4h (需好感≥40)
  • 男公关 100-200币/4h (需好感≥50)
  • 情趣用品推销 60-120币/3h (需堕落≥40)
  • 私人健身教练 70-140币/3h (需亲密≥35)
  • AV男优试镜 150-300币/4h (需堕落≥70)

  ⚠️ 副作用:
  • 牛郎/男公关会降低对她的好感和亲密
  • AV男优会增加堕落度

💰 动作奖励
  • 温柔: 1-3币
  • 亲密: 3-5币
  • 诱惑: 5-8币
  • 支配: 8-12币
  • 极限: 12-20币

━━━ 花钱途径 ━━━
🛍️ 商店 (/商店)
  • 道具: 20-300币
  • 服装: 50-1000币
  • 互动后15%掉落道具

💸 援交 (/援交 <服务>)
  • 约会 100币 - 好感+亲密
  • 私人摄影 200币 - 亲密+兴奋
  • 亲密接触 300币 - 高强度接触
  • 特殊服务 500币 - 极限服务

  ⚠️ 风险:
  • 特殊服务有10%被抓风险
  • 被抓罚款800币+关系严重受损

━━━ 使用技巧 ━━━
💡 赚钱攻略:
  1. 前期做普通打工稳定赚钱
  2. 属性达标后做NSFW工作
  3. 每次动作都有金币奖励
  4. 道具掉落可以卖或用

💡 花钱建议:
  1. 优先买道具增强互动
  2. 解锁关键服装
  3. 援交量力而行
  4. 特殊服务风险高需谨慎

💡 平衡技巧:
  • NSFW打工会降低对她的专一度
  • 援交服务效果好但有风险
  • 合理规划收支，避免破产
"""
        await self.send_text(help_text.strip())

    # ========== v2.0新增帮助方法 ==========

    async def _show_v2_help(self):
        """显示v2.0新功能总览"""
        try:
            from ..utils.help_image_generator import HelpImageGenerator

            sections = [
                ("🎉 v2.0新功能总览", [
                    "欲望剧场v2.0版本新增了四大核心系统",
                    "大幅增强游戏的策略深度和重玩价值",
                    "",
                    "使用以下命令查看详细说明:",
                    "  /帮助 季节 - 四季时间系统",
                    "  /帮助 职业 - 职业养成系统",
                    "  /帮助 事件 - 随机事件系统",
                    "  /帮助 结局 - 多结局系统",
                    "  /帮助 时间 - 42天周期说明"
                ]),
                ("🌸 四季时间系统", [
                    "• 42天游戏周期分为春夏秋冬四季",
                    "• 每个季节有不同的属性加成",
                    "• 8个固定节日提供额外+20%效果",
                    "• 天气系统增加沉浸感",
                    "",
                    "命令: /季节 - 查看当前季节和节日"
                ]),
                ("💼 职业养成系统", [
                    "• 12种职业成长路线",
                    "• 每日自动发放职业收入(10-120币)",
                    "• 满足条件可晋升到更高职业",
                    "• 职业影响最终结局类型",
                    "",
                    "命令: /职业 - 查看职业信息",
                    "      /晋升 - 执行职业晋升"
                ]),
                ("🎲 随机事件系统", [
                    "• 13个随机事件概率触发",
                    "• 每个事件有2-4个选择分支",
                    "• 不同选择导致不同结果",
                    "• 增加游戏不可预测性",
                    "",
                    "命令: /选择 <数字> - 做出事件选择"
                ]),
                ("🎬 多结局系统增强", [
                    "• 从20个基础结局增加到32个结局",
                    "• 新增8个职业相关结局",
                    "• 新增4个季节相关结局",
                    "• 结局优先级系统确保最佳匹配",
                    "",
                    "命令: /结局 - 查看当前结局"
                ]),
                ("⏰ 42天周期玩法", [
                    "• 游戏在第42天自动结束",
                    "• 每7天触发一次周总结",
                    "• 每日互动次数限制",
                    "• 时间管理成为核心策略",
                    "",
                    "命令: /明日 - 推进到下一天",
                    "      /状态 - 查看游戏天数"
                ]),
                ("✨ 新增互动动作", [
                    "• 35+个温情向互动动作",
                    "• 照顾、做饭、陪伴、倾听等",
                    "• 平衡NSFW内容",
                    "• 增加日常关爱玩法"
                ])
            ]

            img_bytes, img_base64 = HelpImageGenerator.generate_help_image(
                "v2.0新功能总览", sections, width=1920
            )

            await self.send_image(img_base64)
            return

        except Exception as e:
            import traceback
            traceback.print_exc()
            pass

        # 文本降级
        help_text = """
🎉 【v2.0新功能总览】

━━━ 四大核心系统 ━━━

🌸 四季时间系统
  • 42天游戏周期分为春夏秋冬四季
  • 每个季节有不同的属性加成
  • 8个固定节日提供额外+20%效果
  • 命令: /季节 查看详情

💼 职业养成系统
  • 12种职业成长路线
  • 每日自动发放收入(10-120币)
  • 满足条件可晋升
  • 影响最终结局
  • 命令: /职业 /晋升

🎲 随机事件系统
  • 13个随机事件概率触发
  • 每个事件有多个选择分支
  • 不同选择不同结果
  • 命令: /选择 <数字>

🎬 多结局系统增强
  • 32个结局(+12个新结局)
  • 职业相关结局(8个)
  • 季节相关结局(4个)
  • 命令: /结局

⏰ 42天周期玩法
  • 第42天自动结束
  • 每7天周总结
  • 每日互动限制
  • 命令: /明日

✨ 新增35+温情互动
  照顾/做饭/陪伴/倾听等

━━━ 查看详细说明 ━━━
/帮助 季节 - 四季系统详解
/帮助 职业 - 职业系统详解
/帮助 事件 - 事件系统详解
/帮助 结局 - 结局系统详解
/帮助 时间 - 时间系统详解
"""
        await self.send_text(help_text.strip())

    async def _show_season_help(self):
        """显示季节系统帮助"""
        help_text = """
🌸 【四季时间系统】

━━━ 四季划分 ━━━
🌸 春天 (第1-10天)
  加成: 好感度 +10%
  氛围: 万物复苏，恋爱的季节

☀️ 夏天 (第11-21天)
  加成: 兴奋度 +15%, 堕落度 +10%
  氛围: 炙热激情，大胆尝试

🍂 秋天 (第22-31天)
  加成: 信任度 +10%, 亲密度 +10%
  氛围: 成熟稳定，关系深化

❄️ 冬天 (第32-42天)
  加成: 好感度 +12%, 亲密度 +12%
  氛围: 相互温暖，彼此依靠

━━━ 8个节日 ━━━
第3天 🌸 樱花祭
第7天 💕 情人节
第17天 🏮 夏日祭
第20天 🎆 花火大会
第24天 🌕 中秋节
第32天 🎃 万圣节
第38天 🎄 圣诞节
第42天 🎉 跨年夜

💡 节日当天所有互动效果 +20%
💡 节日加成与季节加成可叠加

━━━ 天气系统 ━━━
每天有不同天气描述，增加沉浸感
使用 /季节 查看当前天气和节日

━━━ 使用技巧 ━━━
• 在节日当天进行重要互动
• 春天适合建立好感
• 夏天适合大胆尝试
• 秋天适合深化关系
• 冬天适合温情互动
"""
        await self.send_text(help_text.strip())

    async def _show_career_help(self):
        """显示职业系统帮助"""
        help_text = """
💼 【职业养成系统】

━━━ 12种职业路线 ━━━

📚 学生路线
  高中生(10币/天) → 大学生(20币/天)

💼 职场路线
  打工族(15币/天) → 正式员工(40币/天)
  → 高级职员(80币/天) → 部门经理(120币/天)

✍️ 创作路线
  兼职者(12币/天) → 自由职业者(50币/天)
  → 成功自由职业者(100币/天)

🎭 艺能路线
  练习生(15币/天) → 偶像/模特/主播(60-70币/天)
  → 顶级偶像/模特/主播(110-120币/天)

💋 特殊路线
  女招待(30币/天) → 高级援交(80币/天)

━━━ 晋升机制 ━━━
每个职业都有晋升条件:
• 达到指定游戏天数
• 满足属性要求
• 特定职业有多个分支选择

使用 /职业 查看详细条件
满足条件后使用 /晋升 执行晋升

━━━ 职业影响 ━━━
1. 每日收入差异 (10-120币)
2. 影响可获得的结局类型:
  • 职场精英情侣(经理/高级职员)
  • 创作伴侣(成功自由职业者)
  • 明星情侣(顶级偶像/模特/主播)
  • 校园初恋(高中生/大学生)
  • 金丝雀(高级援交)

━━━ 使用技巧 ━━━
• 规划好职业路线影响结局
• 平衡收入和培养时间
• 某些职业路线有特殊结局
• 晋升会立即生效，增加每日收入
"""
        await self.send_text(help_text.strip())

    async def _show_event_help(self):
        """显示事件系统帮助"""
        help_text = """
🎲 【随机事件系统】

━━━ 事件触发 ━━━
每次使用 /明日 推进时间时:
• 有概率触发随机事件
• 触发概率: 5%-18%不等
• 共13个不同事件

━━━ 事件类型 ━━━
朋友来访 - 考验你的理解
生病 - 照顾她的机会
考试压力 - 安慰或施压
购物邀约 - 愿意陪她吗
噩梦 - 安抚她的恐惧
意外摔倒 - 扶她还是...
... 还有更多事件等你发现

━━━ 事件选择 ━━━
每个事件有 2-4 个选择:
• 温柔选择 - 提升好感信任
• 大胆选择 - 提升堕落亲密
• 特殊选择 - 需要满足条件才能解锁

使用 /选择 <数字> 做出选择
例如: /选择 1 或 /选择 2

━━━ 事件效果 ━━━
不同选择导致不同结果:
• 属性变化(±5 to ±15)
• 关系走向改变
• 可能解锁特殊剧情

━━━ 使用技巧 ━━━
• 仔细阅读每个选项的描述
• 根据当前培养方向选择
• 某些选择需要高属性解锁
• 事件选择不可撤销，请谨慎
"""
        await self.send_text(help_text.strip())

    async def _show_ending_help(self):
        """显示结局系统帮助"""
        help_text = """
🎬 【多结局系统】

━━━ 结局分类 ━━━
共32个结局，分为4个等级:

💕 完美结局 (2个)
  • 完美恋人 - 所有属性平衡
  • 纯爱至上 - 高好感低堕落

✨ 好结局 (14个)
  • 禁忌之爱、温柔日常、挚友情深等
  • 职业相关结局(8个):
    职场精英情侣、创作伴侣、明星情侣
    校园初恋等
  • 季节相关结局(4个):
    春日恋曲、夏日狂热、秋日收获
    冬日温暖

😊 普通结局 (6个)
  • 平凡恋人、暧昧不清、肉体关系等

💔 坏结局 (10个)
  • 破碎玩偶、崩坏堕落、逃离结局等
  • 职业坏结局: 堕落偶像、金丝雀

━━━ 结局触发 ━━━
1. 第30天后可使用 /结局 查看当前结局
2. 第42天游戏自动结束并显示结局
3. 也可提前使用 /结局 结束游戏

━━━ 结局判定 ━━━
系统按优先级从高到低检查:
1. 检查完美结局条件
2. 检查好结局条件(含职业/季节)
3. 检查普通结局条件
4. 检查坏结局条件
5. 默认为"平凡恋人"

━━━ 职业结局 ━━━
某些结局需要特定职业:
• 职场精英情侣 - 需要经理/高级职员
• 创作伴侣 - 需要成功自由职业者
• 明星情侣 - 需要顶级偶像/模特/主播
• 校园初恋 - 需要高中生/大学生

━━━ 季节结局 ━━━
在特定季节结束游戏可获得:
• 春日恋曲 - 春天结束
• 夏日狂热 - 夏天结束
• 秋日收获 - 秋天结束
• 冬日温暖 - 冬天结束

━━━ 使用技巧 ━━━
• 第30天后可用 /结局预览 查看所有可能结局
• 根据想要的结局规划职业和季节
• 平衡属性避免坏结局
• 可以多次重开尝试不同结局
"""
        await self.send_text(help_text.strip())

    async def _show_time_help(self):
        """显示时间系统帮助"""
        help_text = """
⏰ 【42天周期系统】

━━━ 时间推进 ━━━
使用 /明日 命令推进到下一天:
• 重置每日互动次数
• 发放职业收入
• 可能触发随机事件
• 显示季节和节日信息

━━━ 每日互动限制 ━━━
不同关系阶段有不同互动次数:

🤝 陌生人 (亲密0-20)
  每日3次互动

😊 朋友 (亲密20-50)
  每日4次互动

💕 亲密 (亲密50-80)
  每日5次互动

❤️ 恋人 (亲密80+)
  每日6次互动

💡 用完今日互动后需要 /明日 推进

━━━ 周期总结 ━━━
每7天触发一次周总结:
• 第8天、第15天、第22天、第29天、第36天
• 显示本周属性变化
• 对比上周进度
• 给出下周建议

━━━ 重要时间点 ━━━
第30天 - 可以开始查看结局
第35天+ - 倒计时提示开始
第42天 - 游戏自动结束

━━━ 游戏结束 ━━━
第42天过完后:
• 游戏自动结束
• 显示最终结局
• 无法继续推进
• 可以使用 /重开 重新开始

━━━ 使用技巧 ━━━
• 合理规划每日互动次数
• 不要过早推进，充分利用每天
• 关键时刻(节日、高互动次数日)多互动
• 第30天后可以预览结局调整策略
• 第42天前确保达到目标属性
"""
        await self.send_text(help_text.strip())


class DTGuideCommand(BaseCommand):
    """游戏说明命令"""

    command_name = "dt_guide"
    command_description = "显示游戏玩法说明"
    command_pattern = r"^/(说明|guide|指南)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        try:
            from ..utils.help_image_generator import HelpImageGenerator

            sections = [
                ("欢迎来到欲望剧场", [
                    "这是一个以九维属性为核心的互动养成游戏",
                    "通过各种互动命令,培养专属于你的角色",
                    "从温柔日常到极限调教,体验完整的成长路径"
                ]),
                ("快速开始", [
                    "1. 输入 /开始 <人格> 创建角色",
                    "   可选人格: 傲娇/天真/妖媚/害羞/高冷",
                    "2. 使用 /快看 查看核心属性",
                    "3. 选择互动命令开始游戏",
                    "   温柔互动: /牵手 /摸头 /抱",
                    "   亲密互动: /亲 /摸 /凝视",
                    "4. 使用 /帮助 查看所有命令"
                ]),
                ("核心玩法-九维属性", [
                    "显性属性(AI可见):",
                    "  好感-喜欢程度 亲密-关系深度 信任-信任度",
                    "隐性属性(影响AI):",
                    "  顺从-服从意愿 堕落-调教程度 欲望-欲望强度",
                    "状态属性(波动):",
                    "  兴奋-当前兴奋 抵抗-反抗意志 羞耻-羞耻感"
                ]),
                ("进化系统", [
                    "共5个进化阶段:",
                    "初识(1) → 熟悉(2) → 亲密(3) → 沦陷(4) → 完全堕落(5)",
                    "每个阶段:",
                    "• 有不同的属性要求",
                    "• 解锁新服装和场景",
                    "• 解锁新互动选项",
                    "• 获得进化奖励"
                ]),
                ("互动技巧", [
                    "温柔互动: 提升好感和信任,适合初期",
                    "亲密互动: 提升亲密度,需要一定好感",
                    "诱惑互动: 提升兴奋和欲望,需要亲密基础",
                    "支配互动: 提升顺从度,需要高信任",
                    "极限互动: 提升堕落度,需要高顺从"
                ]),
                ("经济系统", [
                    "爱心币获取:",
                    "• 每次互动自动获得(1-30币)",
                    "• 打工赚钱(普通/NSFW工作)",
                    "爱心币用途:",
                    "• 购买道具增强互动",
                    "• 购买服装解锁外观",
                    "• 援交服务快速提升属性"
                ]),
                ("风险与收益", [
                    "风险动作(如/强吻):",
                    "• 成功: 大幅提升属性",
                    "• 失败: 属性下降,关系受损",
                    "援交特殊服务:",
                    "• 效果强大但有被抓风险",
                    "• 被抓会罚款且关系严重受损"
                ]),
                ("进阶功能", [
                    "自然语言对话: /聊天 <内容>",
                    "场景切换: 不同场景有属性加成",
                    "服装系统: 不同服装有特殊效果",
                    "道具系统: 使用道具强化互动",
                    "小游戏: 真心话大冒险快速提升",
                    "存档管理: /导出 和 /导入 备份进度"
                ]),
                ("常见问题", [
                    "Q: 如何快速提升属性?",
                    "A: 使用小游戏、道具和高强度互动",
                    "Q: 如何解锁新服装?",
                    "A: 提升进化阶段自动解锁",
                    "Q: 属性为什么会下降?",
                    "A: 24小时后会开始衰减,保持互动即可"
                ]),
                ("游戏建议", [
                    "• 循序渐进,不要急于使用高强度互动",
                    "• 平衡各项属性,避免单一发展",
                    "• 善用/快速互动和/推荐命令",
                    "• 定期使用/导出备份进度",
                    "• 尝试不同人格体验不同风格"
                ])
            ]

            img_bytes, img_base64 = HelpImageGenerator.generate_help_image(
                "欲望剧场 v2.0 - 游戏说明", sections, width=1920
            )

            await self.send_image(img_base64)
            return True, "显示游戏说明", True

        except Exception as e:
            import traceback
            traceback.print_exc()
            # 降级到文本模式
            pass

        # 文本模式降级
        guide_text = """
【欲望剧场 v2.0 - 游戏说明】

━━━ 欢迎来到欲望剧场 ━━━
这是一个以九维属性为核心的互动养成游戏
通过各种互动命令,培养专属于你的角色
从温柔日常到极限调教,体验完整的成长路径

━━━ 快速开始 ━━━
1. 输入 /开始 <人格> 创建角色
   可选人格: 傲娇/天真/妖媚/害羞/高冷
2. 使用 /快看 查看核心属性
3. 选择互动命令开始游戏
   温柔互动: /牵手 /摸头 /抱
   亲密互动: /亲 /摸 /凝视
4. 使用 /帮助 查看所有命令

━━━ 核心玩法-九维属性 ━━━
显性属性(AI可见):
  好感-喜欢程度 亲密-关系深度 信任-信任度
隐性属性(影响AI):
  顺从-服从意愿 堕落-调教程度 欲望-欲望强度
状态属性(波动):
  兴奋-当前兴奋 抵抗-反抗意志 羞耻-羞耻感

━━━ 进化系统 ━━━
共5个进化阶段:
初识(1) → 熟悉(2) → 亲密(3) → 沦陷(4) → 完全堕落(5)
每个阶段:
• 有不同的属性要求
• 解锁新服装和场景
• 解锁新互动选项
• 获得进化奖励

━━━ 互动技巧 ━━━
温柔互动: 提升好感和信任,适合初期
亲密互动: 提升亲密度,需要一定好感
诱惑互动: 提升兴奋和欲望,需要亲密基础
支配互动: 提升顺从度,需要高信任
极限互动: 提升堕落度,需要高顺从

━━━ 经济系统 ━━━
爱心币获取:
• 每次互动自动获得(1-30币)
• 打工赚钱(普通/NSFW工作)
爱心币用途:
• 购买道具增强互动
• 购买服装解锁外观
• 援交服务快速提升属性

━━━ 风险与收益 ━━━
风险动作(如/强吻):
• 成功: 大幅提升属性
• 失败: 属性下降,关系受损
援交特殊服务:
• 效果强大但有被抓风险
• 被抓会罚款且关系严重受损

━━━ 进阶功能 ━━━
自然语言对话: /聊天 <内容>
场景切换: 不同场景有属性加成
服装系统: 不同服装有特殊效果
道具系统: 使用道具强化互动
小游戏: 真心话大冒险快速提升
存档管理: /导出 和 /导入 备份进度

━━━ 常见问题 ━━━
Q: 如何快速提升属性?
A: 使用小游戏、道具和高强度互动
Q: 如何解锁新服装?
A: 提升进化阶段自动解锁
Q: 属性为什么会下降?
A: 24小时后会开始衰减,保持互动即可

━━━ 游戏建议 ━━━
• 循序渐进,不要急于使用高强度互动
• 平衡各项属性,避免单一发展
• 善用/快速互动和/推荐命令
• 定期使用/导出备份进度
• 尝试不同人格体验不同风格

使用 /帮助 查看完整命令列表
"""
        await self.send_text(guide_text.strip())
        return True, "显示游戏说明", True


class DTExportCommand(BaseCommand):
    """导出存档命令"""

    command_name = "dt_export"
    command_description = "导出游戏存档"
    command_pattern = r"^/(导出|export)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        import base64

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
            return False, "角色未创建", False

        # 构建存档数据
        save_data = {
            "version": "2.0",
            "character": char,
            "timestamp": char.get("last_interaction", 0)
        }

        # 序列化并Base64编码
        json_data = json.dumps(save_data, ensure_ascii=False)
        encoded = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')

        # 分段显示（避免消息过长）
        chunk_size = 100
        chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]

        export_msg = f"""📦 【存档导出成功】

存档码（共{len(chunks)}段，总长{len(encoded)}字符）:
"""
        for i, chunk in enumerate(chunks, 1):
            export_msg += f"\n[{i}] {chunk}"

        export_msg += f"""

💾 保存说明:
  • 请妥善保存此存档码
  • 存档码包含所有角色数据
  • 建议复制到安全的地方保存

📥 导入方法:
  1. 复制所有段的内容（不要包含段号[1][2]等）
  2. 按顺序拼接成一个完整字符串
  3. 使用命令: /导入 <完整存档码>

示例（假设有3段）:
  /导入 ABC...DEF...XYZ...
  （ABC、DEF、XYZ分别是[1][2][3]段的内容）

⚠️ 注意:
  • 导入会覆盖当前存档
  • 必须复制所有{len(chunks)}段
  • 拼接时不要有空格或换行
  • 不要包含段号标记"""

        await self.send_text(export_msg)
        return True, "导出存档", True


class DTImportCommand(BaseCommand):
    """导入存档命令"""

    command_name = "dt_import"
    command_description = "导入游戏存档"
    command_pattern = r"^/(导入|import)\s+(.+)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        import base64
        import re

        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        match = re.match(self.command_pattern, self.message.processed_plain_text)
        if not match:
            await self.send_text("❌ 格式错误\n\n使用方法: /导入 <存档码>")
            return False, "格式错误", False

        save_code = match.group(2).strip()
        # 移除可能的空格和换行
        save_code = save_code.replace(" ", "").replace("\n", "")

        try:
            # 检查存档码长度（太短肯定不完整）
            if len(save_code) < 50:
                await self.send_text(f"""❌ 存档码太短（仅{len(save_code)}字符）

存档码应该是一段很长的字符串（通常500-2000字符）

请检查:
  • 是否完整复制了所有存档码
  • 存档码通常分为多段，需要全部拼接
  • 不要遗漏任何字符""")
                return False, "存档码不完整", False

            # Base64解码
            try:
                decoded = base64.b64decode(save_code).decode('utf-8')
            except Exception as decode_error:
                await self.send_text(f"""❌ 存档码解码失败

错误: {str(decode_error)}

可能原因:
  • 存档码包含无效字符
  • 存档码不完整
  • 复制时混入了其他内容

请确保:
  1. 完整复制所有段的存档码
  2. 所有段按顺序拼接（如 [1][2][3]...）
  3. 不要包含段号标记 [1] [2] 等
  4. 不要有额外的空格或换行""")
                return False, f"解码失败: {decode_error}", False

            # JSON解析
            try:
                save_data = json.loads(decoded)
            except json.JSONDecodeError as json_error:
                # 显示部分解码内容帮助诊断
                preview = decoded[:100] if len(decoded) > 100 else decoded
                await self.send_text(f"""❌ 存档数据解析失败

JSON错误: {str(json_error)}

解码后内容预览:
{preview}...

这通常意味着存档码不完整。

请检查:
  • 是否复制了所有分段
  • 分段是否按正确顺序拼接
  • 是否有字符遗漏

提示: 完整的存档码解码后应该是完整的JSON格式""")
                return False, f"JSON解析失败: {json_error}", False

            # 验证数据格式
            if "character" not in save_data:
                await self.send_text("❌ 存档格式错误\n\n存档中缺少角色数据\n请检查存档码是否正确")
                return False, "存档格式错误", False

            # 检查版本
            version = save_data.get("version", "1.0")
            if version != "2.0":
                await self.send_text(f"⚠️ 存档版本不匹配\n\n存档版本: {version}\n当前版本: 2.0\n\n可能会出现兼容性问题，是否继续？\n（暂未实现版本检查）")

            char_data = save_data["character"]

            # 更新user_id和chat_id（覆盖存档中的）
            char_data["user_id"] = user_id
            char_data["chat_id"] = chat_id

            # 保存到数据库（覆盖现有数据）
            await database_api.db_save(
                DTCharacter,
                data=char_data,
                key_field="user_id",
                key_value=user_id
            )

            await self.send_text(f"""✅ 【存档导入成功】

已恢复到:
  🎭 人格: {char_data.get('personality_type', '未知')}
  ⭐ 阶段: {char_data.get('evolution_stage', 1)}/5
  💕 好感: {char_data.get('affection', 0)}/100
  📈 互动次数: {char_data.get('interaction_count', 0)}

使用 /看 查看详细状态""")

            return True, "导入存档", True

        except Exception as e:
            await self.send_text(f"""❌ 导入失败

错误: {str(e)}

可能原因:
  • 存档码不完整
  • 存档码格式错误
  • 存档已损坏

请检查后重试""")
            return False, f"导入失败: {e}", False

