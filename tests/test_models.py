"""
测试 models/__init__.py
- MockLLMClient 行为验证
- LLMClient 缺 API Key 时的报错
"""
import pytest
from unittest.mock import patch, MagicMock
from tests.conftest import MockLLMClient, MOCK_SCRIPT_RESPONSE


class TestMockLLMClient:
    def test_chat_returns_response(self):
        client = MockLLMClient()
        result = client.chat([{"role": "user", "content": "你好"}])
        assert result == MOCK_SCRIPT_RESPONSE

    def test_chat_stream_yields_chunks(self):
        client = MockLLMClient(stream_chunks=["第一段", "第二段", "第三段"])
        chunks = list(client.chat_stream([{"role": "user", "content": "test"}]))
        assert chunks == ["第一段", "第二段", "第三段"]

    def test_test_connection_returns_true(self):
        client = MockLLMClient()
        assert client.test_connection() is True

    def test_custom_response(self):
        custom = "这是自定义响应"
        client = MockLLMClient(response=custom)
        assert client.chat([]) == custom


class TestLLMClientWithoutKey:
    def test_raises_value_error_without_api_key(self):
        """没有 API Key 时应抛出 ValueError"""
        from models import LLMClient
        with pytest.raises(ValueError, match="API Key"):
            LLMClient("deepseek", "deepseek-chat")

    def test_raises_for_unsupported_provider(self):
        """不支持的 provider 应抛出 ValueError"""
        from models import LLMClient
        with pytest.raises(ValueError, match="不支持"):
            LLMClient("nonexistent_provider", "some-model")

    def test_get_client_with_configured_key(self):
        """配置了 API Key 后 get_client 应成功"""
        from config import set_api_key
        from models import get_client
        set_api_key("deepseek", "sk-fake-key-for-test")

        # 构造时不会实际发请求，只要不抛异常即通过
        client = get_client("deepseek", "deepseek-chat")
        assert client is not None
        assert client.provider == "deepseek"
        assert client.model == "deepseek-chat"
