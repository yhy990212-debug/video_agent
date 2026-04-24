"""
Step 1: 爆款文案分析
输入：一个或多个文案文本
输出：结构化分析报告
"""
from models import get_client
from skills import get_context_prompt, add_skill_note
from knowledge_base import get_all_articles_for_context
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

ANALYSIS_SYSTEM_PROMPT = """你是一位专业的自媒体内容分析师，精通短视频和中视频文案的底层逻辑。

你的分析框架基于以下核心理论：
1. **循环结构（CREM）**：观点(C) → 原理(R) → 案例(E) → 方法(M)
2. **价值公式**：用户价值 = (新效用 - 旧效用) - (直接成本 + 交易成本 + 间接成本)
3. **开头职能**：让用户完成"第一次时间付费"，解决4个核心疑虑
4. **情绪节拍**：每15秒给用户一个"续费"理由

分析时请严格按照输出格式，使用 Markdown，保持专业性和实用性。"""

ANALYSIS_USER_TEMPLATE = """请对以下{count}篇文案进行深度分析：

{articles}

---

请按以下格式输出分析报告：

## 📊 整体分析

### 1. 文案类型与定位
- 人设类型：（素人/IP/KOC/其他）
- 内容赛道：
- 目标人群：
- 转化目标：

### 2. 开头钩子分析
- 钩子类型：（争议性观点/痛点场景/数据冲击/身份认同/其他）
- 钩子效果评分：⭐⭐⭐⭐⭐
- 解决了哪些用户疑虑：

### 3. 循环结构拆解（CREM）
对每个主要论点单元进行拆解：

**循环单元 1：[单元名称]**
- 观点(C)：
- 原理(R)：
- 案例(E)：
- 方法(M)：
- 功能：（建立共鸣/制造焦虑/展示价值/推动转化/其他）

（如有更多循环单元，依次列出）

### 4. 情绪节拍分析
- 情绪变化曲线：（低→高→低→高 这样描述）
- 关键情绪节点：（列出3-5个最重要的情绪爆发点）

### 5. 核心金句提炼
列出文案中最有力的 3-5 句话，并说明为何有力：

### 6. 营销转化逻辑
- 如何处理直接成本（价格）：
- 如何处理交易成本（摩擦）：
- 如何处理间接成本（机会成本/心理压力）：
- 转化行动指令：

### 7. 写作手法总结
- 语言风格：（口语化程度 1-10）
- 主要修辞手法：
- 值得学习的写法：
- 可以改进的地方：

## 🎯 可复用框架提炼

基于以上分析，提炼一个可复用的结构模板：

```
【开头】（XX字，功能：XXXX）
  - 钩子类型：
  - 关键要素：

【循环1：XXX】（XX字）
  C - 观点：
  R - 原理：
  E - 案例：
  M - 方法：

【循环2：XXX】（XX字）
  ...

【转化结尾】（XX字）
  - 行动指令：
  - 心理暗示：
```

## 💡 创作建议

基于此分析，在用新选题复刻时需要特别注意：
1.
2.
3."""


def analyze_scripts(scripts: list, titles: list = None) -> str:
    """
    分析一个或多个爆款文案

    Args:
        scripts: 文案内容列表
        titles: 文案标题列表（可选）

    Returns:
        分析报告文本
    """
    if not titles:
        titles = [f"文案{i+1}" for i in range(len(scripts))]

    # 构建文案内容
    articles_text = ""
    for i, (title, script) in enumerate(zip(titles, scripts)):
        articles_text += f"\n\n### 文案{i+1}：{title}\n\n{script}\n"

    user_prompt = ANALYSIS_USER_TEMPLATE.format(
        count=len(scripts),
        articles=articles_text
    )

    # 注入用户记忆 context
    user_context = get_context_prompt()
    system_prompt = ANALYSIS_SYSTEM_PROMPT
    if user_context:
        system_prompt += f"\n\n## 用户背景信息\n{user_context}"

    # 注入知识库 context（最多2篇参考）
    kb_context = get_all_articles_for_context(max_articles=2)
    if kb_context:
        system_prompt += f"\n\n## 知识库参考文章（仅供风格对比）\n{kb_context}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    console.print("[cyan]🔍 正在分析文案...[/cyan]")

    client = get_client()
    analysis = ""
    with console.status("[cyan]AI 分析中...[/cyan]", spinner="dots"):
        analysis = client.chat(messages, temperature=0.3, max_tokens=4000)

    # 自动学习用户文案偏好
    _auto_learn_from_analysis(analysis)

    return analysis


def _auto_learn_from_analysis(analysis: str):
    """从分析结果中自动提取学习笔记"""
    # 简单的规则：提取文案类型和赛道信息
    lines = analysis.split("\n")
    for line in lines:
        if "内容赛道：" in line and len(line) > 8:
            domain = line.split("内容赛道：")[-1].strip()
            if domain and len(domain) < 50:
                add_skill_note(f"用户分析过「{domain}」赛道的文案")
                break
