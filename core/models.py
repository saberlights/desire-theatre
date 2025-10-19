"""
数据库模型定义
"""

import time
import os
from peewee import Model, TextField, BooleanField, FloatField, IntegerField, SqliteDatabase

# 创建独立的数据库实例
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PLUGIN_DIR, "desire_theatre.db")
dt_db = SqliteDatabase(DB_PATH)


class DTCharacter(Model):
    """角色属性表 - 存储每个用户的角色状态"""

    user_id = TextField(index=True)
    chat_id = TextField(index=True)

    # 显性属性（用户可见）
    affection = IntegerField(default=0)      # 好感度 0-100
    intimacy = IntegerField(default=0)       # 亲密度 0-100
    trust = IntegerField(default=50)         # 信任度 0-100

    # 隐性属性（影响AI行为）
    submission = IntegerField(default=50)    # 顺从度 0-100
    desire = IntegerField(default=0)         # 欲望值 0-100
    corruption = IntegerField(default=0)     # 堕落度 0-100

    # 动态状态（波动值）
    arousal = IntegerField(default=0)        # 当前兴奋度 0-100
    resistance = IntegerField(default=100)   # 抵抗意志 0-100
    shame = IntegerField(default=100)        # 羞耻心 0-100

    # 人格相关
    personality_type = TextField(default="tsundere")  # 人格类型
    personality_traits = TextField(default="[]")       # 已解锁特质 JSON
    evolution_stage = IntegerField(default=0)          # 进化阶段

    # 双重人格系统
    personality_integrated = IntegerField(default=0)   # 人格融合次数（接纳路线计数）
    last_mask_crack = FloatField(null=True)            # 上次面具崩塌时间
    personality_war_triggered = IntegerField(default=0) # 人格战争触发次数

    # 统计数据
    interaction_count = IntegerField(default=0)
    total_arousal_gained = IntegerField(default=0)
    challenges_completed = IntegerField(default=0)

    # 货币系统
    coins = IntegerField(default=100)  # 爱心币，初始赠送100

    # 行动点系统
    current_action_points = IntegerField(default=10)  # 当前行动点

    # 虚拟时间系统
    game_day = IntegerField(default=1)  # 游戏天数
    daily_interactions_used = IntegerField(default=0)  # 今日已用互动次数
    last_daily_reset = FloatField(default=time.time)  # 上次每日重置时间
    last_interaction_time = FloatField(default=time.time)  # 最后互动时间

    # 周总结系统
    last_week_snapshot = TextField(default="{}")  # 上周属性快照 JSON

    # 调教进度系统
    training_progress = TextField(default="{}")  # 各动作训练进度 JSON {"动作名": 进度0-100}

    # 心情槽系统
    mood_gauge = IntegerField(default=50)  # 心情值 0-100

    # 场景系统
    current_scene = TextField(default="bedroom")  # 当前场景ID

    # 时间戳
    created_at = FloatField(default=time.time)
    last_interaction = FloatField(default=time.time)
    last_desire_decay = FloatField(default=time.time)

    class Meta:
        database = dt_db
        table_name = "dt_character"
        indexes = (
            (("user_id", "chat_id"), True),  # 联合唯一索引
        )


class DTMemory(Model):
    """记忆系统 - 存储重要互动记忆"""

    memory_id = TextField(unique=True, index=True)
    user_id = TextField(index=True)
    chat_id = TextField(index=True)

    timestamp = FloatField()
    memory_type = TextField()  # "milestone", "preference", "event", "dialogue"

    # 记忆内容
    content = TextField()           # 记忆文本
    context = TextField(null=True)  # 上下文 JSON

    # 记忆重要性
    importance = IntegerField(default=5)  # 1-10
    emotional_impact = IntegerField(default=0)  # 情感冲击力

    # 标签和关联
    tags = TextField(default="[]")  # JSON列表
    related_attributes = TextField(default="{}")  # 当时的属性快照 JSON

    # 使用统计
    recall_count = IntegerField(default=0)
    last_recalled = FloatField(null=True)

    class Meta:
        database = dt_db
        table_name = "dt_memory"


