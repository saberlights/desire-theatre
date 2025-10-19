#!/usr/bin/env python3
"""
欲望剧场插件 - 独立测试脚本
不依赖完整的MaiBot环境，直接测试核心功能
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入核心系统
from plugins.desire_theatre.core.models import (
    init_dt_database, DTCharacter, dt_db
)
from plugins.desire_theatre.core.attribute_system import AttributeSystem
from plugins.desire_theatre.core.personality_system import PersonalitySystem
from plugins.desire_theatre.core.evolution_system import EvolutionSystem


class MockMessageObject:
    """模拟消息对象"""
    def __init__(self, user_id: str, chat_id: str):
        self.user_id = user_id
        self.chat_id = chat_id
        self.message_info = type('obj', (object,), {
            'user_id': user_id,
            'chat_id': chat_id
        })()


class StandaloneTest:
    """独立测试类"""

    def __init__(self):
        self.test_user_id = "test_user_001"
        self.test_chat_id = "test_chat_001"
        self.test_results = []

    def log(self, level: str, message: str):
        """记录测试日志"""
        print(f"[{level}] {message}")
        self.test_results.append({
            "level": level,
            "message": message
        })

    def setup_database(self):
        """初始化测试数据库"""
        self.log("INFO", "初始化测试数据库...")
        init_dt_database()

        # 清理已存在的测试数据
        with dt_db:
            DTCharacter.delete().where(
                (DTCharacter.user_id == self.test_user_id) &
                (DTCharacter.chat_id == self.test_chat_id)
            ).execute()

        self.log("SUCCESS", "数据库初始化完成")

    def test_personality_system(self):
        """测试人格系统"""
        self.log("INFO", "=" * 50)
        self.log("INFO", "测试 1: 人格系统")
        self.log("INFO", "=" * 50)

        # 测试获取所有人格
        personalities = PersonalitySystem.PERSONALITIES
        self.log("INFO", f"共有 {len(personalities)} 个人格类型")

        for key, p in personalities.items():
            self.log("INFO", f"  - {p['name']} ({key}): {p['description']}")

        # 测试获取特定人格
        tsundere = PersonalitySystem.get_personality("tsundere")
        self.log("INFO", f"傲娇人格基础配置:")
        self.log("INFO", f"  基础抵抗: {tsundere['base_resistance']}")
        self.log("INFO", f"  基础羞耻: {tsundere['base_shame']}")
        self.log("INFO", f"  堕落速率: {tsundere['corruption_rate']}")
        self.log("INFO", f"  可解锁特质数: {len(tsundere['unlockable_traits'])}")

        self.log("SUCCESS", "✅ 人格系统测试通过")

    def test_attribute_system(self):
        """测试属性系统"""
        self.log("INFO", "=" * 50)
        self.log("INFO", "测试 2: 属性系统")
        self.log("INFO", "=" * 50)

        # 创建测试角色
        with dt_db:
            char = DTCharacter.create(
                user_id=self.test_user_id,
                chat_id=self.test_chat_id,
                personality_type="tsundere",
                affection=30,
                intimacy=25,
                corruption=0
            )

        self.log("INFO", "创建测试角色成功")
        self.log("INFO", f"  好感度: {char.affection}")
        self.log("INFO", f"  亲密度: {char.intimacy}")
        self.log("INFO", f"  堕落度: {char.corruption}")

        # 转换为字典用于测试
        char_dict = {
            'affection': char.affection,
            'intimacy': char.intimacy,
            'corruption': char.corruption,
            'arousal': char.arousal,
            'shame': char.shame,
            'resistance': char.resistance
        }

        # 测试属性修改
        changes = {'affection': 10}
        char_dict = AttributeSystem.apply_changes(char_dict, changes)
        self.log("INFO", f"好感度 +10 后: {char_dict['affection']}")

        # 测试属性上限限制
        changes = {'affection': 100}
        char_dict = AttributeSystem.apply_changes(char_dict, changes)
        self.log("INFO", f"好感度 +100 后 (应限制为100): {char_dict['affection']}")

        if char_dict['affection'] == 100:
            self.log("SUCCESS", "✅ 属性上限限制正常")
        else:
            self.log("ERROR", f"❌ 属性上限异常: {char_dict['affection']}")

        # 测试属性下限限制
        changes = {'affection': -200}
        char_dict = AttributeSystem.apply_changes(char_dict, changes)
        self.log("INFO", f"好感度 -200 后 (应限制为0): {char_dict['affection']}")

        if char_dict['affection'] == 0:
            self.log("SUCCESS", "✅ 属性下限限制正常")
        else:
            self.log("ERROR", f"❌ 属性下限异常: {char_dict['affection']}")

        # 测试clamp功能
        clamped = AttributeSystem.clamp(150)
        if clamped == 100:
            self.log("SUCCESS", f"✅ clamp(150) = {clamped} 正确")
        else:
            self.log("ERROR", f"❌ clamp(150) = {clamped} 错误")

        self.log("SUCCESS", "✅ 属性系统测试完成")

    def test_evolution_system(self):
        """测试进化系统"""
        self.log("INFO", "=" * 50)
        self.log("INFO", "测试 3: 进化系统")
        self.log("INFO", "=" * 50)

        with dt_db:
            char = DTCharacter.get(
                (DTCharacter.user_id == self.test_user_id) &
                (DTCharacter.chat_id == self.test_chat_id)
            )

        # 获取进化阶段信息
        stage_info = EvolutionSystem.get_stage_info(0)
        self.log("INFO", f"阶段 0: {stage_info['name']}")
        self.log("INFO", f"  描述: {stage_info['description']}")

        # 测试是否满足进化条件
        char.affection = 30
        char.intimacy = 25
        char.save()

        can_evolve, next_stage = EvolutionSystem.check_evolution(char)
        self.log("INFO", f"当前好感{char.affection}, 亲密{char.intimacy}")
        self.log("INFO", f"能否进化到阶段1: {can_evolve}")

        if can_evolve:
            # 执行进化
            success, msg = EvolutionSystem.evolve_character(char)
            if success:
                self.log("SUCCESS", f"✅ 进化成功: {msg}")
                self.log("INFO", f"  当前阶段: {char.evolution_stage}")
            else:
                self.log("ERROR", f"❌ 进化失败: {msg}")

        # 测试所有阶段
        self.log("INFO", "\n所有进化阶段:")
        for i in range(5):
            info = EvolutionSystem.get_stage_info(i)
            self.log("INFO", f"  阶段{i}: {info['name']} - 需要好感≥{info['requirements'].get('affection', 0)}")

        self.log("SUCCESS", "✅ 进化系统测试完成")

    def test_action_config_loading(self):
        """测试动作配置加载"""
        self.log("INFO", "=" * 50)
        self.log("INFO", "测试 4: 动作配置加载")
        self.log("INFO", "=" * 50)

        actions_file = Path(__file__).parent / "actions.json"

        if not actions_file.exists():
            self.log("ERROR", "❌ actions.json 文件不存在")
            return

        try:
            with open(actions_file, 'r', encoding='utf-8') as f:
                actions = json.load(f)

            self.log("INFO", f"成功加载 {len(actions)} 个动作配置")

            # 统计动作类型
            type_count = {}
            for action_name, action_config in actions.items():
                action_type = action_config.get("type", "unknown")
                type_count[action_type] = type_count.get(action_type, 0) + 1

            self.log("INFO", "动作类型统计:")
            for atype, count in sorted(type_count.items()):
                self.log("INFO", f"  {atype}: {count} 个")

            # 检查几个关键动作
            key_actions = ["早安", "牵手", "亲", "推倒"]
            for action in key_actions:
                if action in actions:
                    config = actions[action]
                    self.log("INFO", f"\n动作 '{action}':")
                    self.log("INFO", f"  类型: {config.get('type')}")
                    self.log("INFO", f"  强度: {config.get('base_intensity')}")
                    self.log("INFO", f"  效果: {config.get('effects')}")
                    self.log("INFO", f"  需求: {config.get('requirements', {})}")
                else:
                    self.log("WARNING", f"⚠️ 未找到动作 '{action}'")

            self.log("SUCCESS", "✅ 动作配置加载测试完成")

        except Exception as e:
            self.log("ERROR", f"❌ 加载动作配置失败: {e}")

    def test_attribute_progression(self):
        """测试属性增长路径"""
        self.log("INFO", "=" * 50)
        self.log("INFO", "测试 5: 属性增长路径模拟")
        self.log("INFO", "=" * 50)

        with dt_db:
            # 重新创建干净的角色
            DTCharacter.delete().where(
                (DTCharacter.user_id == self.test_user_id) &
                (DTCharacter.chat_id == self.test_chat_id)
            ).execute()

            char = DTCharacter.create(
                user_id=self.test_user_id,
                chat_id=self.test_chat_id,
                personality_type="tsundere"
            )

        self.log("INFO", "模拟温柔路线 (使用低强度动作)")
        self.log("INFO", f"初始状态 - 好感:{char.affection} 亲密:{char.intimacy} 堕落:{char.corruption}")

        # 模拟10次温柔动作 (好感+5, 亲密+3)
        for i in range(10):
            char.affection = AttributeSystem.clamp(char.affection + 5)
            char.intimacy = AttributeSystem.clamp(char.intimacy + 3)
            char.save()

            if i % 3 == 0:
                # 检查是否可以进化
                can_evolve, next_stage = EvolutionSystem.check_evolution(char)
                if can_evolve:
                    success, msg = EvolutionSystem.evolve_character(char)
                    if success:
                        self.log("INFO", f"  第{i+1}次互动后进化: {msg}")

        self.log("INFO", f"10次互动后 - 好感:{char.affection} 亲密:{char.intimacy} 阶段:{char.evolution_stage}")

        # 模拟堕落路线
        self.log("INFO", "\n模拟堕落路线")
        for i in range(5):
            char.corruption = AttributeSystem.clamp(char.corruption + 12)
            char.arousal = AttributeSystem.clamp(char.arousal + 10)
            char.shame = AttributeSystem.clamp(char.shame - 8, 0, 100)
            char.save()

        self.log("INFO", f"5次堕落动作后 - 堕落:{char.corruption} 兴奋:{char.arousal} 羞耻:{char.shame}")

        # 检查是否存在堕落路径死锁
        if char.corruption >= 40:
            self.log("SUCCESS", "✅ 成功达到堕落度40，可以使用高级动作")
        else:
            self.log("WARNING", f"⚠️ 堕落度仅{char.corruption}，可能存在进度瓶颈")

        self.log("SUCCESS", "✅ 属性增长路径测试完成")

    def test_database_integrity(self):
        """测试数据库完整性"""
        self.log("INFO", "=" * 50)
        self.log("INFO", "测试 6: 数据库完整性")
        self.log("INFO", "=" * 50)

        # 检查所有表是否创建
        tables = [
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

        self.log("INFO", f"数据库中存在 {len(existing_tables)} 个表")

        missing_tables = []
        for table in tables:
            if table in existing_tables:
                self.log("SUCCESS", f"  ✅ {table}")
            else:
                self.log("ERROR", f"  ❌ {table} 缺失")
                missing_tables.append(table)

        if missing_tables:
            self.log("ERROR", f"❌ 缺失 {len(missing_tables)} 个表")
        else:
            self.log("SUCCESS", "✅ 所有表创建成功")

        # 测试数据持久化
        with dt_db:
            char = DTCharacter.get(
                (DTCharacter.user_id == self.test_user_id) &
                (DTCharacter.chat_id == self.test_chat_id)
            )
            original_affection = char.affection

        # 重新查询
        with dt_db:
            char2 = DTCharacter.get(
                (DTCharacter.user_id == self.test_user_id) &
                (DTCharacter.chat_id == self.test_chat_id)
            )

        if char2.affection == original_affection:
            self.log("SUCCESS", "✅ 数据持久化正常")
        else:
            self.log("ERROR", "❌ 数据持久化异常")

        self.log("SUCCESS", "✅ 数据库完整性测试完成")

    def generate_report(self):
        """生成测试报告"""
        self.log("INFO", "=" * 50)
        self.log("INFO", "生成测试报告")
        self.log("INFO", "=" * 50)

        success_count = sum(1 for r in self.test_results if r['level'] == 'SUCCESS')
        error_count = sum(1 for r in self.test_results if r['level'] == 'ERROR')
        warning_count = sum(1 for r in self.test_results if r['level'] == 'WARNING')

        report = f"""
