"""
双重人格系统 - 表层人格(Mask) vs 真实人格(Core)

核心机制:
- Mask: 她对外表现的样子（礼貌、矜持、社会化）
- Core: 她内心真实的欲望（原始、禁忌、本能）
- 两者之间的冲突和分裂会产生戏剧性

作者: MaiBot Community
"""

import random
from typing import Dict, Tuple, Optional, List
import json


class DualPersonalitySystem:
    """双重人格系统"""

    # 面具强度阈值
    MASK_THRESHOLD = {
        "崩溃": 10,      # 面具完全崩溃
        "裂痕": 30,      # 出现裂痕
        "摇晃": 50,      # 摇摇欲坠
        "稳固": 70,      # 相对稳定
        "完美": 90,      # 完美伪装
    }

    # 人格冲突等级
    CONFLICT_LEVELS = {
        "和谐": 20,      # 两人格和谐共处
        "轻微": 40,      # 轻微冲突
        "显著": 60,      # 显著冲突
        "激烈": 80,      # 激烈对抗
        "分裂": 100,     # 人格分裂
    }

    @staticmethod
    def calculate_mask_strength(character: Dict) -> int:
        """
        计算当前面具强度

        影响因素:
        - shame(羞耻心): 越高，越需要伪装
        - resistance(抵抗力): 越高，越能维持面具
        - corruption(堕落度): 越高，面具越难维持
        - arousal(兴奋度): 越高，越容易失控
        """
        shame = character.get("shame", 100)
        resistance = character.get("resistance", 100)
        corruption = character.get("corruption", 0)
        arousal = character.get("arousal", 0)

        # 基础面具强度 = (羞耻心 + 抵抗力) / 2
        base_strength = (shame + resistance) / 2

        # 堕落度和兴奋度会削弱面具
        corruption_penalty = corruption * 0.3
        arousal_penalty = arousal * 0.2

        final_strength = base_strength - corruption_penalty - arousal_penalty

        return max(0, min(100, int(final_strength)))

    @staticmethod
    def calculate_core_desire(character: Dict) -> int:
        """
        计算真实人格的欲望强度

        影响因素:
        - desire(欲望值): 核心欲望
        - arousal(兴奋度): 当前欲望
        - corruption(堕落度): 对禁忌的接受度
        - submission(顺从度): 服从本能的程度
        """
        desire = character.get("desire", 0)
        arousal = character.get("arousal", 0)
        corruption = character.get("corruption", 0)
        submission = character.get("submission", 50)

        # 真实欲望 = 欲望值 * 1.2 + 兴奋度 * 0.5 + 堕落度 * 0.3
        core_desire = desire * 1.2 + arousal * 0.5 + corruption * 0.3

        # 顺从度影响（>50增强，<50削弱）
        if submission > 50:
            core_desire *= (1 + (submission - 50) / 100)
        else:
            core_desire *= (0.7 + submission / 100)

        return max(0, min(100, int(core_desire)))

    @staticmethod
    def calculate_personality_conflict(mask_strength: int, core_desire: int) -> int:
        """
        计算人格冲突强度

        当面具强度和核心欲望都很高时，冲突最激烈
        """
        # 如果两者都高（>60），产生冲突
        if mask_strength > 60 and core_desire > 60:
            conflict = abs(mask_strength - core_desire) + 40
        # 如果面具弱但欲望强，冲突较小（面具已屈服）
        elif mask_strength < 30 and core_desire > 70:
            conflict = 20
        # 如果面具强但欲望弱，冲突较小（欲望未觉醒）
        elif mask_strength > 70 and core_desire < 30:
            conflict = 10
        # 其他情况按差值计算
        else:
            conflict = abs(mask_strength - core_desire)

        return max(0, min(100, conflict))

    @staticmethod
    def generate_dual_response(
        character: Dict,
        action_type: str,
        base_response: str,
        intensity: int
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        生成双重人格回复

        返回: (表层话, 内心独白, 身体反应)
        """
        mask_strength = DualPersonalitySystem.calculate_mask_strength(character)
        core_desire = DualPersonalitySystem.calculate_core_desire(character)
        conflict = DualPersonalitySystem.calculate_personality_conflict(mask_strength, core_desire)

        inner_voice = None
        body_reaction = None

        # 根据冲突等级决定是否暴露内心
        if conflict > 80:
            # 激烈冲突 - 一定会有内心独白和身体反应
            inner_voice_chance = 1.0
            body_reaction_chance = 1.0
        elif conflict > 60:
            # 显著冲突 - 高概率
            inner_voice_chance = 0.8
            body_reaction_chance = 0.7
        elif conflict > 40:
            # 轻微冲突 - 中概率
            inner_voice_chance = 0.5
            body_reaction_chance = 0.5
        elif conflict > 20:
            # 很小冲突 - 低概率
            inner_voice_chance = 0.3
            body_reaction_chance = 0.3
        else:
            # 几乎无冲突
            inner_voice_chance = 0.1
            body_reaction_chance = 0.1

        # 生成内心独白
        if random.random() < inner_voice_chance:
            inner_voice = DualPersonalitySystem._generate_inner_voice(
                character, mask_strength, core_desire, action_type
            )

        # 生成身体反应
        if random.random() < body_reaction_chance:
            body_reaction = DualPersonalitySystem._generate_body_reaction(
                character, mask_strength, core_desire, intensity
            )

        return None, inner_voice, body_reaction  # 表层话直接用base_response

    @staticmethod
    def _generate_inner_voice(
        character: Dict,
        mask_strength: int,
        core_desire: int,
        action_type: str
    ) -> str:
        """生成内心独白"""

        # 根据面具和欲望的关系生成不同的内心话
        if mask_strength > 70 and core_desire > 70:
            # 强烈压抑
            templates = [
                "不行...不能让他看出来我很期待...",
                "明明...明明身体已经...",
                "为什么我会这么想...我疯了吗？",
                "不对...这不是我应该有的想法...",
            ]
        elif mask_strength < 30 and core_desire > 70:
            # 欲望主导
            templates = [
                "好想要...已经忍不住了...",
                "管他的...反正已经这样了...",
                "为什么要停下来...继续啊...",
                "已经...已经无所谓了...",
            ]
        elif mask_strength > 70 and core_desire < 30:
            # 理智占上风
            templates = [
                "冷静点...这样不对...",
                "必须保持距离...",
                "不能让他得寸进尺...",
            ]
        else:
            # 矛盾中
            templates = [
                "我到底在想什么...",
                "这样...真的好吗？",
                "明明应该拒绝的...",
                "为什么心跳得这么快...",
            ]

        return f"[内心: {random.choice(templates)}]"

    @staticmethod
    def _generate_body_reaction(
        character: Dict,
        mask_strength: int,
        core_desire: int,
        intensity: int
    ) -> str:
        """生成身体反应描述"""

        arousal = character.get("arousal", 0)
        shame = character.get("shame", 100)

        reactions = []

        # 高欲望的身体反应
        if core_desire > 70:
            reactions.extend([
                "她的身体微微颤抖着",
                "她的呼吸变得急促",
                "她的手无意识地攥紧了衣角",
                "她的脸颊泛起不正常的潮红",
            ])

        # 高羞耻的反应
        if shame > 70:
            reactions.extend([
                "她下意识地回避了目光",
                "她咬着嘴唇，似乎在克制什么",
                "她的手在颤抖",
            ])

        # 面具崩塌的反应
        if mask_strength < 30:
            reactions.extend([
                "她的眼神已经失去了焦点",
                "她的身体诚实地贴了过来",
                "她已经放弃了抵抗",
            ])

        # 高强度互动的反应
        if intensity > 7:
            reactions.extend([
                "她的身体剧烈地颤抖起来",
                "她发出了压抑的声音",
                "她的双腿已经站不稳了",
            ])

        if reactions:
            return f"[{random.choice(reactions)}]"
        else:
            return "[她的表情有些复杂]"

    @staticmethod
    def check_mask_crack_event(character: Dict) -> Tuple[bool, Optional[str]]:
        """
        检查是否触发"面具裂痕"事件

        返回: (是否触发, 事件描述)
        """
        mask_strength = DualPersonalitySystem.calculate_mask_strength(character)
        core_desire = DualPersonalitySystem.calculate_core_desire(character)
        conflict = DualPersonalitySystem.calculate_personality_conflict(mask_strength, core_desire)

        # 面具强度<30 且 冲突>70 时触发
        if mask_strength < 30 and conflict > 70:
            events = [
                {
                    "title": "【面具崩塌】",
                    "desc": "她的伪装终于撑不住了...\n\n她的眼神从矜持变成了迷离，嘴角的抗拒变成了期待。\n那个端庄的她，正在你眼前一点点瓦解。",
                    "hint": "💡 此时她极度脆弱，你的选择将决定她的未来"
                },
                {
                    "title": "【真实暴露】",
                    "desc": "她再也藏不住了...\n\n\"我...我不想再装了...\"她的声音在颤抖，\n\"一直以来...我都在骗你...骗自己...\"",
                    "hint": "💡 这是她第一次卸下所有伪装"
                },
            ]

            event = random.choice(events)
            message = f"{event['title']}\n\n{event['desc']}\n\n{event['hint']}"
            return True, message

        # 面具强度30-50 且 冲突>80 时触发裂痕
        elif 30 <= mask_strength < 50 and conflict > 80:
            message = "⚠️ 【裂痕显现】\n\n她的表情管理出现了破绽，\n眼神中闪过一丝她极力想隐藏的渴望..."
            return True, message

        return False, None

    @staticmethod
    def check_personality_war_event(character: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        检查是否触发"人格战争"事件

        当面具强度和核心欲望都很高时(>70)，触发人格内战

        返回: (是否触发, 事件数据)
        """
        mask_strength = DualPersonalitySystem.calculate_mask_strength(character)
        core_desire = DualPersonalitySystem.calculate_core_desire(character)

        if mask_strength > 70 and core_desire > 70:
            event_data = {
                "title": "💥 【人格战争】",
                "desc": """她的内心正在经历剧烈的撕扯...

理智告诉她："这是错的，你不应该这样..."
本能却在呐喊："不要再压抑了，去追求你真正想要的！"

她站在原地，身体在颤抖，眼神在游移。
她既想逃跑，又想留下。
她既想拒绝，又想接受。

她正在和自己战斗。""",
                "choices": [
                    {
                        "text": "温柔地抱住她，告诉她\"不用害怕真实的自己\"",
                        "effect": "接纳路线",
                        "result": "降低冲突，两人格融合"
                    },
                    {
                        "text": "趁机攻破她的防线",
                        "effect": "征服路线",
                        "result": "面具崩溃，但可能留下心理创伤"
                    },
                    {
                        "text": "给她空间，让她自己做决定",
                        "effect": "尊重路线",
                        "result": "保护面具，但进展延缓"
                    }
                ],
                "mask_strength": mask_strength,
                "core_desire": core_desire
            }

            return True, event_data

        return False, None

    @staticmethod
    def apply_personality_choice_result(
        character: Dict,
        choice_index: int
    ) -> Tuple[Dict, str]:
        """
        应用人格战争选择的结果

        Args:
            character: 角色数据
            choice_index: 选择索引 (0=接纳, 1=征服, 2=尊重)

        Returns:
            (更新后的角色数据, 结果描述)
        """
        effects = {}

        if choice_index == 0:
            # 接纳路线 - 最佳选择
            effects = {
                "trust": 30,
                "affection": 20,
                "shame": -20,
                "resistance": -15,
                "corruption": 10
            }
            result = """✨ 【接纳自我】

你温柔的话语让她停止了挣扎。

她的眼泪流了下来，不是痛苦，而是解脱。
"谢谢你...让我不用再伪装了..."

她第一次真正地放下了防备，也第一次真正地接纳了自己。

💕 这是你们关系的重要转折点"""

        elif choice_index == 1:
            # 征服路线 - 高风险高回报
            effects = {
                "corruption": 30,
                "submission": 25,
                "trust": -20,
                "shame": -30,
                "resistance": -25,
                "arousal": 40,
            }
            result = """😈 【面具粉碎】

你没有给她思考的机会，直接打破了她的防线。

她的抵抗瓦解了，本能战胜了理智。
她放弃了挣扎，任由欲望吞没自己...

⚠️ 但她的眼神深处，有一丝你无法解读的情绪
⚠️ 这可能会在未来产生影响..."""

        elif choice_index == 2:
            # 尊重路线 - 稳健但慢
            effects = {
                "trust": 15,
                "affection": 10,
                "resistance": 5,  # 反而增加了一点抵抗
            }
            result = """🤝 【尊重边界】

你选择了给她空间。

她深深地看了你一眼，眼神复杂。
"谢谢你...但是..."她没有说下去。

她转身离开了，但你注意到她回头看了你一眼。

📌 她会记住这一刻的"""

        # 应用效果
        from ..attributes.attribute_system import AttributeSystem
        updated_char = AttributeSystem.apply_changes(character, effects)

        # 降低人格冲突（如果选择了接纳）
        if choice_index == 0:
            # 标记人格融合
            updated_char["personality_integrated"] = updated_char.get("personality_integrated", 0) + 1

        return updated_char, result

    @staticmethod
    def get_personality_status(character: Dict) -> Dict:
        """
        获取人格状态报告

        返回包含详细信息的字典
        """
        mask_strength = DualPersonalitySystem.calculate_mask_strength(character)
        core_desire = DualPersonalitySystem.calculate_core_desire(character)
        conflict = DualPersonalitySystem.calculate_personality_conflict(mask_strength, core_desire)

        # 判断状态等级
        if mask_strength >= 90:
            mask_status = "完美伪装"
            mask_emoji = "😇"
        elif mask_strength >= 70:
            mask_status = "相对稳固"
            mask_emoji = "😊"
        elif mask_strength >= 50:
            mask_status = "摇摇欲坠"
            mask_emoji = "😰"
        elif mask_strength >= 30:
            mask_status = "出现裂痕"
            mask_emoji = "😣"
        else:
            mask_status = "濒临崩溃"
            mask_emoji = "😵"

        if core_desire >= 90:
            core_status = "欲火焚身"
            core_emoji = "🔥"
        elif core_desire >= 70:
            core_status = "强烈渴求"
            core_emoji = "💢"
        elif core_desire >= 50:
            core_status = "蠢蠢欲动"
            core_emoji = "💗"
        elif core_desire >= 30:
            core_status = "微弱萌芽"
            core_emoji = "💭"
        else:
            core_status = "沉睡未醒"
            core_emoji = "😴"

        if conflict >= 80:
            conflict_status = "激烈对抗"
            conflict_emoji = "⚡"
            warning = "⚠️ 警告：人格分裂风险极高！"
        elif conflict >= 60:
            conflict_status = "显著冲突"
            conflict_emoji = "💥"
            warning = "⚠️ 注意：她的内心在剧烈挣扎"
        elif conflict >= 40:
            conflict_status = "轻微冲突"
            conflict_emoji = "💫"
            warning = None
        elif conflict >= 20:
            conflict_status = "基本和谐"
            conflict_emoji = "✨"
            warning = None
        else:
            conflict_status = "完全和谐"
            conflict_emoji = "💝"
            warning = None

        return {
            "mask_strength": mask_strength,
            "mask_status": mask_status,
            "mask_emoji": mask_emoji,
            "core_desire": core_desire,
            "core_status": core_status,
            "core_emoji": core_emoji,
            "conflict": conflict,
            "conflict_status": conflict_status,
            "conflict_emoji": conflict_emoji,
            "warning": warning
        }
