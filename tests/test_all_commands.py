"""
测试所有命令是否正确注册和导入
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/root/maimai/MaiBot')

def test_command_imports():
    """测试所有命令是否能正确导入"""
    print("=" * 60)
    print("测试命令导入")
    print("=" * 60)

    try:
        from plugins.desire_theatre.commands import (
            DTActionCommand,
            DTStartGameCommand,
            DTRestartCommand,
            DTStatusCommand,
            DTQuickStatusCommand,
            DTHelpCommand,
            DTExportCommand,
            DTImportCommand,
            DTOutfitListCommand,
            DTWearOutfitCommand,
            DTInventoryCommand,
            DTUseItemCommand,
            DTSceneListCommand,
            DTGoSceneCommand,
            DTTruthCommand,
            DTDareCommand,
            DTDiceCommand,
            DTShopCommand,
            DTBuyItemCommand,
            DTBuyOutfitCommand,
            DTWorkCommand,
            DTPapaKatsuCommand,
        )
        print("✅ 所有命令类导入成功")
        return True
    except ImportError as e:
        print(f"❌ 命令导入失败: {e}")
        return False

def test_command_patterns():
    """测试所有命令的 pattern"""
    print("\n" + "=" * 60)
    print("测试命令 Pattern")
    print("=" * 60)

    # 模拟导入（不依赖完整环境）
    commands_info = [
        # 核心命令
        ("DTStartGameCommand", r"^/(开始|start)\s+(.+)$", ["/开始 傲娇", "/start tsundere"]),
        ("DTRestartCommand", r"^/(重开|restart|reset)$", ["/重开", "/restart"]),
        ("DTStatusCommand", r"^/(看|status|状态)$", ["/看", "/status"]),
        ("DTQuickStatusCommand", r"^/(快看|quick)$", ["/快看", "/quick"]),
        ("DTHelpCommand", r"^/(dt|dt帮助|帮助\s*dt|帮助\s+(命令|游戏|动作|服装|道具|场景|小游戏|进化|经济|所有|all))(?:\s+(命令|游戏|动作|服装|道具|场景|小游戏|进化|经济|所有|all))?$",
         ["/dt", "/帮助 命令", "/帮助 游戏"]),
        ("DTExportCommand", r"^/(导出|export)$", ["/导出", "/export"]),
        ("DTImportCommand", r"^/(导入|import)\s+(.+)$", ["/导入 ABC123", "/import ABC123"]),

        # 服装命令
        ("DTOutfitListCommand", r"^/(服装列表|服装|outfits?)$", ["/服装列表", "/服装", "/outfit"]),
        ("DTWearOutfitCommand", r"^/(穿|wear)\s+(.+)$", ["/穿 女仆装", "/wear maid"]),

        # 道具命令
        ("DTInventoryCommand", r"^/(背包|inventory|物品|道具)$", ["/背包", "/inventory"]),
        ("DTUseItemCommand", r"^/(用|use|使用)\s+(.+)$", ["/用 巧克力", "/use chocolate"]),

        # 场景命令
        ("DTSceneListCommand", r"^/(场景列表|场景|scenes?)$", ["/场景列表", "/场景", "/scene"]),
        ("DTGoSceneCommand", r"^/(去|go|goto)\s+(.+)$", ["/去 卧室", "/go bedroom"]),

        # 游戏命令
        ("DTTruthCommand", r"^/(真心话|truth)$", ["/真心话", "/truth"]),
        ("DTDareCommand", r"^/(大冒险|dare)$", ["/大冒险", "/dare"]),
        ("DTDiceCommand", r"^/(骰子|dice|roll)$", ["/骰子", "/dice"]),

        # 商店命令
        ("DTShopCommand", r"^/(商店|shop|商城)$", ["/商店", "/shop"]),
        ("DTBuyItemCommand", r"^/(买道具|买|buy)\s+(.+?)(?:\s+(\d+))?$", ["/买道具 巧克力", "/买 巧克力 2"]),
        ("DTBuyOutfitCommand", r"^/(买服装|买衣服)\s+(.+)$", ["/买服装 女仆装"]),

        # 经济命令
        ("DTWorkCommand", r"^/(打工|work|赚钱)(?:\s+(.+))?$", ["/打工", "/打工 咖啡店", "/work cafe"]),
        ("DTPapaKatsuCommand", r"^/(援交|爸爸活|包养)(?:\s+(.+))?$", ["/援交", "/援交 约会", "/爸爸活 约会"]),

        # 动作命令（通配）
        ("DTActionCommand", r"^/(.+?)(?:\s+(.+))?$", ["/牵手", "/亲 嘴唇", "/聊天"]),
    ]

    import re

    passed = 0
    failed = 0

    for cmd_name, pattern, test_cases in commands_info:
        print(f"\n测试 {cmd_name}:")
        print(f"  Pattern: {pattern}")

        for test in test_cases:
            match = re.match(pattern, test)
            if match:
                print(f"  ✅ {test}")
                passed += 1
            else:
                print(f"  ❌ {test} - 匹配失败")
                failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0

def test_plugin_registration():
    """测试插件注册"""
    print("\n" + "=" * 60)
    print("测试插件注册")
    print("=" * 60)

    try:
        from plugins.desire_theatre.plugin import DesireTheatrePlugin

        # 创建插件实例（可能会失败，因为环境不完整）
        # plugin = DesireTheatrePlugin()

        # 直接检查 get_plugin_components 方法
        print("检查 get_plugin_components 方法...")

        # 读取源码检查
        with open('/root/maimai/MaiBot/plugins/desire_theatre/plugin.py', 'r') as f:
            content = f.read()

        required_commands = [
            'DTActionCommand',
            'DTStartGameCommand',
            'DTRestartCommand',
            'DTStatusCommand',
            'DTQuickStatusCommand',
            'DTHelpCommand',
            'DTExportCommand',
            'DTImportCommand',
            'DTOutfitListCommand',
            'DTWearOutfitCommand',
            'DTInventoryCommand',
            'DTUseItemCommand',
            'DTSceneListCommand',
            'DTGoSceneCommand',
            'DTTruthCommand',
            'DTDareCommand',
            'DTDiceCommand',
            'DTShopCommand',
            'DTBuyItemCommand',
            'DTBuyOutfitCommand',
            'DTWorkCommand',
            'DTPapaKatsuCommand',
        ]

        all_found = True
        for cmd in required_commands:
            if cmd in content:
                print(f"  ✅ {cmd}")
            else:
                print(f"  ❌ {cmd} - 未在 plugin.py 中找到")
                all_found = False

        if all_found:
            print("\n✅ 所有命令都已在插件中注册")
        else:
            print("\n❌ 部分命令未注册")

        return all_found

    except Exception as e:
        print(f"❌ 插件注册检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_actions_config():
    """测试动作配置"""
    print("\n" + "=" * 60)
    print("测试动作配置")
    print("=" * 60)

    try:
        import json
        with open('/root/maimai/MaiBot/plugins/desire_theatre/actions.json', 'r', encoding='utf-8') as f:
            actions = json.load(f)

        action_count = len(actions.get('actions', {}))
        print(f"✅ 成功加载 {action_count} 个动作配置")

        # 验证必要字段
        required_fields = ['type', 'category', 'description']
        invalid_actions = []

        for action_name, action_config in actions['actions'].items():
            for field in required_fields:
                if field not in action_config:
                    invalid_actions.append(f"{action_name} 缺少字段: {field}")

        if invalid_actions:
            print("❌ 发现无效动作配置:")
            for err in invalid_actions:
                print(f"  - {err}")
            return False
        else:
            print(f"✅ 所有 {action_count} 个动作配置格式正确")
            return True

    except Exception as e:
        print(f"❌ 动作配置加载失败: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("Desire Theatre 插件 - 完整命令测试")
    print("=" * 60)

    results = []

    # 1. 测试命令导入
    results.append(("命令导入", test_command_imports()))

    # 2. 测试命令 pattern
    results.append(("命令Pattern", test_command_patterns()))

    # 3. 测试插件注册
    results.append(("插件注册", test_plugin_registration()))

    # 4. 测试动作配置
    results.append(("动作配置", test_actions_config()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查上述错误")
    print("=" * 60)

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
