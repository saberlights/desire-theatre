"""
结局命令 - /结局, /结局预览
"""

import re
from typing import Tuple

from src.plugin_system import BaseCommand
from src.plugin_system.apis import database_api
from src.common.logger import get_logger

from ..core.models import DTCharacter
from ..core.dual_ending_system import DualEndingSystem

logger = get_logger("dt_ending_commands")


class DTEndingCommand(BaseCommand):
    """触发结局命令"""

    command_name = "dt_ending"
    command_description = "查看当前结局"
    command_pattern = r"^/(结局|ending)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not character:
            await self.send_text("❌ 你还没有开始游戏!使用 /开始 来开始")
            return False, "角色不存在", False

        # 检查游戏天数（建议至少30天）
        game_day = character.get("game_day", 1)

        if game_day < 30:
            await self.send_text(
                f"⏰ 当前游戏进度: 第 {game_day} 天\n\n"
                f"💡 建议至少游玩30天后再查看结局\n"
                f"   这样可以有更充分的时间培养关系\n\n"
                f"确定要现在查看结局吗？\n"
                f"  使用 /确认结局 确认\n"
                f"  或继续游戏，30天后自动触发"
            )
            return True, "等待确认", False

        # 检查双重结局
        emotion_ending = DualEndingSystem.check_emotion_ending(character)
        sexual_ending = DualEndingSystem.check_sexual_ending(character)

        if not emotion_ending or not sexual_ending:
            await self.send_text(
                "❌ 当前没有满足任何结局条件\n\n"
                "💡 继续培养关系，提升各项属性"
            )
            return True, "无可用结局", True

        # 格式化双重结局消息
        ending_message = DualEndingSystem.format_dual_ending_message(
            emotion_ending, sexual_ending, character
        )

        await self.send_text(ending_message)

        logger.info(f"玩家 {user_id} 触发双重结局: 感情={emotion_ending[0]}, 性向={sexual_ending[0]}")

        return True, f"触发结局: {emotion_ending[0]} + {sexual_ending[0]}", True


class DTConfirmEndingCommand(BaseCommand):
    """确认结局命令（游戏天数不足30天时）"""

    command_name = "dt_confirm_ending"
    command_description = "确认查看结局"
    command_pattern = r"^/(确认结局|confirm ending)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not character:
            await self.send_text("❌ 你还没有开始游戏!使用 /开始 来开始")
            return False, "角色不存在", False

        # 检查双重结局
        emotion_ending = DualEndingSystem.check_emotion_ending(character)
        sexual_ending = DualEndingSystem.check_sexual_ending(character)

        if not emotion_ending or not sexual_ending:
            await self.send_text(
                "❌ 当前没有满足任何结局条件\n\n"
                "💡 继续培养关系，提升各项属性"
            )
            return True, "无可用结局", True

        # 格式化双重结局消息
        ending_message = DualEndingSystem.format_dual_ending_message(
            emotion_ending, sexual_ending, character
        )

        await self.send_text(ending_message)

        logger.info(f"玩家 {user_id} 提前触发双重结局: 感情={emotion_ending[0]}, 性向={sexual_ending[0]}")

        return True, f"触发结局: {emotion_ending[0]} + {sexual_ending[0]}", True


class DTEndingPreviewCommand(BaseCommand):
    """结局预览命令"""

    command_name = "dt_ending_preview"
    command_description = "查看所有可能的结局"
    command_pattern = r"^/(结局预览|结局列表|endings)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        user_id = str(self.message.message_info.user_info.user_id)
        chat_id = self.message.chat_stream.stream_id

        # 获取角色
        character = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not character:
            await self.send_text("❌ 你还没有开始游戏!使用 /开始 来开始")
            return False, "角色不存在", False

        # 获取所有可能的感情结局和性向结局
        emotion_endings = DualEndingSystem.get_all_possible_emotion_endings(character)
        sexual_endings = DualEndingSystem.get_all_possible_sexual_endings(character)

        if not emotion_endings and not sexual_endings:
            await self.send_text(
                "❌ 当前没有满足任何结局条件\n\n"
                "💡 继续培养关系，提升各项属性"
            )
            return True, "无可用结局", True

        # 构建预览消息
        preview_parts = ["🎬 【可能的结局预览】\n"]

        # 感情路线结局
        if emotion_endings:
            preview_parts.append("【感情路线】")
            for idx, (ending_id, ending_data) in enumerate(emotion_endings, 1):
                tier = ending_data.get("tier", "普通")
                name = ending_data.get("name", ending_id)

                tier_emoji = {
                    "完美": "🌟",
                    "好": "✨",
                    "普通": "⭐",
                    "坏": "💔"
                }.get(tier, "📌")

                preview_parts.append(f"{idx}. {tier_emoji} {name}")
            preview_parts.append("")
        else:
            preview_parts.append("【感情路线】暂无可用结局\n")

        # 性向路线结局
        if sexual_endings:
            preview_parts.append("【性向路线】")
            for idx, (ending_id, ending_data) in enumerate(sexual_endings, 1):
                tier = ending_data.get("tier", "纯洁")
                name = ending_data.get("name", ending_id)

                tier_emoji = {
                    "纯洁": "👼",
                    "开放": "🌹",
                    "极限": "🔥"
                }.get(tier, "📌")

                preview_parts.append(f"{idx}. {tier_emoji} {name}")
            preview_parts.append("")
        else:
            preview_parts.append("【性向路线】暂无可用结局\n")

        preview_parts.append("━━━━━━━━━━━━━━━━━━━")
        preview_parts.append("💡 提示:")
        preview_parts.append("  • 双重结局系统：感情路线 + 性向路线")
        preview_parts.append("  • 优先级最高的结局会被触发")
        preview_parts.append("  • 使用 /结局 触发结局")

        # 显示当前最可能触发的结局组合
        if emotion_endings and sexual_endings:
            top_emotion = emotion_endings[0][1]
            top_sexual = sexual_endings[0][1]
            preview_parts.append(f"\n🎯 最可能触发:")
            preview_parts.append(f"   {top_emotion['name']} + {top_sexual['name']}")

        await self.send_text("\n".join(preview_parts))

        return True, "显示结局预览", True


