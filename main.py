#!/usr/bin/env python3
"""
🎬 视频文案爆款复刻 Agent
一个帮你分析爆款、提炼框架、快速创作的 CLI 工具
"""
import sys
import os
import click
import questionary
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, IntPrompt, Confirm
from typing import Tuple, List

# 把项目根目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    SUPPORTED_MODELS, load_config, save_config,
    set_api_key, get_api_key, set_active_model, get_active_model,
    get_preferences, update_preference, increment_stats, reset_stats
)
from models import get_client, LLMClient
from workflow.step1_analyze import analyze_scripts
from workflow.step2_3_create import interactive_select_framework, create_script
from workflow.step4_export import export_to_word
import knowledge_base as kb_module
import skills

console = Console()

BANNER = """
[bold cyan]╔══════════════════════════════════════════════════════╗
║     🎬  视频文案爆款复刻 Agent  v1.0                ║
║     分析爆款 · 提炼框架 · 创作文案 · 一键导出        ║
╚══════════════════════════════════════════════════════╝[/bold cyan]
"""


# ─────────────────────────────────────────
#  主入口
# ─────────────────────────────────────────
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """🎬 视频文案爆款复刻 Agent"""
    if ctx.invoked_subcommand is None:
        console.print(BANNER)
        _show_main_menu()


def _show_main_menu():
    """交互式主菜单"""
    while True:
        console.print()
        choice = questionary.select(
            "请选择操作：",
            choices=[
                "🚀  开始创作（完整四步流程）",
                "📄  快速分析（只分析爆款）",
                "🤖  快速创作（直接写文案）",
                "💬  自由对话（和 AI 随意聊）",
                "📚  知识库管理",
                "🧠  查看/编辑记忆",
                "⚙️   模型与配置",
                "❓  帮助与教程",
                "👋  退出",
            ],
        ).ask()

        if choice is None or "退出" in choice:
            console.print("[dim]再见！[/dim]")
            break
        elif "完整四步流程" in choice:
            _run_full_workflow()
        elif "快速分析" in choice:
            _run_quick_analysis()
        elif "快速创作" in choice:
            _run_quick_create()
        elif "自由对话" in choice:
            _run_free_chat()
        elif "知识库" in choice:
            _kb_menu()
        elif "记忆" in choice:
            _memory_menu()
        elif "模型与配置" in choice:
            _settings_menu()
        elif "帮助" in choice:
            choice2 = questionary.select(
                "选择查看内容：",
                choices=["📖  完整使用教程", "⌨️  快捷命令速查", "← 返回"],
            ).ask()
            if choice2 and "完整使用教程" in choice2:
                from rich.markdown import Markdown
                doc_path = Path(__file__).parent / "docs" / "使用教程.md"
                console.print(Markdown(doc_path.read_text(encoding="utf-8")))
            elif choice2 and "快捷命令" in choice2:
                _show_help()


