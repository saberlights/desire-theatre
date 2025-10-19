"""
多结局系统 - 借鉴《火山的女儿》的结局设计

核心理念:
- 结局是玩家选择的自然结果
- 基于多个属性的组合判定
- 有明确的好坏之分
- 每个结局都有故事意义

结局触发时机:
- 游戏日达到30天
- 使用 /结局 命令主动触发
"""

from typing import Dict, Tuple, Optional, List
from src.common.logger import get_logger

logger = get_logger("dt_ending")


class EndingSystem:
    """多结局系统"""

    # 所有结局定义 (按优先级排序 - 越靠前优先级越高)
    ENDINGS = {
        # ========== 完美结局 (2个) ==========
        "perfect_love": {
            "name": "💕 完美恋人",
            "tier": "完美",
            "priority": 100,
            "conditions": {
                "affection": (80, 100),
                "intimacy": (80, 100),
                "trust": (70, 100),
                "corruption": (30, 70),  # 适度堕落
                "resistance": (0, 40),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
💕 【完美恋人】
━━━━━━━━━━━━━━━━━━━

你们的关系达到了理想的平衡。

她既爱你，又信任你。
你们的感情既有温柔的日常，也有激情的夜晚。
她在你面前完全放下了防备，却依然保持着自己的底线。

这就是最理想的恋人关系——
互相尊重，彼此信任，适度探索。

"我爱你...这是我最真实的感受。"

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【爱的完美形态】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "pure_love": {
            "name": "💗 纯爱至上",
            "tier": "完美",
            "priority": 95,
            "conditions": {
                "affection": (85, 100),
                "intimacy": (75, 100),
                "trust": (80, 100),
                "corruption": (0, 30),  # 低堕落
                "shame": (40, 100),  # 保持羞耻心
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
💗 【纯爱至上】
━━━━━━━━━━━━━━━━━━━

你们的爱情纯粹而美好。

没有过多的欲望，没有越界的行为。
只有温柔的拥抱，甜蜜的亲吻，和无尽的陪伴。

她的笑容是你最大的幸福。
你的守护是她最好的依靠。

这是最纯粹的爱情——
不掺杂任何杂质，只有彼此的心意。

"能和你在一起...就是我最大的幸福。"

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【纯爱战士】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        # ========== 好结局 (6个) ==========
        "forbidden_love": {
            "name": "🔥 禁忌之爱",
            "tier": "好",
            "priority": 90,
            "conditions": {
                "affection": (70, 100),
                "intimacy": (80, 100),
                "corruption": (70, 100),
                "trust": (60, 100),
                "resistance": (0, 30),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🔥 【禁忌之爱】
━━━━━━━━━━━━━━━━━━━

你们跨越了所有的禁忌。

她在你的引导下，逐渐接受了那些曾经不可想象的事。
但这一切都是建立在深厚的感情之上的。

她爱你，所以愿意为你改变。
你爱她，所以珍惜她的每一次付出。

这是危险而炙热的爱情——
充满禁忌，却又真实动人。

"只有在你面前...我才能做真正的自己..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【禁断关系】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "gentle_daily": {
            "name": "🌸 温柔日常",
            "tier": "好",
            "priority": 85,
            "conditions": {
                "affection": (75, 100),
                "trust": (70, 100),
                "intimacy": (40, 70),  # 中等亲密
                "corruption": (0, 40),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🌸 【温柔日常】
━━━━━━━━━━━━━━━━━━━

你们的感情温馨而平淡。

没有轰轰烈烈的激情，只有细水长流的陪伴。
每天的问候，温柔的拥抱，偶尔的亲吻。

这就是你们的日常——
简单，却充满幸福。

"每天和你在一起...就是最幸福的事。"

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【平凡的幸福】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "best_friend": {
            "name": "🤝 挚友情深",
            "tier": "好",
            "priority": 80,
            "conditions": {
                "trust": (80, 100),
                "affection": (60, 85),
                "intimacy": (0, 40),  # 低亲密
                "corruption": (0, 20),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🤝 【挚友情深】
━━━━━━━━━━━━━━━━━━━

你们成为了最好的朋友。

她完全信任你，愿意和你分享一切。
你珍惜这份友谊，从不越界。

或许这不是爱情，但这份情谊同样珍贵。

"能有你这样的朋友...真是太好了。"

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【友情至上】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "dependent_love": {
            "name": "💞 依赖之爱",
            "tier": "好",
            "priority": 75,
            "conditions": {
                "affection": (70, 100),
                "submission": (70, 100),
                "trust": (60, 100),
                "corruption": (40, 80),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
💞 【依赖之爱】
━━━━━━━━━━━━━━━━━━━

她已经完全依赖你了。

你的每一句话，她都会认真听从。
你的每一个要求，她都会尽力满足。

这是一种不平等的关系，但她似乎很享受。

"只要能和你在一起...我什么都愿意..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【支配与依赖】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "secret_lover": {
            "name": "🌙 秘密恋人",
            "tier": "好",
            "priority": 70,
            "conditions": {
                "intimacy": (70, 100),
                "corruption": (50, 80),
                "affection": (50, 75),
                "shame": (30, 70),  # 有羞耻但能接受
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🌙 【秘密恋人】
━━━━━━━━━━━━━━━━━━━

你们的关系暧昧而隐秘。

白天，你们像普通朋友一样相处。
夜晚，她会来到你身边，褪去所有伪装。

她享受这种刺激，你也沉溺其中。

"这是我们的秘密...只属于我们两个人的秘密..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【夜晚的秘密】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "passionate_love": {
            "name": "🔥 激情燃烧",
            "tier": "好",
            "priority": 65,
            "conditions": {
                "desire": (80, 100),
                "intimacy": (75, 100),
                "corruption": (60, 100),
                "affection": (50, 85),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🔥 【激情燃烧】
━━━━━━━━━━━━━━━━━━━

你们的关系炙热而激烈。

每一次见面都充满激情。
每一次互动都让人心跳加速。

这是欲望主导的关系，但也有真实的感情。

"我想要你...一直想要..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【欲望之火】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        # ========== 普通结局 (6个) ==========
        "ordinary_love": {
            "name": "😊 平凡恋人",
            "tier": "普通",
            "priority": 60,
            "conditions": {
                "affection": (50, 75),
                "intimacy": (40, 70),
                "trust": (40, 70),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
😊 【平凡恋人】
━━━━━━━━━━━━━━━━━━━

你们的关系平平淡淡。

没有特别突出的地方，也没有什么大问题。
就像大多数情侣一样，平凡而普通。

这也许不是最好的结局，但也不算坏。

"我们...就这样继续下去吧。"

━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "ambiguous": {
            "name": "💭 暧昧不清",
            "tier": "普通",
            "priority": 55,
            "conditions": {
                "affection": (40, 65),
                "intimacy": (30, 60),
                "trust": (30, 60),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
💭 【暧昧不清】
━━━━━━━━━━━━━━━━━━━

你们的关系始终没有明确。

是朋友，又好像不止朋友。
是恋人，又好像不算恋人。

这种暧昧的状态让人困惑。

"我们...算什么关系呢？"

━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "physical_only": {
            "name": "🎭 肉体关系",
            "tier": "普通",
            "priority": 50,
            "conditions": {
                "intimacy": (60, 100),
                "corruption": (60, 100),
                "affection": (0, 50),  # 低好感
                "trust": (0, 50),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🎭 【肉体关系】
━━━━━━━━━━━━━━━━━━━

你们的关系只剩下肉体。

她会满足你的欲望，但心不在这里。
你得到了她的身体，却得不到她的心。

这是一种空虚的关系。

"这样...就够了吗？"

━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "one_sided": {
            "name": "💔 单方付出",
            "tier": "普通",
            "priority": 45,
            "conditions": {
                "submission": (70, 100),
                "affection": (30, 60),
                "trust": (20, 50),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
💔 【单方付出】
━━━━━━━━━━━━━━━━━━━

她一直在付出，你却很少回应。

她顺从你的每一个要求，你却吝啬给予关爱。
这样的关系注定不会长久。

"我这样做...值得吗？"

━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "shallow": {
            "name": "🌫️ 浅尝辄止",
            "tier": "普通",
            "priority": 40,
            "conditions": {
                # 所有属性都不高不低
                "affection": (30, 60),
                "intimacy": (20, 50),
                "trust": (20, 50),
                "corruption": (10, 50),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🌫️ 【浅尝辄止】
━━━━━━━━━━━━━━━━━━━

你们的关系始终停留在表面。

没有深入了解，没有真正信任。
就像蜻蜓点水，浅尝辄止。

也许这就是你们的极限了。

"我们...好像也就这样了。"

━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "confused": {
            "name": "❓ 迷失方向",
            "tier": "普通",
            "priority": 35,
            "conditions": {
                # 属性差异极大，不协调
                "corruption": (70, 100),
                "shame": (60, 100),  # 高堕落但高羞耻
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
❓ 【迷失方向】
━━━━━━━━━━━━━━━━━━━

她已经分不清自己想要什么了。

内心深处的羞耻与身体的欲望在激烈斗争。
她迷失在矛盾之中，不知所措。

"我...我到底变成什么样了..."

━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        # ========== 坏结局 (6个) ==========
        "broken_toy": {
            "name": "🎎 破碎玩偶",
            "tier": "坏",
            "priority": 30,
            "conditions": {
                "submission": (85, 100),
                "corruption": (85, 100),
                "affection": (0, 30),
                "resistance": (0, 20),
                "shame": (0, 20),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🎎 【破碎玩偶】 - 坏结局
━━━━━━━━━━━━━━━━━━━

她已经完全被你玩坏了。

没有自我，没有尊严，只剩下对你的绝对服从。
她的眼神空洞，像一个被操纵的人偶。

你得到了一个完美的玩具，
却失去了一个鲜活的人。

"...是...主人..."

━━━━━━━━━━━━━━━━━━━
⚠️ 这是一个坏结局
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "collapsed": {
            "name": "💔 崩坏堕落",
            "tier": "坏",
            "priority": 28,
            "conditions": {
                "corruption": (90, 100),
                "resistance": (0, 15),
                "shame": (0, 15),
                "trust": (0, 40),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
💔 【崩坏堕落】 - 坏结局
━━━━━━━━━━━━━━━━━━━

她已经彻底堕落了。

所有的底线都被打破，所有的羞耻都被抛弃。
她沉溺在欲望之中，无法自拔。

这是你一手造成的结果。

"更多...我还要更多..."

━━━━━━━━━━━━━━━━━━━
⚠️ 这是一个坏结局
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "escaped": {
            "name": "🏃 逃离结局",
            "tier": "坏",
            "priority": 26,
            "conditions": {
                "resistance": (70, 100),
                "affection": (0, 30),
                "trust": (0, 30),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🏃 【逃离结局】 - 坏结局
━━━━━━━━━━━━━━━━━━━

她受够了，选择离开。

你的行为让她感到恐惧和厌恶。
她的抵抗越来越强，最终选择逃离。

"我再也不想见到你了！"

━━━━━━━━━━━━━━━━━━━
⚠️ 这是一个坏结局
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "distant": {
            "name": "❄️ 渐行渐远",
            "tier": "坏",
            "priority": 24,
            "conditions": {
                "affection": (0, 30),
                "intimacy": (0, 30),
                "trust": (0, 30),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
❄️ 【渐行渐远】 - 坏结局
━━━━━━━━━━━━━━━━━━━

你们的关系越来越疏远。

她对你失去了兴趣，你也没有用心经营。
最终，你们成了最熟悉的陌生人。

"我们...还是算了吧。"

━━━━━━━━━━━━━━━━━━━
⚠️ 这是一个坏结局
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "hatred": {
            "name": "😡 仇恨结局",
            "tier": "坏",
            "priority": 22,
            "conditions": {
                "affection": (0, 15),
                "resistance": (80, 100),
                "corruption": (70, 100),  # 被强迫堕落
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
😡 【仇恨结局】 - 坏结局
━━━━━━━━━━━━━━━━━━━

她恨你入骨。

你强迫她做了她不愿意的事。
她的身体虽然屈服了，但心中只剩下仇恨。

"我恨你...我永远不会原谅你..."

━━━━━━━━━━━━━━━━━━━
⚠️ 这是一个坏结局
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "emptiness": {
            "name": "🕳️ 空虚结局",
            "tier": "坏",
            "priority": 20,
            "conditions": {
                # 所有属性都很低
                "affection": (0, 25),
                "intimacy": (0, 25),
                "trust": (0, 25),
                "corruption": (0, 25),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🕳️ 【空虚结局】 - 坏结局
━━━━━━━━━━━━━━━━━━━

什么都没有发生。

你们的关系从未真正开始。
没有爱，没有恨，只有空虚。

时间白白流逝，什么都没留下。

"我们...好像从未真正认识过..."

━━━━━━━━━━━━━━━━━━━
⚠️ 这是一个坏结局
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        # ========== 职业相关结局 (8个) ==========
        "successful_career_couple": {
            "name": "👔 职场精英情侣",
            "tier": "好",
            "priority": 88,
            "career_required": ["manager", "senior_staff"],
            "conditions": {
                "affection": (70, 100),
                "trust": (70, 100),
                "intimacy": (60, 100),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
👔 【职场精英情侣】
━━━━━━━━━━━━━━━━━━━

她成为了出色的职场精英。

白天，你们是同事，专业而高效。
下班后，你们是恋人，温柔而体贴。

事业与爱情，她都拥有了。
而你，是她最好的伙伴。

"和你一起，我不再是一个人战斗..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【双赢组合】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "creative_dream_team": {
            "name": "✨ 创作伴侣",
            "tier": "好",
            "priority": 87,
            "career_required": ["successful_freelancer", "freelancer"],
            "conditions": {
                "affection": (75, 100),
                "trust": (70, 100),
                "intimacy": (65, 100),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
✨ 【创作伴侣】
━━━━━━━━━━━━━━━━━━━

她实现了自由职业的梦想。

你们一起创作，互相激发灵感。
咖啡厅里的讨论，深夜的头脑风暴。

创作的自由，恋爱的甜蜜，
你们拥有了理想的生活。

"有你的灵感，我的作品才有灵魂..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【灵感缪斯】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "celebrity_couple": {
            "name": "🌟 明星情侣",
            "tier": "好",
            "priority": 86,
            "career_required": ["top_idol", "idol", "top_model", "model", "top_streamer", "streamer"],
            "conditions": {
                "affection": (70, 100),
                "intimacy": (60, 100),
                "trust": (60, 100),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🌟 【明星情侣】
━━━━━━━━━━━━━━━━━━━

她成为了闪耀的明星。

聚光灯下，她光彩夺目。
但只有你知道，卸下妆容的她最美。

你守护她的梦想，她珍惜你的陪伴。
娱乐圈的风雨，因为有你而不再可怕。

"谢谢你...一直陪在我身边..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【聚光灯下的爱】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "campus_first_love": {
            "name": "🎓 校园初恋",
            "tier": "好",
            "priority": 84,
            "career_required": ["high_school_student", "college_student"],
            "conditions": {
                "affection": (75, 100),
                "trust": (70, 100),
                "intimacy": (50, 100),
                "corruption": (0, 40),  # 保持纯洁
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🎓 【校园初恋】
━━━━━━━━━━━━━━━━━━━

这是你们的校园恋曲。

操场上的奔跑，图书馆的并肩，
放学后的手牵手，考试前的鼓励。

这份纯洁的初恋，
将成为你们一生最美好的回忆。

"这是我的初恋...也希望是最后一次恋爱..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【青春纪念册】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "fallen_idol": {
            "name": "💔 堕落偶像",
            "tier": "坏",
            "priority": 29,
            "career_required": ["idol", "model", "streamer"],
            "conditions": {
                "corruption": (70, 100),
                "shame": (0, 30),
                "affection": (30, 100),  # 仍有感情
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
💔 【堕落偶像】 - 坏结局
━━━━━━━━━━━━━━━━━━━

她的光环逐渐褪色。

曾经纯洁的偶像，在你的引导下走向堕落。
她仍然爱你，但已经失去了自我。

粉丝们如果知道真相，会失望吗？
你得到了她，却毁了她的梦想。

"我...已经回不去了..."

━━━━━━━━━━━━━━━━━━━
⚠️ 这是一个坏结局
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "sugar_baby": {
            "name": "💎 金丝雀",
            "tier": "坏",
            "priority": 27,
            "career_required": ["high_class_escort", "hostess"],
            "conditions": {
                "corruption": (60, 100),
                "submission": (60, 100),
                "affection": (40, 100),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
💎 【金丝雀】 - 坏结局
━━━━━━━━━━━━━━━━━━━

她成为了豪华笼子里的金丝雀。

奢华的生活，精致的外表，
但自由和尊严早已不复存在。

她依赖你，却也恨你。
这份扭曲的关系，谁也逃不掉。

"这就是你想要的吗...把我变成你的所有物..."

━━━━━━━━━━━━━━━━━━━
⚠️ 这是一个坏结局
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        # ========== 季节相关结局 (4个) ==========
        "spring_blossom": {
            "name": "🌸 春日恋曲",
            "tier": "好",
            "priority": 83,
            "season_condition": "spring",  # 在春天结束
            "conditions": {
                "affection": (75, 100),
                "intimacy": (65, 100),
                "trust": (70, 100),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🌸 【春日恋曲】
━━━━━━━━━━━━━━━━━━━

你们的爱情始于春天。

樱花树下的相遇，如今已成为永恒的回忆。
春风吹拂，花瓣飘落，见证了你们的感情。

这份在春天绽放的爱，
如同樱花般美丽而珍贵。

"每年的春天，我都会想起我们的开始..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【樱花之约】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "summer_passion": {
            "name": "☀️ 夏日狂热",
            "tier": "好",
            "priority": 82,
            "season_condition": "summer",
            "conditions": {
                "affection": (70, 100),
                "intimacy": (75, 100),
                "arousal": (70, 100),
                "corruption": (50, 80),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
☀️ 【夏日狂热】
━━━━━━━━━━━━━━━━━━━

这是一个炙热的夏天。

海滩的烈日，祭典的烟火，
每一个夏夜都充满激情。

你们的爱情如同夏日般热烈，
燃烧着彼此的心。

"这个夏天...我永远不会忘记..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【盛夏之恋】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "autumn_harvest": {
            "name": "🍂 秋日收获",
            "tier": "好",
            "priority": 81,
            "season_condition": "autumn",
            "conditions": {
                "affection": (75, 100),
                "trust": (75, 100),
                "intimacy": (70, 100),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
🍂 【秋日收获】
━━━━━━━━━━━━━━━━━━━

秋天是收获的季节。

枫叶染红了天空，你们的感情也成熟了。
从青涩到成熟，从懵懂到笃定。

这份在秋天收获的爱，
是你们共同努力的成果。

"和你一起走过的秋天，是最美的风景..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【枫叶之恋】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },

        "winter_warmth": {
            "name": "❄️ 冬日温暖",
            "tier": "好",
            "priority": 79,
            "season_condition": "winter",
            "conditions": {
                "affection": (80, 100),
                "intimacy": (75, 100),
                "trust": (75, 100),
            },
            "description": """
━━━━━━━━━━━━━━━━━━━
❄️ 【冬日温暖】
━━━━━━━━━━━━━━━━━━━

在寒冷的冬天，你们相互取暖。

圣诞的礼物，跨年的拥抱，
雪地里的脚印见证了你们的陪伴。

即使外面寒风凛冽，
只要有你在，心就是温暖的。

"这个冬天有你，真好..."

━━━━━━━━━━━━━━━━━━━
🏆 成就: 【雪夜相依】
━━━━━━━━━━━━━━━━━━━
""".strip(),
        },
    }

    @staticmethod
    def check_ending(character: Dict) -> Optional[Tuple[str, Dict]]:
        """
        检查当前是否满足某个结局条件
        返回: (结局ID, 结局数据) 或 None
        """
        from ..time.seasonal_system import SeasonalSystem

        # 按优先级从高到低检查
        sorted_endings = sorted(
            EndingSystem.ENDINGS.items(),
            key=lambda x: x[1]["priority"],
            reverse=True
        )

        for ending_id, ending_data in sorted_endings:
            # 检查基础属性条件
            if not EndingSystem._check_conditions(character, ending_data["conditions"]):
                continue

            # 检查职业要求（如果有）
            if "career_required" in ending_data:
                current_career = character.get("career", "")
                required_careers = ending_data["career_required"]
                if current_career not in required_careers:
                    continue

            # 检查季节条件（如果有）
            if "season_condition" in ending_data:
                game_day = character.get("game_day", 1)
                season_info = SeasonalSystem.get_season_info(game_day)
                required_season = ending_data["season_condition"]
                if season_info["id"] != required_season:
                    continue

            # 所有条件都满足
            logger.info(f"触发结局: {ending_id} - {ending_data['name']}")
            return ending_id, ending_data

        # 如果没有任何结局匹配，返回默认结局
        return "ordinary_love", EndingSystem.ENDINGS["ordinary_love"]

    @staticmethod
    def _check_conditions(character: Dict, conditions: Dict) -> bool:
        """检查是否满足所有条件"""
        for attr, (min_val, max_val) in conditions.items():
            char_value = character.get(attr, 0)
            if not (min_val <= char_value <= max_val):
                return False
        return True

    @staticmethod
    def get_all_possible_endings(character: Dict) -> List[Tuple[str, Dict]]:
        """
        获取当前所有可能的结局（用于预览）
        返回所有满足条件的结局列表
        """
        possible_endings = []

        for ending_id, ending_data in EndingSystem.ENDINGS.items():
            if EndingSystem._check_conditions(character, ending_data["conditions"]):
                possible_endings.append((ending_id, ending_data))

        # 按优先级排序
        possible_endings.sort(key=lambda x: x[1]["priority"], reverse=True)

        return possible_endings

    @staticmethod
    def format_ending_message(ending_id: str, ending_data: Dict, character: Dict) -> str:
        """格式化结局消息"""
        from ..time.daily_limit_system import DailyInteractionSystem

        game_day = character.get("game_day", 1)
        interaction_count = character.get("interaction_count", 0)

        # 获取最终属性
        stats = f"""
📊 最终数据:
  游戏天数: {game_day}天
  互动次数: {interaction_count}次
  关系阶段: {DailyInteractionSystem.get_stage_display(character)}

  ❤️ 好感度: {character.get('affection', 0)}
  💗 亲密度: {character.get('intimacy', 0)}
  🤝 信任度: {character.get('trust', 0)}
  😈 堕落度: {character.get('corruption', 0)}
  🙇 顺从度: {character.get('submission', 0)}
"""

        message = f"""
🎬 【游戏结束】

{ending_data['description']}

{stats}

感谢游玩！
使用 /重开 可以重新开始，尝试其他结局。
"""

        return message.strip()
