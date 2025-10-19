# 欲望剧场插件 - 架构文档

## 📁 目录结构

```
desire_theatre/
├── plugin.py                    # 插件主入口
├── config.toml                  # 配置文件
├── desire_theatre.db            # 数据库
│
├── core/                        # 核心数据层
│   ├── __init__.py
│   └── models.py               # 数据模型定义 (Peewee ORM)
│
├── systems/                     # 游戏系统（原 core/）
│   ├── attributes/             # 属性系统
│   │   ├── attribute_system.py          # 属性计算与限制
│   │   ├── attribute_conflict_system.py # 属性冲突机制
│   │   └── action_point_system.py       # 行动点系统
│   │
│   ├── personality/            # 人格与情绪系统
│   │   ├── personality_system.py        # 基础人格系统
│   │   ├── dual_personality_system.py   # 双重人格
│   │   ├── mood_gauge_system.py         # 心情槽系统
│   │   └── dynamic_mood_system.py       # 动态情绪
│   │
│   ├── events/                 # 事件系统
│   │   ├── random_event_system.py       # 随机事件
│   │   ├── choice_dilemma_system.py     # 选择困境
│   │   ├── post_action_events.py        # 动作后事件
│   │   └── event_generation_prompt.py   # LLM事件生成
│   │
│   ├── career/                 # 职业养成系统
│   │   └── career_system.py             # 职业发展与晋升
│   │
│   ├── relationship/           # 关系发展系统
│   │   ├── relationship_tension_system.py # 关系张力
│   │   ├── dating_activity_system.py      # 约会活动
│   │   └── evolution_system.py            # 关系进化
│   │
│   ├── actions/                # 动作交互系统
│   │   ├── action_handler.py            # 动作处理核心
│   │   ├── action_growth_system.py      # 动作成长
│   │   ├── training_progress_system.py  # 调教进度
│   │   └── combo_system.py              # 连击系统
│   │
│   ├── time/                   # 时间与周期系统
│   │   ├── daily_limit_system.py        # 每日限制
│   │   ├── seasonal_system.py           # 季节系统
│   │   └── cooldown_manager.py          # 冷却管理
│   │
│   ├── memory/                 # 记忆学习系统
│   │   ├── memory_engine.py             # 记忆引擎
│   │   └── preference_engine.py         # 偏好学习
│   │
│   ├── endings/                # 结局系统
│   │   ├── ending_system.py             # 结局判定
│   │   └── dual_ending_system.py        # 双重结局
│   │
│   ├── scenes/                 # 场景系统
│   │   └── enhanced_scene_system.py     # 增强场景
│   │
│   └── mechanics/              # 其他游戏机制
│       ├── scenario_engine.py           # 场景引擎
│       ├── game_mechanics.py            # 游戏机制
│       ├── confirmation_manager.py      # 二次确认
│       ├── delayed_consequence_system.py # 延迟后果
│       └── surprise_system.py           # 惊喜系统
│
├── features/                   # 扩展功能（原 extensions/）
│   ├── shop/                   # 商店系统
│   │   ├── shop_system.py               # 商店核心
│   │   └── earning_system.py            # 打工赚钱
│   │
│   ├── items/                  # 道具系统
│   │   └── item_system.py               # 道具管理
│   │
│   ├── outfits/                # 服装系统
│   │   └── outfit_system.py             # 服装管理
│   │
│   ├── achievements/           # 成就系统
│   │   └── achievement_system.py        # 成就解锁
│   │
│   ├── scenes/                 # 场景扩展
│   │   └── scene_system.py              # 场景解锁
│   │
│   ├── games/                  # 小游戏
│   │   └── game_system.py               # 真心话大冒险
│   │
│   └── services/               # 付费服务
│       └── paid_service_system.py       # 援交系统
│
├── commands/                   # 命令层（按功能分组）
│   ├── basic/                  # 基础命令
│   │   ├── status_commands.py           # /状态 /职业
│   │   ├── time_commands.py             # /明日
│   │   └── quick_reference.py           # /快速参考
│   │
│   ├── actions/                # 动作命令
│   │   ├── action_commands.py           # 所有互动动作
│   │   └── chat_command.py              # /聊天
│   │
│   ├── character/              # 角色命令
│   │   ├── personality_commands.py      # 人格相关
│   │   └── unified_choice_command.py    # /选择
│   │
│   ├── career/                 # 职业命令
│   │   ├── work_commands.py             # /打工
│   │   └── v2_system_commands.py        # /晋升
│   │
│   ├── shop/                   # 商店命令
│   │   ├── shop_commands.py             # /商店
│   │   ├── item_commands.py             # /道具 /使用道具
│   │   └── outfit_commands.py           # /服装 /换装
│   │
│   ├── social/                 # 社交命令
│   │   └── papa_katsu_commands.py       # /援交
│   │
│   ├── endings/                # 结局命令
│   │   └── ending_commands.py           # /结局
│   │
│   └── extensions/             # 扩展命令
│       └── extension_commands.py        # 其他功能
│
├── utils/                      # 工具类
│   ├── prompt_builder.py                # Prompt 构建
│   └── help_image_generator.py          # 帮助图片生成
│
├── tests/                      # 测试文件
│   ├── test_commands.py
│   ├── test_all_commands.py
│   ├── simple_test.py
│   └── ...
│
└── docs/                       # 文档
    ├── reports/                # 测试报告
    └── guides/                 # 开发指南
```

