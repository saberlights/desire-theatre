"""
Desire Theatre 插件命令测试脚本
测试所有命令的配置和pattern是否正确
"""

import re
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_command_patterns():
    """测试所有命令的正则表达式pattern"""

    print("=" * 80)
    print("🔍 Desire Theatre 命令 Pattern 测试")
    print("=" * 80)

    # 定义测试用例
    test_cases = {
        # 核心命令
        "开始游戏": {
            "pattern": r"^/(开始|start)(?:\s+(傲娇|天真|妖媚|害羞|高冷|tsundere|innocent|seductive|shy|cold))?$",
            "valid": ["/开始", "/开始 傲娇", "/start tsundere", "/start"],
            "invalid": ["/开始傲娇", "/开始 xxx"]
        },
        "查看状态": {
            "pattern": r"^/(看|status|状态)$",
            "valid": ["/看", "/status", "/状态"],
            "invalid": ["/看 xxx", "/看看"]
        },
        "快速状态": {
            "pattern": r"^/(快看|quick)$",
            "valid": ["/快看", "/quick"],
            "invalid": ["/快看看", "/quick x"]
        },
        "重开游戏": {
            "pattern": r"^/(重开|restart|reset|确认重开)$",
            "valid": ["/重开", "/restart", "/reset", "/确认重开"],
            "invalid": ["/重开游戏", "/restart now"]
        },
        "导出存档": {
            "pattern": r"^/(导出|export)$",
            "valid": ["/导出", "/export"],
            "invalid": ["/导出存档", "/export save"]
        },
        "导入存档": {
            "pattern": r"^/(导入|import)\s+(.+)$",
            "valid": ["/导入 ABC123", "/import xyz"],
            "invalid": ["/导入", "/import"]
        },

        # 扩展命令
        "服装列表": {
            "pattern": r"^/(服装列表|outfits|wardrobe)$",
            "valid": ["/服装列表", "/outfits", "/wardrobe"],
            "invalid": ["/服装列表 xxx"]
        },
        "穿服装": {
            "pattern": r"^/(穿|wear)\s+(.+)$",
            "valid": ["/穿 女仆装", "/wear maid"],
            "invalid": ["/穿", "/wear"]
        },
        "道具背包": {
            "pattern": r"^/(背包|道具背包|inventory|items)$",
            "valid": ["/背包", "/道具背包", "/inventory", "/items"],
            "invalid": ["/背包 xxx"]
        },
        "使用道具": {
            "pattern": r"^/(用|use|使用)\s+(.+)$",
            "valid": ["/用 爱情药水", "/use potion"],
            "invalid": ["/用", "/use"]
        },
        "场景列表": {
            "pattern": r"^/(场景列表|scenes)$",
            "valid": ["/场景列表", "/scenes"],
            "invalid": ["/场景列表 xxx"]
        },
        "切换场景": {
            "pattern": r"^/(去|goto)\s+(.+)$",
            "valid": ["/去 卧室", "/goto bedroom"],
            "invalid": ["/去", "/goto"]
        },

        # 游戏系统
        "真心话": {
            "pattern": r"^/(真心话|truth)$",
            "valid": ["/真心话", "/truth"],
            "invalid": ["/真心话游戏"]
        },
        "大冒险": {
            "pattern": r"^/(大冒险|dare)$",
            "valid": ["/大冒险", "/dare"],
            "invalid": ["/大冒险游戏"]
        },
        "骰子": {
            "pattern": r"^/(骰子|dice|roll)$",
            "valid": ["/骰子", "/dice", "/roll"],
            "invalid": ["/骰子 6"]
        },

        # 经济系统
        "商店": {
            "pattern": r"^/(商店|shop|store)$",
            "valid": ["/商店", "/shop", "/store"],
            "invalid": ["/商店 xxx"]
        },
        "购买道具": {
            "pattern": r"^/(买道具|buy)\s+(.+)$",
            "valid": ["/买道具 爱情药水", "/buy potion"],
            "invalid": ["/买道具", "/buy"]
        },
        "购买服装": {
            "pattern": r"^/(买服装|买衣服)\s+(.+)$",
            "valid": ["/买服装 女仆装", "/买衣服 学生制服"],
            "invalid": ["/买服装", "/买衣服"]
        },
        "打工": {
            "pattern": r"^/(打工|work)\s+(.+)$",
            "valid": ["/打工 咖啡店", "/work cafe"],
            "invalid": ["/打工", "/work"]
        },
        "援交": {
            "pattern": r"^/(援交|爸爸活|papa)\s+(.+)$",
            "valid": ["/援交 约会", "/爸爸活 摄影", "/papa date"],
            "invalid": ["/援交", "/papa"]
        },
    }

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for command_name, test_data in test_cases.items():
        pattern = test_data["pattern"]
        valid_cases = test_data["valid"]
        invalid_cases = test_data["invalid"]

        print(f"\n📝 测试命令: {command_name}")
        print(f"   Pattern: {pattern}")

        # 测试应该匹配的情况
        for case in valid_cases:
            total_tests += 1
            if re.match(pattern, case):
                print(f"   ✅ '{case}' - 匹配成功")
                passed_tests += 1
            else:
                print(f"   ❌ '{case}' - 匹配失败（应该匹配）")
                failed_tests.append((command_name, case, "应该匹配但未匹配"))

        # 测试不应该匹配的情况
        for case in invalid_cases:
            total_tests += 1
            if not re.match(pattern, case):
                print(f"   ✅ '{case}' - 正确拒绝")
                passed_tests += 1
            else:
                print(f"   ❌ '{case}' - 错误匹配（不应该匹配）")
                failed_tests.append((command_name, case, "不应该匹配但匹配了"))

    # 统计结果
    print("\n" + "=" * 80)
    print(f"📊 测试统计")
    print("=" * 80)
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests} ✅")
    print(f"失败: {len(failed_tests)} ❌")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")

    if failed_tests:
        print("\n❌ 失败详情:")
        for cmd, case, reason in failed_tests:
            print(f"   [{cmd}] '{case}' - {reason}")

    return passed_tests == total_tests


