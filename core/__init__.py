"""
欲望剧场核心模块
"""

from .models import *
from ..systems.attributes.attribute_system import AttributeSystem
from ..systems.personality.personality_system import PersonalitySystem
from ..systems.memory.memory_engine import MemoryEngine
from ..systems.memory.preference_engine import PreferenceEngine
from ..systems.mechanics.scenario_engine import ScenarioEngine
from ..systems.actions.combo_system import ComboSystem
from ..systems.mechanics.game_mechanics import GameMechanics

__all__ = [
    # 核心数据库模型
    "DTCharacter",
    "DTMemory",
    "DTPreference",
    "DTStoryline",
    "DTEvent",

    # 扩展数据库模型
    "DTOutfit",
    "DTUserOutfit",
    "DTCurrentOutfit",
    "DTItem",
    "DTUserInventory",
    "DTAchievement",
    "DTUserAchievement",

    # 核心系统
    "AttributeSystem",
    "PersonalitySystem",
    "MemoryEngine",
    "PreferenceEngine",
    "ScenarioEngine",
    "ComboSystem",
    "GameMechanics",
]
