"""
LLM 统一接口层 - 支持 DeepSeek / Kimi / 豆包 / 通义千问 / 智谱
所有 provider 均使用 OpenAI-compatible API
"""
from openai import OpenAI
from config import get_api_key, SUPPORTED_MODELS
from typing import Iterator, Optional, Union, List


class LLMClient:
    """统一的 LLM 客户端"""

    def __init__(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        self.config = SUPPORTED_MODELS.get(provider)
        if not self.config:
            raise ValueError(f"不支持的 provider: {provider}")

        api_key = get_api_key(provider)
        if not api_key:
            raise ValueError(
                f"未找到 {self.config['name']} 的 API Key。\n"
                f"请运行: video-agent key set --provider {provider}"
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url=self.config["base_url"],
        )

    def chat(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 8000,
        stream: bool = False,
    ) -> Union[str, Iterator]:
        """发送对话请求"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        response = self.client.chat.completions.create(**kwargs)
        if stream:
            return response
        return response.choices[0].message.content

    def chat_stream(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 8000,
    ) -> Iterator[str]:
        """流式输出"""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def test_connection(self) -> bool:
        """测试连接是否正常"""
        try:
            result = self.chat(
                [{"role": "user", "content": "你好，请回复'连接成功'"}],
                max_tokens=50
            )
            return bool(result)
        except Exception:
            return False


def get_client(provider: Optional[str] = None, model: Optional[str] = None) -> LLMClient:
    """快捷获取 LLM 客户端"""
    from config import get_active_model
    if provider is None or model is None:
        provider, model = get_active_model()
    return LLMClient(provider, model)
