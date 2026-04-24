"""
测试 workflow/step2_3_create.py
使用 Mock LLM，不需要真实 API Key
"""
import pytest
from unittest.mock import patch
from workflow.step2_3_create import create_script
from tests.conftest import MOCK_SCRIPT_RESPONSE


class TestCreateScript:
    def test_returns_string(self, patch_llm_script):
        result = create_script(
            topic="如何3个月提高数学成绩",
            framework="CREM框架：观点→原理→案例→方法",
            word_count=1000,
            stream_output=False,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_formal_draft(self, patch_llm_script):
        """结果应包含正式稿章节标记"""
        result = create_script(
            topic="高考英语备考",
            framework="通用框架",
            word_count=800,
            stream_output=False,
        )
        assert "正式稿" in result

    def test_contains_annotated_version(self, patch_llm_script):
        """结果应包含注释版章节标记"""
        result = create_script(
            topic="数学刷题技巧",
            framework="CREM",
            word_count=1000,
            stream_output=False,
        )
        assert "注释版" in result

    def test_stream_output(self, patch_llm_script):
        """流式输出应正常收集所有 chunk"""
        result = create_script(
            topic="语文作文技巧",
            framework="苦情大戏框架",
            word_count=1200,
            stream_output=True,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_extra_requirements_accepted(self, patch_llm_script):
        """额外要求字段不应导致报错"""
        result = create_script(
            topic="物理备考",
            framework="CREM",
            word_count=1000,
            extra_requirements="开头必须用问句，结尾必须有推课话术",
            stream_output=False,
        )
        assert isinstance(result, str)

    def test_skill_note_recorded(self, patch_llm_script):
        """创作完毕应记录 skill note"""
        create_script(
            topic="化学备考技巧",
            framework="CREM",
            stream_output=False,
        )
        from skills import load_memory
        mem = load_memory()
        notes = mem.get("skill_notes", [])
        assert any("化学备考技巧" in n["note"] for n in notes)