class DTEndingListCommand(BaseCommand):
    """所有结局图鉴命令"""

    command_name = "dt_ending_catalog"
    command_description = "查看所有结局图鉴"
    command_pattern = r"^/(结局图鉴|结局大全|all endings)$"

    async def execute(self) -> Tuple[bool, str, bool]:
        # 构建双重结局图鉴
        catalog_parts = ["🎬 【结局图鉴】\n"]

        # === 感情路线结局 ===
        catalog_parts.append("【感情路线】")

        # 按优先级分类感情结局
        perfect_emotion = []
        good_emotion = []
        normal_emotion = []
        bad_emotion = []

        for ending_id, ending_data in DualEndingSystem.EMOTION_ENDINGS.items():
            tier = ending_data.get("tier", "普通")
            name = ending_data.get("name", ending_id)

            if tier == "完美":
                perfect_emotion.append(name)
            elif tier == "好":
                good_emotion.append(name)
            elif tier == "普通":
                normal_emotion.append(name)
            elif tier == "坏":
                bad_emotion.append(name)

        if perfect_emotion:
            catalog_parts.append("  🌟 【完美】")
            for name in perfect_emotion:
                catalog_parts.append(f"    {name}")
        if good_emotion:
            catalog_parts.append("  ✨ 【好】")
            for name in good_emotion:
                catalog_parts.append(f"    {name}")
        if normal_emotion:
            catalog_parts.append("  ⭐ 【普通】")
            for name in normal_emotion:
                catalog_parts.append(f"    {name}")
        if bad_emotion:
            catalog_parts.append("  💔 【坏】")
            for name in bad_emotion:
                catalog_parts.append(f"    {name}")

        catalog_parts.append("")

        # === 性向路线结局 ===
        catalog_parts.append("【性向路线】")

        # 按类别分类性向结局
        pure_sexual = []
        open_sexual = []
        extreme_sexual = []

        for ending_id, ending_data in DualEndingSystem.SEXUAL_ENDINGS.items():
            tier = ending_data.get("tier", "纯洁")
            name = ending_data.get("name", ending_id)

            if tier == "纯洁":
                pure_sexual.append(name)
            elif tier == "开放":
                open_sexual.append(name)
            elif tier == "极限":
                extreme_sexual.append(name)

        if pure_sexual:
            catalog_parts.append("  👼 【纯洁】")
            for name in pure_sexual:
                catalog_parts.append(f"    {name}")
        if open_sexual:
            catalog_parts.append("  🌹 【开放】")
            for name in open_sexual:
                catalog_parts.append(f"    {name}")
        if extreme_sexual:
            catalog_parts.append("  🔥 【极限】")
            for name in extreme_sexual:
                catalog_parts.append(f"    {name}")

        catalog_parts.append("")
        catalog_parts.append("━━━━━━━━━━━━━━━━━━━")
        catalog_parts.append(f"感情路线: {len(DualEndingSystem.EMOTION_ENDINGS)} 个结局")
        catalog_parts.append(f"性向路线: {len(DualEndingSystem.SEXUAL_ENDINGS)} 个结局")
        catalog_parts.append(f"总计组合: {len(DualEndingSystem.EMOTION_ENDINGS) * len(DualEndingSystem.SEXUAL_ENDINGS)} 种可能")
        catalog_parts.append("\n💡 提示:")
        catalog_parts.append("  • 使用 /结局预览 查看当前可触发的结局")
        catalog_parts.append("  • 双重结局：感情路线 + 性向路线")
        catalog_parts.append("  • 不同的培养方式会导向不同结局组合")

        await self.send_text("\n".join(catalog_parts))

        return True, "显示结局图鉴", True