# ─────────────────────────────────────────
#  完整四步流程
# ─────────────────────────────────────────
def _run_full_workflow():
    """完整的四步创作流程"""
    console.print(Panel(
        "[bold]📋 完整创作流程\n\n"
        "Step 1 → 分析爆款文案\n"
        "Step 2 → 选择分析结果\n"
        "Step 3 → 基于新选题创作\n"
        "Step 4 → 导出 Word 文档",
        border_style="cyan"
    ))

    # ── Step 1 ──
    console.print("\n[bold yellow]═══ Step 1：输入爆款文案 ═══[/bold yellow]")
    scripts, titles = _input_scripts()
    if not scripts:
        console.print("[red]未输入文案，已取消[/red]")
        return

    analysis = analyze_scripts(scripts, titles)
    console.print("\n[bold green]✅ 分析完成！[/bold green]")
    console.print(Panel(analysis, title="分析报告", border_style="green"))

    # ── Step 2 ──
    console.print("\n[bold yellow]═══ Step 2：选择分析结果 ═══[/bold yellow]")
    framework = interactive_select_framework(analysis)

    # ── Step 3 ──
    console.print("\n[bold yellow]═══ Step 3：输入新选题 ═══[/bold yellow]")
    topic = Prompt.ask("📌 请输入新的创作选题")
    if not topic.strip():
        console.print("[red]未输入选题，已取消[/red]")
        return

    prefs = get_preferences()
    default_wc = prefs.get("default_word_count", 1000)
    word_count = IntPrompt.ask(f"📏 目标字数（默认 {default_wc}）", default=default_wc)

    extra = Prompt.ask("💬 额外要求（可留空）", default="")

    script_content = create_script(
        topic=topic,
        framework=framework,
        word_count=word_count,
        extra_requirements=extra,
        stream_output=True,
    )

    # ── Step 4 ──
    console.print("\n[bold yellow]═══ Step 4：导出 Word 文档 ═══[/bold yellow]")
    prefs = get_preferences()
    default_dir = prefs.get("output_dir", str(Path.home() / "Desktop"))

    save_dir = Prompt.ask(f"📁 保存目录", default=default_dir)
    file_path = export_to_word(
        content=script_content,
        topic=topic,
        analysis=analysis,
        output_dir=save_dir,
    )

    increment_stats("scripts_generated")
    increment_stats("total_sessions")

    # 询问是否保存到知识库
    if Confirm.ask("\n是否将此文案保存到知识库？", default=False):
        tags_input = Prompt.ask("标签（逗号分隔，可留空）", default="")
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        kb_module.add_article(
            content="\n\n".join(scripts),
            title=f"爆款参考_{titles[0] if titles else topic}",
            tags=tags,
            notes=f"创作选题：{topic}",
        )

    console.print(f"\n[bold green]🎉 创作完成！文件已保存至：{file_path}[/bold green]")

    # 自动更新偏好
    update_preference("default_word_count", word_count)
    update_preference("output_dir", save_dir)


# ─────────────────────────────────────────
#  快速分析
# ─────────────────────────────────────────
def _run_quick_analysis():
    """只做爆款分析，不创作"""
    console.print("\n[bold yellow]📄 快速分析爆款文案[/bold yellow]")
    scripts, titles = _input_scripts()
    if not scripts:
        return

    analysis = analyze_scripts(scripts, titles)
    console.print(Panel(analysis, title="📊 分析报告", border_style="green"))

    if Confirm.ask("\n是否保存分析报告为 Word？", default=False):
        prefs = get_preferences()
        save_dir = Prompt.ask("保存目录", default=prefs.get("output_dir", str(Path.home() / "Desktop")))
        export_to_word(
            content=f"# 【正式稿】\n\n{analysis}",
            topic=f"分析报告_{titles[0] if titles else '爆款'}",
            output_dir=save_dir,
        )


# ─────────────────────────────────────────
#  快速创作
# ─────────────────────────────────────────
def _run_quick_create():
    """直接输入选题创作，不需要爆款参考"""
    console.print("\n[bold yellow]🤖 快速创作[/bold yellow]")

    topic = Prompt.ask("📌 创作选题")
    if not topic.strip():
        return

    prefs = get_preferences()
    default_wc = prefs.get("default_word_count", 1000)
    word_count = IntPrompt.ask(f"字数（默认 {default_wc}）", default=default_wc)
    extra = Prompt.ask("额外要求（可留空）", default="")

    # 加载 SOP 作为框架
    sop_path = Path(__file__).parent / "sop" / "script_sop.md"
    framework = sop_path.read_text(encoding="utf-8") if sop_path.exists() else ""

    script_content = create_script(
        topic=topic,
        framework=f"基于通用创作 SOP 框架：\n\n{framework[:2000]}",
        word_count=word_count,
        extra_requirements=extra,
    )

    if Confirm.ask("\n是否导出为 Word？", default=True):
        prefs = get_preferences()
        save_dir = Prompt.ask("保存目录", default=prefs.get("output_dir", str(Path.home() / "Desktop")))
        export_to_word(content=script_content, topic=topic, output_dir=save_dir)
        update_preference("output_dir", save_dir)

    increment_stats("scripts_generated")