class DTPreference(Model):
    """偏好学习表 - AI学习到的用户癖好"""

    user_id = TextField(index=True)
    chat_id = TextField(index=True)

    preference_type = TextField()  # "fetish", "scenario", "keyword", "forbidden"
    content = TextField()          # 偏好内容

    # 权重和统计
    weight = IntegerField(default=10)        # 权重 0-100
    trigger_count = IntegerField(default=0)  # 触发次数
    positive_reactions = IntegerField(default=0)
    negative_reactions = IntegerField(default=0)

    # 学习信息
    learned_from = TextField(null=True)  # 从哪次互动学到的
    confidence = FloatField(default=0.5)  # 置信度

    created_at = FloatField(default=time.time)
    last_triggered = FloatField(null=True)

    class Meta:
        database = dt_db
        table_name = "dt_preference"


class DTStoryline(Model):
    """剧情线管理表"""

    user_id = TextField(index=True)
    chat_id = TextField(index=True)
    storyline_id = TextField(index=True)

    storyline_name = TextField()
    storyline_type = TextField()  # "main", "side", "hidden"

    # 进度
    progress = FloatField(default=0.0)  # 0.0-1.0
    current_chapter = TextField(default="Chapter 1")

    # 状态
    is_active = BooleanField(default=True)
    is_completed = BooleanField(default=False)
    is_unlocked = BooleanField(default=True)

    # 解锁条件
    unlock_conditions = TextField(default="{}")  # JSON

    # 里程碑
    milestones_reached = TextField(default="[]")  # JSON列表

    created_at = FloatField(default=time.time)
    completed_at = FloatField(null=True)

    class Meta:
        database = dt_db
        table_name = "dt_storyline"


class DTEvent(Model):
    """事件记录表 - 记录触发的特殊事件"""

    event_id = TextField(unique=True, index=True)
    user_id = TextField(index=True)
    chat_id = TextField(index=True)

    event_type = TextField()  # "scenario", "challenge", "milestone", "random", "interaction"
    event_name = TextField()

    timestamp = FloatField()

    # 事件数据
    event_data = TextField(default="{}")  # JSON
    user_choice = TextField(null=True)    # 用户的选择
    outcome = TextField(null=True)        # 结果

    # 影响
    attribute_changes = TextField(default="{}")  # 属性变化 JSON

    class Meta:
        database = dt_db
        table_name = "dt_event"


# ========================================================================
# 扩展数据库模型
# ========================================================================

class DTOutfit(Model):
    """服装表"""
    outfit_id = TextField(unique=True, index=True)
    outfit_name = TextField()
    outfit_category = TextField()  # "normal", "sexy", "cosplay", "lingerie"
    description = TextField()
    unlock_condition = TextField(default="{}")  # JSON
    attribute_modifiers = TextField(default="{}")  # JSON
    arousal_bonus = IntegerField(default=0)
    shame_modifier = IntegerField(default=0)
    special_effects = TextField(default="[]")  # JSON
    is_unlocked_by_default = BooleanField(default=False)
    unlock_cost = IntegerField(default=0)  # 商店价格/解锁成本

    class Meta:
        database = dt_db
        table_name = "dt_outfit"


class DTUserOutfit(Model):
    """用户拥有的服装"""
    user_id = TextField(index=True)
    chat_id = TextField(index=True)
    outfit_id = TextField(index=True)
    unlocked_at = FloatField(default=time.time)
    times_worn = IntegerField(default=0)
    last_worn = FloatField(null=True)

    class Meta:
        database = dt_db
        table_name = "dt_user_outfit"


class DTCurrentOutfit(Model):
    """当前穿着的服装"""
    user_id = TextField(index=True)
    chat_id = TextField(index=True)
    outfit_id = TextField()
    equipped_at = FloatField(default=time.time)

    class Meta:
        database = dt_db
        table_name = "dt_current_outfit"
        indexes = (
            (("user_id", "chat_id"), True),
        )


