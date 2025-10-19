"""
动作成长系统 - 让动作随关系发展而进化

核心理念:
- 15个核心动作覆盖完整游戏流程
- 同一动作在不同关系阶段有不同效果
- 玩家能直观感受到关系的进展
"""

from typing import Dict, Tuple


class ActionGrowthSystem:
    """动作成长系统"""

    # 15个核心动作定义
    CORE_ACTIONS = {
        # === 温柔系 (stranger→friend) ===
        "问候": {
            "command": ["早安", "晚安", "你好"],
            "type": "gentle",
            "stranger": {
                "effects": {"affection": 3, "trust": 2},
                "intensity": 1,
                "description": "礼貌的问候"
            },
            "friend": {
                "effects": {"affection": 5, "trust": 3, "intimacy": 2},
                "intensity": 2,
                "description": "温暖的日常问候"
            },
            "close": {
                "effects": {"affection": 6, "intimacy": 4, "desire": 2},
                "intensity": 3,
                "description": "带着期待的问候"
            },
            "lover": {
                "effects": {"affection": 8, "intimacy": 5, "desire": 3},
                "intensity": 3,
                "description": "甜蜜的早晚安"
            }
        },

        "聊天": {
            "command": ["聊天", "说话", "交流"],
            "type": "gentle",
            "stranger": {
                "effects": {"affection": 2, "trust": 4},
                "intensity": 1,
                "description": "试探性的对话"
            },
            "friend": {
                "effects": {"affection": 4, "trust": 6, "intimacy": 2},
                "intensity": 2,
                "description": "轻松的交流"
            },
            "close": {
                "effects": {"affection": 5, "trust": 7, "intimacy": 4},
                "intensity": 3,
                "description": "深入的谈心"
            },
            "lover": {
                "effects": {"affection": 6, "trust": 8, "intimacy": 5, "desire": 2},
                "intensity": 3,
                "description": "亲密的私语"
            }
        },

        "牵手": {
            "command": ["牵手", "握手"],
            "type": "gentle",
            "stranger": {
                "effects": {"affection": 4, "intimacy": 2, "trust": 2},
                "intensity": 2,
                "description": "小心翼翼地牵起手"
            },
            "friend": {
                "effects": {"affection": 6, "intimacy": 5, "trust": 3},
                "intensity": 3,
                "description": "自然地十指紧扣"
            },
            "close": {
                "effects": {"affection": 7, "intimacy": 7, "desire": 3},
                "intensity": 4,
                "description": "温柔地抚摸她的手"
            },
            "lover": {
                "effects": {"affection": 8, "intimacy": 8, "desire": 5},
                "intensity": 4,
                "description": "亲吻她的手背"
            }
        },

        # === 亲密系 (friend→close) ===
        "拥抱": {
            "command": ["抱", "拥抱", "搂"],
            "type": "intimate",
            "stranger": {
                "blocked": True,
                "reason": "关系还不够亲密,她会感到不适"
            },
            "friend": {
                "effects": {"affection": 5, "intimacy": 6, "trust": 4},
                "intensity": 3,
                "description": "友好的拥抱"
            },
            "close": {
                "effects": {"affection": 7, "intimacy": 10, "desire": 4, "arousal": 3},
                "intensity": 5,
                "description": "紧紧相拥"
            },
            "lover": {
                "effects": {"affection": 8, "intimacy": 12, "desire": 6, "arousal": 5},
                "intensity": 6,
                "description": "深情的拥抱,感受彼此的温度"
            }
        },

        "亲吻": {
            "command": ["亲", "吻", "kiss"],
            "type": "intimate",
            "has_targets": True,  # 有部位选择
            "stranger": {
                "blocked": True,
                "reason": "太快了,她会躲开"
            },
            "friend": {
                "targets": {
                    "额头": {"affection": 6, "intimacy": 5, "trust": 3},
                    "脸颊": {"affection": 7, "intimacy": 6, "arousal": 2}
                },
                "intensity": 4,
                "description": "轻柔的亲吻"
            },
            "close": {
                "targets": {
                    "额头": {"affection": 7, "intimacy": 6, "desire": 2},
                    "脸颊": {"affection": 8, "intimacy": 7, "arousal": 3},
                    "嘴唇": {"affection": 10, "intimacy": 12, "arousal": 8, "desire": 5, "shame": -3}
                },
                "intensity": 6,
                "description": "深情的亲吻"
            },
            "lover": {
                "targets": {
                    "额头": {"affection": 8, "intimacy": 7, "desire": 3},
                    "脸颊": {"affection": 9, "intimacy": 8, "arousal": 4},
                    "嘴唇": {"affection": 12, "intimacy": 15, "arousal": 12, "desire": 8, "shame": -5},
                    "脖子": {"intimacy": 10, "arousal": 10, "desire": 8, "corruption": 3}
                },
                "intensity": 7,
                "description": "热烈的深吻"
            }
        },

        "抚摸": {
            "command": ["摸", "抚摸", "摸摸"],
            "type": "seductive",
            "has_targets": True,
            "stranger": {
                "targets": {
                    "头": {"affection": 5, "intimacy": 3, "trust": 2}
                },
                "intensity": 2,
                "description": "轻轻摸头"
            },
            "friend": {
                "targets": {
                    "头": {"affection": 7, "intimacy": 5, "trust": 3},
                    "脸": {"affection": 6, "intimacy": 6, "arousal": 2},
                    "手": {"affection": 5, "intimacy": 4, "trust": 4}
                },
                "intensity": 3,
                "description": "温柔的抚摸"
            },
            "close": {
                "targets": {
                    "头": {"affection": 8, "intimacy": 6},
                    "脸": {"affection": 7, "intimacy": 8, "arousal": 4},
                    "手": {"affection": 6, "intimacy": 5, "trust": 5},
                    "腰": {"intimacy": 10, "arousal": 8, "desire": 5, "shame": -2}
                },
                "intensity": 5,
                "description": "大胆的抚摸"
            },
            "lover": {
                "targets": {
                    "头": {"affection": 9, "intimacy": 7},
                    "脸": {"affection": 8, "intimacy": 10, "arousal": 5},
                    "腰": {"intimacy": 12, "arousal": 10, "desire": 7, "shame": -3},
                    "胸": {"intimacy": 15, "arousal": 15, "desire": 10, "corruption": 5, "shame": -5}
                },
                "intensity": 7,
                "description": "情欲的爱抚"
            }
        },

        # === 挑逗系 (close→lover) ===
        "诱惑": {
            "command": ["诱惑", "撩"],
            "type": "seductive",
            "stranger": {
                "blocked": True,
                "reason": "她会觉得你很轻浮"
            },
            "friend": {
                "effects": {"intimacy": 4, "desire": 3, "arousal": 2, "resistance": -2},
                "intensity": 4,
                "description": "轻微的言语挑逗"
            },
            "close": {
                "effects": {"intimacy": 6, "desire": 6, "arousal": 6, "corruption": 3, "resistance": -4, "shame": -3},
                "intensity": 6,
                "description": "大胆的挑逗"
            },
            "lover": {
                "effects": {"intimacy": 8, "desire": 10, "arousal": 10, "corruption": 5, "resistance": -6, "shame": -5},
                "intensity": 7,
                "description": "露骨的言语挑逗"
            }
        },

        "挑逗": {
            "command": ["挑逗", "撩拨"],
            "type": "seductive",
            "stranger": {
                "blocked": True,
                "reason": "太唐突了"
            },
            "friend": {
                "blocked": True,
                "reason": "关系还不够亲密"
            },
            "close": {
                "effects": {"intimacy": 8, "desire": 8, "arousal": 8, "corruption": 4, "resistance": -5, "shame": -4},
                "intensity": 6,
                "description": "肢体挑逗"
            },
            "lover": {
                "effects": {"intimacy": 10, "desire": 12, "arousal": 12, "corruption": 6, "resistance": -7, "shame": -6},
                "intensity": 8,
                "description": "充满暗示的挑逗"
            }
        },

        "脱衣": {
            "command": ["脱", "脱衣", "脱掉"],
            "type": "seductive",
            "stranger": {
                "blocked": True,
                "reason": "她会立刻离开"
            },
            "friend": {
                "blocked": True,
                "reason": "太快了,她不会答应"
            },
            "close": {
                "effects": {"intimacy": 10, "arousal": 10, "desire": 8, "corruption": 5, "shame": -6, "resistance": -5},
                "intensity": 7,
                "description": "缓缓脱去衣物"
            },
            "lover": {
                "effects": {"intimacy": 12, "arousal": 15, "desire": 12, "corruption": 7, "shame": -8, "resistance": -7},
                "intensity": 9,
                "description": "大胆地褪去衣物"
            }
        },

        # === 强势系 ===
        "壁咚": {
            "command": ["壁咚"],
            "type": "dominant",
            "stranger": {
                "blocked": True,
                "reason": "她会被吓到"
            },
            "friend": {
                "effects": {"intimacy": 5, "arousal": 5, "desire": 3, "submission": 3},
                "intensity": 5,
                "description": "突然的壁咚"
            },
            "close": {
                "effects": {"intimacy": 8, "arousal": 10, "desire": 7, "submission": 6, "corruption": 3},
                "intensity": 7,
                "description": "强势的壁咚"
            },
            "lover": {
                "effects": {"intimacy": 10, "arousal": 12, "desire": 10, "submission": 8, "corruption": 5},
                "intensity": 8,
                "description": "霸道的壁咚"
            }
        },

        "推倒": {
            "command": ["推倒", "扑倒"],
            "type": "dominant",
            "stranger": {
                "blocked": True,
                "reason": "这是犯罪！"
            },
            "friend": {
                "blocked": True,
                "reason": "她会生气地推开你"
            },
            "close": {
                "effects": {"intimacy": 10, "arousal": 12, "desire": 10, "submission": 8, "corruption": 5, "resistance": -6},
                "intensity": 8,
                "description": "将她推倒在床上"
            },
            "lover": {
                "effects": {"intimacy": 12, "arousal": 18, "desire": 15, "submission": 10, "corruption": 8, "resistance": -10},
                "intensity": 9,
                "description": "霸道地将她压倒"
            }
        },

        "命令": {
            "command": ["命令", "要求"],
            "type": "dominant",
            "stranger": {
                "blocked": True,
                "reason": "她凭什么听你的？"
            },
            "friend": {
                "blocked": True,
                "reason": "关系不足以让她服从"
            },
            "close": {
                "effects": {"submission": 8, "corruption": 4, "resistance": -5, "shame": -3},
                "intensity": 6,
                "description": "发出命令"
            },
            "lover": {
                "effects": {"submission": 12, "corruption": 6, "resistance": -8, "shame": -5, "desire": 3},
                "intensity": 7,
                "description": "强势的命令"
            }
        },

        # === 深度系 ===
        "舔舐": {
            "command": ["舔", "舔舐"],
            "type": "corrupting",
            "has_targets": True,
            "stranger": {
                "blocked": True,
                "reason": "..."
            },
            "friend": {
                "blocked": True,
                "reason": "太过分了！"
            },
            "close": {
                "targets": {
                    "耳朵": {"intimacy": 12, "arousal": 12, "desire": 8, "corruption": 5, "shame": -5},
                    "脖子": {"intimacy": 15, "arousal": 15, "desire": 10, "corruption": 6, "shame": -6}
                },
                "intensity": 8,
                "description": "舔舐敏感部位"
            },
            "lover": {
                "targets": {
                    "耳朵": {"intimacy": 15, "arousal": 15, "desire": 10, "corruption": 6, "shame": -6},
                    "脖子": {"intimacy": 18, "arousal": 18, "desire": 12, "corruption": 8, "shame": -7},
                    "身体": {"intimacy": 20, "arousal": 22, "desire": 15, "corruption": 10, "shame": -10}
                },
                "intensity": 9,
                "description": "充满欲望的舔舐"
            }
        },

        "侵犯": {
            "command": ["侵犯", "进攻"],
            "type": "corrupting",
            "stranger": {
                "blocked": True,
                "reason": "报警了"
            },
            "friend": {
                "blocked": True,
                "reason": "关系崩溃！"
            },
            "close": {
                "blocked": True,
                "reason": "她强烈抵抗"
            },
            "lover": {
                "effects": {"intimacy": 20, "arousal": 25, "desire": 20, "corruption": 15, "submission": 10, "shame": -15, "resistance": -15},
                "intensity": 10,
                "description": "深度的侵犯"
            }
        },

        "调教": {
            "command": ["调教", "训练"],
            "type": "corrupting",
            "stranger": {
                "blocked": True,
                "reason": "..."
            },
            "friend": {
                "blocked": True,
                "reason": "她会报警"
            },
            "close": {
                "blocked": True,
                "reason": "她不会接受"
            },
            "lover": {
                "requirements": {"corruption": 50, "submission": 60},
                "effects": {"submission": 15, "corruption": 12, "desire": 10, "arousal": 15, "shame": -20, "resistance": -20},
                "intensity": 10,
                "description": "深度调教"
            }
        }
    }

    @staticmethod
    def get_action_by_stage(action_key: str, character: Dict) -> Tuple[bool, Dict, str]:
        """
        根据关系阶段获取动作配置

        返回: (是否可用, 动作配置, 阶段名称)
        """
        if action_key not in ActionGrowthSystem.CORE_ACTIONS:
            return False, {}, ""

        # 获取关系阶段
        from .daily_limit_system import DailyInteractionSystem
        stage = DailyInteractionSystem.get_relationship_stage(character)

        action_def = ActionGrowthSystem.CORE_ACTIONS[action_key]
        stage_config = action_def.get(stage, {})

        # 检查该阶段是否被阻止
        if stage_config.get("blocked", False):
            return False, stage_config, stage

        return True, stage_config, stage

    @staticmethod
    def get_commands_for_action(action_key: str) -> list:
        """获取动作的所有命令别名"""
        if action_key not in ActionGrowthSystem.CORE_ACTIONS:
            return []
        return ActionGrowthSystem.CORE_ACTIONS[action_key].get("command", [])

    @staticmethod
    def find_action_by_command(command: str) -> str:
        """根据命令找到对应的动作key"""
        for action_key, action_def in ActionGrowthSystem.CORE_ACTIONS.items():
            if command in action_def.get("command", []):
                return action_key
        return None

    @staticmethod
    def get_all_available_actions(character: Dict) -> list:
        """获取当前阶段所有可用的动作"""
        from .daily_limit_system import DailyInteractionSystem
        stage = DailyInteractionSystem.get_relationship_stage(character)

        available = []
        for action_key, action_def in ActionGrowthSystem.CORE_ACTIONS.items():
            stage_config = action_def.get(stage, {})
            if not stage_config.get("blocked", False):
                commands = action_def.get("command", [])
                if commands:
                    available.append({
                        "key": action_key,
                        "command": commands[0],  # 使用第一个命令作为主命令
                        "type": action_def.get("type", "unknown"),
                        "intensity": stage_config.get("intensity", 5)
                    })

        return sorted(available, key=lambda x: x["intensity"])