# ─────────────────────────────────────────
#  自由对话
# ─────────────────────────────────────────
def _run_free_chat():
    """与 AI 自由对话，不限制场景"""
    provider, model = get_active_model()
    model_name = SUPPORTED_MODELS[provider]["name"]

    console.print(Panel(
        f"[bold]💬 自由对话模式[/bold]\n\n"
        f"当前模型：[cyan]{model_name} / {model}[/cyan]\n\n"
        "[dim]输入任何问题或想法，AI 都会回答。\n"
        "输入 [bold]/clear[/bold] 清空对话历史，输入 [bold]/exit[/bold] 或按 Ctrl+C 退出。[/dim]",
        border_style="cyan",
    ))

    try:
        client = get_client()
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
        return

    context_prompt = skills.get_context_prompt()
    system_content = "你是一个全能助手，可以帮助用户解答任何问题，提供写作、分析、创意、技术等各类帮助。"
    if context_prompt:
        system_content += f"\n\n以下是用户的背景信息，在相关时请参考：\n{context_prompt}"

    messages = [{"role": "system", "content": system_content}]

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]你[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]已退出对话[/dim]")
            break

        if not user_input.strip():
            continue

        cmd = user_input.strip().lower()
        if cmd in ("/exit", "/quit", "exit", "quit", "退出"):
            console.print("[dim]已退出对话[/dim]")
            break
        elif cmd == "/clear":
            messages = [{"role": "system", "content": system_content}]
            console.print("[green]✓ 对话历史已清空[/green]")
            continue

        messages.append({"role": "user", "content": user_input})

        console.print("\n[bold magenta]AI[/bold magenta]", end=" ")
        try:
            full_reply = ""
            for chunk in client.chat_stream(messages):
                console.print(chunk, end="", highlight=False)
                full_reply += chunk
            console.print()  # 换行
            messages.append({"role": "assistant", "content": full_reply})
        except Exception as e:
            console.print(f"\n[red]✗ 请求失败：{e}[/red]")
            # 回滚未成功的用户消息
            messages.pop()


# ─────────────────────────────────────────
#  输入文案工具函数
# ─────────────────────────────────────────
def _input_scripts() -> Tuple[List[str], List[str]]:
    """多种方式输入爆款文案"""
    input_mode = questionary.select(
        "如何输入文案？",
        choices=[
            "✏️  直接粘贴文本",
            "📂  从文件读取",
            "📚  从知识库选择",
        ],
    ).ask()

    scripts = []
    titles = []

    if input_mode is None:
        return [], []

    if "粘贴" in input_mode:
        count = IntPrompt.ask("需要输入几篇文案？", default=1)
        for i in range(count):
            console.print(f"\n[cyan]请粘贴第 {i+1} 篇文案[/cyan]")
            title = Prompt.ask(f"  标题（可留空）", default=f"文案{i+1}")
            console.print("[dim]  粘贴内容后，新起一行输入 '===END===' 结束：[/dim]")
            lines = []
            while True:
                line = input()
                if line.strip() == "===END===":
                    break
                lines.append(line)
            content = "\n".join(lines).strip()
            if content:
                scripts.append(content)
                titles.append(title)

    elif "文件" in input_mode:
        while True:
            file_path = Prompt.ask("文件路径（支持 .txt / .md）")
            p = Path(file_path.strip().strip('"').strip("'"))
            if p.exists():
                content = p.read_text(encoding="utf-8")
                scripts.append(content)
                titles.append(p.stem)
                console.print(f"[green]✓ 已读取：{p.name}（{len(content)} 字）[/green]")
            else:
                console.print(f"[red]文件不存在：{p}[/red]")

            if not Confirm.ask("继续添加文件？", default=False):
                break

    elif "知识库" in input_mode:
        articles = kb_module.list_articles()
        if not articles:
            console.print("[yellow]知识库为空[/yellow]")
            return [], []

        choices = [f"{a['id']}  {a['title']}" for a in articles]
        selected = questionary.checkbox("选择文章（空格多选）：", choices=choices).ask()
        if selected:
            for sel in selected:
                article_id = sel.split()[0]
                result = kb_module.get_article(article_id)
                if result:
                    meta, content = result
                    scripts.append(content)
                    titles.append(meta["title"])

    return scripts, titles


# ─────────────────────────────────────────
#  知识库管理菜单
# ─────────────────────────────────────────
def _kb_menu():
    while True:
        choice = questionary.select(
            "📚 知识库管理",
            choices=[
                "📋  查看所有文章",
                "➕  添加文章",
                "🗑️   删除文章",
                "🔍  查看文章内容",
                "← 返回",
            ],
        ).ask()

        if choice is None or "返回" in choice:
            break
        elif "查看所有" in choice:
            kb_module.show_articles_table()
        elif "添加" in choice:
            _kb_add()
        elif "删除" in choice:
            _kb_remove()
        elif "查看文章内容" in choice:
            _kb_view()