def test_actions_config():
    """测试 actions.json 配置文件"""

    print("\n" + "=" * 80)
    print("📦 测试 actions.json 配置")
    print("=" * 80)

    actions_file = Path(__file__).parent / "actions.json"

    if not actions_file.exists():
        print("❌ actions.json 文件不存在！")
        return False

    try:
        with open(actions_file, 'r', encoding='utf-8') as f:
            actions_config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}")
        return False

    if "actions" not in actions_config:
        print("❌ 缺少 'actions' 键")
        return False

    actions = actions_config["actions"]
    print(f"✅ 成功加载配置，共 {len(actions)} 个动作")

    # 验证每个动作的配置
    required_fields = ["type", "category", "description"]
    issues = []

    print("\n📋 动作列表:")
    for action_name, action_data in actions.items():
        print(f"   • {action_name} - {action_data.get('description', '无描述')}")

        # 检查必需字段
        for field in required_fields:
            if field not in action_data:
                issues.append(f"动作 '{action_name}' 缺少必需字段: {field}")

        # 检查类型是否合法
        valid_types = ["gentle", "intimate", "seductive", "dominant", "corrupting",
                      "risky", "mood_locked", "outfit", "item", "scene", "game", "gift"]
        if action_data.get("type") not in valid_types:
            issues.append(f"动作 '{action_name}' 的 type '{action_data.get('type')}' 不合法")

    # 按类型统计
    print("\n📊 动作类型统计:")
    type_count = {}
    for action_data in actions.values():
        action_type = action_data.get("type", "unknown")
        type_count[action_type] = type_count.get(action_type, 0) + 1

    for action_type, count in sorted(type_count.items()):
        print(f"   {action_type}: {count}个")

    if issues:
        print("\n⚠️ 发现问题:")
        for issue in issues:
            print(f"   • {issue}")
        return False

    print("\n✅ 所有动作配置验证通过！")
    return True


