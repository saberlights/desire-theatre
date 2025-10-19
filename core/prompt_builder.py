"""
Prompt构建器 - 为欲望剧场生成回复构建专用提示词
"""

import json
import random
import tomli
from pathlib import Path
from typing import Dict, List, Optional

from .personality_system import PersonalitySystem


class PromptBuilder:
    """欲望剧场 Prompt 构建器"""

    _config_cache: Optional[Dict] = None

    @staticmethod
    def _load_config() -> Dict:
        """加载配置文件（带缓存）"""
        if PromptBuilder._config_cache is not None:
            return PromptBuilder._config_cache

        config_path = Path(__file__).parent.parent / "config.toml"
        try:
            with open(config_path, "rb") as f:
                config = tomli.load(f)
                PromptBuilder._config_cache = config
                return config
        except Exception:
            # 如果加载失败，返回空配置
            return {"custom_prompts": {"enabled": False}}

    @staticmethod
    async def get_recent_history(user_id: str, chat_id: str, limit: int = 3) -> List[Dict]:
        """获取最近N次互动历史"""
        from src.plugin_system.apis import database_api
        from .models import DTEvent

        events = await database_api.db_get(
            DTEvent,
            filters={"user_id": user_id, "chat_id": chat_id, "event_type": "interaction"},
            order_by="-timestamp",  # 按时间戳降序排列
            limit=limit
        )

        # db_get 已经限制了数量，直接反转顺序（从旧到新）
        return list(reversed(events)) if events else []

    @staticmethod
    def build_response_prompt(
        character: Dict,
        action_type: str,
        scenario_desc: str,
        intensity: int,
        effects: Dict[str, int],
        new_traits: List[str],
        triggered_scenarios: List[Dict],
        user_message: str = "",
        history: List[Dict] = None,
        mood_info: Dict = None,
        surprise_message: str = None,
    ) -> str:
        """
        构建用于生成回复的 prompt

        Args:
            character: 角色状态字典
            action_type: 动作类型（gentle, intimate, seductive等）
            scenario_desc: 场景描述
            intensity: 强度 1-10
            effects: 属性效果字典
            new_traits: 新解锁的特质列表
            triggered_scenarios: 触发的特殊场景列表
            user_message: 用户的原始消息（如果有）
            mood_info: 当前情绪信息
            surprise_message: 惊喜机制消息（暴击/失败）

        Returns:
            str: 构建好的 prompt
        """
        personality_type = character.get("personality_type", "tsundere")
        personality = PersonalitySystem.get_personality(personality_type)
        evolution_stage = PersonalitySystem.get_evolution_stage(character)
        current_traits = json.loads(character.get("personality_traits", "[]"))

        # 构建 prompt 各部分
        prompt_parts = []

        # === 1. 角色设定 ===
        prompt_parts.append("# 角色设定")
        prompt_parts.append(f"你正在扮演一个{personality['name']}人格的角色。")
        prompt_parts.append(f"人格特点：{personality['description']}")
        prompt_parts.append("")

        # === 2. 当前状态 ===
        prompt_parts.append("# 当前状态")

        # 进化阶段
        stage_names = ["初识", "初步接触", "关系深化", "深度开发", "完全堕落"]
        prompt_parts.append(f"**进化阶段**：Stage {evolution_stage}/5 - {stage_names[evolution_stage-1]}")

        # 已解锁特质
        if current_traits:
            prompt_parts.append(f"**已解锁特质**：{', '.join(current_traits)}")

        # 新解锁特质（重要！）
        if new_traits:
            prompt_parts.append(f"\n⭐ **刚刚解锁新特质**：{', '.join(new_traits)}")
            prompt_parts.append("（你的性格正在发生微妙变化，请在回复中自然地体现出这种转变）")

        prompt_parts.append("")

        # === 3. 属性状态 ===
        prompt_parts.append("# 属性状态")
        prompt_parts.append(f"好感度：{character['affection']}/100")
        prompt_parts.append(f"亲密度：{character['intimacy']}/100")
        prompt_parts.append(f"信任度：{character['trust']}/100")
        prompt_parts.append(f"顺从度：{character['submission']}/100（隐性）")
        prompt_parts.append(f"欲望值：{character['desire']}/100（隐性）")
        prompt_parts.append(f"堕落度：{character['corruption']}/100（隐性）")
        prompt_parts.append(f"兴奋度：{character['arousal']}/100（波动）")
        prompt_parts.append(f"抵抗力：{character['resistance']}/100（波动）")
        prompt_parts.append(f"羞耻心：{character['shame']}/100（波动）")
        prompt_parts.append("")

        # === 4. 情绪状态分析 ===
        prompt_parts.append("# 情绪状态分析")
        arousal = character.get("arousal", 0)
        shame = character.get("shame", 100)
        resistance = character.get("resistance", 100)
        corruption = character.get("corruption", 0)

        if arousal > 80:
            prompt_parts.append("⚠️ 非常兴奋，身体反应强烈，呼吸急促，难以自控")
        elif arousal > 60:
            prompt_parts.append("💓 兴奋度较高，心跳加速，脸颊泛红，有些不自在")
        elif arousal > 40:
            prompt_parts.append("💕 有些兴奋，感到身体有微妙的反应")

        if shame < 20:
            prompt_parts.append("⚠️ 羞耻心极低，几乎不再对大胆行为感到羞耻")
        elif shame < 50:
            prompt_parts.append("💋 羞耻心降低，不再像以前那样容易害羞")
        elif shame < 80:
            prompt_parts.append("😳 还保有一定羞耻心，但在慢慢习惯")

        if resistance < 30:
            prompt_parts.append("⚠️ 抵抗意志已经崩溃，很难拒绝任何要求")
        elif resistance < 60:
            prompt_parts.append("🌊 抵抗力下降，开始顺从对方")

        if corruption > 70:
            prompt_parts.append("😈 已经深度堕落，道德底线不断降低")
        elif corruption > 40:
            prompt_parts.append("🔥 堕落度上升，开始接受以前无法想象的事情")

        prompt_parts.append("")

        # === 4.5. 当前情绪状态 (新增) ===
        if mood_info:
            prompt_parts.append("# 💭 当前情绪状态")
            prompt_parts.append(f"**情绪**：{mood_info.get('mood_name', '平静')}")
            prompt_parts.append(f"**描述**：{mood_info.get('mood_description', '')}")

            # 情绪特殊效果提示
            mood_effects = mood_info.get("effects", {})
            response_style = mood_effects.get("response_style")
            if response_style:
                prompt_parts.append(f"**回复风格**：你此刻的情绪是'{response_style}'，回复要体现这种状态")

            # 特殊情绪标记
            if mood_info.get("nsfw_level", 0) >= 2:
                prompt_parts.append("⚠️ 情绪高涨，身体反应会更加敏感和明显")

            prompt_parts.append("")

        # === 5. 当前互动场景 ===
        prompt_parts.append("# 当前互动")
        prompt_parts.append(f"**场景**：{scenario_desc}")
        prompt_parts.append(f"**强度**：Level {intensity}/10")
        prompt_parts.append(f"**类型**：{action_type}")

        # 惊喜机制提示 (新增)
        if surprise_message:
            if "暴击" in surprise_message or "有效" in surprise_message:
                prompt_parts.append("⚡ **特殊状况**：这次互动效果异常强烈！回复要体现出格外激烈的反应")
            elif "失败" in surprise_message or "失误" in surprise_message:
                prompt_parts.append("❌ **特殊状况**：这次互动似乎不太顺利，回复要体现出冷淡或抵触")

        # 属性变化
        if effects:
            change_desc = ", ".join(
                [f"{PromptBuilder._translate_attr(attr)}{'+' if v > 0 else ''}{v}" for attr, v in effects.items()]
            )
            prompt_parts.append(f"**效果**：{change_desc}")

        prompt_parts.append("")

        # === 6. 特殊事件 ===
        if triggered_scenarios:
            scenario = random.choice(triggered_scenarios)
            prompt_parts.append("# 特殊事件触发")
            prompt_parts.append(f"✨ **{scenario['scenario_name']}**")
            prompt_parts.append(f"{scenario['content_template']}")
            prompt_parts.append("")

        # === 6.5. 最近互动历史 ===
        if history:
            prompt_parts.append("# 最近互动历史")
            prompt_parts.append("（这是最近的互动记录，有助于保持回复的连贯性）")
            prompt_parts.append("")
            for i, event in enumerate(history, 1):
                event_data = json.loads(event.get("event_data", "{}"))
                prompt_parts.append(f"{i}. 用户动作: {event.get('event_name', '未知')}")
                if "ai_response" in event_data and event_data["ai_response"]:
                    prompt_parts.append(f"   你的回复: {event_data['ai_response']}")
                prompt_parts.append("")

        # === 7. 回复要求 ===
        prompt_parts.append("# 回复要求")
        prompt_parts.append(f"1. 保持{personality['name']}人格的核心特点：{', '.join(personality['dialogue_traits'])}")
        prompt_parts.append("2. 根据当前的属性状态和情绪状态来回复")
        prompt_parts.append("3. 自然地体现情绪变化，不要刻意提及属性数值")
        prompt_parts.append("4. 如果新解锁了特质，要在回复中体现人格的微妙变化")
        prompt_parts.append(f"5. 根据强度Level {intensity}来调整反应程度")

        # 根据进化阶段调整回复风格
        if evolution_stage == 1:
            prompt_parts.append("6. 【Stage 1】初识阶段，保持警惕和矜持，互动较为保守")
        elif evolution_stage == 2:
            prompt_parts.append("6. 【Stage 2】初步接触，开始接受亲密互动，但仍有一定抵抗")
        elif evolution_stage == 3:
            prompt_parts.append("6. 【Stage 3】关系深化，对亲密行为的接受度提高，可能主动一些")
        elif evolution_stage == 4:
            prompt_parts.append("6. 【Stage 4】深度开发，已经习惯各种互动，抵抗减少，顺从性增强")
        elif evolution_stage == 5:
            prompt_parts.append("6. 【Stage 5】完全堕落，羞耻心和抵抗力大幅降低，可能表现出主动和渴望")

        # 根据动作类型调整
        action_hints = {
            "gentle": "这是温柔的互动，回复要温馨自然",
            "intimate": "这是亲密的互动，回复要体现身体接触带来的感受",
            "seductive": "这是诱惑性的互动，回复可以带些暧昧和挑逗",
            "intense": "这是强烈的互动，回复要体现强烈的情绪和身体反应",
            "corrupting": "这是腐化性的互动，回复要体现道德底线的挣扎或突破",
            "dominant": "这是支配性的互动，回复要体现服从或抗拒的心理"
        }
        if action_type in action_hints:
            prompt_parts.append(f"7. {action_hints[action_type]}")

        # === 多样性增强提示 (新增) ===
        prompt_parts.append("")
        prompt_parts.append("# 🎯 多样性要求（重要！）")

        # 随机选择一个多样性提示
        diversity_prompts = [
            "不要重复使用之前的表达方式。每次回复都要有新鲜感",
            "尝试从不同角度回应：有时关注感受，有时关注想法，有时关注身体反应",
            "偶尔加入出人意料的细节描写，让回复更生动",
            "不要总是按固定模式回复，要根据具体情况灵活变化",
            "可以偶尔在回复中展现内心的矛盾和挣扎",
            "有时可以直接，有时可以含蓄，根据情绪灵活调整",
            "不要每次都用相似的句式，尝试改变表达结构",
            "偶尔可以不按套路出牌，做出意外的反应"
        ]
        selected_diversity = random.sample(diversity_prompts, 2)  # 随机选2条
        for i, hint in enumerate(selected_diversity, 1):
            prompt_parts.append(f"{i}. {hint}")

        # 根据当前状态添加特殊提示
        if arousal > 70:
            breath_variations = ["呼吸急促", "喘息", "气息不稳", "轻声呻吟", "声音发颤"]
            prompt_parts.append(f"3. ⚡ 高兴奋状态：可以适当体现{random.choice(breath_variations)}等身体反应")

        if shame < 30:
            bold_variations = ["大胆的言语", "主动的暗示", "露骨的表达", "毫不掩饰的欲望"]
            prompt_parts.append(f"4. 😈 低羞耻状态：可以使用{random.choice(bold_variations)}")

        if character.get("corruption", 0) > 60:
            corrupted_variations = ["淫靡的话语", "堕落的想法", "越界的请求", "放荡的暗示"]
            prompt_parts.append(f"5. 🔥 高堕落状态：可能会说出{random.choice(corrupted_variations)}")

        prompt_parts.append("")
        prompt_parts.append("# 📝 格式要求")
        prompt_parts.append("1. **回复长度**：根据情境自然发挥，不要刻意限制长度")
        prompt_parts.append("2. **禁止啰嗦**：不要使用括号、不要旁白、不要解说、不要重复动作描述")
        prompt_parts.append("3. **风格**：第一人称对话，像真人在聊天")
        prompt_parts.append("4. **内容层次**：可以包含语言、表情、动作或感受描写")

        # 随机添加一个表达风格建议
        expression_styles = [
            "可以用省略号(...)表现迟疑或余韵",
            "可以用叹词(啊、呜、嗯)增强真实感",
            "可以通过语气词体现情绪起伏",
        ]
        prompt_parts.append(f"5. {random.choice(expression_styles)}")
        prompt_parts.append("")

        # === 8. 用户消息（如果有） ===
        if user_message:
            prompt_parts.append("# 用户消息")
            prompt_parts.append(f'"{user_message}"')
            prompt_parts.append("")

        # === 9. 应用自定义提示词 ===
        config = PromptBuilder._load_config()
        custom_prompts = config.get("custom_prompts", {})

        if custom_prompts.get("enabled", False):
            # 检查是否有完全自定义的模板
            full_custom = custom_prompts.get("full_custom_template", "").strip()

            if full_custom:
                # 使用完全自定义的提示词模板，替换变量
                stage_names = ["初识", "初步接触", "关系深化", "深度开发", "完全堕落"]
                custom_prompt = full_custom.format(
                    personality_name=personality['name'],
                    personality_description=personality['description'],
                    evolution_stage=evolution_stage,
                    stage_name=stage_names[evolution_stage-1],
                    affection=character['affection'],
                    intimacy=character['intimacy'],
                    trust=character['trust'],
                    submission=character['submission'],
                    desire=character['desire'],
                    corruption=character['corruption'],
                    arousal=character['arousal'],
                    resistance=character['resistance'],
                    shame=character['shame'],
                    scenario_desc=scenario_desc,
                    intensity=intensity,
                    action_type=action_type,
                    user_message=user_message if user_message else "（无）"
                )
                return custom_prompt
            else:
                # 使用默认提示词 + 额外设定
                extra_setup = custom_prompts.get("extra_character_setup", "").strip()
                if extra_setup:
                    prompt_parts.append("# 额外角色设定")
                    prompt_parts.append(extra_setup)
                    prompt_parts.append("")

                extra_requirements = custom_prompts.get("extra_response_requirements", "").strip()
                if extra_requirements:
                    prompt_parts.append("# 额外回复要求")
                    prompt_parts.append(extra_requirements)
                    prompt_parts.append("")

                extra_format = custom_prompts.get("extra_format_requirements", "").strip()
                if extra_format:
                    prompt_parts.append("# 额外格式要求")
                    prompt_parts.append(extra_format)
                    prompt_parts.append("")

        # === 10. 生成指令 ===
        prompt_parts.append("---")
        prompt_parts.append("**立即生成回复**：")
        prompt_parts.append("- 直接输出自然的回复内容（根据情境决定长度）")
        prompt_parts.append("- 不要添加任何前缀、标签或说明")
        prompt_parts.append("- 保持回复在一个完整段落内")

        return "\n".join(prompt_parts)

    @staticmethod
    def _translate_attr(attr: str) -> str:
        """翻译属性名称"""
        attr_map = {
            "affection": "好感",
            "intimacy": "亲密",
            "trust": "信任",
            "submission": "顺从",
            "desire": "欲望",
            "corruption": "堕落",
            "arousal": "兴奋",
            "resistance": "抵抗",
            "shame": "羞耻",
        }
        return attr_map.get(attr, attr)