class DTItem(Model):
    """道具表"""
    item_id = TextField(unique=True, index=True)
    item_name = TextField()
    item_category = TextField()  # "toy", "consumable", "special"
    description = TextField()
    effect_description = TextField()
    attribute_effects = TextField(default="{}")  # JSON
    duration_minutes = IntegerField(default=0)  # 0=即时效果
    tags = TextField(default="[]")  # JSON
    intensity_level = IntegerField(default=1)  # 1-10
    unlock_condition = TextField(default="{}")
    price = IntegerField(default=0)  # 商店价格

    class Meta:
        database = dt_db
        table_name = "dt_item"


class DTUserInventory(Model):
    """用户背包"""
    user_id = TextField(index=True)
    chat_id = TextField(index=True)
    item_id = TextField(index=True)
    quantity = IntegerField(default=1)
    acquired_at = FloatField(default=time.time)
    times_used = IntegerField(default=0)
    last_used = FloatField(null=True)

    class Meta:
        database = dt_db
        table_name = "dt_user_inventory"


class DTAchievement(Model):
    """成就表"""
    achievement_id = TextField(unique=True, index=True)
    achievement_name = TextField()
    achievement_category = TextField()  # "milestone", "hidden", "collection"
    description = TextField()
    hint = TextField(null=True)  # 解锁提示
    unlock_conditions = TextField(default="{}")  # JSON
    is_hidden = BooleanField(default=False)
    reward_points = IntegerField(default=10)
    reward_items = TextField(default="[]")  # JSON
    rarity = TextField(default="common")  # "common", "rare", "epic", "legendary"

    class Meta:
        database = dt_db
        table_name = "dt_achievement"


class DTUserAchievement(Model):
    """用户成就"""
    user_id = TextField(index=True)
    chat_id = TextField(index=True)
    achievement_id = TextField(index=True)
    unlocked_at = FloatField(default=time.time)
    progress = FloatField(default=1.0)  # 进度 0.0-1.0

    class Meta:
        database = dt_db
        table_name = "dt_user_achievement"


class DTScene(Model):
    """场景表"""
    scene_id = TextField(unique=True, index=True)
    scene_name = TextField()
    scene_category = TextField()  # "private", "public", "semi_private"
    description = TextField()
    unlock_condition = TextField(default="{}")  # JSON
    available_actions = TextField(default="[]")  # JSON
    attribute_modifiers = TextField(default="{}")  # JSON
    special_effects = TextField(default="[]")  # JSON
    is_unlocked_by_default = BooleanField(default=False)

    class Meta:
        database = dt_db
        table_name = "dt_scene"


class DTVisitedScene(Model):
    """场景访问记录"""
    user_id = TextField(index=True)
    chat_id = TextField(index=True)
    scene_id = TextField(index=True)
    visited_at = FloatField(default=time.time)

    class Meta:
        database = dt_db
        table_name = "dt_visited_scene"


class DTGameRecord(Model):
    """游戏记录"""
    user_id = TextField(index=True)
    chat_id = TextField(index=True)
    game_type = TextField()  # "truth", "dare", "dice"
    game_result = TextField()
    timestamp = FloatField(default=time.time)

    class Meta:
        database = dt_db
        table_name = "dt_game_record"


def init_dt_database():
    """初始化欲望剧场数据库表"""
    with dt_db:
        dt_db.create_tables([
            # 核心表
            DTCharacter,
            DTMemory,
            DTPreference,
            DTStoryline,
            DTEvent,
            # 扩展表
            DTOutfit,
            DTUserOutfit,
            DTCurrentOutfit,
            DTItem,
            DTUserInventory,
            DTAchievement,
            DTUserAchievement,
            DTScene,
            DTVisitedScene,
            DTGameRecord,
        ], safe=True)
