"""
Step 2: 用户选择分析结果
Step 3: 基于新选题创作
"""
from models import get_client
from skills import get_context_prompt, add_skill_note, update_writing_preference
from knowledge_base import get_all_articles_for_context
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm

console = Console()

CREATION_SYSTEM_PROMPT = """你是一位专业的自媒体视频文案创作者，擅长口播稿件写作。

你的创作哲学：
1. **不要卖产品，展示解决问题的实际过程**
2. **开头是让用户完成第一次"时间付费"**
3. **循环结构**：观点→原理→案例→方法，每个循环推进一步
4. **原生感**：口语化、有情绪、带入感强
5. **动词 > 名词 > 形容词**
6. **数据比总结更有力**
7. **白描（直接描述行为/事实）比修辞更有穿透力**

写作检验清单（输出前自检）：
- [ ] 开头能解决用户4个核心疑虑
- [ ] 每15秒有一个情绪或信息峰值
- [ ] 痛苦已被"翻译"成可感知的成本
- [ ] 有具体数据或案例支撑
- [ ] 结尾有明确的行动指令
- [ ] 字数符合要求"""

CREATION_USER_TEMPLATE = """请基于以下信息，为我创作一篇视频口播文案：

## 新创作选题
{topic}

## 参考框架（来自爆款文案分析）
{selected_framework}

## 字数要求
目标字数：{word_count} 字（允许±10%浮动）

## 额外创作要求
{extra_requirements}

---

请按以下格式输出：

# 【正式稿】

（这里输出可以直接录制的口播文案，无结构标注）

---

# 【注释版】

（这里输出带结构标注的版本，每段标注其功能，如：[开头-钩子]、[循环1-观点]、[循环1-案例] 等）

---

# 【创作说明】

简要说明：
- 选用了哪种开头钩子及原因
- 使用了几个循环单元及各自的功能
- 如何处理转化/营销节点
- 字数统计：正式稿约 XX 字"""


def interactive_select_framework(analysis: str) -> str:
    """
    交互式让用户选择分析结果的哪些部分

    Returns:
        用户选择的框架文本
    """
    console.print("\n[bold yellow]📋 Step 2：选择要使用的分析结果[/bold yellow]")
    console.print("你可以选择全部使用，或者只使用部分内容：\n")

    use_all = Confirm.ask("是否使用全部分析结果？", default=True)
    if use_all:
        return analysis

    # 让用户手动输入想使用的部分
    console.print("\n[cyan]请粘贴/输入你想保留的分析内容[/cyan]")
    console.print("[dim]（输入完成后，在新的一行输入 '===END===' 结束）[/dim]\n")

    lines = []
    while True:
        line = input()
        if line.strip() == "===END===":
            break
        lines.append(line)

    selected = "\n".join(lines).strip()
    if not selected:
        console.print("[yellow]未输入内容，将使用全部分析结果[/yellow]")
        return analysis

    return selected


def create_script(
    topic: str,
    framework: str,
    word_count: int = 1000,
    extra_requirements: str = "",
    stream_output: bool = True,
) -> str:
    """
    基于选题和框架创作视频文案

    Args:
        topic: 新创作选题
        framework: 参考框架（来自 Step 2 选择）
        word_count: 目标字数
        extra_requirements: 额外要求
        stream_output: 是否流式输出

    Returns:
        生成的文案内容
    """
    # 构建 system prompt，注入用户记忆
    system_prompt = CREATION_SYSTEM_PROMPT
    user_context = get_context_prompt()
    if user_context:
        system_prompt += f"\n\n## 用户创作背景\n{user_context}"

    # 注入知识库
    kb_context = get_all_articles_for_context(max_articles=3)
    if kb_context:
        system_prompt += f"\n\n## 知识库优质文案（学习风格参考）\n{kb_context}"

    user_prompt = CREATION_USER_TEMPLATE.format(
        topic=topic,
        selected_framework=framework,
        word_count=word_count,
        extra_requirements=extra_requirements if extra_requirements else "无特殊要求",
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    console.print(f"\n[bold cyan]✍️  Step 3: 正在基于「{topic}」创作文案...[/bold cyan]\n")
    console.print("[dim]─" * 60 + "[/dim]\n")

    client = get_client()
    result = ""

    if stream_output:
        for chunk in client.chat_stream(messages, temperature=0.75, max_tokens=6000):
            console.print(chunk, end="")
            result += chunk
        console.print("\n")
    else:
        with console.status("[cyan]创作中...[/cyan]", spinner="dots"):
            result = client.chat(messages, temperature=0.75, max_tokens=6000)
        console.print(result)

    # 记录学习笔记
    add_skill_note(f"为选题「{topic[:30]}」创作了约 {word_count} 字的文案")

    return result
