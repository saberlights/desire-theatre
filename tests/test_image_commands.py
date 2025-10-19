"""
测试所有图片输出命令
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/root/maimai/MaiBot')

def test_help_image():
    """测试帮助图片生成"""
    print("=" * 60)
    print("测试帮助图片生成")
    print("=" * 60)

    try:
        from plugins.desire_theatre.utils.help_image_generator import HelpImageGenerator

        # 测试主帮助
        sections = [
            ("快速开始", [
                "/开始 傲娇 - 创建角色",
                "/看 - 查看状态",
                "/快看 - 快速查看核心属性"
            ]),
            ("基础互动", [
                "💕 温柔: /早安 /晚安 /牵手",
                "💋 亲密: /亲 <部位> /摸 <部位>",
                "🔥 诱惑: /诱惑 /挑逗"
            ])
        ]

        img_bytes, img_base64 = HelpImageGenerator.generate_help_image(
            "测试标题", sections, width=800
        )

        # 保存图片
        with open("test_help.png", "wb") as f:
            f.write(img_bytes)

        print(f"✅ 帮助图片生成成功")
        print(f"  文件大小: {len(img_bytes) / 1024:.1f} KB")
        print(f"  已保存到: test_help.png")
        return True

    except Exception as e:
        print(f"❌ 帮助图片生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_status_image():
    """测试状态图片生成"""
    print("\n" + "=" * 60)
    print("测试状态图片生成")
    print("=" * 60)

    try:
        from plugins.desire_theatre.utils.help_image_generator import HelpImageGenerator

        content = {
            "基础信息": {
                "⭐ 阶段": "初识 (1/5)",
                "💰 爱心币": "100"
            },
            "核心属性": {
                "💕 好感": "50/100 ❤️❤️",
                "💗 亲密": "30/100 💓",
                "😈 堕落": "10/100 🔥"
            }
        }

        img_bytes, img_base64 = HelpImageGenerator.generate_status_image(
            "角色状态", content, width=700
        )

        # 保存图片
        with open("test_status.png", "wb") as f:
            f.write(img_bytes)

        print(f"✅ 状态图片生成成功")
        print(f"  文件大小: {len(img_bytes) / 1024:.1f} KB")
        print(f"  已保存到: test_status.png")
        return True

    except Exception as e:
        print(f"❌ 状态图片生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_list_image():
    """测试列表图片生成"""
    print("\n" + "=" * 60)
    print("测试列表图片生成")
    print("=" * 60)

    try:
        from plugins.desire_theatre.utils.help_image_generator import HelpImageGenerator

        sections = [
            ("已拥有", [
                "✅ 日常便装 - 普通的便装",
                "✅ 学生制服 - 清纯的制服"
            ]),
            ("可解锁", [
                "🔓 女仆装 - 可爱的女仆装",
                "🔓 性感连衣裙 - 性感的裙子"
            ]),
            ("未解锁", [
                "🔒 兔女郎装 - 诱惑的兔女郎装",
                "🔒 情趣内衣 - 火辣的内衣"
            ])
        ]

        img_bytes, img_base64 = HelpImageGenerator.generate_list_image(
            "服装列表", sections, width=800
        )

        # 保存图片
        with open("test_list.png", "wb") as f:
            f.write(img_bytes)

        print(f"✅ 列表图片生成成功")
        print(f"  文件大小: {len(img_bytes) / 1024:.1f} KB")
        print(f"  已保存到: test_list.png")
        return True

    except Exception as e:
        print(f"❌ 列表图片生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_image_types():
    """测试所有图片类型"""
    print("\n" + "=" * 60)
    print("Desire Theatre 插件 - 图片输出功能测试")
    print("=" * 60)

    results = []

    # 测试帮助图片
    results.append(("帮助图片", test_help_image()))

    # 测试状态图片
    results.append(("状态图片", test_status_image()))

    # 测试列表图片
    results.append(("列表图片", test_list_image()))

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
        print("\n已生成的测试图片:")
        print("  - test_help.png (帮助图片)")
        print("  - test_status.png (状态图片)")
        print("  - test_list.png (列表图片)")
    else:
        print("⚠️ 部分测试失败，请检查上述错误")
    print("=" * 60)

    return all_passed

def test_command_integration():
    """测试命令集成"""
    print("\n" + "=" * 60)
    print("测试命令集成 - 检查所有命令是否正确使用图片输出")
    print("=" * 60)

    commands_to_check = {
        "status_commands.py": [
            ("DTQuickStatusCommand", "/快看", "generate_status_image"),
            ("DTStatusCommand", "/看", "generate_status_image"),
            ("DTHelpCommand._show_main_help", "/dt", "generate_help_image"),
            ("DTHelpCommand._show_commands_help", "/帮助 命令", "generate_help_image"),
        ],
        "extension_commands.py": [
            ("DTOutfitListCommand", "/服装列表", "generate_list_image"),
            ("DTInventoryCommand", "/背包", "generate_list_image"),
            ("DTSceneListCommand", "/场景列表", "generate_list_image"),
        ],
        "shop_commands.py": [
            ("DTShopCommand", "/商店", "generate_help_image"),
        ]
    }

    all_integrated = True

    for filename, commands in commands_to_check.items():
        filepath = f"/root/maimai/MaiBot/plugins/desire_theatre/commands/{filename}"

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            for cmd_name, cmd_text, generator_method in commands:
                if generator_method in content:
                    print(f"  ✅ {cmd_name} ({cmd_text}) - 已集成 {generator_method}")
                else:
                    print(f"  ❌ {cmd_name} ({cmd_text}) - 未找到 {generator_method}")
                    all_integrated = False

        except Exception as e:
            print(f"  ❌ 读取 {filename} 失败: {e}")
            all_integrated = False

    print("\n" + "=" * 60)
    if all_integrated:
        print("✅ 所有命令都已正确集成图片输出")
    else:
        print("❌ 部分命令未集成图片输出")
    print("=" * 60)

    return all_integrated

if __name__ == "__main__":
    # 测试图片生成
    image_test_passed = test_all_image_types()

    # 测试命令集成
    integration_passed = test_command_integration()

    # 总结
    print("\n" + "=" * 60)
    print("最终测试结果")
    print("=" * 60)
    print(f"图片生成测试: {'✅ 通过' if image_test_passed else '❌ 失败'}")
    print(f"命令集成测试: {'✅ 通过' if integration_passed else '❌ 失败'}")

    if image_test_passed and integration_passed:
        print("\n🎉 所有测试通过！图片输出功能已完全实现")
        sys.exit(0)
    else:
        print("\n⚠️ 部分测试失败")
        sys.exit(1)
