"""
动作处理器 - 核心互动逻辑
"""

import json
import time
import random
import os
from typing import Dict, Tuple, Optional, List

from src.plugin_system.apis import database_api, llm_api, send_api
from src.common.logger import get_logger

from .models import DTCharacter, DTEvent
from .attribute_system import AttributeSystem
from .personality_system import PersonalitySystem
from .prompt_builder import PromptBuilder
from .action_growth_system import ActionGrowthSystem

logger = get_logger("dt_action_handler")


class ActionHandler:
    """动作处理器"""

    @staticmethod
    async def execute_action(
        action_name: str,
        action_params: str,
        user_id: str,
        chat_id: str,
        message_obj  # 消息对象，用于send_text和generate_reply
    ) -> Tuple[bool, str, bool]:
        """
        执行动作
        返回: (是否成功, 结果消息, 是否拦截后续消息)
        """
        # 1. 获取角色（需要先获取角色才能判断阶段）
        character = await ActionHandler._get_or_create_character(user_id, chat_id)

        # 2. 检查动作是否存在并获取当前阶段的配置
        can_use, stage_config, stage = ActionGrowthSystem.get_action_by_stage(action_name, character)

        if not stage_config:
            return False, f"未知动作: {action_name}", False

        # 2.1 检查该阶段是否被阻止
        if not can_use:
            block_reason = stage_config.get("reason", "当前关系阶段无法使用此动作")
            await send_api.text_to_stream(
                text=f"❌ {block_reason}",
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )
            return False, block_reason, False

        # 2.2 构建兼容旧系统的 action_config（用于后续逻辑）
        action_def = ActionGrowthSystem.CORE_ACTIONS[action_name]
        action_config = {
            "type": action_def.get("type", "gentle"),
            "effects": stage_config.get("effects", {}),
            "base_intensity": stage_config.get("intensity", 5),
            "requirements": stage_config.get("requirements", {}),
        }

        # 如果动作有部位选择（has_targets），添加 target_effects
        if action_def.get("has_targets", False):
            action_config["target_effects"] = stage_config.get("targets", {})

        # 2.5. 【新增】检查每日互动次数限制
        from .daily_limit_system import DailyInteractionSystem

        can_interact, reason, remaining, limit = DailyInteractionSystem.check_can_interact(character)

        if not can_interact:
            # 达到每日限制，返回拒绝消息
            await send_api.text_to_stream(
                text=reason,
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )
            # 保存可能的自动推进更新
            await database_api.db_save(
                DTCharacter,
                data=character,
                key_field="user_id",
                key_value=user_id
            )
            return False, "今日互动已用完", False

        # 2.6. 【新增】检查行动点
        from .action_point_system import ActionPointSystem

        action_cost = ActionPointSystem.get_action_cost(action_config.get("type", "gentle"), action_name)
        can_afford, cost_reason = ActionPointSystem.can_afford_action(character, action_cost)

        if not can_afford:
            await send_api.text_to_stream(
                text=cost_reason,
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )
            return False, "行动点不足", False

        # 3. 应用衰减
        character = await ActionHandler._apply_decay(character)

        # 3.5. 【新增】检查并触发待发生的延迟后果
        from .delayed_consequence_system import DelayedConsequenceSystem

        pending_consequences = await DelayedConsequenceSystem.check_pending_consequences(user_id, chat_id)

        if pending_consequences:
            for consequence in pending_consequences:
                # 触发延迟后果
                updated_character, consequence_message = await DelayedConsequenceSystem.trigger_consequence(
                    user_id, chat_id, consequence, character
                )
                character = updated_character

                # 显示后果消息
                await send_api.text_to_stream(
                    text=consequence_message,
                    stream_id=message_obj.chat_stream.stream_id,
                    storage_message=True
                )

                logger.info(f"触发延迟后果: {user_id} - {consequence['type']}")

            # 保存更新后的角色状态
            await database_api.db_save(
                DTCharacter,
                data=character,
                key_field="user_id",
                key_value=user_id
            )

        # 4. 检查前置条件
        can_execute, reason = ActionHandler._check_requirements(
            character, action_config.get("requirements", {})
        )
        if not can_execute:
            await send_api.text_to_stream(
                text=f"❌ {reason}",
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )
            return False, reason, False

        # 4.3. 【新增】检查情绪锁定条件
        if "mood_required" in action_config:
            from .dynamic_mood_system import DynamicMoodSystem
            current_mood = DynamicMoodSystem.calculate_current_mood(character)
            required_mood = action_config["mood_required"]

            if current_mood.get("mood_name") != required_mood:
                mood_hint = action_config.get("mood_locked_hint", f"此动作需要特定情绪: {required_mood}")
                await send_api.text_to_stream(
                    text=f"🔒 【情绪限定动作】\n{mood_hint}\n\n当前情绪: {current_mood.get('mood_name', '平静')}",
                    stream_id=message_obj.chat_stream.stream_id,
                    storage_message=True
                )
                return False, f"需要情绪: {required_mood}", False

        # 4.5. 检查冷却时间
        cooldown_seconds = action_config.get("cooldown", 0)
        if cooldown_seconds > 0:
            from .cooldown_manager import CooldownManager

            can_use, remaining = CooldownManager.check_cooldown(
                user_id, chat_id, action_name, cooldown_seconds
            )

            if not can_use:
                remaining_str = CooldownManager.format_time(remaining)
                await send_api.text_to_stream(
                    text=f"❌ 【{action_name}】冷却中\n\n⏰ 还需等待: {remaining_str}\n💡 该动作有冷却时间限制，请稍后再试",
                    stream_id=message_obj.chat_stream.stream_id,
                    storage_message=True
                )
                return False, f"冷却中，剩余{remaining_str}", False

        # 4.6. 检查是否需要二次确认
        if action_config.get("requires_confirmation", False):
            from .confirmation_manager import ConfirmationManager

            # 检查是否是确认动作（通过参数中的"确认"关键字）
            if "确认" in action_params:
                # 验证确认状态
                is_confirmed, confirmation_data = ConfirmationManager.check_confirmation(
                    user_id, chat_id, f"action_{action_name}"
                )

                if not is_confirmed:
                    await send_api.text_to_stream(
                        text=f"❌ 没有待确认的【{action_name}】操作，或确认已超时\n\n重新输入 /{action_name} 开始执行",
                        stream_id=message_obj.chat_stream.stream_id,
                        storage_message=True
                    )
                    return False, "无待确认操作", False

                # 从确认数据中恢复原始参数
                action_params = confirmation_data.get("original_params", "")
            else:
                # 首次请求，创建确认状态
                ConfirmationManager.create_confirmation(
                    user_id, chat_id, f"action_{action_name}",
                    action_data={"original_params": action_params}
                )

                # 计算预览效果
                preview_effects, preview_intensity = ActionHandler._calculate_effects(
                    action_config, action_params, character
                )

                # 构建确认消息
                effect_preview = []
                attr_names = {
                    "affection": "好感", "intimacy": "亲密", "trust": "信任",
                    "submission": "顺从", "desire": "欲望", "corruption": "堕落",
                    "arousal": "兴奋", "resistance": "抵抗", "shame": "羞耻"
                }

                for attr, change in preview_effects.items():
                    if change != 0:
                        name = attr_names.get(attr, attr)
                        sign = "+" if change > 0 else ""
                        effect_preview.append(f"  {name}{sign}{change}")

                confirm_msg = f"""
⚠️ 【高强度动作确认】

动作: {action_name} {action_params if action_params else ""}
强度: {"🔥" * min(preview_intensity, 10)} ({preview_intensity}/10)

预计效果:
{chr(10).join(effect_preview) if effect_preview else "  (无直接属性变化)"}

⚠️ 此动作为高强度互动，请确认是否继续

  • 输入 /{action_name} {action_params} 确认 继续
  • 60秒内不确认将自动取消
""".strip()

                await send_api.text_to_stream(
                    text=confirm_msg,
                    stream_id=message_obj.chat_stream.stream_id,
                    storage_message=True
                )

                return True, "等待确认", False

        # 5. 检查并提示参数
        needs_params = ("target_effects" in action_config or "modifiers" in action_config)
        if needs_params and not action_params.strip():
            # 动作需要参数但用户没提供，显示帮助
            help_msg_parts = [f"💡 【{action_name} - 使用提示】\n"]

            # 显示target_effects（部位选项）
            if "target_effects" in action_config:
                targets = list(action_config["target_effects"].keys())
                help_msg_parts.append("可选部位:")
                for target in targets:
                    target_info = action_config["target_effects"][target]
                    # 检查是否有条件限制
                    conditions = []
                    if "min_intimacy" in target_info:
                        conditions.append(f"需要亲密≥{target_info['min_intimacy']}")
                    if "min_corruption" in target_info:
                        conditions.append(f"需要堕落≥{target_info['min_corruption']}")

                    condition_str = f" ({', '.join(conditions)})" if conditions else ""
                    help_msg_parts.append(f"  • {target}{condition_str}")

                help_msg_parts.append(f"\n使用方法: /{action_name} <部位>")
                help_msg_parts.append(f"示例: /{action_name} {targets[0]}")

            # 显示modifiers（修饰词选项）
            if "modifiers" in action_config:
                modifiers = list(action_config["modifiers"].keys())
                help_msg_parts.append("\n可选修饰词:")
                for modifier in modifiers:
                    help_msg_parts.append(f"  • {modifier}")

                help_msg_parts.append(f"\n使用方法: /{action_name} <修饰词>")
                help_msg_parts.append(f"示例: /{action_name} {modifiers[0]}")

            # 如果两者都有
            if "target_effects" in action_config and "modifiers" in action_config:
                help_msg_parts.append(f"\n也可以组合: /{action_name} <修饰词> <部位>")

            await send_api.text_to_stream(
                text="\n".join(help_msg_parts),
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

            return True, "显示参数帮助", False

        # === 5.5. 【新增】记忆系统 - 检查承诺一致性 ===
        from .memory_engine import MemoryEngine

        is_contradiction, broken_promise, memory_penalty = await MemoryEngine.check_promise_consistency(
            user_id, chat_id, action_name, action_config.get("type", "gentle")
        )

        if is_contradiction and memory_penalty:
            # 显示矛盾警告
            await send_api.text_to_stream(
                text=f"💔 【她想起了你的承诺】\n\n\"{broken_promise}\"\n\n...但你现在的行为...",
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )
            # 应用惩罚
            character = AttributeSystem.apply_changes(character, memory_penalty)
            logger.warning(f"检测到承诺违背: {user_id} - {broken_promise}")

        # === 5.6. 【新增】记忆系统 - 检查习惯期待 ===
        expectation_broken, expectation_msg = await MemoryEngine.check_habit_expectation(
            user_id, chat_id, action_name
        )

        if expectation_broken and expectation_msg:
            await send_api.text_to_stream(
                text=f"💭 【她有些失落】\n\n{expectation_msg}",
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

        # 6. 计算效果和强度
        base_effects, base_intensity = ActionHandler._calculate_effects(
            action_config, action_params, character
        )

        # === 6.2. 【新增】应用调教进度修正 ===
        from .training_progress_system import TrainingProgressSystem

        # 检查是否是可训练动作
        if action_name in TrainingProgressSystem.TRAINABLE_ACTIONS:
            # 应用训练进度的效果修正
            training_modified_effects = TrainingProgressSystem.apply_training_modifier(
                character, action_name, base_effects
            )

            # 更新训练进度
            new_progress, progress_msg = TrainingProgressSystem.update_training_progress(
                character, action_name
            )

            # 如果有进度消息（例如突破、解锁变种），显示
            if progress_msg:
                await send_api.text_to_stream(
                    text=progress_msg,
                    stream_id=message_obj.chat_stream.stream_id,
                    storage_message=True
                )

            logger.info(f"调教进度更新: {action_name} -> {new_progress}%")
        else:
            # 非训练动作，不修正
            training_modified_effects = base_effects

        # === 6.3. 【新增】风险动作系统 - 处理高风险动作的成功/失败判定 ===
        risk_result_message = None
        if action_config.get("type") == "risky" and "risk_probability" in action_config:
            is_success, risk_message, risk_effects = ActionHandler._calculate_risk_action(
                action_config, character, action_name
            )

            # 使用风险结果覆盖训练修正后的效果
            training_modified_effects = risk_effects
            risk_result_message = risk_message

            logger.info(f"风险动作判定: {action_name} - {'成功' if is_success else '失败'}")

        # === 6.4. 【新增】应用场景效果倍率 ===
        from .enhanced_scene_system import EnhancedSceneSystem

        current_scene_id = character.get("current_scene", "bedroom")
        scene_modified_effects, scene_hint = EnhancedSceneSystem.apply_scene_effects(
            training_modified_effects, current_scene_id
        )

        # 显示场景提示（如果有）
        if scene_hint:
            await send_api.text_to_stream(
                text=scene_hint,
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

        logger.info(f"场景效果应用: {current_scene_id}")

        # === 6.5. 【改造】使用心情槽系统（替换复杂的18种情绪） ===
        from .mood_gauge_system import MoodGaugeSystem

        mood_value = character.get("mood_gauge", 50)
        mood_level_name, mood_level_data = MoodGaugeSystem.get_current_mood_level(mood_value)

        logger.info(f"当前心情: {mood_level_name} ({mood_value}/100)")

        # === 6.6. 【简化】应用心情效果到互动（移除复杂的惊喜系统） ===
        # 心情槽会影响正向效果的倍率
        modified_effects, mood_hint, has_special_dialogue = MoodGaugeSystem.apply_mood_to_effects(
            scene_modified_effects, mood_value
        )

        intensity = base_intensity

        # === 6.7. 【v2.0新增】应用季节和节日加成 ===
        from .seasonal_system import SeasonalSystem

        game_day = character.get("game_day", 1)

        # 应用季节加成
        season_modified_effects = SeasonalSystem.apply_seasonal_bonus(
            character, modified_effects, game_day
        )

        # 应用节日加成
        final_modified_effects, is_festival, festival_name = SeasonalSystem.apply_festival_bonus(
            character, season_modified_effects, game_day
        )

        # 如果是节日,显示节日提示
        if is_festival:
            await send_api.text_to_stream(
                text=f"🎉 【{festival_name}】节日加成生效！互动效果+20%",
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

        logger.info(f"季节/节日加成后: {final_modified_effects}, 心情等级: {mood_level_name}")

        # === 6.8. 【新增】应用属性冲突机制 ===
        from .attribute_conflict_system import AttributeConflictSystem

        conflict_modified_effects, conflict_messages = AttributeConflictSystem.apply_conflict_modifiers(
            character, final_modified_effects
        )

        # 检查属性冲突警告
        conflict_warnings = AttributeConflictSystem.check_conflict_warnings(character)

        logger.info(f"属性冲突修正后: {conflict_modified_effects}")

        # 7. 应用效果
        updated_char = AttributeSystem.apply_changes(character, conflict_modified_effects)

        # 7. 检查特质解锁
        new_traits = PersonalitySystem.check_trait_unlocks(updated_char)
        if new_traits:
            current_traits = json.loads(updated_char.get("personality_traits", "[]"))
            current_traits.extend(new_traits)
            updated_char["personality_traits"] = json.dumps(current_traits, ensure_ascii=False)

        # 9. 检查特殊事件触发
        from .scenario_engine import ScenarioEngine
        triggered_scenarios = ScenarioEngine.check_scenario_triggers(updated_char)

        # 9. 构建场景描述
        scenario_desc = ActionHandler._build_scenario(action_name, action_params, action_config)

        # 9.5. 获取历史记忆
        history = await PromptBuilder.get_recent_history(user_id, chat_id, 3)

        # 10. 构建 Prompt（使用插件自己的 PromptBuilder）
        # 构建简化的心情信息（替代复杂的情绪系统）
        simple_mood_info = {
            "mood_name": mood_level_name,
            "mood_value": mood_value,
            "mood_description": mood_level_data.get("description", "")
        }

        prompt = PromptBuilder.build_response_prompt(
            character=updated_char,
            action_type=action_config.get("type", "gentle"),
            scenario_desc=scenario_desc,
            intensity=intensity,
            effects=conflict_modified_effects,  # 使用冲突修正后的效果
            new_traits=new_traits,
            triggered_scenarios=triggered_scenarios,
            user_message=f"对你执行了: {scenario_desc}",
            history=history,
            mood_info=simple_mood_info,  # 【改造】传入简化的心情信息
            surprise_message=None  # 【移除】移除复杂的惊喜系统
        )

        # 11. 使用 llm_api 直接调用回复模型生成回复
        models = llm_api.get_available_models()
        replyer_model = models.get("replyer")

        if not replyer_model:
            logger.error("未找到 'replyer' 模型配置")
            await send_api.text_to_stream(
                text="❌ 系统错误：未找到回复模型配置",
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )
            return False, "未找到回复模型", False

        success_llm, ai_response, reasoning, model_name = await llm_api.generate_with_model(
            prompt=prompt,
            model_config=replyer_model,
            request_type="desire_theatre.response"
        )

        if success_llm and ai_response:
            # === 【优化】合并所有输出为一条消息 ===
            from .dual_personality_system import DualPersonalitySystem
            from .post_action_events import PostActionEventSystem

            # 收集所有输出部分
            output_parts = []

            # 1. AI生成的主要回复
            output_parts.append(ai_response)

            # 2. 内心独白和身体反应
            _, inner_voice, body_reaction = DualPersonalitySystem.generate_dual_response(
                updated_char, action_config.get("type", "gentle"), ai_response, intensity
            )
            if inner_voice:
                output_parts.append(f"\n{inner_voice}")
            if body_reaction:
                output_parts.append(f"\n{body_reaction}")

            # 3. 属性变化反馈（简洁版）
            feedback_parts = []
            attr_names = {
                "affection": "好感", "intimacy": "亲密", "trust": "信任",
                "submission": "顺从", "desire": "欲望", "corruption": "堕落",
                "arousal": "兴奋", "resistance": "抵抗", "shame": "羞耻"
            }
            emoji_map = {
                "affection": "❤️", "intimacy": "💗", "trust": "🤝",
                "submission": "🙇", "desire": "🔥", "corruption": "😈",
                "arousal": "💓", "resistance": "🛡️", "shame": "😳"
            }
            for attr, change in conflict_modified_effects.items():
                if change != 0:
                    emoji = emoji_map.get(attr, "📊")
                    name = attr_names.get(attr, attr)
                    sign = "+" if change > 0 else ""
                    feedback_parts.append(f"{emoji}{name}{sign}{change}")
            if feedback_parts:
                output_parts.append(f"\n〔{' '.join(feedback_parts)}〕")

            # 发送合并后的主消息
            await send_api.text_to_stream(
                text="\n".join(output_parts),
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

            # === 检查并触发动作后事件 ===
            simple_mood_for_events = {
                "mood_name": mood_level_name,
                "mood_value": mood_value
            }
            post_events = PostActionEventSystem.check_post_action_events(
                updated_char, action_name, simple_mood_for_events
            )
            for event in post_events:
                updated_char = PostActionEventSystem.apply_event_effects(updated_char, event)

            # === 更新心情槽 ===
            is_first_today = (updated_char.get("daily_interactions_used", 0) == 0)
            mood_change = MoodGaugeSystem.calculate_mood_change(
                action_success=True,
                is_combo=False,
                is_first_today=is_first_today,
                interactions_used_up=(remaining <= 1)
            )
            new_mood, mood_change_msg = MoodGaugeSystem.update_mood(
                updated_char, mood_change, "互动成功"
            )
        else:
            logger.error(f"LLM生成回复失败: {ai_response}")
            await send_api.text_to_stream(
                text="❌ 生成回复失败，请稍后重试",
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

        # 11.5. 【新增】消耗每日互动次数
        from .daily_limit_system import DailyInteractionSystem
        DailyInteractionSystem.consume_interaction(updated_char)

        # 11.6. 【新增】消耗行动点
        from .action_point_system import ActionPointSystem
        ActionPointSystem.consume_action_points(updated_char, action_cost)

        # 12. 保存角色状态
        is_daily_first = await ActionHandler._save_character(user_id, chat_id, updated_char)

        # 12.01. 【新增】给予金币奖励（静默）
        from ..extensions.earning_system import EarningSystem
        coin_reward = EarningSystem.calculate_action_reward(action_config)
        updated_char["coins"] = updated_char.get("coins", 100) + coin_reward

        await database_api.db_save(
            DTCharacter,
            data=updated_char,
            key_field="user_id",
            key_value=user_id
        )

        # 12.1. 设置冷却时间
        cooldown_seconds = action_config.get("cooldown", 0)
        if cooldown_seconds > 0:
            from .cooldown_manager import CooldownManager
            CooldownManager.set_cooldown(user_id, chat_id, action_name)

        # 12.5. 检查进化阶段升级
        from .evolution_system import EvolutionSystem
        can_evolve, new_stage, stage_info = EvolutionSystem.check_evolution(updated_char)

        if can_evolve and new_stage:
            # 升级阶段
            updated_char["evolution_stage"] = new_stage

            # 应用进化奖励
            updated_char = EvolutionSystem.apply_evolution_rewards(updated_char, stage_info)

            # 解锁奖励（服装、道具等）
            await EvolutionSystem.unlock_evolution_rewards(user_id, chat_id, stage_info.get("rewards", {}))

            # 保存更新后的角色
            await ActionHandler._save_character(user_id, chat_id, updated_char)

            # 发送进化提示
            evolution_msg = f"""
🎉 【进化！】

恭喜！你们的关系进化到了新的阶段！

✨ {stage_info['name']} ✨

{stage_info['description']}

🔓 解锁内容:
{chr(10).join(f"  • {unlock}" for unlock in stage_info['unlocks'])}
""".strip()

            await send_api.text_to_stream(
                text=evolution_msg,
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

            logger.info(f"角色进化: {user_id} -> 阶段{new_stage}")

        # 13. 记录事件（用于统计和历史记忆）
        await ActionHandler._record_event(user_id, chat_id, action_name, conflict_modified_effects, ai_response if success_llm else "")

        # 13.5. 【新增】记忆系统 - 追踪习惯
        from .memory_engine import MemoryEngine
        await MemoryEngine.track_habit(user_id, chat_id, action_name)

        # 13.6. 【新增】延迟后果系统 - 安排新的延迟后果
        from .delayed_consequence_system import DelayedConsequenceSystem

        # 判断是否应该安排延迟后果
        consequence_type = DelayedConsequenceSystem.should_schedule_consequence(
            action_name, action_config.get("type", "gentle"), updated_char
        )

        if consequence_type:
            await DelayedConsequenceSystem.schedule_delayed_consequence(
                user_id, chat_id, consequence_type, action_name
            )
            logger.info(f"安排延迟后果: {user_id} - {consequence_type} ({action_name})")

        # 14. 后续检查（解锁、成就等）
        await ActionHandler._post_action_checks(message_obj, user_id, chat_id, updated_char)

        return True, f"执行动作: {action_name}", True

    @staticmethod
    def _check_requirements(character: Dict, requirements: Dict) -> Tuple[bool, str]:
        """检查前置条件"""
        for attr, required in requirements.items():
            char_value = character.get(attr, 0)

            if isinstance(required, str) and required.startswith("<"):
                threshold = int(required[1:])
                if char_value >= threshold:
                    return False, ActionHandler._build_error_message(attr, char_value, threshold, is_less_than=True)
            else:
                threshold = int(required)
                if char_value < threshold:
                    return False, ActionHandler._build_error_message(attr, char_value, threshold, is_less_than=False)

        return True, ""

    @staticmethod
    def _build_error_message(attr: str, current: int, required: int, is_less_than: bool) -> str:
        """构建详细的错误提示消息，包含建议"""
        attr_names = {
            "affection": "好感度",
            "intimacy": "亲密度",
            "trust": "信任度",
            "submission": "顺从度",
            "desire": "欲望值",
            "corruption": "堕落度",
            "arousal": "兴奋度",
            "resistance": "抵抗力",
            "shame": "羞耻心"
        }

        attr_name = attr_names.get(attr, attr)

        # 构建基础错误信息
        if is_less_than:
            error_msg = f"{attr_name}太高了（需要<{required}，当前{current}）"
        else:
            error_msg = f"{attr_name}不足（需要≥{required}，当前{current}）"

        # 根据不同属性提供针对性建议
        suggestions = []

        if not is_less_than:  # 需要提升属性
            if attr == "affection":
                suggestions = [
                    "/早安 /晚安 - 每日问候（好感+5）",
                    "/牵手 - 温柔互动（好感+4）",
                    "/摸头 - 温柔抚摸（好感+4）"
                ]
            elif attr == "intimacy":
                suggestions = [
                    "/抱 - 拥抱互动（亲密+4）",
                    "/亲 额头 - 亲吻额头（亲密+3）",
                    "/牵手 - 牵手（亲密+3）"
                ]
            elif attr == "trust":
                suggestions = [
                    "/牵手 - 建立信任（信任+3）",
                    "/摸头 - 温柔互动（信任+3）",
                    "/聊天 - 日常交流（信任+2）"
                ]
            elif attr == "corruption":
                suggestions = [
                    "/诱惑 - 诱惑互动（堕落+5）",
                    "/挑逗 - 挑逗她（堕落+6）",
                    "/舔 - 进一步互动（堕落+8）"
                ]
            elif attr == "submission":
                suggestions = [
                    "/命令 - 发出命令（顺从+8）",
                    "/调教 - 调教互动（顺从+10）"
                ]
        else:  # 需要降低属性
            if attr == "shame":
                suggestions = [
                    "/诱惑 - 降低羞耻心（羞耻-5）",
                    "/挑逗 - 大胆互动（羞耻-6）",
                    "/舔 - 进一步互动（羞耻-8）"
                ]
            elif attr == "resistance":
                suggestions = [
                    "/抚摸 - 温柔抚摸（抵抗-4）",
                    "/诱惑 - 诱惑互动（抵抗-6）"
                ]

        # 添加建议到错误消息
        if suggestions:
            error_msg += "\n\n💡 建议尝试:\n" + "\n".join(f"  {s}" for s in suggestions)
            error_msg += f"\n\n当前差距: {abs(current - required)}"

        return error_msg

    @staticmethod
    def _calculate_effects(
        action_config: Dict,
        params: str,
        character: Dict
    ) -> Tuple[Dict[str, int], int]:
        """
        计算动作效果和强度
        返回: (效果字典, 强度)
        """
        effects = {}
        intensity = action_config.get("base_intensity", 5)

        # 1. 基础效果
        if "effects" in action_config:
            effects.update(action_config["effects"])

        # 2. 目标部位效果（如 /亲 嘴唇）
        if "target_effects" in action_config and params:
            target = params.split()[0]
            if target in action_config["target_effects"]:
                target_effect = action_config["target_effects"][target]

                # 检查该部位的额外条件
                if "min_intimacy" in target_effect:
                    if character.get("intimacy", 0) < target_effect["min_intimacy"]:
                        # 条件不足，不使用该部位效果
                        pass
                    else:
                        effects.update({k: v for k, v in target_effect.items() if k not in ["min_intimacy", "min_corruption"]})
                elif "min_corruption" in target_effect:
                    if character.get("corruption", 0) < target_effect["min_corruption"]:
                        pass
                    else:
                        effects.update({k: v for k, v in target_effect.items() if k not in ["min_intimacy", "min_corruption"]})
                else:
                    effects.update(target_effect)

        # 3. 修饰词加成（如 /抱 紧紧）
        if "modifiers" in action_config:
            for modifier, modifier_effects in action_config["modifiers"].items():
                if modifier in params:
                    # 应用修饰词效果
                    for key, value in modifier_effects.items():
                        if key == "intensity":
                            intensity += value
                        elif key in effects:
                            effects[key] += value
                        else:
                            effects[key] = value

        return effects, max(1, min(10, intensity))

    @staticmethod
    def _calculate_risk_action(
        action_config: Dict,
        character: Dict,
        action_name: str
    ) -> Tuple[bool, str, Dict[str, int]]:
        """
        计算风险动作的成功/失败
        返回: (是否成功, 结果消息, 最终效果)
        """
        base_risk = action_config.get("risk_probability", 0.5)
        risk_modifiers = action_config.get("risk_modifiers", {})

        # 计算实际风险概率
        actual_risk = base_risk

        # 应用风险调整因子
        for condition, modifier in risk_modifiers.items():
            if ">" in condition:
                # 例如 "affection>70"
                attr, threshold = condition.split(">")
                if character.get(attr, 0) > int(threshold):
                    actual_risk += modifier  # modifier通常是负数，降低风险
            elif "=" in condition:
                # 例如 "mood=发情期" (需要从当前情绪判断)
                attr, value = condition.split("=")
                if attr == "mood":
                    from .dynamic_mood_system import DynamicMoodSystem
                    current_mood = DynamicMoodSystem.calculate_current_mood(character)
                    if current_mood.get("mood_name") == value:
                        actual_risk += modifier
            elif "<" in condition:
                # 例如 "resistance<40"
                attr, threshold = condition.split("<")
                if character.get(attr, 100) < int(threshold):
                    actual_risk += modifier

        # 限制风险概率在 0.05 - 0.95 之间
        actual_risk = max(0.05, min(0.95, actual_risk))

        # 随机判定
        is_success = random.random() >= actual_risk

        # 构建结果消息
        if is_success:
            success_effects = action_config.get("success_effects", {})
            risk_percent = int((1 - actual_risk) * 100)

            success_messages = [
                f"🎯【冒险成功】（成功率{risk_percent}%）她没有抗拒你的大胆举动！",
                f"✨【赌对了】（成功率{risk_percent}%）她意外地接受了...！",
                f"💫【幸运】（成功率{risk_percent}%）时机刚刚好！"
            ]
            message = random.choice(success_messages)
            return True, message, success_effects
        else:
            failure_effects = action_config.get("failure_effects", {})
            fail_percent = int(actual_risk * 100)

            failure_messages = [
                f"❌【冒险失败】（失败率{fail_percent}%）她生气地推开了你...",
                f"💔【弄巧成拙】（失败率{fail_percent}%）这让她很不高兴！",
                f"😤【惹怒了她】（失败率{fail_percent}%）她的好感度下降了..."
            ]
            message = random.choice(failure_messages)

            # 检查是否有特殊失败标记
            if failure_effects.get("relationship_damage"):
                message += "\n⚠️ 关系受损严重！"
            if failure_effects.get("bad_end_warning"):
                message += "\n🚨 危险！继续这样可能导致坏结局！"

            return False, message, failure_effects

    @staticmethod
    def _build_scenario(action_name: str, params: str, action_config: Dict) -> str:
        """构建场景描述"""
        if params:
            return f"{action_name} {params}"
        return action_name

    @staticmethod
    async def _send_attribute_feedback(message_obj, effects: Dict[str, int]):
        """发送属性变化反馈（中文显示）"""
        feedback_parts = []

        # 属性中文映射
        attr_names = {
            "affection": "好感", "intimacy": "亲密", "trust": "信任",
            "submission": "顺从", "desire": "欲望", "corruption": "堕落",
            "arousal": "兴奋", "resistance": "抵抗", "shame": "羞耻"
        }

        emoji_map = {
            "affection": "❤️", "intimacy": "💗", "trust": "🤝",
            "submission": "🙇", "desire": "🔥", "corruption": "😈",
            "arousal": "💓", "resistance": "🛡️", "shame": "😳"
        }

        for attr, change in effects.items():
            if change != 0:
                emoji = emoji_map.get(attr, "📊")
                name = attr_names.get(attr, attr)
                sign = "+" if change > 0 else ""
                feedback_parts.append(f"{emoji}{name}{sign}{change}")

        if feedback_parts:
            await send_api.text_to_stream(
                text=f"〔{' '.join(feedback_parts)}〕",
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

    @staticmethod
    async def _get_or_create_character(user_id: str, chat_id: str) -> Dict:
        """获取或创建角色"""
        char = await database_api.db_get(
            DTCharacter,
            filters={"user_id": user_id, "chat_id": chat_id},
            single_result=True
        )

        if not char:
            # 创建新角色（默认傲娇人格）
            personality = PersonalitySystem.get_personality("tsundere")

            char = {
                "user_id": user_id,
                "chat_id": chat_id,
                "affection": 0,
                "intimacy": 0,
                "trust": 50,
                "submission": 50,
                "desire": 0,
                "corruption": 0,
                "arousal": 0,
                "resistance": personality["base_resistance"],
                "shame": personality["base_shame"],
                "personality_type": "tsundere",
                "personality_traits": "[]",
                "evolution_stage": 1,
                "interaction_count": 0,
                "total_arousal_gained": 0,
                "challenges_completed": 0,
                "created_at": time.time(),
                "last_interaction": time.time(),
                "last_desire_decay": time.time(),
                # 虚拟时间系统
                "game_day": 1,
                "daily_interactions_used": 0,
                "last_daily_reset": time.time(),
                "last_interaction_time": time.time(),
                # 心情槽系统
                "mood_gauge": 50,  # 初始心情值
            }

            await database_api.db_save(
                DTCharacter,
                data=char,
                key_field="user_id",
                key_value=user_id
            )

            logger.info(f"创建新角色: {user_id}")

        return char

    @staticmethod
    async def _apply_decay(character: Dict) -> Dict:
        """应用属性衰减"""
        last_decay = character.get("last_desire_decay", time.time())
        hours_passed = (time.time() - last_decay) / 3600

        if hours_passed >= 1:
            decay_changes = AttributeSystem.calculate_decay(character, hours_passed)
            character = AttributeSystem.apply_changes(character, decay_changes)
            character["last_desire_decay"] = time.time()

        return character

    @staticmethod
    async def _save_character(user_id: str, chat_id: str, character: Dict):
        """保存角色状态"""
        import datetime

        # 检查是否是今日首次互动
        last_interaction = character.get("last_interaction", 0)
        now = time.time()

        # 获取上次互动的日期和当前日期
        last_date = datetime.datetime.fromtimestamp(last_interaction).date()
        current_date = datetime.datetime.fromtimestamp(now).date()

        # 如果是新的一天，给予每日奖励
        is_daily_first = last_date < current_date
        if is_daily_first:
            character["affection"] = AttributeSystem.clamp(character.get("affection", 0) + 10)
            character["trust"] = AttributeSystem.clamp(character.get("trust", 0) + 5)
            logger.info(f"每日首次互动奖励: {user_id} - 好感+10, 信任+5")

        character["last_interaction"] = now
        character["interaction_count"] = character.get("interaction_count", 0) + 1

        await database_api.db_save(
            DTCharacter,
            data=character,
            key_field="user_id",
            key_value=user_id
        )

        return is_daily_first

    @staticmethod
    async def _record_event(user_id: str, chat_id: str, action_name: str, effects: Dict, ai_response: str = ""):
        """记录事件（用于历史记忆和统计）"""
        event_id = f"evt_{int(time.time() * 1000000)}_{random.randint(1000, 9999)}"

        await database_api.db_save(
            DTEvent,
            data={
                "event_id": event_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "event_type": "interaction",
                "event_name": action_name,
                "timestamp": time.time(),
                "event_data": json.dumps({
                    "action": action_name,
                    "ai_response": ai_response
                }, ensure_ascii=False),
                "attribute_changes": json.dumps(effects, ensure_ascii=False)
            },
            key_field="event_id",
            key_value=event_id
        )

    @staticmethod
    async def _post_action_checks(message_obj, user_id: str, chat_id: str, character: Dict):
        """互动后的检查（解锁、掉落等）"""

        # === 【新增】检查双重人格事件 ===
        from .dual_personality_system import DualPersonalitySystem

        # 1. 检查人格战争事件（优先级高）
        war_triggered, war_event_data = DualPersonalitySystem.check_personality_war_event(character)
        if war_triggered and war_event_data:
            # 显示人格战争事件
            event_message = f"""{war_event_data['title']}

{war_event_data['desc']}

━━━━━━━━━━━━━━━━━━━
💭 面具强度: {war_event_data['mask_strength']}/100
🔥 真实欲望: {war_event_data['core_desire']}/100
━━━━━━━━━━━━━━━━━━━

请选择你的回应:
"""
            for idx, choice in enumerate(war_event_data['choices']):
                event_message += f"\n{idx+1}. {choice['text']}"
                event_message += f"\n   → {choice['effect']}"

            await send_api.text_to_stream(
                text=event_message,
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

            # 记录触发次数
            character["personality_war_triggered"] = character.get("personality_war_triggered", 0) + 1
            await database_api.db_save(
                DTCharacter,
                data=character,
                key_field="user_id",
                key_value=user_id
            )

            # 注意：这里不处理玩家选择，需要通过另一个命令处理
            logger.info(f"触发人格战争事件: {user_id}")

        # 2. 检查面具崩塌/裂痕事件
        crack_triggered, crack_message = DualPersonalitySystem.check_mask_crack_event(character)
        if crack_triggered and crack_message:
            await send_api.text_to_stream(
                text=crack_message,
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

            # 记录崩塌时间
            character["last_mask_crack"] = time.time()
            await database_api.db_save(
                DTCharacter,
                data=character,
                key_field="user_id",
                key_value=user_id
            )

            logger.info(f"触发面具事件: {user_id}")

        # === 【新增】检查关系张力危机 ===
        from .relationship_tension_system import RelationshipTensionSystem

        # 检查是否触发关系危机
        crisis_triggered, crisis_event = RelationshipTensionSystem.check_relationship_crisis(character)
        if crisis_triggered and crisis_event:
            # 显示危机事件
            crisis_message = f"""{crisis_event['title']}

{crisis_event['desc']}

━━━━━━━━━━━━━━━━━━━
⚠️ 关系正在经历考验...
━━━━━━━━━━━━━━━━━━━"""

            await send_api.text_to_stream(
                text=crisis_message,
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

            # 应用危机惩罚
            character = AttributeSystem.apply_changes(character, crisis_event['penalty'])
            await database_api.db_save(
                DTCharacter,
                data=character,
                key_field="user_id",
                key_value=user_id
            )

            logger.warning(f"触发关系危机: {user_id} - {crisis_event['crisis_type']}")

            # 显示平衡建议
            balance_suggestion = RelationshipTensionSystem.get_balance_suggestion(character)
            if balance_suggestion != "✅ 关系平衡良好！继续保持":
                await send_api.text_to_stream(
                    text=balance_suggestion,
                    stream_id=message_obj.chat_stream.stream_id,
                    storage_message=True
                )

        # === 【新增】检查选择困境事件 ===
        from .choice_dilemma_system import ChoiceDilemmaSystem

        # 检查是否触发选择困境
        dilemma_triggered, dilemma_data = ChoiceDilemmaSystem.check_dilemma_trigger(character)
        if dilemma_triggered and dilemma_data:
            # 【修复】先保存数据，再发送消息（避免时序问题）
            character["pending_dilemma"] = dilemma_data['dilemma_id']
            character["dilemma_triggered_at"] = time.time()
            await database_api.db_save(
                DTCharacter,
                data=character,
                key_field="user_id",
                key_value=user_id
            )

            logger.info(f"触发选择困境: {user_id} - {dilemma_data['dilemma_id']}")

            # 构建困境消息
            dilemma_message = f"""{dilemma_data['title']}

{dilemma_data['description']}

━━━━━━━━━━━━━━━━━━━
⚠️ 这是一个重要的选择...
━━━━━━━━━━━━━━━━━━━

你的选择:"""

            for idx, choice in enumerate(dilemma_data['choices'], 1):
                dilemma_message += f"\n\n{idx}. 【{choice['text']}】"
                dilemma_message += f"\n   {choice['description']}"

            dilemma_message += f"\n\n使用 /选择 <1/2> 做出选择"

            await send_api.text_to_stream(
                text=dilemma_message,
                stream_id=message_obj.chat_stream.stream_id,
                storage_message=True
            )

        # 随机掉落道具（15%概率）
        if random.random() < 0.15:
            from ..extensions.item_system import ItemSystem
            from ..core.models import DTItem

            # 获取所有道具
            all_items = await database_api.db_get(DTItem)

            if all_items:
                # 根据角色属性筛选可掉落的道具
                available_drops = []
                for item in all_items:
                    # 检查解锁条件
                    unlock_condition = json.loads(item.get("unlock_condition", "{}"))
                    unlocked = True

                    for attr, value in unlock_condition.items():
                        char_value = character.get(attr, 0)
                        if isinstance(value, str) and value.startswith("<"):
                            if char_value >= int(value[1:]):
                                unlocked = False
                                break
                        else:
                            if char_value < int(value):
                                unlocked = False
                                break

                    if unlocked:
                        # 根据强度等级设置掉落权重（强度越低越容易掉落）
                        intensity = item.get("intensity_level", 5)
                        weight = max(1, 11 - intensity)  # 强度10的权重1，强度1的权重10
                        available_drops.extend([item] * weight)

                if available_drops:
                    # 随机选择一个道具
                    dropped_item = random.choice(available_drops)

                    # 添加到背包
                    await ItemSystem.add_item(user_id, chat_id, dropped_item["item_id"], 1)

                    # 发送掉落提示
                    rarity_emoji = {
                        1: "⭐", 2: "⭐", 3: "✨",
                        4: "✨", 5: "💫", 6: "💫",
                        7: "🌟", 8: "🌟", 9: "💥", 10: "💥"
                    }.get(dropped_item.get("intensity_level", 1), "⭐")

                    drop_msg = f"""🎁 【道具掉落】

{rarity_emoji} {dropped_item['item_name']}

{dropped_item['effect_description']}

已自动添加到背包！使用 /背包 查看"""

                    await send_api.text_to_stream(
                        text=drop_msg,
                        stream_id=message_obj.chat_stream.stream_id,
                        storage_message=True
                    )

                    logger.info(f"道具掉落: {user_id} - {dropped_item['item_name']}")

        # 检查成就解锁
        from ..extensions.achievement_system import AchievementSystem
        newly_unlocked = await AchievementSystem.check_achievements(user_id, chat_id, character)

        if newly_unlocked:
            # 发送成就解锁通知
            for ach in newly_unlocked:
                rarity_emoji = {
                    "common": "⭐",
                    "rare": "✨",
                    "epic": "💫",
                    "legendary": "🌟"
                }
                emoji = rarity_emoji.get(ach.get("rarity", "common"), "🏆")

                ach_msg = f"""{emoji} 【成就解锁】

{ach['achievement_name']}
{ach['description']}

奖励: +{ach.get('reward_points', 0)} 积分"""

                await send_api.text_to_stream(
                    text=ach_msg,
                    stream_id=message_obj.chat_stream.stream_id,
                    storage_message=True
                )

                logger.info(f"成就解锁: {user_id} - {ach['achievement_name']}")
