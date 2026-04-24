"""
测试公共配置 - conftest.py
- 隔离测试环境（使用临时目录，不污染真实配置）
- 提供 Mock LLM 客户端（无需真实 API Key）
- 提供常用 fixtures
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# 把项目根目录加入 path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ──────────────────────────────────────────────────────────────
# 环境隔离：把 config/knowledge_base/skills 的存储重定向到 tmp
# ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """
    每个测试都在独立的临时目录中运行，互不干扰，也不污染真实配置。
    - ~/.video-agent  → tmp_path/dot-video-agent
    - KB articles dir → tmp_path/kb/articles
    - skills memory   → tmp_path/skills
    """
    # 重定向 config 模块的路径
    fake_config_dir = tmp_path / "dot-video-agent"
    fake_config_dir.mkdir()

    import config as cfg_module
    monkeypatch.setattr(cfg_module, "CONFIG_DIR", fake_config_dir)
    monkeypatch.setattr(cfg_module, "CONFIG_FILE", fake_config_dir / "config.json")
    monkeypatch.setattr(cfg_module, "KEY_FILE", fake_config_dir / ".key")

    # 重定向 knowledge_base 模块的路径
    import knowledge_base as kb_module
    fake_kb_dir = tmp_path / "kb"
    fake_articles_dir = fake_kb_dir / "articles"
    fake_articles_dir.mkdir(parents=True)
    monkeypatch.setattr(kb_module, "KB_DIR", fake_kb_dir)
    monkeypatch.setattr(kb_module, "ARTICLES_DIR", fake_articles_dir)
    monkeypatch.setattr(kb_module, "INDEX_FILE", fake_kb_dir / "index.json")

    # 重定向 skills 模块的路径
    import skills as skills_module
    fake_skills_dir = tmp_path / "skills"
    fake_skills_dir.mkdir()
    monkeypatch.setattr(skills_module, "SKILLS_DIR", fake_skills_dir)
    monkeypatch.setattr(skills_module, "MEMORY_FILE", fake_skills_dir / "user_memory.json")

    yield tmp_path


# ──────────────────────────────────────────────────────────────
# Mock LLM 客户端
# ──────────────────────────────────────────────────────────────

MOCK_ANALYSIS_RESPONSE = """\
## 一、内容类型与定位
测试类型：教育营销类 | 平台：B站 | 定位：高中备考干货

## 二、开头钩子分析
类型：痛点共鸣型
目标受众：高三备考学生
情绪触发：考试失败的焦虑感

## 三、CREM 循环结构
循环1：
- 观点(C)：传统刷题方法效率极低
- 原理(R)：大脑对重复信息会产生钝化
- 案例(E)：某同学刷了500道题分数仍不提升
- 方法(M)：精题精练，每题必反思

## 四、情绪节奏
0-30秒：焦虑峰值（考试失败场景）
30-90秒：共鸣谷底（自学困境）
90-180秒：希望上升（方法揭示）
180秒+：行动高峰（报课转化）

## 五、金句摘录
- "刷题刷不完，不如刷方法"
- "用对方法，1小时抵3小时"

## 六、营销转化逻辑
痛点放大 → 方法展示 → 效果承诺 → 行动指令

## 七、可复用框架模板
开头：{痛点场景} + {目标受众身份确认}
主体：CREM×3循环
结尾：效果对比 + 低风险行动指令
"""

MOCK_SCRIPT_RESPONSE = """\
# 【正式稿】

很多同学花了三个月备考，却在最后关头崩溃了。

你刷了500道数学题，结果考试还是做错。不是你不够努力，而是方法错了。

今天教你一个我独创的「精题反思法」，让你的复习效率提升3倍。

第一步：每道错题必须写出错误原因，不是答案，是原因。
第二步：找到同类题型的底层规律，一次性攻克一类题。
第三步：每周做一次自我测评，把规律转化成肌肉记忆。

用这个方法，我辅导的学生平均提分40分。现在点击主页，领取免费的「备考规划手册」。

---

# 【注释版】

[开头-痛点钩子] 很多同学花了三个月备考，却在最后关头崩溃了。

[循环1-观点] 你刷了500道数学题，结果考试还是做错。[循环1-原理] 不是你不够努力，而是方法错了。

[过渡-价值承诺] 今天教你一个我独创的「精题反思法」，让你的复习效率提升3倍。

[循环1-方法] 第一步：每道错题必须写出错误原因，不是答案，是原因。
第二步：找到同类题型的底层规律，一次性攻克一类题。
第三步：每周做一次自我测评，把规律转化成肌肉记忆。

[结尾-转化] 用这个方法，我辅导的学生平均提分40分。现在点击主页，领取免费的「备考规划手册」。

---

# 【创作说明】

- 开头钩子：痛点共鸣型，直击"努力无效"的焦虑
- 循环单元：1个完整CREM循环
- 转化节点：效果数据（40分）+ 低门槛行动（免费资料）
- 字数统计：正式稿约 200 字
"""


class MockLLMClient:
    """
    模拟 LLM 客户端，无需真实 API Key。
    可在各测试中替换 get_client() 的返回值。
    """

    def __init__(self, response: str = None, stream_chunks: list = None):
        self._response = response or MOCK_SCRIPT_RESPONSE
        self._stream_chunks = stream_chunks or [self._response]

    def chat(self, messages, temperature=0.7, max_tokens=8000, stream=False):
        if stream:
            return iter(self._stream_chunks)
        return self._response

    def chat_stream(self, messages, temperature=0.7, max_tokens=8000):
        for chunk in self._stream_chunks:
            yield chunk

    def test_connection(self):
        return True


@pytest.fixture
def mock_llm_analysis():
    """返回分析报告的 Mock LLM"""
    return MockLLMClient(response=MOCK_ANALYSIS_RESPONSE,
                         stream_chunks=[MOCK_ANALYSIS_RESPONSE])


@pytest.fixture
def mock_llm_script():
    """返回文案稿件的 Mock LLM"""
    return MockLLMClient(response=MOCK_SCRIPT_RESPONSE,
                         stream_chunks=[MOCK_SCRIPT_RESPONSE])


@pytest.fixture
def patch_llm_analysis(mock_llm_analysis):
    """patch get_client 返回分析用 mock"""
    with patch("workflow.step1_analyze.get_client", return_value=mock_llm_analysis):
        yield mock_llm_analysis


@pytest.fixture
def patch_llm_script(mock_llm_script):
    """patch get_client 返回创作用 mock"""
    with patch("workflow.step2_3_create.get_client", return_value=mock_llm_script):
        yield mock_llm_script


# ──────────────────────────────────────────────────────────────
# 测试数据
# ──────────────────────────────────────────────────────────────

SAMPLE_SCRIPT = """\
大家好，今天讲一个很多人都搞错的数学题型。

我教了10年高中数学，见过太多同学因为这个失分。
核心问题是：他们只记公式，不理解原理。

今天我用3步法彻底解决这个问题：
第一步，理解公式背后的几何含义。
第二步，画图辅助，建立空间感。
第三步，做题时先写思路再算数。

用这个方法，我学生的数学平均提了30分。
感兴趣的同学点赞关注，我每周都会更新。
"""

@pytest.fixture
def sample_script():
    return SAMPLE_SCRIPT
