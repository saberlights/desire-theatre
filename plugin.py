"""
欲望剧场 (Desire Theatre) - 动态NSFW叙事引擎
作者: MaiBot Community
版本: 2.0.0 (重构版)

核心特性:
- 九维属性系统（好感、亲密、信任、顺从、欲望、堕落、兴奋、抵抗、羞耻）
- 动态人格演化（5种基础模板 + 无限演化路径）
- 纯命令控制（50+动作命令）
- 连击系统（连续互动获得加成）
- 特殊事件触发系统
"""

from typing import List, Tuple, Type

from src.plugin_system import (
    BasePlugin,
    register_plugin,
    ComponentInfo,
    ConfigField,
)
from src.common.logger import get_logger

logger = get_logger("desire_theatre")


@register_plugin
class DesireTheatrePlugin(BasePlugin):
    """欲望剧场插件"""

    plugin_name = "desire_theatre"
    enable_plugin = True
    dependencies = []
    python_dependencies = []
    config_file_name = "config.toml"

    config_section_descriptions = {
        "plugin": "插件配置",
        "custom_prompts": "自定义提示词配置",
    }

    config_schema = {
        "plugin": {
            "config_version": ConfigField(type=str, default="2.0.0", description="配置版本"),
            "enabled": ConfigField(type=bool, default=False, description="是否启用"),
            "default_personality": ConfigField(
                type=str, default="tsundere", description="默认人格类型(tsundere/innocent/seductive/shy/cold)"
            ),
        },
        "custom_prompts": {
            "enabled": ConfigField(type=bool, default=False, description="是否启用自定义提示词"),
            "extra_character_setup": ConfigField(type=str, default="", description="额外的角色设定"),
            "extra_response_requirements": ConfigField(type=str, default="", description="额外的回复要求"),
            "extra_format_requirements": ConfigField(type=str, default="", description="额外的格式要求"),
            "full_custom_template": ConfigField(type=str, default="", description="完全自定义的提示词模板"),
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 初始化数据库
        from .core.models import init_dt_database
        init_dt_database()

        # 初始化扩展系统（异步）
        self._init_extensions_async()

        logger.info("欲望剧场插件初始化完成 (v2.0.0)")

    def _init_extensions_async(self):
        """异步初始化扩展数据"""
        import asyncio

        async def init():
            from .features.outfits.outfit_system import OutfitSystem
            from .features.items.item_system import ItemSystem
            from .features.achievements.achievement_system import AchievementSystem
            from .features.scenes.scene_system import SceneSystem
            from .features.games.game_system import GameSystem

            await OutfitSystem.initialize_outfits()
            await ItemSystem.initialize_items()
            await AchievementSystem.initialize_achievements()
            await SceneSystem.initialize_scenes()
            logger.info("扩展系统初始化完成")

        # 创建任务
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(init())
            else:
                loop.run_until_complete(init())
        except Exception as e:
            logger.error(f"扩展系统初始化失败: {e}", exc_info=True)

    def get_plugin_components(self) -> List[Tuple[ComponentInfo, Type]]:
        # Actions commands
        from .commands.actions.action_commands import (
            DTActionCommand,
            DTStartGameCommand,
            DTRestartCommand,
            DTQuickInteractCommand,
            DTRecommendCommand,
        )
        from .commands.actions.chat_command import DTChatCommand

        # Basic commands
        from .commands.basic.status_commands import (
            DTStatusCommand,
            DTQuickStatusCommand,
            DTHelpCommand,
            DTGuideCommand,
            DTExportCommand,
            DTImportCommand,
        )
        from .commands.basic.quick_reference import DTQuickReferenceCommand
        from .commands.basic.time_commands import DTNextDayCommand

        # Character commands
        from .commands.character.personality_commands import (
            DTPersonalityStatusCommand,
            DTDilemmaChoiceCommand,
        )
        from .commands.character.unified_choice_command import DTUnifiedChoiceCommand

        # Career commands
        from .commands.career.work_commands import DTWorkCommand
        from .commands.career.v2_system_commands import (
            DTSeasonCommand,
            DTCareerCommand,
            DTPromotionCommand,
        )

        # Shop commands
        from .commands.shop.shop_commands import (
            DTShopCommand,
            DTBuyItemCommand,
            DTBuyOutfitCommand,
        )
        from .commands.shop.item_commands import (
            DTInventoryCommand,
            DTUseItemCommand,
        )
        from .commands.shop.outfit_commands import (
            DTOutfitListCommand,
            DTWearOutfitCommand,
        )

        # Social commands
        from .commands.social.papa_katsu_commands import DTPapaKatsuCommand

        # Endings commands
        from .commands.endings.ending_commands import (
            DTEndingCommand,
            DTConfirmEndingCommand,
            DTEndingPreviewCommand,
            DTEndingListCommand,
        )

        # Extensions commands
        from .commands.extensions.extension_commands import (
            DTSceneListCommand,
            DTGoSceneCommand,
            DTTruthCommand,
            DTDareCommand,
            DTDiceCommand,
        )

        components = [
            # 核心命令（具体命令优先）
            (DTStartGameCommand.get_command_info(), DTStartGameCommand),
            (DTRestartCommand.get_command_info(), DTRestartCommand),
            (DTStatusCommand.get_command_info(), DTStatusCommand),
            (DTQuickStatusCommand.get_command_info(), DTQuickStatusCommand),
            (DTHelpCommand.get_command_info(), DTHelpCommand),
            (DTGuideCommand.get_command_info(), DTGuideCommand),
            (DTQuickReferenceCommand.get_command_info(), DTQuickReferenceCommand),
            (DTExportCommand.get_command_info(), DTExportCommand),
            (DTImportCommand.get_command_info(), DTImportCommand),
            (DTChatCommand.get_command_info(), DTChatCommand),
            (DTQuickInteractCommand.get_command_info(), DTQuickInteractCommand),
            (DTRecommendCommand.get_command_info(), DTRecommendCommand),

            # 时间推进命令
            (DTNextDayCommand.get_command_info(), DTNextDayCommand),

            # v2.0 新增系统命令
            (DTSeasonCommand.get_command_info(), DTSeasonCommand),
            (DTCareerCommand.get_command_info(), DTCareerCommand),
            (DTPromotionCommand.get_command_info(), DTPromotionCommand),

            # 统一选择命令（智能处理事件选择和人格选择）
            (DTUnifiedChoiceCommand.get_command_info(), DTUnifiedChoiceCommand),

            # 结局系统命令
            (DTEndingCommand.get_command_info(), DTEndingCommand),
            (DTConfirmEndingCommand.get_command_info(), DTConfirmEndingCommand),
            (DTEndingPreviewCommand.get_command_info(), DTEndingPreviewCommand),
            (DTEndingListCommand.get_command_info(), DTEndingListCommand),

            # 双重人格系统命令
            (DTPersonalityStatusCommand.get_command_info(), DTPersonalityStatusCommand),
            (DTDilemmaChoiceCommand.get_command_info(), DTDilemmaChoiceCommand),

            # 扩展命令
            (DTOutfitListCommand.get_command_info(), DTOutfitListCommand),
            (DTWearOutfitCommand.get_command_info(), DTWearOutfitCommand),
            (DTInventoryCommand.get_command_info(), DTInventoryCommand),
            (DTUseItemCommand.get_command_info(), DTUseItemCommand),
            (DTSceneListCommand.get_command_info(), DTSceneListCommand),
            (DTGoSceneCommand.get_command_info(), DTGoSceneCommand),
            (DTTruthCommand.get_command_info(), DTTruthCommand),
            (DTDareCommand.get_command_info(), DTDareCommand),
            (DTDiceCommand.get_command_info(), DTDiceCommand),

            # 商店、赚钱和付费服务系统
            (DTShopCommand.get_command_info(), DTShopCommand),
            (DTBuyItemCommand.get_command_info(), DTBuyItemCommand),
            (DTBuyOutfitCommand.get_command_info(), DTBuyOutfitCommand),
            (DTWorkCommand.get_command_info(), DTWorkCommand),
            (DTPapaKatsuCommand.get_command_info(), DTPapaKatsuCommand),

            # 通配动作命令（放在最后作为兜底）
            (DTActionCommand.get_command_info(), DTActionCommand),
        ]

        return components
