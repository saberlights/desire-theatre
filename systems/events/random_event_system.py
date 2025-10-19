"""
随机事件系统 - 借鉴《火山女儿》的事件卡机制

核心理念:
- 增加不可预测性和故事性
- 外部事件影响关系发展
- 玩家面临选择和后果
- 塑造更真实的世界观
"""

from typing import Dict, Tuple, Optional, List
import random
import json
from src.common.logger import get_logger

logger = get_logger("dt_random_events")


class RandomEventSystem:
    """随机事件系统"""

    # 事件定义
    EVENTS = {
        # ========== 社交类事件 ==========
        "friend_visit": {
            "name": "朋友来访",
            "category": "social",
            "emoji": "👥",
            "trigger_chance": 0.15,  # 15%概率
            "trigger_conditions": {
                "game_day": (5, 40),  # 只在5-40天触发
            },
            "description": "她的朋友突然来找她了",
            "story_text": "\"抱歉，我朋友突然来了，今天可能要陪她...\"",
            "choices": [
                {
                    "text": "理解地让她去陪朋友",
                    "effects": {
                        "trust": 10,
                        "affection": 5,
                        "daily_interactions_used": 0,  # 不消耗今日互动
                    },
                    "result_text": "她感激地看着你：\"你真善解人意...\"",
                },
                {
                    "text": "要求她留下来陪你",
                    "effects": {
                        "affection": -5,
                        "resistance": 10,
                        "trust": -3,
                    },
                    "result_text": "她有些为难：\"可是我已经答应了她...\"",
                },
                {
                    "text": "提议一起见她的朋友",
                    "requirements": {"intimacy": 40},
                    "effects": {
                        "affection": 8,
                        "trust": 8,
                        "intimacy": 5,
                    },
                    "result_text": "她惊喜地笑了：\"真的吗？那太好了！\"",
                },
            ],
        },

        "family_call": {
            "name": "家人来电",
            "category": "social",
            "emoji": "📞",
            "trigger_chance": 0.12,
            "trigger_conditions": {},
            "description": "她的家人打电话来了",
            "story_text": "她接起电话，表情有些紧张...",
            "choices": [
                {
                    "text": "安静地等她打完电话",
                    "effects": {
                        "trust": 8,
                        "affection": 5,
                    },
                    "result_text": "她挂断电话后松了口气：\"谢谢你的耐心...\"",
                },
                {
                    "text": "好奇地旁听",
                    "effects": {
                        "trust": -5,
                        "resistance": 5,
                    },
                    "result_text": "她注意到你在听，有些不悦...",
                },
            ],
        },

        "ex_appears": {
            "name": "前任出现",
            "category": "social",
            "emoji": "💔",
            "trigger_chance": 0.08,
            "trigger_conditions": {
                "intimacy": (30, 100),  # 关系达到一定程度才触发
                "game_day": (10, 35),
            },
            "description": "她的前任突然联系她",
            "story_text": "她看着手机，表情复杂：\"是...我的前任...\"",
            "choices": [
                {
                    "text": "相信她，让她自己处理",
                    "effects": {
                        "trust": 15,
                        "affection": 10,
                    },
                    "result_text": "她感动地抱住你：\"谢谢你相信我...\"",
                },
                {
                    "text": "表现出醋意和占有欲",
                    "effects": {
                        "affection": 5,
                        "submission": 8,
                        "resistance": -5,
                    },
                    "result_text": "她脸红了：\"你...吃醋了吗？\"",
                },
                {
                    "text": "冷淡对待",
                    "effects": {
                        "affection": -10,
                        "trust": -8,
                        "resistance": 15,
                    },
                    "result_text": "她失望地低下头...",
                },
            ],
        },

        # ========== 工作/学习类事件 ==========
        "work_stress": {
            "name": "工作压力",
            "category": "work",
            "emoji": "💼",
            "trigger_chance": 0.18,
            "trigger_conditions": {},
            "description": "她今天工作压力很大",
            "story_text": "她看起来很疲惫：\"今天真是糟糕的一天...\"",
            "choices": [
                {
                    "text": "温柔地安慰她",
                    "effects": {
                        "affection": 12,
                        "trust": 10,
                        "mood_gauge": 15,
                    },
                    "result_text": "她靠在你肩上：\"有你在真好...\"",
                },
                {
                    "text": "帮她按摩放松",
                    "effects": {
                        "affection": 10,
                        "intimacy": 8,
                        "arousal": 5,
                        "mood_gauge": 20,
                    },
                    "result_text": "她舒服地叹了口气：\"你的手真温柔...\"",
                },
                {
                    "text": "提议做点刺激的事来放松",
                    "requirements": {"corruption": 40, "intimacy": 50},
                    "effects": {
                        "arousal": 15,
                        "corruption": 8,
                        "shame": -10,
                        "mood_gauge": 25,
                    },
                    "result_text": "她愣了一下，然后红着脸点了点头...",
                },
            ],
        },

        "exam_coming": {
            "name": "考试临近",
            "category": "work",
            "emoji": "📚",
            "trigger_chance": 0.10,
            "trigger_conditions": {
                "game_day": (8, 20),  # 特定时间段
            },
            "description": "她有重要考试要准备",
            "story_text": "\"抱歉，我得去复习了，考试快到了...\"",
            "choices": [
                {
                    "text": "陪她一起复习",
                    "effects": {
                        "affection": 15,
                        "trust": 12,
                        "daily_interactions_used": 1,  # 只消耗1次
                    },
                    "result_text": "她开心地笑了：\"和你一起学习效率都变高了！\"",
                },
                {
                    "text": "给她独处空间",
                    "effects": {
                        "trust": 8,
                        "affection": 5,
                        "daily_interactions_used": 0,
                    },
                    "result_text": "她感激地说：\"谢谢你的体谅...\"",
                },
                {
                    "text": "诱惑她放松一下",
                    "requirements": {"intimacy": 45},
                    "effects": {
                        "affection": -5,
                        "arousal": 10,
                        "resistance": 8,
                    },
                    "result_text": "她有些犹豫：\"现在...真的不太好...\"",
                },
            ],
        },

        # ========== 健康/状态类事件 ==========
        "feeling_unwell": {
            "name": "身体不适",
            "category": "health",
            "emoji": "🤒",
            "trigger_chance": 0.10,
            "trigger_conditions": {},
            "description": "她今天身体不太舒服",
            "story_text": "她脸色苍白：\"有点头疼...可能感冒了...\"",
            "choices": [
                {
                    "text": "细心照顾她",
                    "effects": {
                        "affection": 20,
                        "trust": 15,
                        "intimacy": 10,
                        "mood_gauge": 20,
                    },
                    "result_text": "她感动得眼眶湿润：\"你对我真好...\"",
                },
                {
                    "text": "陪她去看医生",
                    "effects": {
                        "affection": 15,
                        "trust": 12,
                        "coins": -20,  # 花费金币
                    },
                    "result_text": "她紧紧握着你的手：\"有你陪着我很安心...\"",
                },
                {
                    "text": "让她自己休息",
                    "effects": {
                        "affection": -8,
                        "trust": -5,
                    },
                    "result_text": "她失望地点了点头...",
                },
            ],
        },

        "drunk": {
            "name": "喝醉了",
            "category": "health",
            "emoji": "🍺",
            "trigger_chance": 0.08,
            "trigger_conditions": {
                "intimacy": (25, 100),
            },
            "description": "她喝醉了",
            "story_text": "她脸色绯红，有些站不稳...",
            "choices": [
                {
                    "text": "扶她回家照顾她",
                    "effects": {
                        "affection": 18,
                        "trust": 15,
                        "intimacy": 12,
                    },
                    "result_text": "她迷迷糊糊地靠在你肩上...",
                },
                {
                    "text": "趁机做些亲密的事",
                    "requirements": {"corruption": 30},
                    "effects": {
                        "intimacy": 20,
                        "corruption": 15,
                        "shame": -15,
                        "trust": -10,  # 降低信任
                    },
                    "result_text": "她迷迷糊糊地没有拒绝...",
                },
                {
                    "text": "把她交给朋友",
                    "effects": {
                        "affection": -12,
                        "trust": -15,
                    },
                    "result_text": "她睁开眼睛，失望地看着你...",
                },
            ],
        },

        # ========== 特殊事件 ==========
        "rainy_day": {
            "name": "突然下雨",
            "category": "special",
            "emoji": "🌧️",
            "trigger_chance": 0.12,
            "trigger_conditions": {},
            "description": "突然下起了大雨",
            "story_text": "你们被困在了雨中...",
            "choices": [
                {
                    "text": "共撑一把伞",
                    "effects": {
                        "intimacy": 12,
                        "affection": 10,
                        "arousal": 5,
                    },
                    "result_text": "雨伞下，你们靠得很近，能感受到彼此的心跳...",
                },
                {
                    "text": "找个地方避雨",
                    "effects": {
                        "intimacy": 15,
                        "arousal": 8,
                    },
                    "result_text": "你们躲进了一个无人的屋檐下...",
                },
                {
                    "text": "在雨中奔跑",
                    "effects": {
                        "affection": 15,
                        "mood_gauge": 20,
                    },
                    "result_text": "她笑着和你一起在雨中奔跑，像个孩子一样...",
                },
            ],
        },

        "unexpected_gift": {
            "name": "意外的礼物",
            "category": "special",
            "emoji": "🎁",
            "trigger_chance": 0.08,
            "trigger_conditions": {
                "affection": (40, 100),
            },
            "description": "她准备了礼物给你",
            "story_text": "她害羞地递给你一个包装精美的盒子：\"这个...给你...\"",
            "choices": [
                {
                    "text": "开心地接受",
                    "effects": {
                        "affection": 15,
                        "intimacy": 10,
                        "mood_gauge": 20,
                    },
                    "result_text": "她看到你开心的样子，也笑了...",
                },
                {
                    "text": "回赠更贵重的礼物",
                    "requirements": {"coins": 50},
                    "effects": {
                        "affection": 20,
                        "trust": 12,
                        "coins": -50,
                    },
                    "result_text": "她惊喜地说：\"这...太贵重了...\"",
                },
                {
                    "text": "用吻表达感谢",
                    "requirements": {"intimacy": 50},
                    "effects": {
                        "intimacy": 18,
                        "arousal": 12,
                        "shame": -8,
                    },
                    "result_text": "她脸红了，但没有推开你...",
                },
            ],
        },

        "nightmare": {
            "name": "噩梦惊醒",
            "category": "special",
            "emoji": "😨",
            "trigger_chance": 0.06,
            "trigger_conditions": {
                "intimacy": (60, 100),  # 需要亲密关系
            },
            "description": "她半夜从噩梦中惊醒",
            "story_text": "深夜，她被噩梦惊醒，浑身颤抖...",
            "choices": [
                {
                    "text": "温柔地抱着她安慰",
                    "effects": {
                        "affection": 25,
                        "trust": 20,
                        "intimacy": 15,
                    },
                    "result_text": "她紧紧抱着你，逐渐平静下来...",
                },
                {
                    "text": "陪她聊天直到天亮",
                    "effects": {
                        "affection": 20,
                        "trust": 18,
                        "mood_gauge": 15,
                    },
                    "result_text": "\"有你在，我不害怕了...\"",
                },
            ],
        },

        "jealous_moment": {
            "name": "吃醋时刻",
            "category": "special",
            "emoji": "😤",
            "trigger_chance": 0.10,
            "trigger_conditions": {
                "affection": (50, 100),
            },
            "description": "她看到你和别人说话吃醋了",
            "story_text": "她看着你和其他人说话，撅起了嘴...",
            "choices": [
                {
                    "text": "立刻过去哄她",
                    "effects": {
                        "affection": 15,
                        "intimacy": 10,
                        "submission": 5,
                    },
                    "result_text": "她还在装生气，但眼中藏着笑意...",
                },
                {
                    "text": "故意继续聊",
                    "effects": {
                        "affection": -10,
                        "resistance": 15,
                        "mood_gauge": -10,
                    },
                    "result_text": "她真的生气了，转身离开...",
                },
                {
                    "text": "霸道地宣示主权",
                    "requirements": {"submission": 40},
                    "effects": {
                        "submission": 15,
                        "arousal": 12,
                        "shame": -8,
                    },
                    "result_text": "她脸红了，乖巧地跟着你走...",
                },
            ],
        },
    }

    @staticmethod
    def check_and_trigger_event(character: Dict) -> Optional[Tuple[str, Dict]]:
        """
        检查是否触发随机事件

        Returns:
            (事件ID, 事件数据) 或 None
        """
        game_day = character.get("game_day", 1)

        # 收集所有可能触发的事件
        possible_events = []

        for event_id, event_data in RandomEventSystem.EVENTS.items():
            # 检查触发条件
            if not RandomEventSystem._check_trigger_conditions(character, event_data):
                continue

            # 检查概率
            if random.random() < event_data["trigger_chance"]:
                possible_events.append((event_id, event_data))

        # 如果有多个事件同时满足条件，随机选择一个
        if possible_events:
            event_id, event_data = random.choice(possible_events)
            logger.info(f"触发随机事件: {event_id} - {event_data['name']}")
            return event_id, event_data

        return None

    @staticmethod
    def _check_trigger_conditions(character: Dict, event_data: Dict) -> bool:
        """检查事件触发条件"""
        conditions = event_data.get("trigger_conditions", {})

        for condition_key, condition_value in conditions.items():
            char_value = character.get(condition_key, 0)

            if isinstance(condition_value, tuple):
                # 范围条件
                min_val, max_val = condition_value
                if not (min_val <= char_value <= max_val):
                    return False
            else:
                # 精确匹配
                if char_value != condition_value:
                    return False

        return True

    @staticmethod
    def check_choice_requirements(character: Dict, choice: Dict) -> bool:
        """检查选择的前置条件"""
        requirements = choice.get("requirements", {})

        for attr, required in requirements.items():
            char_value = character.get(attr, 0)
            if char_value < required:
                return False

        return True

    @staticmethod
    def apply_choice_effects(
        character: Dict,
        choice: Dict
    ) -> Tuple[Dict, Dict[str, int]]:
        """
        应用选择的效果

        Returns:
            (更新后的角色数据, 属性变化)
        """
        effects = choice.get("effects", {})
        attribute_changes = {}

        for attr, change in effects.items():
            if attr in character:
                old_value = character.get(attr, 0)
                new_value = old_value + change

                # 限制范围（属性一般0-100）
                if attr in ["affection", "intimacy", "trust", "corruption", "submission",
                           "desire", "arousal", "resistance", "shame"]:
                    new_value = max(0, min(100, new_value))

                character[attr] = new_value
                attribute_changes[attr] = change

        logger.info(f"应用事件选择效果: {attribute_changes}")

        return character, attribute_changes

    @staticmethod
    def format_event_message(event_data: Dict, character: Dict) -> str:
        """
        格式化事件消息

        Returns:
            事件消息文本
        """
        choices_text = []

        for i, choice in enumerate(event_data["choices"], 1):
            choice_text = f"{i}. {choice['text']}"

            # 检查是否满足条件
            if not RandomEventSystem.check_choice_requirements(character, choice):
                requirements = choice.get("requirements", {})
                req_text = ", ".join(f"{k}≥{v}" for k, v in requirements.items())
                choice_text += f" 🔒({req_text})"

            choices_text.append(choice_text)

        return f"""
━━━━━━━━━━━━━━━━━━━
🎲 【随机事件】
━━━━━━━━━━━━━━━━━━━

{event_data['emoji']} {event_data['name']}

{event_data['story_text']}

━━━━━━━━━━━━━━━━━━━
💭 你的选择:

{chr(10).join(choices_text)}

━━━━━━━━━━━━━━━━━━━
💡 使用 /选择 <数字> 做出决定
""".strip()

    @staticmethod
    def get_event_by_id(event_id: str) -> Optional[Dict]:
        """根据ID获取事件"""
        return RandomEventSystem.EVENTS.get(event_id)

    @staticmethod
    def get_all_events_by_category(category: str) -> List[Tuple[str, Dict]]:
        """获取指定分类的所有事件"""
        return [
            (event_id, event_data)
            for event_id, event_data in RandomEventSystem.EVENTS.items()
            if event_data.get("category") == category
        ]

    @staticmethod
    async def generate_event_content_with_llm(
        event_id: str,
        event_data: Dict,
        character: Dict,
        history: List[Dict] = None
    ) -> Optional[Dict]:
        """
        使用 LLM 生成事件内容（story_text 和 choices）

        Args:
            event_id: 事件ID
            event_data: 原始事件数据（包含category, name等元信息）
            character: 角色数据
            history: 对话历史

        Returns:
            包含生成内容的字典: {"story_text": str, "choices": [...]}
            如果生成失败返回 None
        """
        try:
            from src.plugin_system.apis import llm_api
            from ..events.event_generation_prompt import EventGenerationPrompt

            # 获取事件元信息
            event_category = event_data.get("category", "special")
            event_name = event_data.get("name", "未知事件")
            num_choices = len(event_data.get("choices", []))

            # 构建 Prompt
            prompt = EventGenerationPrompt.build_event_prompt(
                event_category=event_category,
                event_name=event_name,
                character=character,
                history=history,
                num_choices=num_choices
            )

            # 调用 LLM
            models = llm_api.get_available_models()
            replyer_model = models.get("replyer")

            if not replyer_model:
                logger.error("未找到 'replyer' 模型配置")
                return None

            success, ai_response, reasoning, model_name = await llm_api.generate_with_model(
                prompt=prompt,
                model_config=replyer_model,
                request_type="desire_theatre.generate_event"
            )

            if not success or not ai_response:
                logger.error(f"LLM生成事件失败: {ai_response}")
                return None

            # 解析 LLM 返回的 JSON
            # 尝试提取 JSON 内容（可能被包裹在 ```json ... ``` 中）
            response_text = ai_response.strip()

            # 如果有代码块标记，提取其中的内容
            if "```json" in response_text:
                start = response_text.find("```json") + len("```json")
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + len("```")
                end = response_text.rfind("```")
                response_text = response_text[start:end].strip()

            # 解析 JSON
            generated_content = json.loads(response_text)

            # 验证格式
            if not isinstance(generated_content, dict):
                logger.error("LLM返回的不是字典格式")
                return None

            if "story_text" not in generated_content or "choices" not in generated_content:
                logger.error("LLM返回缺少必要字段")
                return None

            logger.info(f"成功生成事件内容: {event_id} - {event_name}")
            return generated_content

        except json.JSONDecodeError as e:
            logger.error(f"解析LLM返回的JSON失败: {e}\n原始内容: {ai_response}")
            return None
        except Exception as e:
            logger.error(f"生成事件内容失败: {e}", exc_info=True)
            return None

    @staticmethod
    def merge_generated_content(original_event: Dict, generated_content: Dict) -> Dict:
        """
        合并原始事件数据和LLM生成的内容

        Args:
            original_event: 原始事件数据（包含effects等）
            generated_content: LLM生成的内容（story_text和choices）

        Returns:
            合并后的完整事件数据
        """
        # 创建副本避免修改原始数据
        merged_event = dict(original_event)

        # 替换 story_text
        merged_event["story_text"] = generated_content["story_text"]

        # 合并 choices
        # 保留原始的 effects 和 requirements，只替换 text 和 result_text
        original_choices = merged_event.get("choices", [])
        generated_choices = generated_content.get("choices", [])

        new_choices = []
        for i, original_choice in enumerate(original_choices):
            new_choice = dict(original_choice)

            # 如果有对应的生成内容，替换文本
            if i < len(generated_choices):
                new_choice["text"] = generated_choices[i].get("text", original_choice.get("text", ""))
                new_choice["result_text"] = generated_choices[i].get("result_text", original_choice.get("result_text", ""))

            new_choices.append(new_choice)

        merged_event["choices"] = new_choices

        return merged_event

    @staticmethod
    async def generate_dynamic_event(
        character: Dict,
        history: List[Dict] = None
    ) -> Optional[Dict]:
        """
        生成完全动态的随机事件（包括事件类型、选项、效果）

        Args:
            character: 角色数据
            history: 对话历史

        Returns:
            完整的事件数据字典，包含所有字段
            如果生成失败返回 None
        """
        try:
            from src.plugin_system.apis import llm_api
            from ..events.event_generation_prompt import EventGenerationPrompt

            # 构建动态事件生成 Prompt
            prompt = EventGenerationPrompt.build_dynamic_event_prompt(
                character=character,
                history=history
            )

            # 调用 LLM
            models = llm_api.get_available_models()
            replyer_model = models.get("replyer")

            if not replyer_model:
                logger.error("未找到 'replyer' 模型配置")
                return None

            success, ai_response, reasoning, model_name = await llm_api.generate_with_model(
                prompt=prompt,
                model_config=replyer_model,
                request_type="desire_theatre.generate_dynamic_event"
            )

            if not success or not ai_response:
                logger.error(f"LLM生成动态事件失败: {ai_response}")
                return None

            # 解析 LLM 返回的 JSON
            response_text = ai_response.strip()

            # 提取 JSON 内容
            if "```json" in response_text:
                start = response_text.find("```json") + len("```json")
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + len("```")
                end = response_text.rfind("```")
                response_text = response_text[start:end].strip()

            # 解析 JSON
            generated_event = json.loads(response_text)

            # 验证格式
            if not isinstance(generated_event, dict):
                logger.error("LLM返回的不是字典格式")
                return None

            required_fields = ["event_name", "event_category", "event_emoji", "story_text", "choices"]
            for field in required_fields:
                if field not in generated_event:
                    logger.error(f"LLM返回缺少必要字段: {field}")
                    return None

            # 补充一些元信息
            generated_event["name"] = generated_event["event_name"]
            generated_event["category"] = generated_event["event_category"]
            generated_event["emoji"] = generated_event["event_emoji"]

            logger.info(f"成功生成动态事件: {generated_event['event_name']} ({generated_event['event_category']})")
            return generated_event

        except json.JSONDecodeError as e:
            logger.error(f"解析LLM返回的JSON失败: {e}\n原始内容: {ai_response}")
            return None
        except Exception as e:
            logger.error(f"生成动态事件失败: {e}", exc_info=True)
            return None