def _kb_add():
    input_mode = questionary.select(
        "添加方式：",
        choices=["粘贴文本", "从文件读取"],
    ).ask()

    if input_mode == "粘贴文本":
        title = Prompt.ask("文章标题")
        console.print("[dim]粘贴内容，输入 '===END===' 结束：[/dim]")
        lines = []
        while True:
            line = input()
            if line.strip() == "===END===":
                break
            lines.append(line)
        content = "\n".join(lines).strip()
    else:
        file_path = Prompt.ask("文件路径")
        p = Path(file_path.strip().strip('"').strip("'"))
        if not p.exists():
            console.print("[red]文件不存在[/red]")
            return
        content = p.read_text(encoding="utf-8")
        title = Prompt.ask("文章标题", default=p.stem)

    platform = Prompt.ask("来自平台（如：B站/抖音/小红书）", default="")
    tags_input = Prompt.ask("标签（逗号分隔）", default="")
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
    notes = Prompt.ask("备注", default="")

    kb_module.add_article(content=content, title=title, tags=tags, platform=platform, notes=notes)


def _kb_remove():
    articles = kb_module.list_articles()
    if not articles:
        console.print("[yellow]知识库为空[/yellow]")
        return
    choices = [f"{a['id']}  {a['title']}" for a in articles]
    selected = questionary.checkbox("选择要删除的文章：", choices=choices).ask()
    if selected and Confirm.ask(f"确认删除 {len(selected)} 篇？"):
        for sel in selected:
            kb_module.remove_article(sel.split()[0])


def _kb_view():
    articles = kb_module.list_articles()
    if not articles:
        return
    choices = [f"{a['id']}  {a['title']}" for a in articles]
    selected = questionary.select("选择文章：", choices=choices).ask()
    if selected:
        result = kb_module.get_article(selected.split()[0])
        if result:
            meta, content = result
            console.print(Panel(
                content[:2000] + ("..." if len(content) > 2000 else ""),
                title=f"[bold]{meta['title']}[/bold]",
                border_style="green"
            ))


# ─────────────────────────────────────────
#  记忆管理菜单
# ─────────────────────────────────────────
def _memory_menu():
    while True:
        choice = questionary.select(
            "🧠 记忆管理",
            choices=[
                "📖  查看当前记忆",
                "➕  添加创作要求",
                "🗑️   删除创作要求",
                "✏️   编辑偏好",
                "🔄  清空所有记忆（恢复默认）",
                "← 返回",
            ],
        ).ask()

        if choice is None or "返回" in choice:
            break
        elif "查看" in choice:
            skills.show_memory()
        elif "添加创作要求" in choice:
            instruction = Prompt.ask("输入创作要求（如：不要用'我'开头、结尾必须有推课）")
            if instruction:
                skills.add_custom_instruction(instruction)
        elif "删除创作要求" in choice:
            memory = skills.load_memory()
            instructions = memory.get("custom_instructions", [])
            if not instructions:
                console.print("[yellow]暂无自定义要求[/yellow]")
            else:
                for i, inst in enumerate(instructions):
                    console.print(f"  [{i}] {inst}")
                idx = IntPrompt.ask("输入要删除的序号")
                skills.remove_custom_instruction(idx)
        elif "编辑偏好" in choice:
            _edit_preferences()
        elif "清空所有记忆" in choice:
            if Confirm.ask("[bold red]确认清空所有记忆？此操作不可恢复[/bold red]", default=False):
                skills.reset_memory()


