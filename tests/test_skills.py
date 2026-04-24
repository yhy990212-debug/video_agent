"""
测试 skills/__init__.py (记忆系统)
- 自定义创作指令的增删
- 偏好更新
- get_context_prompt 生成
- session 日志记录
"""
import pytest
from skills import (
    load_memory, save_memory,
    add_custom_instruction, remove_custom_instruction,
    add_skill_note, log_session,
    get_context_prompt, show_memory,
    update_writing_preference,
)


class TestLoadMemory:
    def test_default_memory_on_first_run(self):
        mem = load_memory()
        assert "writing_preferences" in mem
        assert "custom_instructions" in mem
        assert "skill_notes" in mem
        assert "session_history" in mem

    def test_returns_dict(self):
        assert isinstance(load_memory(), dict)


class TestCustomInstructions:
    def test_add_instruction(self):
        add_custom_instruction("结尾必须有引导关注的指令")
        mem = load_memory()
        assert "结尾必须有引导关注的指令" in mem["custom_instructions"]

    def test_no_duplicate_instructions(self):
        add_custom_instruction("不要用第一人称")
        add_custom_instruction("不要用第一人称")
        mem = load_memory()
        assert mem["custom_instructions"].count("不要用第一人称") == 1

    def test_remove_instruction(self):
        # 确保从干净状态开始
        from skills import load_memory, save_memory
        mem = load_memory()
        mem["custom_instructions"] = []
        save_memory(mem)

        add_custom_instruction("要删除的指令")
        remove_custom_instruction(0)
        mem = load_memory()
        assert "要删除的指令" not in mem["custom_instructions"]

    def test_remove_out_of_range_is_safe(self):
        remove_custom_instruction(999)  # 不应抛异常

    def test_multiple_instructions_order(self):
        from skills import load_memory, save_memory
        # 确保从干净状态开始
        mem = load_memory()
        mem["custom_instructions"] = []
        save_memory(mem)

        add_custom_instruction("指令A")
        add_custom_instruction("指令B")
        add_custom_instruction("指令C")
        mem = load_memory()
        instructions = mem["custom_instructions"]
        assert instructions[0] == "指令A"
        assert instructions[1] == "指令B"
        assert instructions[2] == "指令C"


class TestSkillNotes:
    def test_add_skill_note(self):
        add_skill_note("用户偏好口语化表达")
        mem = load_memory()
        notes = mem["skill_notes"]
        assert any("口语化" in n["note"] for n in notes)

    def test_notes_capped_at_50(self):
        for i in range(60):
            add_skill_note(f"笔记{i}")
        mem = load_memory()
        assert len(mem["skill_notes"]) <= 50


class TestSessionLog:
    def test_log_session(self):
        log_session("为选题「高考数学」创作了1000字文案")
        mem = load_memory()
        assert len(mem["session_history"]) == 1
        assert "高考数学" in mem["session_history"][0]["summary"]

    def test_session_history_capped_at_20(self):
        for i in range(25):
            log_session(f"会话{i}")
        mem = load_memory()
        assert len(mem["session_history"]) <= 20


class TestContextPrompt:
    def test_empty_memory_returns_string(self):
        result = get_context_prompt()
        assert isinstance(result, str)

    def test_includes_domain_when_set(self):
        mem = load_memory()
        mem["content_domain"] = "高中教育"
        save_memory(mem)
        result = get_context_prompt()
        assert "高中教育" in result

    def test_includes_platform_when_set(self):
        mem = load_memory()
        mem["platform"] = "B站"
        save_memory(mem)
        result = get_context_prompt()
        assert "B站" in result

    def test_includes_custom_instructions(self):
        add_custom_instruction("每段不超过50字")
        result = get_context_prompt()
        assert "每段不超过50字" in result

    def test_includes_recent_skill_notes(self):
        add_skill_note("用户喜欢用数字开头")
        result = get_context_prompt()
        assert "用数字开头" in result

    def test_full_profile(self):
        mem = load_memory()
        mem["content_domain"] = "数学教育"
        mem["platform"] = "抖音"
        mem["persona"] = "10年数学老教师"
        mem["writing_preferences"]["tone"] = ["口语化", "亲切"]
        save_memory(mem)
        add_custom_instruction("开头不超过3句话")

        result = get_context_prompt()
        assert "数学教育" in result
        assert "抖音" in result
        assert "10年数学老教师" in result
        assert "口语化" in result
        assert "开头不超过3句话" in result


class TestUpdateWritingPreference:
    def test_update_tone(self):
        update_writing_preference("tone", ["激情", "有力量"])
        mem = load_memory()
        assert mem["writing_preferences"]["tone"] == ["激情", "有力量"]

    def test_update_word_count_range(self):
        update_writing_preference("word_count_range", [1200, 2000])
        mem = load_memory()
        assert mem["writing_preferences"]["word_count_range"] == [1200, 2000]
