"""
欲望剧场核心模块
"""

from .models import *
from .attribute_system import AttributeSystem
from .personality_system import PersonalitySystem
from .memory_engine import MemoryEngine
from .preference_engine import PreferenceEngine
from .scenario_engine import ScenarioEngine
from .combo_system import ComboSystem
from .game_mechanics import GameMechanics

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