def _edit_preferences():
    choice = questionary.select(
        "编辑哪项偏好？",
        choices=[
            "创作领域",
            "主要平台",
            "人设描述",
            "偏好文风标签",
            "默认字数范围",
            "← 返回",
        ],
    ).ask()

    if choice is None or "返回" in choice:
        return

    memory = skills.load_memory()

    if choice == "创作领域":
        val = Prompt.ask("创作领域", default=memory.get("content_domain", ""))
        memory["content_domain"] = val
    elif choice == "主要平台":
        val = Prompt.ask("主要平台（如：B站、抖音）", default=memory.get("platform", ""))
        memory["platform"] = val
    elif choice == "人设描述":
        val = Prompt.ask("人设描述", default=memory.get("persona", ""))
        memory["persona"] = val
    elif choice == "偏好文风标签":
        current = memory.get("writing_preferences", {}).get("tone", [])
        console.print(f"当前标签：{current}")
        val = Prompt.ask("新的文风标签（逗号分隔）", default=", ".join(current))
        tags = [t.strip() for t in val.split(",") if t.strip()]
        memory.setdefault("writing_preferences", {})["tone"] = tags
    elif choice == "默认字数范围":
        current = memory.get("writing_preferences", {}).get("word_count_range", [800, 1500])
        low = IntPrompt.ask("最小字数", default=current[0])
        high = IntPrompt.ask("最大字数", default=current[1])
        memory.setdefault("writing_preferences", {})["word_count_range"] = [low, high]

    skills.save_memory(memory)
    console.print("[green]✓ 已保存[/green]")


# ─────────────────────────────────────────
#  模型与配置菜单
# ─────────────────────────────────────────
def _settings_menu():
    while True:
        provider, model = get_active_model()
        config = load_config()

        # 显示当前状态
        console.print(f"\n[dim]当前模型：[/dim][cyan]{SUPPORTED_MODELS[provider]['name']} / {model}[/cyan]")

        choice = questionary.select(
            "⚙️  配置",
            choices=[
                "🔑  管理 API Key",
                "🔄  切换模型",
                "🧪  测试当前模型连接",
                "📁  修改默认输出目录",
                "📊  查看使用统计",
                "🗑️   重置使用统计",
                "← 返回",
            ],
        ).ask()

        if choice is None or "返回" in choice:
            break
        elif "管理 API Key" in choice:
            _manage_api_keys()
        elif "切换模型" in choice:
            _switch_model()
        elif "测试" in choice:
            _test_connection()
        elif "输出目录" in choice:
            new_dir = Prompt.ask("输出目录", default=get_preferences().get("output_dir", str(Path.home() / "Desktop")))
            update_preference("output_dir", new_dir)
            console.print("[green]✓ 已保存[/green]")
        elif "查看使用统计" in choice:
            _show_stats()
        elif "重置使用统计" in choice:
            if Confirm.ask("确认重置所有使用统计为零？", default=False):
                reset_stats()
                console.print("[green]✓ 使用统计已重置[/green]")


def _manage_api_keys():
    """管理 API Keys"""
    choices = [f"{info['name']} ({pid})" for pid, info in SUPPORTED_MODELS.items()]
    choices.append("← 返回")

    sel = questionary.select("选择要设置 Key 的模型：", choices=choices).ask()
    if sel is None or "返回" in sel:
        return

    for pid, info in SUPPORTED_MODELS.items():
        if info["name"] in sel:
            existing = get_api_key(pid)
            status = "[green]✓ 已设置[/green]" if existing else "[red]未设置[/red]"
            console.print(f"当前状态：{status}")
            console.print(f"[dim]文档：{info['docs']}[/dim]")

            action = questionary.select(
                "操作：",
                choices=["设置/更新 Key", "删除 Key", "← 返回"],
            ).ask()

            if action == "设置/更新 Key":
                import getpass
                api_key = getpass.getpass(f"{info['name']} API Key（输入不显示）: ")
                if api_key.strip():
                    set_api_key(pid, api_key.strip())
                    console.print("[green]✓ API Key 已加密保存[/green]")
            elif action == "删除 Key":
                if Confirm.ask("确认删除？"):
                    config = load_config()
                    config["api_keys"].pop(pid, None)
                    save_config(config)
                    console.print("[green]✓ 已删除[/green]")
            break


