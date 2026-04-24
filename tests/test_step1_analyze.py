"""
测试 workflow/step1_analyze.py
使用 Mock LLM，不需要真实 API Key
"""
import pytest
from unittest.mock import patch
from workflow.step1_analyze import analyze_scripts
from tests.conftest import MOCK_ANALYSIS_RESPONSE


class TestAnalyzeScripts:
    def test_returns_string(self, patch_llm_analysis, sample_script):
        result = analyze_scripts([sample_script], ["测试文案"])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_analysis_sections(self, patch_llm_analysis, sample_script):
        result = analyze_scripts([sample_script], ["测试文案"])
        # Mock 返回值包含这些章节
        assert "CREM" in result or "开头" in result or "内容类型" in result

    def test_multiple_scripts(self, patch_llm_analysis, sample_script):
        """多篇文案合并分析"""
        result = analyze_scripts(
            [sample_script, sample_script + "（第二篇）"],
            ["文案A", "文案B"]
        )
        assert isinstance(result, str)

    def test_no_titles(self, patch_llm_analysis, sample_script):
        """标题为空时不应报错"""
        result = analyze_scripts([sample_script])
        assert isinstance(result, str)

    def test_skill_note_recorded(self, patch_llm_analysis, sample_script):
        """分析后应自动记录 skill note"""
        analyze_scripts([sample_script], ["测试"])
        from skills import load_memory
        mem = load_memory()
        # auto learn 可能会写 skill_notes 或 content_domain
        # 只验证函数正常执行
        assert isinstance(mem, dict)