def test_action_pattern():
    """测试动作命令的通配 pattern"""

    print("\n" + "=" * 80)
    print("🎯 测试动作命令 Pattern")
    print("=" * 80)

    # 加载 actions.json 获取所有动作名称
    actions_file = Path(__file__).parent / "actions.json"

    try:
        with open(actions_file, 'r', encoding='utf-8') as f:
            actions_config = json.load(f)
        action_names = list(actions_config["actions"].keys())
    except Exception as e:
        print(f"❌ 无法加载 actions.json: {e}")
        return False

    # 按长度降序排序
    action_names.sort(key=len, reverse=True)

    # 构建 pattern
    escaped_actions = [re.escape(name) for name in action_names]
    actions_pattern = "|".join(escaped_actions)
    pattern = rf"^/({actions_pattern})(?:\s+(.+))?$"

    print(f"✅ 成功构建动作 pattern（包含 {len(action_names)} 个动作）")

    # 测试用例
    test_cases = {
        "无参数动作": [
            ("/牵手", "牵手", ""),
            ("/早安", "早安", ""),
            ("/抱", "抱", "")
        ],
        "带参数动作": [
            ("/亲 嘴唇", "亲", "嘴唇"),
            ("/摸 头", "摸", "头"),
            ("/诱惑 眼神", "诱惑", "眼神")
        ],
        "长动作名": [
            ("/挑逗敏感点", "挑逗敏感点", ""),
            ("/突破防线", "突破防线", ""),
            ("/羞辱play", "羞辱play", "")
        ],
        "应该失败": [
            ("/不存在的动作", None, None),
            ("牵手", None, None),  # 缺少斜杠
        ]
    }

    passed = 0
    failed = 0

    for category, cases in test_cases.items():
        print(f"\n📝 测试类别: {category}")
        for test_input, expected_action, expected_param in cases:
            match = re.match(pattern, test_input)

            if expected_action is None:
                # 应该不匹配
                if match is None:
                    print(f"   ✅ '{test_input}' - 正确拒绝")
                    passed += 1
                else:
                    print(f"   ❌ '{test_input}' - 错误匹配")
                    failed += 1
            else:
                # 应该匹配
                if match:
                    actual_action = match.group(1)
                    actual_param = match.group(2).strip() if match.group(2) else ""

                    if actual_action == expected_action and actual_param == expected_param:
                        print(f"   ✅ '{test_input}' → 动作='{actual_action}', 参数='{actual_param}'")
                        passed += 1
                    else:
                        print(f"   ❌ '{test_input}' - 解析错误")
                        print(f"      期望: 动作='{expected_action}', 参数='{expected_param}'")
                        print(f"      实际: 动作='{actual_action}', 参数='{actual_param}'")
                        failed += 1
                else:
                    print(f"   ❌ '{test_input}' - 匹配失败")
                    failed += 1

    print(f"\n📊 测试结果: {passed}通过, {failed}失败")
    return failed == 0


