"""
知识库管理模块
- 存储优质爆款文案供学习
- 支持增删查
- 自动提取文案特征供创作参考
"""
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table

KB_DIR = Path(__file__).parent
ARTICLES_DIR = KB_DIR / "articles"
INDEX_FILE = KB_DIR / "index.json"

console = Console()


def _load_index() -> dict:
    """加载知识库索引"""
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.exists():
        _save_index({"articles": []})
        return {"articles": []}
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index(index: dict):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def add_article(
    content: str,
    title: str,
    tags: list = None,
    platform: str = "",
    notes: str = "",
) -> str:
    """添加文章到知识库，返回文章 ID"""
    article_id = hashlib.md5(content.encode()).hexdigest()[:8]
    article_path = ARTICLES_DIR / f"{article_id}.txt"
    article_path.write_text(content, encoding="utf-8")

    index = _load_index()
    # 检查是否已存在
    existing_ids = [a["id"] for a in index["articles"]]
    if article_id in existing_ids:
        console.print(f"[yellow]⚠ 该文章已存在（ID: {article_id}）[/yellow]")
        return article_id

    meta = {
        "id": article_id,
        "title": title,
        "platform": platform,
        "tags": tags or [],
        "notes": notes,
        "added_at": datetime.now().isoformat(),
        "char_count": len(content),
    }
    index["articles"].append(meta)
    _save_index(index)
    console.print(f"[green]✓ 已添加到知识库（ID: {article_id}）[/green]")
    return article_id


def remove_article(article_id: str) -> bool:
    """从知识库删除文章"""
    index = _load_index()
    articles = index["articles"]
    to_remove = [a for a in articles if a["id"] == article_id]
    if not to_remove:
        console.print(f"[red]✗ 未找到 ID 为 {article_id} 的文章[/red]")
        return False

    index["articles"] = [a for a in articles if a["id"] != article_id]
    _save_index(index)

    article_path = ARTICLES_DIR / f"{article_id}.txt"
    if article_path.exists():
        article_path.unlink()
    console.print(f"[green]✓ 已删除文章（ID: {article_id}）[/green]")
    return True


def get_article(article_id: str) -> Optional[tuple[dict, str]]:
    """获取文章元信息和内容"""
    index = _load_index()
    meta = next((a for a in index["articles"] if a["id"] == article_id), None)
    if not meta:
        return None
    article_path = ARTICLES_DIR / f"{article_id}.txt"
    if not article_path.exists():
        return None
    content = article_path.read_text(encoding="utf-8")
    return meta, content


def list_articles(tag_filter: str = None) -> list:
    """列出所有文章"""
    index = _load_index()
    articles = index["articles"]
    if tag_filter:
        articles = [a for a in articles if tag_filter in a.get("tags", [])]
    return articles


def show_articles_table():
    """用 Rich 展示知识库文章列表"""
    articles = list_articles()
    if not articles:
        console.print("[yellow]知识库为空，使用 'kb add' 添加文章[/yellow]")
        return

    table = Table(title=f"📚 知识库 ({len(articles)} 篇)", show_lines=True)
    table.add_column("ID", style="cyan", width=10)
    table.add_column("标题", style="white", min_width=20)
    table.add_column("平台", style="blue", width=10)
    table.add_column("标签", style="green", width=20)
    table.add_column("字数", style="yellow", width=8)
    table.add_column("添加时间", style="dim", width=12)

    for a in articles:
        tags_str = ", ".join(a.get("tags", []))
        added = a.get("added_at", "")[:10]
        table.add_row(
            a["id"],
            a["title"],
            a.get("platform", ""),
            tags_str,
            str(a.get("char_count", 0)),
            added,
        )
    console.print(table)


def get_all_articles_for_context(max_articles: int = 5) -> str:
    """获取知识库内容，用于注入 LLM context"""
    articles = list_articles()
    if not articles:
        return ""

    # 取最近添加的几篇
    recent = sorted(articles, key=lambda x: x.get("added_at", ""), reverse=True)[:max_articles]
    parts = []
    for meta in recent:
        result = get_article(meta["id"])
        if result:
            _, content = result
            parts.append(
                f"【参考文章：{meta['title']}（{meta.get('platform', '')}）】\n{content[:2000]}"
            )
    return "\n\n---\n\n".join(parts)
