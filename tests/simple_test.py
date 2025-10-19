#!/usr/bin/env python3
"""
欲望剧场插件 - 简化测试脚本
专注于数据完整性和配置验证
"""

import sys
import json
from pathlib import Path

# 添加项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from plugins.desire_theatre.core.models import init_dt_database, DTCharacter, dt_db

print("=" * 60)
print("欲望剧场插件 - 简化测试")
print("=" * 60)

# 测试结果收集
results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "tests": []
}

def test(name: str):
    """测试装饰器"""
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
        return wrapper
    return decorator

@test("数据库初始化")
def test_database_init():
    """测试数据库初始化"""
    init_dt_database()

    # 检查所有表是否创建
    expected_tables = [
        'dt_character', 'dt_memory', 'dt_preference', 'dt_storyline', 'dt_event',
        'dt_outfit', 'dt_user_outfit', 'dt_current_outfit',
        'dt_item', 'dt_user_inventory',
        'dt_achievement', 'dt_user_achievement',
        'dt_scene', 'dt_visited_scene',
        'dt_game_record'
    ]

    with dt_db:
        cursor = dt_db.execute_sql(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = [row[0] for row in cursor.fetchall()]

    print(f"  期望表数: {len(expected_tables)}")
    print(f"  实际表数: {len(existing_tables)}")

    missing = []
    for table in expected_tables:
        if table not in existing_tables:
            missing.append(table)

    if missing:
        raise Exception(f"缺失表: {missing}")

    print(f"  所有 {len(expected_tables)} 个表创建成功")

@test("角色创建和属性限制")
def test_character_creation():
    """测试角色创建"""
    test_user = "test_user_simple"
    test_chat = "test_chat_simple"

    # 清理旧数据
    with dt_db:
        DTCharacter.delete().where(
            (DTCharacter.user_id == test_user) &
            (DTCharacter.chat_id == test_chat)
        ).execute()

    # 创建角色
    with dt_db:
        char = DTCharacter.create(
            user_id=test_user,
            chat_id=test_chat,
            personality_type="tsundere",
            affection=50,
            intimacy=30,
            corruption=20
        )

    print(f"  角色创建成功:")
    print(f"    好感度: {char.affection}")
    print(f"    亲密度: {char.intimacy}")
    print(f"    堕落度: {char.corruption}")
    print(f"    人格类型: {char.personality_type}")

    # 验证读取
    with dt_db:
        char2 = DTCharacter.get(
            (DTCharacter.user_id == test_user) &
            (DTCharacter.chat_id == test_chat)
        )

    if char2.affection != 50:
        raise Exception(f"属性读取失败: 期望50, 实际{char2.affection}")

    print("  数据持久化验证通过")

@test("动作配置文件完整性")
def test_actions_config():
    """测试动作配置文件"""
    actions_file = Path(__file__).parent / "actions.json"

    if not actions_file.exists():
        raise Exception("actions.json 文件不存在")

    with open(actions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        actions = data.get("actions", {})

    print(f"  加载动作数: {len(actions)}")

    # 统计动作类型
    type_counts = {}
    missing_fields = []

    for action_name, config in actions.items():
        # 检查必需字段
        required_fields = ["type", "base_intensity"]
        for field in required_fields:
            if field not in config:
                missing_fields.append(f"{action_name}.{field}")

        # 统计类型
        action_type = config.get("type", "unknown")
        type_counts[action_type] = type_counts.get(action_type, 0) + 1

    print(f"  动作类型分布:")
    for atype, count in sorted(type_counts.items()):
        print(f"    {atype}: {count} 个")

    if missing_fields:
        raise Exception(f"缺少必需字段: {missing_fields[:5]}")  # 只显示前5个

@test("人格配置完整性")
def test_personality_config():
    """测试人格配置"""
    from plugins.desire_theatre.core.personality_system import PersonalitySystem

    personalities = PersonalitySystem.PERSONALITIES
    print(f"  人格类型数: {len(personalities)}")

    required_fields = ["name", "description", "base_resistance", "base_shame", "dialogue_traits"]

    for ptype, config in personalities.items():
        for field in required_fields:
            if field not in config:
                raise Exception(f"人格 {ptype} 缺少字段: {field}")

    print("  所有人格配置完整")

    # 显示人格列表
    for ptype, config in personalities.items():
        print(f"    - {config['name']} ({ptype})")

@test("进化阶段数据")
def test_evolution_stages():
    """测试进化系统数据"""
    from plugins.desire_theatre.core.evolution_system import EvolutionSystem

    # 测试所有阶段名称
    for stage in range(6):
        name = EvolutionSystem.get_stage_name(stage)
        print(f"  阶段{stage}: {name}")

    if not name:  # 检查最后一个阶段是否有名称
        raise Exception("进化阶段名称缺失")

@test("数值平衡 - 堕落路径")
def test_corruption_path():
    """测试堕落度增长路径"""
    print("  模拟堕落路径...")

    # 从actions.json加载配置
    actions_file = Path(__file__).parent / "actions.json"
    with open(actions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        actions = data.get("actions", {})

    # 找出所有能增加corruption的动作
    corruption_actions = []
    for name, config in actions.items():
        effects = config.get("effects", {})
        if "corruption" in effects and effects["corruption"] > 0:
            req = config.get("requirements", {})
            corruption_actions.append({
                "name": name,
                "gain": effects["corruption"],
                "req_corruption": req.get("corruption", 0),
                "req_intimacy": req.get("intimacy", 0)
            })

    # 按需求排序
    corruption_actions.sort(key=lambda x: x["req_corruption"])

    print(f"  找到 {len(corruption_actions)} 个堕落动作")

    # 检查前10个低门槛动作
    print("  低门槛堕落动作 (需求corruption<30):")
    low_threshold = [a for a in corruption_actions if a["req_corruption"] < 30]
    for action in low_threshold[:5]:
        print(f"    {action['name']}: +{action['gain']} (需求堕落≥{action['req_corruption']})")

    if len(low_threshold) < 3:
        results["warnings"] += 1
        print("  ⚠️ 警告: 低门槛堕落动作较少，可能存在路径死锁")

@test("每日互动次数计算")
def test_daily_interactions():
    """测试每日互动限制"""
    from plugins.desire_theatre.core.evolution_system import EvolutionSystem

    # 模拟各阶段的每日互动次数
    limits = {
        0: 3,  # 陌生人
        1: 4,  # 朋友
        2: 5,  # 亲密
        3: 6,  # 恋人
        4: 6,  # 深度
    }

    total_days = 42
    avg_interactions = sum(limits.values()) / len(limits)
    total_possible = int(avg_interactions * total_days)

    print(f"  42天总互动次数估算: {total_possible}")
    print(f"  平均每天: {avg_interactions:.1f} 次")

    if total_possible < 200:
        results["warnings"] += 1
        print("  ⚠️ 警告: 总互动次数可能不足以完成所有内容")
    else:
        print("  ✓ 总互动次数充足")

# 运行所有测试
test_database_init()
test_character_creation()
test_actions_config()
test_personality_config()
test_evolution_stages()
test_corruption_path()
test_daily_interactions()

# 打印总结
print("\n" + "=" * 60)
print("测试总结")
print("=" * 60)
print(f"✅ 通过: {results['passed']}")
print(f"❌ 失败: {results['failed']}")
print(f"⚠️  警告: {results['warnings']}")
print("=" * 60)

# 详细报告
if results['failed'] > 0:
    print("\n失败测试:")
    for test in results['tests']:
        if test['status'] == 'FAIL':
            print(f"  - {test['name']}: {test.get('error', 'Unknown')}")

# 返回状态码
sys.exit(0 if results['failed'] == 0 else 1)