def generate_command_list():
    """生成完整的命令列表文档"""

    print("\n" + "=" * 80)
    print("📄 生成命令列表文档")
    print("=" * 80)

    # 加载 actions.json
    actions_file = Path(__file__).parent / "actions.json"

    try:
        with open(actions_file, 'r', encoding='utf-8') as f:
            actions_config = json.load(f)
        actions = actions_config["actions"]
    except Exception as e:
        print(f"❌ 无法加载 actions.json: {e}")
        return

    # 按类型分组
    actions_by_type = {}
    for name, data in actions.items():
        action_type = data.get("type", "unknown")
        if action_type not in actions_by_type:
            actions_by_type[action_type] = []
        actions_by_type[action_type].append((name, data))

    # 生成文档
    doc = []
    doc.append("# Desire Theatre 完整命令列表\n")
    doc.append("## 核心命令\n")
    doc.append("| 命令 | 说明 |\n")
    doc.append("|------|------|\n")
    doc.append("| /开始 [人格] | 创建角色（傲娇/天真/妖媚/害羞/高冷） |\n")
    doc.append("| /看 | 查看详细状态 |\n")
    doc.append("| /快看 | 快速查看核心属性 |\n")
    doc.append("| /帮助 [类别] | 查看帮助信息 |\n")
    doc.append("| /重开 | 重置游戏 |\n")
    doc.append("| /导出 | 导出存档 |\n")
    doc.append("| /导入 <码> | 导入存档 |\n")
    doc.append("| /快速互动 | 随机选择动作 |\n")
    doc.append("| /推荐 | AI推荐下一步 |\n")

    doc.append("\n## 扩展命令\n")
    doc.append("| 命令 | 说明 |\n")
    doc.append("|------|------|\n")
    doc.append("| /服装列表 | 查看所有服装 |\n")
    doc.append("| /穿 <服装> | 穿上指定服装 |\n")
    doc.append("| /背包 | 查看道具背包 |\n")
    doc.append("| /用 <道具> | 使用道具 |\n")
    doc.append("| /场景列表 | 查看所有场景 |\n")
    doc.append("| /去 <场景> | 切换场景 |\n")
    doc.append("| /真心话 | 真心话游戏 |\n")
    doc.append("| /大冒险 | 大冒险游戏 |\n")
    doc.append("| /骰子 | 掷骰子 |\n")

    doc.append("\n## 经济系统\n")
    doc.append("| 命令 | 说明 |\n")
    doc.append("|------|------|\n")
    doc.append("| /商店 | 查看商店 |\n")
    doc.append("| /买道具 <名称> | 购买道具 |\n")
    doc.append("| /买服装 <名称> | 购买服装 |\n")
    doc.append("| /打工 <工作> | 打工赚钱 |\n")
    doc.append("| /援交 <服务> | 付费援交服务 |\n")

    doc.append("\n## 互动动作命令\n")

    type_names = {
        "gentle": "温柔互动",
        "intimate": "亲密互动",
        "seductive": "诱惑互动",
        "dominant": "支配互动",
        "corrupting": "堕落互动",
        "risky": "风险动作",
        "mood_locked": "情绪专属"
    }

    for action_type in ["gentle", "intimate", "seductive", "dominant", "corrupting", "risky", "mood_locked"]:
        if action_type in actions_by_type:
            doc.append(f"\n### {type_names.get(action_type, action_type)}\n")
            doc.append("| 命令 | 说明 | 强度 |\n")
            doc.append("|------|------|------|\n")

            for name, data in sorted(actions_by_type[action_type]):
                intensity = data.get("base_intensity", "?")
                description = data.get("description", "")

                # 处理参数提示
                param_hint = ""
                if "target_effects" in data:
                    param_hint = " [部位]"
                elif "modifiers" in data:
                    param_hint = " [方式]"

                doc.append(f"| /{name}{param_hint} | {description} | {intensity} |\n")

    # 保存文档
    output_file = Path(__file__).parent / "COMMAND_LIST.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("".join(doc))

    print(f"✅ 命令列表文档已生成: {output_file}")
    print(f"   共包含 {len(actions)} 个互动动作")


def main():
    """主测试函数"""

    print("\n🎭 Desire Theatre 插件命令测试套件\n")

    results = []

    # 1. 测试命令 pattern
    print("\n[1/4] 测试命令 Pattern...")
    results.append(("命令Pattern", test_command_patterns()))

    # 2. 测试 actions.json 配置
    print("\n[2/4] 测试动作配置文件...")
    results.append(("动作配置", test_actions_config()))

    # 3. 测试动作命令 pattern
    print("\n[3/4] 测试动作命令Pattern...")
    results.append(("动作Pattern", test_action_pattern()))

    # 4. 生成命令列表
    print("\n[4/4] 生成命令列表文档...")
    generate_command_list()
    results.append(("命令列表", True))

    # 总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 所有测试通过！插件命令配置正常。")
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误。")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
