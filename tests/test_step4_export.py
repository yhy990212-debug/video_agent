"""
测试 workflow/step4_export.py
- 解析文案各章节
- 生成 Word 文档（验证文件创建、大小合理）
- 不同内容格式的健壮性
"""
import pytest
from pathlib import Path
from workflow.step4_export import export_to_word, _parse_content_sections
from tests.conftest import MOCK_SCRIPT_RESPONSE


class TestParseContentSections:
    def test_parse_three_sections(self):
        sections = _parse_content_sections(MOCK_SCRIPT_RESPONSE)
        assert "正式稿" in sections
        assert "注释版" in sections
        assert "创作说明" in sections

    def test_section_content_not_empty(self):
        sections = _parse_content_sections(MOCK_SCRIPT_RESPONSE)
        assert len(sections["正式稿"]) > 10
        assert len(sections["注释版"]) > 10

    def test_fallback_for_unformatted_content(self):
        """没有标准章节标记时，全文作为正式稿"""
        plain = "这是一段普通文案，没有任何章节标记。"
        sections = _parse_content_sections(plain)
        assert "正式稿" in sections
        assert sections["正式稿"] == plain


class TestExportToWord:
    def test_file_created(self, tmp_path):
        path = export_to_word(
            content=MOCK_SCRIPT_RESPONSE,
            topic="测试选题",
            output_dir=str(tmp_path),
        )
        assert Path(path).exists()
        assert path.endswith(".docx")

    def test_file_size_reasonable(self, tmp_path):
        path = export_to_word(
            content=MOCK_SCRIPT_RESPONSE,
            topic="测试选题",
            output_dir=str(tmp_path),
        )
        size = Path(path).stat().st_size
        assert size > 5000      # 至少5KB（不是空文件）
        assert size < 5_000_000 # 不超过5MB

    def test_custom_filename(self, tmp_path):
        path = export_to_word(
            content=MOCK_SCRIPT_RESPONSE,
            topic="测试",
            output_dir=str(tmp_path),
            filename="my_script.docx",
        )
        assert Path(path).name == "my_script.docx"

    def test_with_analysis_appended(self, tmp_path):
        """附带分析报告时文件也应正常生成"""
        analysis = "## 分析\n这是一份分析报告，内容略。"
        path = export_to_word(
            content=MOCK_SCRIPT_RESPONSE,
            topic="带分析的文案",
            analysis=analysis,
            output_dir=str(tmp_path),
        )
        assert Path(path).exists()

    def test_output_dir_auto_created(self, tmp_path):
        """输出目录不存在时应自动创建"""
        new_dir = tmp_path / "subdir" / "output"
        path = export_to_word(
            content=MOCK_SCRIPT_RESPONSE,
            topic="测试",
            output_dir=str(new_dir),
        )
        assert Path(path).exists()

    def test_topic_with_special_chars(self, tmp_path):
        """选题含特殊字符时文件名应被正确清理"""
        path = export_to_word(
            content=MOCK_SCRIPT_RESPONSE,
            topic='高考数学 "核心" / 技巧 * 大全',
            output_dir=str(tmp_path),
        )
        assert Path(path).exists()

    def test_plain_content_also_works(self, tmp_path):
        """不含章节标记的普通文本也应正常导出"""
        plain = "这是一篇没有格式的文案。\n第二段。\n第三段。"
        path = export_to_word(
            content=plain,
            topic="普通文案",
            output_dir=str(tmp_path),
        )
        assert Path(path).exists()

    def test_word_file_is_valid_docx(self, tmp_path):
        """生成的文件应是有效的 .docx"""
        from docx import Document
        path = export_to_word(
            content=MOCK_SCRIPT_RESPONSE,
            topic="验证格式",
            output_dir=str(tmp_path),
        )
        # 不抛异常就是有效 docx
        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        assert len(paragraphs) > 0
