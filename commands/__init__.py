"""
命令组件
"""

from .action_commands import (
    DTActionCommand,
    DTStartGameCommand,
    DTRestartCommand,
    DTQuickInteractCommand,
    DTRecommendCommand,
)
from .status_commands import (
    DTStatusCommand,
    DTQuickStatusCommand,
    DTHelpCommand,
    DTGuideCommand,
    DTExportCommand,
    DTImportCommand,
)
from .quick_reference import DTQuickReferenceCommand
from .chat_command import DTChatCommand
from .extension_commands import (
    DTOutfitListCommand,
    DTWearOutfitCommand,
    DTInventoryCommand,
    DTUseItemCommand,
    DTSceneListCommand,
    DTGoSceneCommand,
    DTTruthCommand,
    DTDareCommand,
    DTDiceCommand,
)
from .shop_commands import DTShopCommand, DTBuyItemCommand, DTBuyOutfitCommand
from .work_commands import DTWorkCommand
from .papa_katsu_commands import DTPapaKatsuCommand
from .personality_commands import DTPersonalityStatusCommand, DTDilemmaChoiceCommand

__all__ = [
    "DTActionCommand",
    "DTStartGameCommand",
    "DTRestartCommand",
    "DTQuickInteractCommand",
    "DTRecommendCommand",
    "DTStatusCommand",
    "DTQuickStatusCommand",
    "DTHelpCommand",
    "DTGuideCommand",
    "DTExportCommand",
    "DTImportCommand",
    "DTQuickReferenceCommand",
    "DTChatCommand",
    "DTOutfitListCommand",
    "DTWearOutfitCommand",
    "DTInventoryCommand",
    "DTUseItemCommand",
    "DTSceneListCommand",
    "DTGoSceneCommand",
    "DTTruthCommand",
    "DTDareCommand",
    "DTDiceCommand",
    "DTShopCommand",
    "DTBuyItemCommand",
    "DTBuyOutfitCommand",
    "DTWorkCommand",
    "DTPapaKatsuCommand",
    "DTPersonalityStatusCommand",
    "DTDilemmaChoiceCommand",
]

