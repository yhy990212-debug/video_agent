"""
Skills / Memory 系统
- 记录用户使用习惯
- 学习用户的创作偏好
- 随时间持续完善 agent 行为
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console

SKILLS_DIR = Path(__file__).parent
MEMORY_FILE = SKILLS_DIR / "user_memory.json"
SKILL_FILE = SKILLS_DIR / "SKILL.md"

console = Console()

DEFAULT_MEMORY = {
    "writing_preferences": {
        "tone": [],           # 用户喜欢的文风标签
        "avoid": [],          # 用户不喜欢的元素
        "frameworks": [],     # 用户常用的表达框架
        "word_count_range": [800, 1500],
    },
    "content_domain": "",     # 主要创作领域
    "platform": "",           # 主要发布平台
    "persona": "",            # 人设描述
    "custom_instructions": [],# 用户明确的创作要求列表
    "session_history": [],    # 近期会话摘要（最多保留 20 条）
    "skill_notes": [],        # agent 自动学习到的偏好笔记
}


def load_memory() -> dict:
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    if not MEMORY_FILE.exists():
        save_memory(DEFAULT_MEMORY)
        return dict(DEFAULT_MEMORY)
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in DEFAULT_MEMORY.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        return dict(DEFAULT_MEMORY)


def save_memory(memory: dict):
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def add_custom_instruction(instruction: str):
    """添加用户明确说明的创作要求"""
    memory = load_memory()
    if instruction not in memory["custom_instructions"]:
        memory["custom_instructions"].append(instruction)
        save_memory(memory)
        console.print(f"[green]✓ 已记住：{instruction}[/green]")


def remove_custom_instruction(index: int):
    """删除第 index 条自定义指令（0-based）"""
    memory = load_memory()
    instructions = memory.get("custom_instructions", [])
    if 0 <= index < len(instructions):
        removed = instructions.pop(index)
        save_memory(memory)
        console.print(f"[green]✓ 已删除：{removed}[/green]")
    else:
        console.print(f"[red]✗ 索引超出范围[/red]")


def add_skill_note(note: str):
    """Agent 自动学习并记录偏好笔记"""
    memory = load_memory()
    entry = {"note": note, "time": datetime.now().isoformat()}
    memory["skill_notes"].append(entry)
    # 最多保留 50 条
    memory["skill_notes"] = memory["skill_notes"][-50:]
    save_memory(memory)


def log_session(summary: str):
    """记录会话摘要"""
    memory = load_memory()
    entry = {"summary": summary, "time": datetime.now().isoformat()}
    memory["session_history"].append(entry)
    memory["session_history"] = memory["session_history"][-20:]
    save_memory(memory)


def get_context_prompt() -> str:
    """生成注入 LLM 的用户习惯 context"""
    memory = load_memory()
    parts = []

    if memory.get("content_domain"):
        parts.append(f"创作领域：{memory['content_domain']}")
    if memory.get("platform"):
        parts.append(f"主要平台：{memory['platform']}")
    if memory.get("persona"):
        parts.append(f"人设定位：{memory['persona']}")

    prefs = memory.get("writing_preferences", {})
    if prefs.get("tone"):
        parts.append(f"偏好文风：{', '.join(prefs['tone'])}")
    if prefs.get("avoid"):
        parts.append(f"需要避免：{', '.join(prefs['avoid'])}")
    if prefs.get("frameworks"):
        parts.append(f"常用框架：{', '.join(prefs['frameworks'])}")

    word_range = prefs.get("word_count_range", [800, 1500])
    parts.append(f"常用字数范围：{word_range[0]}-{word_range[1]} 字")

    custom = memory.get("custom_instructions", [])
    if custom:
        parts.append("用户特别说明：")
        for i, inst in enumerate(custom, 1):
            parts.append(f"  {i}. {inst}")

    skill_notes = memory.get("skill_notes", [])
    if skill_notes:
        recent_notes = skill_notes[-5:]
        parts.append("近期学习到的偏好：")
        for sn in recent_notes:
            parts.append(f"  - {sn['note']}")

    return "\n".join(parts) if parts else ""


def show_memory():
    """展示当前记忆内容"""
    from rich.panel import Panel
    from rich.text import Text
    memory = load_memory()

    text = Text()
    text.append("📝 当前记忆内容\n\n", style="bold")

    if memory.get("content_domain"):
        text.append(f"创作领域: ", style="bold cyan")
        text.append(f"{memory['content_domain']}\n")
    if memory.get("platform"):
        text.append(f"主要平台: ", style="bold cyan")
        text.append(f"{memory['platform']}\n")
    if memory.get("persona"):
        text.append(f"人设定位: ", style="bold cyan")
        text.append(f"{memory['persona']}\n")

    custom = memory.get("custom_instructions", [])
    if custom:
        text.append("\n自定义创作要求:\n", style="bold yellow")
        for i, inst in enumerate(custom):
            text.append(f"  [{i}] {inst}\n")

    notes = memory.get("skill_notes", [])
    if notes:
        text.append(f"\nAgent 学习笔记 (最近5条):\n", style="bold green")
        for sn in notes[-5:]:
            text.append(f"  • {sn['note']}\n", style="dim")

    console.print(Panel(text, border_style="blue"))


def update_writing_preference(key: str, value):
    """更新写作偏好"""
    memory = load_memory()
    if "writing_preferences" not in memory:
        memory["writing_preferences"] = {}
    memory["writing_preferences"][key] = value
    save_memory(memory)


def reset_memory():
    """清空所有记忆，恢复默认状态"""
    import copy
    save_memory(copy.deepcopy(DEFAULT_MEMORY))
    console.print("[green]✓ 记忆已清空，恢复初始状态[/green]")
