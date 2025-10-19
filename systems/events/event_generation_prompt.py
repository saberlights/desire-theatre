"""
事件生成 Prompt 模板

用于通过 LLM 动态生成随机事件和选择困境的文本内容
"""

from typing import Dict, List


class EventGenerationPrompt:
    """事件生成 Prompt 构建器"""

    @staticmethod
    def build_dynamic_event_prompt(
        character: Dict,
        history: List[Dict] = None
    ) -> str:
        """
        构建完全动态的事件生成 Prompt（包括事件类型、选项、效果）

        Args:
            character: 角色数据
            history: 对话历史

        Returns:
            完整的 prompt
        """
        personality_type = character.get("personality_type", "tsundere")
        affection = character.get("affection", 0)
        intimacy = character.get("intimacy", 0)
        trust = character.get("trust", 0)
        corruption = character.get("corruption", 0)
        submission = character.get("submission", 0)
        desire = character.get("desire", 0)
        shame = character.get("shame", 0)
        resistance = character.get("resistance", 0)
        game_day = character.get("game_day", 1)
        career = character.get("career", "高中生")
        coins = character.get("coins", 100)

        # 构建关系阶段描述
        if intimacy < 20:
            relationship = "陌生人阶段"
        elif intimacy < 50:
            relationship = "朋友阶段"
        elif intimacy < 80:
            relationship = "亲密阶段"
        else:
            relationship = "恋人阶段"

        # 构建历史对话上下文
        history_context = ""
        if history:
            recent_interactions = []
            for h in history[-5:]:
                if h.get("user"):
                    recent_interactions.append(f"玩家: {h['user']}")
                if h.get("assistant"):
                    recent_interactions.append(f"角色: {h['assistant']}")
            if recent_interactions:
                history_context = f"""
最近的互动记录:
{chr(10).join(recent_interactions)}
"""

        prompt = f"""你是一个专业的互动游戏设计师，正在为恋爱养成游戏设计随机事件。

# 游戏背景
这是一个恋爱养成游戏，玩家与一位少女培养关系。游戏有九维属性系统，通过各种互动和随机事件推进剧情。

# 当前游戏状态
人格类型: {personality_type}
游戏进度: 第{game_day}天 (共42天)
关系阶段: {relationship}
职业: {career}
金币: {coins}

核心属性:
- 好感度: {affection}/100
- 亲密度: {intimacy}/100
- 信任度: {trust}/100
- 堕落度: {corruption}/100
- 顺从度: {submission}/100
- 欲望值: {desire}/100
- 羞耻心: {shame}/100
- 抵抗度: {resistance}/100
{history_context}
# 任务要求
请根据当前状态和历史互动，创造一个**全新的随机事件**。

事件应该：
1. **自然融入当前情境** - 符合角色关系阶段和最近发生的事情
2. **有戏剧性** - 带来意外、冲突或转机
3. **有真实的选择困境** - 选项之间有明显区别和权衡
4. **影响关系发展** - 通过属性变化推动剧情

事件可以涉及（但不限于）：
- 日常生活事件（天气、购物、聚会、节日）
- 人际关系（朋友、家人、前任、陌生人）
- 情感时刻（争吵、和解、表白、误会）
- 意外状况（生病、受伤、迷路、危险）
- 社交场合（约会、聚会、公共场所）
- 个人困境（工作/学业压力、道德选择、心理冲突）

# 输出格式
严格按照以下JSON格式输出：

```json
{{
  "event_name": "事件名称（3-6字）",
  "event_category": "事件类别（social/work/romance/crisis/special之一）",
  "event_emoji": "代表事件的emoji（一个）",
  "story_text": "事件描述（60-120字，描述发生了什么，以她的对话或情境描写结尾）",
  "choices": [
    {{
      "text": "选项1标题（10-20字）",
      "result_text": "选择后的结果（40-80字，包含她的反应）",
      "effects": {{
        "affection": 0,
        "intimacy": 0,
        "trust": 0,
        "corruption": 0,
        "submission": 0,
        "desire": 0,
        "arousal": 0,
        "resistance": 0,
        "shame": 0,
        "coins": 0
      }},
      "requirements": {{}}
    }},
    {{
      "text": "选项2标题",
      "result_text": "选择后的结果",
      "effects": {{
        "affection": 0,
        "intimacy": 0,
        "trust": 0
      }},
      "requirements": {{}}
    }},
    {{
      "text": "选项3标题（可选）",
      "result_text": "选择后的结果",
      "effects": {{}},
      "requirements": {{
        "intimacy": 40
      }}
    }}
  ]
}}
```

# effects 属性变化规则（重要！）
根据选项性质设置合理的数值：

**温柔/关怀选项**: affection +8~15, trust +5~12, intimacy +3~8
**大胆/亲密选项**: intimacy +10~20, arousal +8~15, shame -5~-15, corruption +5~10
**拒绝/冷淡选项**: affection -10~-20, trust -8~-15, resistance +10~20
**顺从/迎合选项**: submission +8~15, affection +5~10, trust可能-3~-8
**挑战/挑逗选项**: desire +10~18, corruption +8~15, shame -8~-15
**花费金币**: coins -20~-100（根据选项设定）
**获得金币**: coins +20~+80

每个选项的 effects 应该：
- 至少影响2-4个属性
- 有正向和负向变化的权衡
- 数值范围 -25 到 +25 之间
- requirements 用于限制高级选项（如 "intimacy": 50 表示需要亲密度≥50）

# 注意事项
1. 事件要**符合当前关系阶段**：
   - 陌生人阶段：日常偶遇、小误会、简单互动
   - 朋友阶段：共同活动、小冲突、渐进亲密
   - 亲密阶段：情感纠葛、深入互动、关系考验
   - 恋人阶段：深层矛盾、激情时刻、未来规划

2. 事件要**与最近互动有关联**（如果有历史）

3. 选项要**有真实的两难**，不要有明显的"最优解"

4. 角色对话加引号「」或""

5. 只输出JSON，不要任何其他文字

6. 确保JSON格式完全正确，可以被解析

现在请生成一个全新的随机事件。
"""

        return prompt.strip()

    @staticmethod
    def build_dynamic_dilemma_prompt(
        character: Dict,
        history: List[Dict] = None
    ) -> str:
        """
        构建完全动态的困境生成 Prompt（包括困境类型、选项、效果）

        Args:
            character: 角色数据
            history: 对话历史

        Returns:
            完整的 prompt
        """
        personality_type = character.get("personality_type", "tsundere")
        affection = character.get("affection", 0)
        intimacy = character.get("intimacy", 0)
        trust = character.get("trust", 0)
        corruption = character.get("corruption", 0)
        submission = character.get("submission", 0)
        desire = character.get("desire", 0)
        shame = character.get("shame", 0)
        resistance = character.get("resistance", 0)
        game_day = character.get("game_day", 1)
        career = character.get("career", "高中生")
        coins = character.get("coins", 100)

        # 构建关系阶段描述
        if intimacy < 20:
            relationship = "陌生人阶段"
        elif intimacy < 50:
            relationship = "朋友阶段"
        elif intimacy < 80:
            relationship = "亲密阶段"
        else:
            relationship = "恋人阶段"

        # 构建历史对话上下文
        history_context = ""
        if history:
            recent_interactions = []
            for h in history[-5:]:
                if h.get("user"):
                    recent_interactions.append(f"玩家: {h['user']}")
                if h.get("assistant"):
                    recent_interactions.append(f"角色: {h['assistant']}")
            if recent_interactions:
                history_context = f"""
最近的互动记录:
{chr(10).join(recent_interactions)}
"""

        prompt = f"""你是一个专业的互动游戏设计师，正在为恋爱养成游戏设计**选择困境**。

# 游戏背景
这是一个恋爱养成游戏，玩家与一位少女培养关系。选择困境是游戏中的关键转折点，强迫玩家做出艰难的决策。

# 当前游戏状态
人格类型: {personality_type}
游戏进度: 第{game_day}天 (共42天)
关系阶段: {relationship}
职业: {career}
金币: {coins}

核心属性:
- 好感度: {affection}/100
- 亲密度: {intimacy}/100
- 信任度: {trust}/100
- 堕落度: {corruption}/100
- 顺从度: {submission}/100
- 欲望值: {desire}/100
- 羞耻心: {shame}/100
- 抵抗度: {resistance}/100
{history_context}
# 任务要求
请根据当前状态和历史互动，创造一个**全新的选择困境**。

选择困境应该：
1. **强迫玩家做出艰难的选择** - 没有完美答案，只有权衡
2. **有深远影响** - 选择会影响关系的未来走向
3. **符合当前关系阶段** - 困境的性质要与亲密度匹配
4. **有情感冲击** - 让玩家感受到选择的重量
5. **与最近互动有关** - 如果有历史记录，困境要有连贯性

困境类型可以涉及（但不限于）：
- 道德冲突（理智vs欲望、原则vs感情）
- 信任危机（真相vs谎言、坦诚vs隐瞒）
- 承诺考验（履行vs违背、付出vs保留）
- 关系分岔（认真vs暧昧、承诺vs自由）
- 牺牲要求（为她付出vs保护自己）
- 忠诚考验（她vs他人、独占vs分享）
- 底线抉择（道德底线vs她的要求）

# 输出格式
严格按照以下JSON格式输出：

```json
{{
  "dilemma_name": "困境名称（3-6字）",
  "dilemma_emoji": "代表困境的emoji（一个）",
  "title": "困境标题（包含emoji，如：💔 【道德的十字路口】）",
  "description": "困境描述（80-150字，描述关键时刻和她的状态，以'现在，你必须做出选择：'或类似引导语结尾）",
  "choices": [
    {{
      "id": "choice_1_id",
      "text": "选项1标题（10-20字）",
      "description": "选项1说明（15-30字，补充说明这个选择的含义）",
      "effects": {{
        "affection": 0,
        "intimacy": 0,
        "trust": 0,
        "corruption": 0,
        "submission": 0,
        "desire": 0,
        "arousal": 0,
        "resistance": 0,
        "shame": 0,
        "coins": 0
      }},
      "consequence_text": "选择后的即时后果（40-80字，包含她的反应）",
      "long_term": "长期影响描述（20-40字，这个选择的深远影响）"
    }},
    {{
      "id": "choice_2_id",
      "text": "选项2标题",
      "description": "选项2说明",
      "effects": {{
        "affection": 0,
        "intimacy": 0,
        "trust": 0
      }},
      "consequence_text": "选择后的即时后果",
      "long_term": "长期影响描述"
    }}
  ]
}}
```

# effects 属性变化规则（重要！）
根据选择的性质设置合理的数值，确保两个选择有明显的权衡：

**示例1 - 道德困境**:
- 选项A（满足欲望）: desire +20, arousal +15, corruption +10, shame -20, trust -15
- 选项B（保护尊严）: trust +25, affection +15, desire -10, arousal -20

**示例2 - 信任危机**:
- 选项A（坦诚真相）: trust +30, affection -25, resistance +20, corruption -15
- 选项B（善意谎言）: affection +20, trust -10, submission +10

**示例3 - 承诺考验**:
- 选项A（履行承诺）: trust +40, affection +30, coins -200
- 选项B（违背承诺）: trust -40, affection -25, resistance +25, coins +0

**效果设置原则**:
- 每个选项应影响 3-6 个属性
- 必须有正向和负向变化的权衡
- 数值范围 -50 到 +50 之间
- 困境越重大，属性变化越大
- 不要有明显的"最优解"

# 注意事项
1. 困境要**符合当前关系阶段**：
   - 陌生人阶段：简单的信任考验、小误会
   - 朋友阶段：友情vs爱情、界限试探
   - 亲密阶段：深层矛盾、道德困境、承诺考验
   - 恋人阶段：关系定义、未来规划、牺牲要求

2. 困境要**与最近互动有关联**（如果有历史）

3. 两个选项要**形成真正的对立**，没有明显的好坏之分

4. 角色对话加引号「」或""

5. 只输出JSON，不要任何其他文字

6. 确保JSON格式完全正确，可以被解析

7. choice_id 使用简短的英文标识符（如 satisfy_desire, protect_dignity）

现在请生成一个全新的选择困境。
"""

        return prompt.strip()

    @staticmethod
    def build_event_prompt(
        event_category: str,
        event_name: str,
        character: Dict,
        history: List[Dict] = None,
        num_choices: int = 2
    ) -> str:
        """
        构建事件生成的 Prompt

        Args:
            event_category: 事件类别 (social/work/health/special)
            event_name: 事件名称
            character: 角色数据
            history: 对话历史
            num_choices: 选项数量（2-4个）

        Returns:
            完整的 prompt
        """
        # 获取角色基本信息
        personality_type = character.get("personality_type", "tsundere")
        affection = character.get("affection", 0)
        intimacy = character.get("intimacy", 0)
        trust = character.get("trust", 0)
        corruption = character.get("corruption", 0)
        submission = character.get("submission", 0)
        game_day = character.get("game_day", 1)

        # 构建关系阶段描述
        if intimacy < 20:
            relationship = "陌生人阶段，刚开始认识"
        elif intimacy < 50:
            relationship = "朋友阶段，已经比较熟悉"
        elif intimacy < 80:
            relationship = "亲密阶段，关系密切"
        else:
            relationship = "恋人阶段，非常亲密"

        # 构建历史对话上下文
        history_context = ""
        if history:
            recent_interactions = []
            for h in history[-3:]:  # 最近3条
                if h.get("user"):
                    recent_interactions.append(f"玩家: {h['user']}")
                if h.get("assistant"):
                    recent_interactions.append(f"角色: {h['assistant']}")
            if recent_interactions:
                history_context = f"""
最近的互动:
{chr(10).join(recent_interactions)}
"""

        # 类别相关的特殊说明
        category_notes = {
            "social": "涉及人际关系、朋友、家人、社交场合等",
            "work": "涉及工作、学习、考试、压力等",
            "health": "涉及身体状况、情绪状态、健康问题等",
            "special": "特殊情境、浪漫时刻、意外状况等"
        }

        category_note = category_notes.get(event_category, "")

        prompt = f"""你是一个专业的互动游戏文案作家，正在为一个恋爱养成游戏生成随机事件。

# 游戏背景
这是一个恋爱养成游戏，玩家正在培养与一位少女的关系。游戏的核心是九维属性系统和选择-后果机制。

# 当前角色状态
人格类型: {personality_type}
游戏进度: 第{game_day}天
关系阶段: {relationship}

属性值:
- 好感度: {affection}/100
- 亲密度: {intimacy}/100
- 信任度: {trust}/100
- 堕落度: {corruption}/100
- 顺从度: {submission}/100
{history_context}
# 事件类型
事件类别: {event_category} ({category_note})
事件名称: {event_name}

# 任务要求
请基于当前角色状态和历史互动，生成一个**{event_name}**相关的随机事件，包括：

1. **事件描述** (story_text):
   - 50-100字
   - 第三人称描述当前发生的情况
   - 符合角色人格特点
   - 与历史互动有一定连贯性
   - 语言生动，有画面感
   - 以省略号结尾，留下悬念

2. **选项列表** ({num_choices}个选项):
   每个选项包含：
   - **选项文字** (10-20字): 玩家可以做出的选择
   - **结果文本** (30-60字): 角色对该选择的反应，包含对话或心理描写

# 选项设计原则
- 选项1: 温柔/积极/关怀的选择（通常增加好感、信任）
- 选项2: 中立/普通的选择
- 选项{num_choices}: 大胆/亲密/挑战性的选择（通常增加亲密度、堕落度，但可能降低信任）

选项之间要有明显区别，给玩家真正的决策困境。

# 输出格式
严格按照以下JSON格式输出：

```json
{{
  "story_text": "事件描述文本...",
  "choices": [
    {{
      "text": "选项1文字",
      "result_text": "选项1的结果文本（包含角色反应）"
    }},
    {{
      "text": "选项2文字",
      "result_text": "选项2的结果文本（包含角色反应）"
    }}
  ]
}}
```

# 注意事项
1. 文本必须符合角色的{personality_type}人格特点
2. 根据当前属性值调整语气和亲密程度
3. 事件要自然融入当前关系阶段，不要过于突兀
4. 角色的对话要加引号「」或""
5. 只输出JSON，不要有任何其他说明文字
6. 确保JSON格式完全正确，可以被直接解析

现在请生成事件内容。
"""

        return prompt.strip()

    @staticmethod
    def build_dilemma_prompt(
        dilemma_name: str,
        dilemma_theme: str,
        character: Dict,
        history: List[Dict] = None,
        num_choices: int = 2
    ) -> str:
        """
        构建选择困境生成的 Prompt

        Args:
            dilemma_name: 困境名称
            dilemma_theme: 困境主题描述
            character: 角色数据
            history: 对话历史
            num_choices: 选项数量（通常是2个）

        Returns:
            完整的 prompt
        """
        personality_type = character.get("personality_type", "tsundere")
        affection = character.get("affection", 0)
        intimacy = character.get("intimacy", 0)
        trust = character.get("trust", 0)
        corruption = character.get("corruption", 0)
        submission = character.get("submission", 0)
        desire = character.get("desire", 0)
        shame = character.get("shame", 0)
        game_day = character.get("game_day", 1)

        # 构建关系阶段描述
        if intimacy < 20:
            relationship = "陌生人阶段"
        elif intimacy < 50:
            relationship = "朋友阶段"
        elif intimacy < 80:
            relationship = "亲密阶段"
        else:
            relationship = "恋人阶段"

        # 构建历史对话上下文
        history_context = ""
        if history:
            recent_interactions = []
            for h in history[-3:]:
                if h.get("user"):
                    recent_interactions.append(f"玩家: {h['user']}")
                if h.get("assistant"):
                    recent_interactions.append(f"角色: {h['assistant']}")
            if recent_interactions:
                history_context = f"""
最近的互动:
{chr(10).join(recent_interactions)}
"""

        prompt = f"""你是一个专业的互动游戏文案作家，正在为恋爱养成游戏生成**选择困境**事件。

# 游戏背景
这是一个恋爱养成游戏，选择困境是关键的情节转折点，强迫玩家做出艰难的选择，每个选择都有代价，影响后续发展。

# 当前角色状态
人格类型: {personality_type}
游戏进度: 第{game_day}天
关系阶段: {relationship}

核心属性:
- 好感度: {affection}/100
- 亲密度: {intimacy}/100
- 信任度: {trust}/100
- 堕落度: {corruption}/100
- 顺从度: {submission}/100
- 欲望值: {desire}/100
- 羞耻心: {shame}/100
{history_context}
# 困境类型
困境名称: {dilemma_name}
困境主题: {dilemma_theme}

# 任务要求
生成一个深刻的**{dilemma_name}**情境，包括：

1. **困境描述** (description):
   - 80-150字
   - 第二/三人称混合，描述一个需要抉择的关键时刻
   - 体现角色内心的矛盾和挣扎
   - 营造紧张感和情绪张力
   - 可以包含角色的对话（用引号）
   - 最后一句是"现在，你必须做出选择："或类似引导语

2. **选项列表** ({num_choices}个选项):
   每个选项包含：
   - **选项标题** (text): 10-20字，简洁概括选择
   - **选项说明** (description): 15-30字，补充说明这个选择的含义
   - **即时后果** (consequence_text): 40-80字，角色对该选择的即时反应
   - **长期影响** (long_term): 20-40字，这个选择的深远影响

# 选项设计原则（重要！）
- **没有完美答案**：每个选择都有利弊
- **真实的两难**：选项之间形成明显对立
- **深远影响**：选择会影响角色成长和关系走向
- **情感冲击**：选择要有情感重量

示例对比：
- 选项A: 满足她的需求（短期快乐，长期信任下降）
- 选项B: 尊重她的犹豫（短期失望，长期信任上升）

# 输出格式
严格按照以下JSON格式输出：

```json
{{
  "description": "困境情境描述...你必须做出选择：",
  "choices": [
    {{
      "text": "选项1标题",
      "description": "选项1说明",
      "consequence_text": "她的即时反应...",
      "long_term": "长期影响描述"
    }},
    {{
      "text": "选项2标题",
      "description": "选项2说明",
      "consequence_text": "她的即时反应...",
      "long_term": "长期影响描述"
    }}
  ]
}}
```

# 注意事项
1. 困境要符合角色的{personality_type}人格
2. 根据当前属性值设计合适深度的困境
3. 对话加引号「」或""
4. 只输出JSON，不要任何其他文字
5. 确保JSON格式完全正确

现在请生成困境内容。
"""

        return prompt.strip()

