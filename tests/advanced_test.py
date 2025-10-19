#!/usr/bin/env python3
"""
欲望剧场插件 - 高级功能测试
测试扩展系统、事件系统、结局系统等
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from plugins.desire_theatre.core.models import (
    init_dt_database, DTCharacter, DTOutfit, DTItem, DTScene,
    DTEvent, dt_db
)
from plugins.desire_theatre.core.personality_system import PersonalitySystem
from plugins.desire_theatre.core.attribute_system import AttributeSystem

print("=" * 60)
print("欲望剧场插件 - 高级功能测试")
print("=" * 60)

results = {"passed": 0, "failed": 0, "warnings": 0, "tests": []}

def test(name: str):
    def decorator(func):
        def wrapper():
            print(f"\n{'='*50}")
            print(f"测试: {name}")
            print('='*50)
            try:
                func()
                results["passed"] += 1
                results["tests"].append({"name": name, "status": "PASS"})
                print(f"✅ {name} - 通过")
            except Exception as e:
                results["failed"] += 1
                results["tests"].append({"name": name, "status": "FAIL", "error": str(e)})
                print(f"❌ {name} - 失败: {e}")
                import traceback
                traceback.print_exc()
        return wrapper
    return decorator

@test("扩展系统 - 服装系统")
def test_outfit_system():
    """测试服装系统"""
    from plugins.desire_theatre.extensions.outfit_system import OutfitSystem

    test_user = "test_outfit_user"
    test_chat = "test_chat"

    # 初始化数据库
    init_dt_database()

    # 测试获取服装列表
    outfits = OutfitSystem.OUTFITS
    print(f"  定义的服装数: {len(outfits)}")

    if len(outfits) == 0:
        raise Exception("未定义任何服装")

    # 显示几个服装示例
    print("  服装示例:")
    for i, (outfit_id, outfit_info) in enumerate(list(outfits.items())[:5]):
        print(f"    - {outfit_info['name']} ({outfit_id}): {outfit_info.get('description', 'N/A')}")

    # 测试默认解锁的服装
    default_outfits = [
        outfit_id for outfit_id, info in outfits.items()
        if info.get('is_unlocked_by_default', False)
    ]
    print(f"  默认解锁的服装: {len(default_outfits)} 个")

    if len(default_outfits) == 0:
        results["warnings"] += 1
        print("  ⚠️ 警告: 没有默认解锁的服装")

@test("扩展系统 - 道具系统")
def test_item_system():
    """测试道具系统"""
    from plugins.desire_theatre.extensions.item_system import ItemSystem

    items = ItemSystem.ITEMS
    print(f"  定义的道具数: {len(items)}")

    if len(items) == 0:
        raise Exception("未定义任何道具")

    # 分类统计
    categories = {}
    for item_id, item_info in items.items():
        category = item_info.get('category', 'unknown')
        categories[category] = categories.get(category, 0) + 1

    print("  道具分类:")
    for category, count in categories.items():
        print(f"    {category}: {count} 个")

    # 显示几个道具示例
    print("  道具示例:")
    for i, (item_id, item_info) in enumerate(list(items.items())[:5]):
        print(f"    - {item_info['name']}: {item_info.get('description', 'N/A')}")

@test("扩展系统 - 场景系统")
def test_scene_system():
    """测试场景系统"""
    from plugins.desire_theatre.extensions.scene_system import SceneSystem

    scenes = SceneSystem.SCENES
    print(f"  定义的场景数: {len(scenes)}")

    if len(scenes) == 0:
        raise Exception("未定义任何场景")

    # 分类统计
    categories = {}
    for scene_id, scene_info in scenes.items():
        category = scene_info.get('category', 'unknown')
        categories[category] = categories.get(category, 0) + 1

    print("  场景分类:")
    for category, count in categories.items():
        print(f"    {category}: {count} 个")

    # 默认解锁场景
    default_scenes = [
        scene_id for scene_id, info in scenes.items()
        if info.get('is_unlocked_by_default', False)
    ]
    print(f"  默认解锁场景: {len(default_scenes)} 个")

    # 显示场景示例
    print("  场景示例:")
    for i, (scene_id, scene_info) in enumerate(list(scenes.items())[:5]):
        print(f"    - {scene_info['name']}: {scene_info.get('description', 'N/A')[:50]}...")

@test("扩展系统 - 商店系统")
def test_shop_system():
    """测试商店系统"""
    from plugins.desire_theatre.extensions.shop_system import ShopSystem

    # 测试获取可购买的道具
    items = ShopSystem.get_shop_items()
    print(f"  商店道具数: {len(items)}")

    if len(items) == 0:
        results["warnings"] += 1
        print("  ⚠️ 警告: 商店没有道具")

    # 测试获取可购买的服装
    outfits = ShopSystem.get_shop_outfits()
    print(f"  商店服装数: {len(outfits)}")

    if len(outfits) == 0:
        results["warnings"] += 1
        print("  ⚠️ 警告: 商店没有服装")

    # 显示价格范围
    if items:
        prices = [item.get('price', 0) for item in items.values()]
        print(f"  道具价格范围: {min(prices)} - {max(prices)} 爱心币")

    if outfits:
        prices = [outfit.get('price', 0) for outfit in outfits.values()]
        print(f"  服装价格范围: {min(prices)} - {max(prices)} 爱心币")

@test("双重人格系统 - 配置检查")
def test_dual_personality():
    """测试双重人格系统"""
    from plugins.desire_theatre.core.dual_personality_system import DualPersonalitySystem

    # 检查人格战争配置
    if not hasattr(DualPersonalitySystem, 'PERSONALITY_WAR_EVENTS'):
        raise Exception("缺少人格战争事件配置")

    events = DualPersonalitySystem.PERSONALITY_WAR_EVENTS
    print(f"  人格战争事件数: {len(events)}")

    if len(events) == 0:
        raise Exception("未定义人格战争事件")

    # 显示事件示例
    print("  事件示例:")
    for i, event in enumerate(events[:3]):
        print(f"    {i+1}. {event.get('name', 'N/A')}")
        print(f"       触发条件: {event.get('trigger_condition', {})}")

@test("随机事件系统 - 配置检查")
def test_random_events():
    """测试随机事件系统"""
    from plugins.desire_theatre.core.random_event_system import RandomEventSystem

    events = RandomEventSystem.RANDOM_EVENTS
    print(f"  随机事件数: {len(events)}")

    if len(events) == 0:
        raise Exception("未定义随机事件")

    # 分类统计
    types = {}
    for event in events:
        event_type = event.get('type', 'unknown')
        types[event_type] = types.get(event_type, 0) + 1

    print("  事件类型分布:")
    for etype, count in types.items():
        print(f"    {etype}: {count} 个")

    # 显示几个事件
    print("  事件示例:")
    for i, event in enumerate(events[:3]):
        print(f"    {i+1}. {event.get('name', 'N/A')}")
        print(f"       概率: {event.get('probability', 0) * 100}%")

@test("选择困境系统 - 配置检查")
def test_choice_dilemma():
    """测试选择困境系统"""
    from plugins.desire_theatre.core.choice_dilemma_system import ChoiceDilemmaSystem

    dilemmas = ChoiceDilemmaSystem.DILEMMAS
    print(f"  选择困境数: {len(dilemmas)}")

    if len(dilemmas) == 0:
        raise Exception("未定义选择困境")

    # 检查困境结构
    for dilemma in dilemmas[:3]:
        if 'choices' not in dilemma:
            raise Exception(f"困境 {dilemma.get('id')} 缺少choices字段")

        if len(dilemma['choices']) != 2:
            raise Exception(f"困境 {dilemma.get('id')} 的选项不是2个")

    print("  困境示例:")
    for i, dilemma in enumerate(dilemmas[:3]):
        print(f"    {i+1}. {dilemma.get('description', 'N/A')[:50]}...")
        print(f"       选项数: {len(dilemma.get('choices', []))}")

@test("结局系统 - 配置检查")
def test_ending_system():
    """测试结局系统"""
    from plugins.desire_theatre.core.ending_system import EndingSystem

    endings = EndingSystem.ENDINGS
    print(f"  结局数: {len(endings)}")

    if len(endings) == 0:
        raise Exception("未定义结局")

    # 分类统计
    types = {}
    for ending in endings:
        ending_type = ending.get('type', 'unknown')
        types[ending_type] = types.get(ending_type, 0) + 1

    print("  结局类型分布:")
    for etype, count in sorted(types.items()):
        print(f"    {etype}: {count} 个")

    # 显示结局示例
    print("  结局示例:")
    for i, ending in enumerate(endings[:5]):
        print(f"    {i+1}. [{ending.get('type')}] {ending.get('name')}")
        print(f"       条件: {list(ending.get('conditions', {}).keys())}")

@test("职业系统 - 配置检查")
def test_career_system():
    """测试职业系统"""
    from plugins.desire_theatre.core.career_system import CareerSystem

    careers = CareerSystem.CAREERS
    print(f"  职业数: {len(careers)}")

    if len(careers) == 0:
        raise Exception("未定义职业")

    # 分类
    categories = {}
    for career_id, career_info in careers.items():
        category = career_info.get('category', 'unknown')
        categories[category] = categories.get(category, 0) + 1

    print("  职业分类:")
    for category, count in categories.items():
        print(f"    {category}: {count} 个")

    # 显示职业示例
    print("  职业示例:")
    for i, (career_id, career_info) in enumerate(list(careers.items())[:5]):
        print(f"    - {career_info['name']}: 收入 {career_info.get('daily_income', 0)} 币/天")

@test("完整游戏流程模拟 - 温柔路线")
def test_gentle_route():
    """模拟完整的温柔路线游戏流程"""
    print("  模拟42天温柔路线...")

    test_user = "test_gentle_route"
    test_chat = "test_chat"

    # 初始化
    init_dt_database()

    with dt_db:
        DTCharacter.delete().where(
            (DTCharacter.user_id == test_user) &
            (DTCharacter.chat_id == test_chat)
        ).execute()

        char = DTCharacter.create(
            user_id=test_user,
            chat_id=test_chat,
            personality_type="tsundere",
            coins=100
        )

    # 加载动作配置
    actions_file = Path(__file__).parent / "actions.json"
    with open(actions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        actions = data.get("actions", {})

    # 选择温柔动作
    gentle_actions = [
        name for name, config in actions.items()
        if config.get('type') == 'gentle'
    ]

    print(f"  可用温柔动作: {len(gentle_actions)} 个")

    # 模拟42天
    total_interactions = 0
    daily_limit = 3

    for day in range(1, 43):
        # 每天的互动限制随阶段增加
        if char.evolution_stage >= 1:
            daily_limit = 4
        if char.evolution_stage >= 2:
            daily_limit = 5
        if char.evolution_stage >= 3:
            daily_limit = 6

        # 每天执行互动
        for _ in range(daily_limit):
            # 随机选择温柔动作
            import random
            action_name = random.choice(gentle_actions[:5])  # 使用最常见的几个
            action_config = actions[action_name]

            # 应用效果
            effects = action_config.get('effects', {})
            char_dict = {
                'affection': char.affection,
                'intimacy': char.intimacy,
                'trust': char.trust,
                'arousal': char.arousal,
                'shame': char.shame,
                'resistance': char.resistance
            }

            char_dict = AttributeSystem.apply_changes(char_dict, effects)

            # 更新角色
            char.affection = char_dict['affection']
            char.intimacy = char_dict['intimacy']
            char.trust = char_dict['trust']
            char.arousal = char_dict['arousal']
            char.shame = char_dict['shame']
            char.resistance = char_dict['resistance']

            total_interactions += 1

        # 检查进化
        from plugins.desire_theatre.core.evolution_system import EvolutionSystem
        can_evolve, next_stage, stage_info = EvolutionSystem.check_evolution(char)
        if can_evolve and next_stage and next_stage > char.evolution_stage:
            char.evolution_stage = next_stage
            if day <= 10:
                print(f"    第{day}天: 进化到阶段{next_stage}")

        char.game_day = day
        char.save()

    print(f"  42天后最终状态:")
    print(f"    好感度: {char.affection}/100")
    print(f"    亲密度: {char.intimacy}/100")
    print(f"    信任度: {char.trust}/100")
    print(f"    进化阶段: {char.evolution_stage}/5")
    print(f"    总互动次数: {total_interactions}")

    # 验证是否达到好结局条件
    if char.affection >= 80 and char.trust >= 70:
        print("  ✅ 达到好结局条件")
    else:
        print("  ⚠️ 未达到好结局条件")

@test("完整游戏流程模拟 - 堕落路线")
def test_corruption_route():
    """模拟堕落路线"""
    print("  模拟堕落路线...")

    test_user = "test_corruption_route"
    test_chat = "test_chat"

    with dt_db:
        DTCharacter.delete().where(
            (DTCharacter.user_id == test_user) &
            (DTCharacter.chat_id == test_chat)
        ).execute()

        char = DTCharacter.create(
            user_id=test_user,
            chat_id=test_chat,
            personality_type="innocent",  # 天真人格堕落更快
            coins=100
        )

    # 加载动作
    actions_file = Path(__file__).parent / "actions.json"
    with open(actions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        actions = data.get("actions", {})

    # 策略: 先建立好感和亲密,再堕落
    print("  阶段1: 建立基础关系 (1-7天)")
    for day in range(1, 8):
        for _ in range(3):
            effects = {'affection': 5, 'intimacy': 3}
            char_dict = {'affection': char.affection, 'intimacy': char.intimacy,
                        'corruption': char.corruption, 'arousal': char.arousal,
                        'shame': char.shame, 'resistance': char.resistance}
            char_dict = AttributeSystem.apply_changes(char_dict, effects)
            char.affection = char_dict['affection']
            char.intimacy = char_dict['intimacy']
        char.save()

    print(f"    7天后: 好感{char.affection} 亲密{char.intimacy}")

    print("  阶段2: 开始堕落 (8-21天)")
    for day in range(8, 22):
        for _ in range(4):
            # 使用堕落动作
            effects = {'corruption': 12, 'arousal': 10, 'shame': -8}
            char_dict = {'affection': char.affection, 'intimacy': char.intimacy,
                        'corruption': char.corruption, 'arousal': char.arousal,
                        'shame': char.shame, 'resistance': char.resistance}
            char_dict = AttributeSystem.apply_changes(char_dict, effects)
            char.corruption = char_dict['corruption']
            char.arousal = char_dict['arousal']
            char.shame = char_dict['shame']
        char.save()

    print(f"    21天后: 堕落{char.corruption} 兴奋{char.arousal} 羞耻{char.shame}")

    print("  阶段3: 深度开发 (22-42天)")
    for day in range(22, 43):
        for _ in range(5):
            effects = {'corruption': 15, 'submission': 10, 'resistance': -10}
            char_dict = {'affection': char.affection, 'intimacy': char.intimacy,
                        'corruption': char.corruption, 'arousal': char.arousal,
                        'shame': char.shame, 'resistance': char.resistance,
                        'submission': char.submission}
            char_dict = AttributeSystem.apply_changes(char_dict, effects)
            char.corruption = char_dict['corruption']
            char.submission = char_dict['submission']
            char.resistance = char_dict['resistance']
        char.save()

    print(f"  42天后最终状态:")
    print(f"    堕落度: {char.corruption}/100")
    print(f"    顺从度: {char.submission}/100")
    print(f"    抵抗值: {char.resistance}/100")
    print(f"    羞耻心: {char.shame}/100")

    if char.corruption >= 80:
        print("  ✅ 达到完全堕落")
    elif char.corruption >= 60:
        print("  ✅ 达到深度堕落")
    else:
        print("  ⚠️ 堕落度不足")

# 运行所有测试
test_outfit_system()
test_item_system()
test_scene_system()
test_shop_system()
test_dual_personality()
test_random_events()
test_choice_dilemma()
test_ending_system()
test_career_system()
test_gentle_route()
test_corruption_route()

# 打印总结
print("\n" + "=" * 60)
print("高级功能测试总结")
print("=" * 60)
print(f"✅ 通过: {results['passed']}")
print(f"❌ 失败: {results['failed']}")
print(f"⚠️  警告: {results['warnings']}")
print("=" * 60)

if results['failed'] > 0:
    print("\n失败测试:")
    for test in results['tests']:
        if test['status'] == 'FAIL':
            print(f"  - {test['name']}")
            print(f"    错误: {test.get('error', 'Unknown')}")

sys.exit(0 if results['failed'] == 0 else 1)