## 🎯 架构设计原则

### 1. **分层架构**
- **Core 层**: 数据模型定义
- **Systems 层**: 游戏逻辑系统
- **Features 层**: 可选扩展功能
- **Commands 层**: 用户交互接口
- **Utils 层**: 公共工具

### 2. **模块化设计**
- 每个子系统在独立目录中
- 通过 `__init__.py` 导出公共接口
- 最小化模块间耦合

### 3. **职责分离**
- **Systems**: 游戏核心逻辑，不依赖 Commands
- **Features**: 可插拔的扩展功能
- **Commands**: 只负责命令解析和调用 Systems/Features

### 4. **清晰的依赖关系**
```
Commands → Features → Systems → Core
   ↓          ↓          ↓
Utils ← ← ← ← ← ← ← ← ← ←
```

## 📦 主要模块说明

### Systems (游戏系统)

| 模块 | 职责 | 关键文件 |
|------|------|---------|
| attributes | 属性计算、冲突、行动点 | attribute_system.py |
| personality | 人格、心情、情绪 | dual_personality_system.py |
| events | 随机事件、选择困境 | random_event_system.py |
| career | 职业发展、晋升 | career_system.py |
| relationship | 关系张力、进化 | relationship_tension_system.py |
| actions | 动作处理、成长、调教 | action_handler.py |
| time | 时间管理、季节、冷却 | daily_limit_system.py |
| memory | 记忆、偏好学习 | memory_engine.py |
| endings | 结局判定 | ending_system.py |
| scenes | 场景效果 | enhanced_scene_system.py |
| mechanics | 其他机制 | confirmation_manager.py |

### Features (扩展功能)

| 模块 | 职责 |
|------|------|
| shop | 商店、打工赚钱 |
| items | 道具管理 |
| outfits | 服装系统 |
| achievements | 成就解锁 |
| scenes | 场景解锁 |
| games | 小游戏 |
| services | 付费服务 |

### Commands (命令层)

| 分组 | 命令示例 |
|------|---------|
| basic | /状态 /明日 /职业 |
| actions | /抱 /亲 /摸 |
| character | /选择 /人格 |
| career | /打工 /晋升 |
| shop | /商店 /换装 |
| social | /援交 |
| endings | /结局 |

## 🔧 Import 规范

### 从 Commands 导入 Systems
```python
from ..systems.actions.action_handler import ActionHandler
from ..systems.events.random_event_system import RandomEventSystem
```

### 从 Systems 导入 Core
```python
from ...core.models import DTCharacter
```

### Systems 之间相互导入
```python
from ..attributes.attribute_system import AttributeSystem
from ..personality.mood_gauge_system import MoodGaugeSystem
```

### 从任何地方导入 Utils
```python
from ...utils.prompt_builder import PromptBuilder
```

## 📝 开发指南

### 添加新系统
1. 在 `systems/` 下创建新目录
2. 添加系统文件和 `__init__.py`
3. 在 `__init__.py` 中导出公共接口
4. 在对应的 Commands 中调用

### 添加新功能
1. 在 `features/` 下创建新目录
2. 实现功能逻辑
3. 在 `commands/` 中添加对应命令
4. 更新配置文件

### 添加新命令
1. 确定命令分组（basic/actions/shop等）
2. 在对应目录创建命令文件
3. 继承 `BaseCommand`
4. 在 `plugin.py` 中注册

## 🎨 重构收益

1. **清晰度提升**: 一眼就能找到对应功能的代码
2. **维护性增强**: 修改某个系统不影响其他系统
3. **扩展性更好**: 新增功能有明确的归属位置
4. **团队协作**: 不同成员可以独立开发不同模块
5. **测试友好**: 每个模块可以独立测试

## 📊 文件统计

- Systems 子模块: 11 个
- Features 子模块: 7 个
- Commands 分组: 8 个
- Python 文件总数: 97 个

---

**重构完成日期**: 2025-10-19
**架构版本**: v2.0
