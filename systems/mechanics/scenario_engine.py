"""
情境触发引擎
"""

import time
import random
from typing import Dict, List
from datetime import datetime


class ScenarioEngine:
    """情境触发引擎"""

    # 情境定义库
    SCENARIOS = {
        "first_touch": {
            "name": "初次触碰",
            "conditions": {"affection": 30, "intimacy": 10, "arousal": 20},
            "probability": 0.8,
            "content_template": "不经意间，你的手碰到了她的手..."
        },

        "late_night_call": {
            "name": "深夜来电",
            "conditions": {"intimacy": 40, "desire": 30},
            "time_condition": lambda: 22 <= datetime.now().hour or datetime.now().hour <= 2,
            "probability": 0.7,
            "content_template": "已经很晚了，她突然发来消息..."
        },

        "jealousy": {
            "name": "吃醋事件",
            "conditions": {"affection": 50},
            "trigger_condition": lambda char: (time.time() - char["last_interaction"]) > 86400,
            "probability": 0.8,
            "content_template": "你好久没理她了..."
        },

        "resistance_break": {
            "name": "抵抗崩溃",
            "conditions": {"resistance": "<40", "arousal": 60},
            "probability": 0.9,
            "content_template": "她的抵抗终于崩溃了..."
        },

        "shame_challenge": {
            "name": "羞耻挑战",
            "conditions": {"shame": "<60", "trust": 40},
            "probability": 0.7,
            "content_template": "她提出了一个大胆的提议..."
        },

        "corruption_milestone": {
            "name": "堕落里程碑",
            "conditions": {"corruption": 30},
            "trigger_once": True,
            "probability": 1.0,
            "content_template": "她已经不是当初的样子了..."
        },

        # 新增随机事件
        "high_arousal_loss_control": {
            "name": "失控边缘",
            "conditions": {"arousal": 80},
            "probability": 0.3,
            "content_template": "她的身体开始失控，呼吸变得急促..."
        },

        "shame_breakdown": {
            "name": "羞耻崩溃",
            "conditions": {"shame": "<10"},
            "probability": 0.5,
            "content_template": "她已经完全放开了羞耻心，不再掩饰自己的欲望..."
        },

        "submission_awakening": {
            "name": "顺从觉醒",
            "conditions": {"submission": 70, "corruption": 40},
            "probability": 0.4,
            "content_template": "她开始享受这种被支配的感觉..."
        },

        "desire_overflow": {
            "name": "欲望溢出",
            "conditions": {"desire": 80, "arousal": 70},
            "probability": 0.6,
            "content_template": "她的欲望已经到了难以抑制的地步..."
        },

        "trust_deepening": {
            "name": "信任深化",
            "conditions": {"trust": 80, "intimacy": 60},
            "probability": 0.5,
            "content_template": "她对你的信任达到了前所未有的程度..."
        },

        "moral_struggle": {
            "name": "道德挣扎",
            "conditions": {"corruption": 40, "shame": 40},
            "probability": 0.3,
            "content_template": "她在道德底线和欲望之间激烈挣扎..."
        },

        "body_awakening": {
            "name": "身体觉醒",
            "conditions": {"intimacy": 50, "arousal": 60, "shame": "<70"},
            "probability": 0.4,
            "content_template": "她的身体开始觉醒，对你的触碰变得异常敏感..."
        },

        "initiative_change": {
            "name": "主动转变",
            "conditions": {"submission": 60, "desire": 70},
            "probability": 0.5,
            "content_template": "她第一次主动表达了自己的渴望..."
        }
    }

    @staticmethod
    def check_scenario_triggers(character: Dict) -> List[Dict]:
        """检查可触发的情境"""
        triggered = []

        for scenario_id, scenario_def in ScenarioEngine.SCENARIOS.items():
            # 检查基础条件
            conditions_met = True
            conditions = scenario_def.get("conditions", {})

            for attr, required in conditions.items():
                if isinstance(required, str) and required.startswith("<"):
                    # 小于条件
                    threshold = int(required[1:])
                    if character.get(attr, 0) >= threshold:
                        conditions_met = False
                        break
                else:
                    # 大于等于条件
                    threshold = int(required)
                    if character.get(attr, 0) < threshold:
                        conditions_met = False
                        break

            if not conditions_met:
                continue

            # 检查时间条件
            if "time_condition" in scenario_def:
                if not scenario_def["time_condition"]():
                    continue

            # 检查自定义触发条件
            if "trigger_condition" in scenario_def:
                if not scenario_def["trigger_condition"](character):
                    continue

            # 概率判定
            probability = scenario_def.get("probability", 0.5)
            if random.random() < probability:
                triggered.append({
                    "scenario_id": scenario_id,
                    "scenario_name": scenario_def["name"],
                    "content_template": scenario_def["content_template"]
                })

        return triggered