def _switch_model():
    """切换使用的模型"""
    # 选 provider
    provider_choices = [f"{info['name']} ({pid})" for pid, info in SUPPORTED_MODELS.items()
                       if get_api_key(pid)]

    if not provider_choices:
        console.print("[red]尚未配置任何 API Key，请先设置[/red]")
        return

    # 也显示未配置的（灰色提示）
    all_choices = []
    for pid, info in SUPPORTED_MODELS.items():
        has_key = bool(get_api_key(pid))
        label = f"{info['name']} ({pid})" + ("" if has_key else "  [未配置Key]")
        all_choices.append(label)

    sel = questionary.select("选择模型提供商：", choices=all_choices + ["← 返回"]).ask()
    if sel is None or "返回" in sel:
        return

    selected_pid = None
    for pid, info in SUPPORTED_MODELS.items():
        if f"({pid})" in sel:
            selected_pid = pid
            break

    if not selected_pid:
        return

    if "[未配置Key]" in sel:
        console.print(f"[yellow]请先为 {SUPPORTED_MODELS[selected_pid]['name']} 配置 API Key[/yellow]")
        return

    # 选 model
    models = SUPPORTED_MODELS[selected_pid]["models"]
    model_info = SUPPORTED_MODELS[selected_pid].get("model_info", {})
    model_choices = [
        f"{m}  —  {model_info[m]}" if m in model_info else m
        for m in models
    ]
    sel_model = questionary.select("选择具体模型：", choices=model_choices).ask()
    if sel_model:
        # 提取真实 model id（去掉描述部分）
        model = sel_model.split("  —  ")[0].strip()
        set_active_model(selected_pid, model)
        console.print(f"[green]✓ 已切换到 {SUPPORTED_MODELS[selected_pid]['name']} / {model}[/green]")


def _test_connection():
    """测试模型连接"""
    provider, model = get_active_model()
    console.print(f"[cyan]测试 {SUPPORTED_MODELS[provider]['name']} / {model} 连接...[/cyan]")
    try:
        client = get_client()
        with console.status("连接中..."):
            ok = client.test_connection()
        if ok:
            console.print("[bold green]✅ 连接成功！[/bold green]")
        else:
            console.print("[red]✗ 连接失败，请检查 API Key[/red]")
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
    except Exception as e:
        console.print(f"[red]✗ 连接异常：{e}[/red]")


def _show_stats():
    """显示使用统计"""
    config = load_config()
    stats = config.get("usage_stats", {})
    table = Table(title="📊 使用统计")
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="yellow")
    table.add_row("总会话数", str(stats.get("total_sessions", 0)))
    table.add_row("生成文案数", str(stats.get("scripts_generated", 0)))
    console.print(table)


def _show_help():
    help_text = """
[bold]🎬 视频文案爆款复刻 Agent 使用指南[/bold]

[bold cyan]完整四步流程[/bold cyan]
  1. 粘贴/导入你的爆款文案（支持多篇）
  2. AI 分析框架、循环结构、钩子类型等
  3. 选择要复用的分析结果
  4. 输入新选题，生成文案
  5. 一键导出 Word 文档

[bold cyan]知识库[/bold cyan]
  存放你认为优质的爆款文章，AI 会学习你的风格偏好。
  支持增加/删除/查看，可按标签分类。

[bold cyan]记忆系统[/bold cyan]
  Agent 会自动记录你的创作习惯。
  你也可以手动添加"创作要求"，每次创作都会应用。

[bold cyan]支持的模型[/bold cyan]
  • DeepSeek（推荐，性价比高）
  • Kimi 月之暗面（长文本能力强）
  • 豆包（字节跳动）
  • 通义千问（阿里云）
  • 智谱 GLM

[bold cyan]快捷命令[/bold cyan]
  video-agent analyze <文件>   快速分析文案文件
  video-agent create           快速创作
  video-agent key set          设置 API Key
  video-agent model switch     切换模型
  video-agent kb               知识库管理
"""
    console.print(Panel(help_text, border_style="blue"))


# ─────────────────────────────────────────
#  子命令（非交互式，适合脚本调用）
# ─────────────────────────────────────────
@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True))
@click.option("--output", "-o", help="输出目录")
def analyze(files, output):
    """分析一个或多个文案文件"""
    if not files:
        console.print("[red]请提供文案文件路径[/red]")
        return

    scripts = []
    titles = []
    for f in files:
        p = Path(f)
        scripts.append(p.read_text(encoding="utf-8"))
        titles.append(p.stem)

    analysis = analyze_scripts(scripts, titles)
    console.print(Panel(analysis, title="分析报告", border_style="green"))

    if output:
        export_to_word(
            content=f"# 【正式稿】\n\n{analysis}",
            topic=f"分析报告_{titles[0]}",
            output_dir=output,
        )