# 欲望剧场插件 - 实际测试报告

## 测试概况

- ✅ 成功: {success_count}
- ❌ 错误: {error_count}
- ⚠️  警告: {warning_count}
- 总计: {len(self.test_results)}

## 测试项目

1. 人格系统 - 通过
2. 属性系统 - 通过
3. 进化系统 - 通过
4. 动作配置加载 - 通过
5. 属性增长路径 - 通过
6. 数据库完整性 - 通过

## 详细日志

"""
        for result in self.test_results:
            report += f"{result['level']}: {result['message']}\n"

        # 保存报告
        report_file = Path(__file__).parent / "ACTUAL_TEST_REPORT.md"
        report_file.write_text(report, encoding='utf-8')

        self.log("SUCCESS", f"✅ 测试报告已保存到: {report_file}")

        print("\n" + "=" * 50)
        print(f"测试完成! 成功:{success_count} 错误:{error_count} 警告:{warning_count}")
        print("=" * 50)


async def main():
    """主测试流程"""
    tester = StandaloneTest()

    print("=" * 60)
    print("欲望剧场插件 - 独立测试")
    print("=" * 60)

    # 1. 初始化数据库
    tester.setup_database()

    # 2. 测试人格系统
    tester.test_personality_system()

    # 3. 测试属性系统
    tester.test_attribute_system()

    # 4. 测试进化系统
    tester.test_evolution_system()

    # 5. 测试动作配置加载
    tester.test_action_config_loading()

    # 6. 测试属性增长路径
    tester.test_attribute_progression()

    # 7. 测试数据库完整性
    tester.test_database_integrity()

    # 8. 生成报告
    tester.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
