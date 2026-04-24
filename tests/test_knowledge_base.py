"""
测试 knowledge_base/__init__.py
- 添加/删除/查询文章
- 重复检测（MD5）
- 标签过滤
- 上下文注入
"""
import pytest
from knowledge_base import (
    add_article, remove_article, get_article,
    list_articles, show_articles_table,
    get_all_articles_for_context,
)

ARTICLE_CONTENT = """\
大家好，我是一名高中数学老师。
今天给大家讲一个刷题误区：只刷量，不刷质。
正确方法是每道错题必须写错误分析，找到背后的知识漏洞。
用这个方法，我的学生平均提分35分。
"""

ARTICLE_CONTENT_2 = """\
很多同学英语阅读理解总是扣分，核心原因只有一个：词汇量不够。
但词汇量不够不是你的问题，是你记单词的方式错了。
正确方式是用「语境记忆法」：不背单词表，而是在真题中遇见单词再记。
这样记住的单词，考试时绝对不会忘。
"""


class TestAddArticle:
    def test_add_returns_article_id(self):
        article_id = add_article(ARTICLE_CONTENT, title="数学干货")
        assert article_id is not None
        assert len(article_id) == 8  # MD5前8位

    def test_article_stored_on_disk(self, tmp_path):
        import knowledge_base as kb
        add_article(ARTICLE_CONTENT, title="数学干货")
        assert len(list(kb.ARTICLES_DIR.glob("*.txt"))) == 1

    def test_duplicate_rejected(self):
        id1 = add_article(ARTICLE_CONTENT, title="第一次")
        id2 = add_article(ARTICLE_CONTENT, title="第二次（重复）")
        # 相同内容应返回相同ID，知识库只有一篇
        assert id1 == id2
        assert len(list_articles()) == 1

    def test_add_with_tags(self):
        add_article(ARTICLE_CONTENT, title="带标签", tags=["数学", "高考"])
        articles = list_articles()
        assert articles[0]["tags"] == ["数学", "高考"]

    def test_add_with_platform(self):
        add_article(ARTICLE_CONTENT, title="B站爆款", platform="B站")
        articles = list_articles()
        assert articles[0]["platform"] == "B站"

    def test_add_multiple_articles(self):
        add_article(ARTICLE_CONTENT, title="数学")
        add_article(ARTICLE_CONTENT_2, title="英语")
        assert len(list_articles()) == 2


class TestRemoveArticle:
    def test_remove_existing_article(self):
        article_id = add_article(ARTICLE_CONTENT, title="待删除")
        assert len(list_articles()) == 1
        remove_article(article_id)
        assert len(list_articles()) == 0

    def test_remove_nonexistent_is_safe(self):
        # 不应抛异常
        remove_article("nonexist")

    def test_file_deleted_on_remove(self, tmp_path):
        import knowledge_base as kb
        article_id = add_article(ARTICLE_CONTENT, title="待删除")
        remove_article(article_id)
        assert not (kb.ARTICLES_DIR / f"{article_id}.txt").exists()


class TestGetArticle:
    def test_get_returns_meta_and_content(self):
        article_id = add_article(ARTICLE_CONTENT, title="数学干货", tags=["数学"])
        result = get_article(article_id)
        assert result is not None
        meta, content = result
        assert meta["title"] == "数学干货"
        assert meta["tags"] == ["数学"]
        assert "刷题误区" in content

    def test_get_nonexistent_returns_none(self):
        assert get_article("deadbeef") is None


class TestListArticles:
    def test_empty_kb(self):
        assert list_articles() == []

    def test_lists_all_articles(self):
        add_article(ARTICLE_CONTENT, title="数学")
        add_article(ARTICLE_CONTENT_2, title="英语")
        arts = list_articles()
        assert len(arts) == 2
        titles = {a["title"] for a in arts}
        assert "数学" in titles
        assert "英语" in titles

    def test_tag_filter(self):
        add_article(ARTICLE_CONTENT, title="数学", tags=["数学", "干货"])
        add_article(ARTICLE_CONTENT_2, title="英语", tags=["英语"])
        math_arts = list_articles(tag_filter="数学")
        assert len(math_arts) == 1
        assert math_arts[0]["title"] == "数学"


class TestGetAllArticlesForContext:
    def test_empty_returns_empty_string(self):
        result = get_all_articles_for_context()
        assert result == ""

    def test_returns_content_snippet(self):
        add_article(ARTICLE_CONTENT, title="数学干货")
        result = get_all_articles_for_context()
        assert "数学干货" in result
        assert len(result) > 0

    def test_respects_max_articles(self):
        for i in range(5):
            # 内容需不同，否则重复检测会去重
            add_article(f"文章内容{i} " + "x" * 100, title=f"文章{i}")
        result = get_all_articles_for_context(max_articles=2)
        # 结果不应太长（只取2篇的摘录）
        assert result.count("文章") <= 6  # 标题出现次数有限