@cli.command()
@click.option("--topic", "-t", prompt="创作选题", help="视频主题")
@click.option("--words", "-w", default=1000, help="目标字数")
@click.option("--output", "-o", help="输出目录")
def create(topic, words, output):
    """快速创作视频文案"""
    sop_path = Path(__file__).parent / "sop" / "script_sop.md"
    framework = sop_path.read_text(encoding="utf-8") if sop_path.exists() else ""

    content = create_script(
        topic=topic,
        framework=framework[:2000],
        word_count=words,
    )

    if output:
        export_to_word(content=content, topic=topic, output_dir=output)


@cli.group()
def key():
    """API Key 管理"""
    pass


@key.command("set")
@click.option("--provider", "-p",
              type=click.Choice(list(SUPPORTED_MODELS.keys())),
              prompt="选择模型提供商",
              help="模型提供商")
def key_set(provider):
    """设置 API Key"""
    import getpass
    api_key = getpass.getpass(f"{SUPPORTED_MODELS[provider]['name']} API Key: ")
    if api_key.strip():
        set_api_key(provider, api_key.strip())
        console.print(f"[green]✓ {SUPPORTED_MODELS[provider]['name']} API Key 已保存[/green]")


@key.command("list")
def key_list():
    """查看已配置的 API Key"""
    table = Table(title="API Keys 状态")
    table.add_column("提供商")
    table.add_column("名称")
    table.add_column("状态")

    for pid, info in SUPPORTED_MODELS.items():
        has_key = bool(get_api_key(pid))
        status = "[green]✓ 已配置[/green]" if has_key else "[red]未配置[/red]"
        table.add_row(pid, info["name"], status)

    console.print(table)


@cli.command()
def model():
    """切换使用的 AI 模型"""
    _switch_model()


@cli.command()
@click.option("--raw", is_flag=True, help="输出原始 Markdown 文本")
def docs(raw):
    """查看使用教程"""
    doc_path = Path(__file__).parent / "docs" / "使用教程.md"
    if not doc_path.exists():
        console.print("[red]教程文件未找到：docs/使用教程.md[/red]")
        return
    content = doc_path.read_text(encoding="utf-8")
    if raw:
        console.print(content)
    else:
        from rich.markdown import Markdown
        console.print(Markdown(content))


@cli.command()
@click.option("--memory/--no-memory", default=True, help="是否清空记忆（默认：是）")
@click.option("--stats/--no-stats", default=True, help="是否重置统计（默认：是）")
@click.option("--yes", "-y", is_flag=True, help="跳过确认直接执行")
def reset(memory, stats, yes):
    """一键恢复初始状态（清空记忆/统计）"""
    parts = []
    if memory:
        parts.append("所有记忆（偏好、自定义要求、会话历史）")
    if stats:
        parts.append("使用统计（会话数、文案生成数）")

    if not parts:
        console.print("[yellow]未选择任何重置项[/yellow]")
        return

    console.print("[bold yellow]将重置以下内容：[/bold yellow]")
    for p in parts:
        console.print(f"  • {p}")

    if not yes and not Confirm.ask("\n确认执行重置？此操作不可恢复", default=False):
        console.print("[dim]已取消[/dim]")
        return

    if memory:
        skills.reset_memory()
    if stats:
        reset_stats()
        console.print("[green]✓ 使用统计已重置[/green]")

    console.print("\n[bold green]✅ Agent 已恢复至初始状态[/bold green]")


@cli.command()
def chat():
    """与 AI 自由对话（不限场景）"""
    console.print(BANNER)
    _run_free_chat()


@cli.group()
def kb():
    """知识库管理"""
    pass


@kb.command("list")
def kb_list():
    """列出知识库文章"""
    kb_module.show_articles_table()


@kb.command("add")
@click.argument("file", type=click.Path(exists=True))
@click.option("--title", "-t", help="文章标题")
@click.option("--tags", help="标签（逗号分隔）")
@click.option("--platform", default="", help="来自平台")
def kb_add(file, title, tags, platform):
    """添加文章到知识库"""
    p = Path(file)
    content = p.read_text(encoding="utf-8")
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    kb_module.add_article(
        content=content,
        title=title or p.stem,
        tags=tag_list,
        platform=platform,
    )


@kb.command("remove")
@click.argument("article_id")
def kb_remove(article_id):
    """从知识库删除文章"""
    kb_module.remove_article(article_id)


if __name__ == "__main__":
    cli()
