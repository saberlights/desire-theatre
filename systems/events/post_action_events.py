"""
动作后随机触发事件系统
角色在用户动作后可能产生的额外反应和互动
"""

import random
import time
from typing import Dict, Optional, List


class PostActionEventSystem:
    """动作后事件系统"""

    # 事件库 - 根据不同情况触发
    EVENTS = {
        # ========== 积极反应事件 ==========
        "主动亲吻": {
            "probability": 0.15,
            "conditions": lambda c, action: (
                c.get("affection", 0) > 60 and
                c.get("intimacy", 0) > 50 and
                action in ["牵手", "摸头", "抱"]
            ),
            "responses": [
                "她突然踮起脚尖，在你脸颊上轻轻吻了一下，然后害羞地低下头",
                "\"谢谢你...\"她说着，主动吻上了你的嘴唇",
                "她红着脸凑近，小心翼翼地亲了你一下"
            ],
            "effects": {
                "intimacy": 5,
                "affection": 3,
                "arousal": 8
            },
            "event_type": "romantic"
        },

        "主动拥抱": {
            "probability": 0.18,
            "conditions": lambda c, action: (
                c.get("affection", 0) > 50 and
                c.get("trust", 0) > 60 and
                action in ["早安", "晚安", "摸头"]
            ),
            "responses": [
                "她突然抱住了你，把头埋在你怀里",
                "\"能再抱一会吗？\"她轻声请求道",
                "她紧紧抱住你，不愿放开"
            ],
            "effects": {
                "intimacy": 6,
                "trust": 4,
                "arousal": 3
            },
            "event_type": "intimate"
        },

        "撒娇": {
            "probability": 0.2,
            "conditions": lambda c, action: (
                c.get("affection", 0) > 40 and
                c.get("personality_type", "") in ["tsundere", "innocent", "shy"]
            ),
            "responses": [
                "\"哼，下次...下次也要这样对我！\"她傲娇地说",
                "\"人家还想要...\"她拉着你的衣角撒娇",
                "她用水汪汪的眼神看着你，显然还想要更多",
                "\"再来一次嘛~\"她用撒娇的语气说"
            ],
            "effects": {
                "affection": 3,
                "desire": 5
            },
            "event_type": "cute"
        },

        # ========== 被动反应事件 ==========
        "身体颤抖": {
            "probability": 0.25,
            "conditions": lambda c, action: (
                c.get("arousal", 0) > 50 and
                action in ["摸", "亲", "诱惑", "舔"]
            ),
            "responses": [
                "她的身体不受控制地颤抖起来，发出细微的呻吟",
                "\"啊...\"她轻呼一声，身体明显地抖了一下",
                "她咬着嘴唇，努力压抑着身体的颤抖"
            ],
            "effects": {
                "arousal": 10,
                "resistance": -5,
                "shame": -3
            },
            "event_type": "reaction"
        },

        "腿软": {
            "probability": 0.2,
            "conditions": lambda c, action: (
                c.get("arousal", 0) > 70 and
                action in ["亲", "摸", "舔", "推倒"]
            ),
            "responses": [
                "她的腿突然一软，差点站不稳，不得不抓住你的肩膀",
                "\"等...等一下...\"她腿软得几乎要跪下来",
                "她身体一软，整个人靠在你身上"
            ],
            "effects": {
                "arousal": 12,
                "resistance": -10,
                "submission": 5
            },
            "event_type": "reaction"
        },

        "失禁": {
            "probability": 0.08,
            "conditions": lambda c, action: (
                c.get("arousal", 0) > 85 and
                c.get("shame", 100) < 40 and
                action in ["摸", "舔", "推倒", "调教"]
            ),
            "responses": [
                "\"不...不要...\"她惊慌地说，但身体已经失去了控制...",
                "她羞愧地发现自己竟然...\"对不起...我...\"",
                "\"啊...怎么会...\"她湿润的痕迹出卖了她"
            ],
            "effects": {
                "arousal": 20,
                "shame": -15,
                "corruption": 10,
                "resistance": -15
            },
            "event_type": "extreme",
            "nsfw_level": 3
        },

        "主动脱衣": {
            "probability": 0.12,
            "conditions": lambda c, action: (
                c.get("corruption", 0) > 50 and
                c.get("desire", 0) > 60 and
                c.get("shame", 100) < 50
            ),
            "responses": [
                "\"既然...既然你都这样了...\"她开始慢慢脱下衣服",
                "她咬着嘴唇，主动解开了扣子",
                "\"不用你动手...我自己来...\"她害羞但坚定地说"
            ],
            "effects": {
                "corruption": 8,
                "arousal": 15,
                "shame": -10,
                "desire": 10
            },
            "event_type": "initiative",
            "nsfw_level": 2
        },

        # ========== 抗拒事件 ==========
        "害羞躲避": {
            "probability": 0.3,
            "conditions": lambda c, action: (
                c.get("intimacy", 0) < 30 and
                c.get("shame", 100) > 60 and
                action in ["亲", "摸", "抱"]
            ),
            "responses": [
                "\"等...等一下！太快了！\"她红着脸往后退",
                "她害羞得不行，用手挡住了脸",
                "\"不要...太羞耻了...\"她小声抗议"
            ],
            "effects": {
                "shame": 5,
                "resistance": 10,
                "arousal": -5
            },
            "event_type": "resist"
        },

        "挣扎反抗": {
            "probability": 0.25,
            "conditions": lambda c, action: (
                c.get("resistance", 100) > 60 and
                c.get("submission", 50) < 40 and
                action in ["推倒", "命令", "调教", "羞辱"]
            ),
            "responses": [
                "\"不要！放开我！\"她用力挣扎",
                "她奋力反抗，试图推开你",
                "\"你这个混蛋！\"她愤怒地说，但力气越来越小"
            ],
            "effects": {
                "resistance": 5,
                "submission": -3,
                "arousal": 5  # 反抗中也会有微妙的兴奋
            },
            "event_type": "resist"
        },

        "口是心非": {
            "probability": 0.35,
            "conditions": lambda c, action: (
                c.get("personality_type", "") == "tsundere" and
                c.get("affection", 0) > 30
            ),
            "responses": [
                "\"才...才不是因为喜欢你！\"她红着脸别过头",
                "\"只是...只是让你做一次而已！不要误会！\"",
                "\"哼！我可没有很舒服！\"她嘴硬道",
                "\"下次可不会这么容易就让你得逞！\"她傲娇地说"
            ],
            "effects": {
                "affection": 2,
                "trust": 1
            },
            "event_type": "tsundere"
        },

        # ========== 情绪爆发事件 ==========
        "泪流满面": {
            "probability": 0.1,
            "conditions": lambda c, action: (
                c.get("arousal", 0) > 80 or
                (c.get("shame", 100) < 20 and c.get("corruption", 0) > 60)
            ),
            "responses": [
                "她泪流满面，不知是委屈还是快感过度",
                "眼泪止不住地流下来，她咬着嘴唇不让自己哭出声",
                "\"呜...\"她哭了起来，却又不愿停下"
            ],
            "effects": {
                "arousal": 15,
                "intimacy": 8,
                "resistance": -20
            },
            "event_type": "emotional",
            "nsfw_level": 2
        },

        "意识模糊": {
            "probability": 0.15,
            "conditions": lambda c, action: (
                c.get("arousal", 0) > 90
            ),
            "responses": [
                "她的意识开始模糊，眼神失焦，只剩下本能的反应",
                "\"不...不行了...要...要坏掉了...\"她语无伦次地说",
                "她已经什么都顾不上了，完全沉浸在快感中"
            ],
            "effects": {
                "arousal": 10,
                "resistance": -30,
                "shame": -20,
                "corruption": 12
            },
            "event_type": "extreme",
            "nsfw_level": 3
        },

        # ========== 主动请求事件 ==========
        "主动请求": {
            "probability": 0.2,
            "conditions": lambda c, action: (
                c.get("desire", 0) > 70 and
                c.get("shame", 100) < 40
            ),
            "responses": [
                "\"还...还想要...\"她小声说",
                "\"能不能...再继续？\"她眼神迷离",
                "\"不要停...求你了...\"她主动抓住你的手",
                "\"我还没...还没满足...\"她大胆地说"
            ],
            "effects": {
                "desire": 10,
                "submission": 8,
                "shame": -8
            },
            "event_type": "request",
            "nsfw_level": 2
        },

        "反向调教": {
            "probability": 0.08,
            "conditions": lambda c, action: (
                c.get("corruption", 0) > 70 and
                c.get("submission", 50) < 30 and
                c.get("personality_type", "") in ["seductive", "cold"]
            ),
            "responses": [
                "\"就这点程度？\"她妩媚一笑，\"让我来教教你...\"",
                "她突然反客为主，把你推倒在床上",
                "\"看来需要我主动了呢~\"她舔了舔嘴唇"
            ],
            "effects": {
                "corruption": 10,
                "desire": 15,
                "submission": -10,
                "dominant_trait": True
            },
            "event_type": "reversal",
            "nsfw_level": 2
        },

        # ========== 特殊状态事件 ==========
        "进入高潮": {
            "probability": 0.12,
            "conditions": lambda c, action: (
                c.get("arousal", 0) > 88 and
                action in ["推倒", "舔", "调教", "侵犯"]
            ),
            "responses": [
                "\"啊——！\"她猛地抽搐起来，达到了顶点",
                "她的身体剧烈颤抖，完全失去了控制",
                "\"不行了...要去了...！\"她尖叫着达到了高潮"
            ],
            "effects": {
                "arousal": -50,  # 释放后大幅下降
                "post_orgasm_time": "now",  # 标记进入贤者时间
                "intimacy": 15,
                "corruption": 10,
                "shame": -15,
                "satisfaction": 100
            },
            "event_type": "climax",
            "nsfw_level": 3,
            "special_trigger": "orgasm"
        },

        "敏感点发现": {
            "probability": 0.18,
            "conditions": lambda c, action: (
                action in ["摸", "亲", "舔"] and
                random.random() < 0.2
            ),
            "responses": [
                "\"啊！那里...那里不行！\"她猛地一颤，你似乎发现了她的敏感点",
                "当你触碰到那里时，她的反应格外激烈",
                "\"呀...那里太敏感了...\"她害羞地说"
            ],
            "effects": {
                "arousal": 15,
                "sensitivity_increased": True,
                "shame": -5
            },
            "event_type": "discovery",
            "nsfw_level": 2,
            "unlock_hint": "发现了敏感点！下次针对该部位效果+50%"
        },

        "习惯养成": {
            "probability": 0.1,
            "conditions": lambda c, action: (
                c.get("interaction_count", 0) > 50 and
                c.get("corruption", 0) > 40
            ),
            "responses": [
                "\"每天...每天都要这样...\"她已经习惯了你的触碰",
                "\"没有你的话...我会...\"她意识到自己已经离不开了",
                "她的身体已经记住了你的形状"
            ],
            "effects": {
                "dependency": 20,
                "corruption": 8,
                "affection": 10
            },
            "event_type": "addiction",
            "nsfw_level": 2
        }
    }

    # 连锁事件 - 某个事件触发后可能引发下一个
    CHAIN_EVENTS = {
        "进入高潮": {
            "next_possible": ["泪流满面", "意识模糊"],
            "probability": 0.5
        },
        "主动请求": {
            "next_possible": ["主动脱衣", "主动亲吻"],
            "probability": 0.3
        }
    }

    @staticmethod
    def check_post_action_events(
        character: Dict,
        action_name: str,
        current_mood: Optional[Dict] = None
    ) -> List[Dict]:
        """
        检查动作后可能触发的事件
        返回: 触发的事件列表
        """
        triggered_events = []

        for event_id, event_data in PostActionEventSystem.EVENTS.items():
            # 检查条件
            try:
                if not event_data["conditions"](character, action_name):
                    continue
            except Exception:
                continue

            # 概率判定（情绪可能影响概率）
            base_probability = event_data["probability"]

            # 如果情绪触发事件，增加概率
            if current_mood and current_mood.get("triggers_events", False):
                base_probability *= 1.5

            if random.random() < base_probability:
                # 随机选择一个回复
                response = random.choice(event_data["responses"])

                triggered_events.append({
                    "event_id": event_id,
                    "event_type": event_data["event_type"],
                    "response": response,
                    "effects": event_data.get("effects", {}),
                    "nsfw_level": event_data.get("nsfw_level", 1),
                    "special_trigger": event_data.get("special_trigger", None),
                    "unlock_hint": event_data.get("unlock_hint", None)
                })

                # 检查连锁事件
                if event_id in PostActionEventSystem.CHAIN_EVENTS:
                    chain_data = PostActionEventSystem.CHAIN_EVENTS[event_id]
                    if random.random() < chain_data["probability"]:
                        # 可能触发连锁事件
                        next_event_id = random.choice(chain_data["next_possible"])
                        if next_event_id in PostActionEventSystem.EVENTS:
                            next_event = PostActionEventSystem.EVENTS[next_event_id]
                            next_response = random.choice(next_event["responses"])
                            triggered_events.append({
                                "event_id": next_event_id,
                                "event_type": next_event["event_type"],
                                "response": next_response,
                                "effects": next_event.get("effects", {}),
                                "nsfw_level": next_event.get("nsfw_level", 1),
                                "is_chain": True
                            })

                # 通常只触发一个主要事件（除非连锁）
                break

        return triggered_events

    @staticmethod
    def format_event_message(event: Dict) -> str:
        """
        格式化事件消息用于显示
        """
        event_type_emoji = {
            "romantic": "💕",
            "intimate": "💗",
            "cute": "🌸",
            "reaction": "💫",
            "extreme": "💦",
            "initiative": "😈",
            "resist": "🙅",
            "tsundere": "😤",
            "emotional": "😢",
            "request": "🔥",
            "reversal": "👑",
            "climax": "✨",
            "discovery": "💡",
            "addiction": "💊"
        }

        emoji = event_type_emoji.get(event["event_type"], "✨")
        chain_prefix = "【连锁】" if event.get("is_chain", False) else ""

        message = f"\n{emoji} {chain_prefix}【额外反应】\n{event['response']}"

        # 如果有解锁提示
        if event.get("unlock_hint"):
            message += f"\n\n💡 {event['unlock_hint']}"

        return message

    @staticmethod
    def apply_event_effects(character: Dict, event: Dict) -> Dict:
        """
        应用事件效果到角色
        """
        from ..attributes.attribute_system import AttributeSystem

        effects = event.get("effects", {})
        updated_char = character.copy()

        for attr, change in effects.items():
            if attr == "post_orgasm_time":
                if change == "now":
                    import time
                    updated_char["post_orgasm_time"] = time.time()
            elif attr == "sensitivity_increased":
                updated_char["sensitivity_increased"] = True
                updated_char["sensitivity_end_time"] = time.time() + 3600  # 1小时效果
            elif attr in ["dependency", "satisfaction", "dominant_trait"]:
                # 特殊属性
                updated_char[attr] = updated_char.get(attr, 0) + change
            else:
                # 普通属性
                current_value = updated_char.get(attr, 0)
                new_value = AttributeSystem.clamp(current_value + change)
                updated_char[attr] = new_value

        # 特殊处理：高潮后记录
        if event.get("special_trigger") == "orgasm":
            updated_char["last_orgasm_time"] = time.time()
            updated_char["orgasm_count"] = updated_char.get("orgasm_count", 0) + 1

        return updated_char
