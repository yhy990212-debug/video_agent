"""
配置管理模块 - 负责 API Key、模型选择、用户偏好的持久化存储
"""
import json
import os
from pathlib import Path
from typing import Optional, Tuple
from cryptography.fernet import Fernet

CONFIG_DIR = Path.home() / ".video-agent"
CONFIG_FILE = CONFIG_DIR / "config.json"
KEY_FILE = CONFIG_DIR / ".key"

SUPPORTED_MODELS = {
    "deepseek": {
        "name": "DeepSeek",
        "models": [
            "deepseek-chat",
            "deepseek-reasoner",
        ],
        "model_info": {
            "deepseek-chat":     "V3，64K 上下文，综合能力强，性价比最高（推荐）",
            "deepseek-reasoner": "R1，64K 上下文，深度推理模型，适合复杂逻辑",
        },
        "base_url": "https://api.deepseek.com/v1",
        "docs": "https://platform.deepseek.com/api-docs/",
    },
    "kimi": {
        "name": "Kimi (月之暗面)",
        "models": [
            "moonshot-v1-8k",
            "moonshot-v1-32k",
            "moonshot-v1-128k",
            "kimi-latest",
        ],
        "model_info": {
            "moonshot-v1-8k":    "8K 上下文，适合短文本，速度最快",
            "moonshot-v1-32k":   "32K 上下文，适合中等长度文档（推荐）",
            "moonshot-v1-128k":  "128K 超长上下文，适合长文档分析",
            "kimi-latest":       "最新版本，持续迭代更新",
        },
        "base_url": "https://api.moonshot.cn/v1",
        "docs": "https://platform.moonshot.cn/docs/api/",
    },
    "doubao": {
        "name": "豆包 (字节跳动)",
        "models": [
            "doubao-pro-4k",
            "doubao-pro-32k",
            "doubao-pro-128k",
            "doubao-pro-256k",
            "doubao-lite-4k",
            "doubao-lite-32k",
            "doubao-lite-128k",
        ],
        "model_info": {
            "doubao-pro-4k":    "Pro 旗舰版，4K 上下文，国内访问稳定",
            "doubao-pro-32k":   "Pro 旗舰版，32K 上下文（推荐）",
            "doubao-pro-128k":  "Pro 旗舰版，128K 超长上下文",
            "doubao-pro-256k":  "Pro 旗舰版，256K 超长上下文，适合超长文档",
            "doubao-lite-4k":   "Lite 轻量版，4K 上下文，速度快成本低",
            "doubao-lite-32k":  "Lite 轻量版，32K 上下文，均衡之选",
            "doubao-lite-128k": "Lite 轻量版，128K 上下文，轻量长文本",
        },
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "docs": "https://www.volcengine.com/docs/82379/1302008",
    },
    "qwen": {
        "name": "通义千问 (阿里云)",
        "models": [
            "qwen-turbo",
            "qwen-plus",
            "qwen-max",
            "qwen-long",
            "qwen2.5-72b-instruct",
            "qwen2.5-32b-instruct",
            "qwen2.5-14b-instruct",
        ],
        "model_info": {
            "qwen-turbo":           "速度最快，成本最低，适合高频调用",
            "qwen-plus":            "性能均衡，中文理解强（推荐）",
            "qwen-max":             "最强旗舰版，效果最好",
            "qwen-long":            "超长上下文专用，支持百万 Token",
            "qwen2.5-72b-instruct": "Qwen2.5 72B 开源版，指令遵循强",
            "qwen2.5-32b-instruct": "Qwen2.5 32B 开源版，性价比高",
            "qwen2.5-14b-instruct": "Qwen2.5 14B 开源版，轻量高效",
        },
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "docs": "https://help.aliyun.com/zh/model-studio/",
    },
    "zhipu": {
        "name": "智谱 GLM",
        "models": [
            "glm-4-plus",
            "glm-4",
            "glm-4-air",
            "glm-4-airx",
            "glm-4-flash",
            "glm-4-long",
            "glm-zero-preview",
        ],
        "model_info": {
            "glm-4-plus":        "GLM-4 旗舰增强版，能力全面提升（推荐）",
            "glm-4":             "GLM-4 标准版，综合能力强",
            "glm-4-air":         "GLM-4 轻量版，速度快价格低",
            "glm-4-airx":        "GLM-4 超快版，极致推理速度",
            "glm-4-flash":       "GLM-4 闪速版，有免费额度",
            "glm-4-long":        "GLM-4 长文本版，128K 上下文",
            "glm-zero-preview":  "GLM-Zero 预览版，深度推理模型",
        },
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "docs": "https://open.bigmodel.cn/dev/api",
    },
}

DEFAULT_CONFIG = {
    "active_provider": "deepseek",
    "active_model": "deepseek-chat",
    "api_keys": {},
    "user_preferences": {
        "default_word_count": 1000,
        "output_dir": str(Path.home() / "Desktop"),
        "language_style": "口语化",
        "content_type": "高中教培",
    },
    "usage_stats": {
        "total_sessions": 0,
        "scripts_generated": 0,
        "favorite_frameworks": [],
    }
}


def _get_or_create_key() -> bytes:
    """获取或创建加密密钥"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    KEY_FILE.chmod(0o600)
    return key


def _encrypt(text: str) -> str:
    f = Fernet(_get_or_create_key())
    return f.encrypt(text.encode()).decode()


def _decrypt(token: str) -> str:
    f = Fernet(_get_or_create_key())
    return f.decrypt(token.encode()).decode()


def load_config() -> dict:
    """加载配置，不存在则初始化"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 合并默认配置（防止版本升级后字段缺失）
        for k, v in DEFAULT_CONFIG.items():
            if k not in data:
                data[k] = v
        return data
    except (json.JSONDecodeError, KeyError):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)


def save_config(config: dict):
    """保存配置"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def set_api_key(provider: str, api_key: str):
    """加密存储 API Key"""
    config = load_config()
    config["api_keys"][provider] = _encrypt(api_key)
    save_config(config)


def get_api_key(provider: str) -> Optional[str]:
    """获取解密后的 API Key"""
    config = load_config()
    encrypted = config.get("api_keys", {}).get(provider)
    if not encrypted:
        return None
    try:
        return _decrypt(encrypted)
    except Exception:
        return None


def set_active_model(provider: str, model: str):
    """设置当前使用的模型"""
    config = load_config()
    config["active_provider"] = provider
    config["active_model"] = model
    save_config(config)


def get_active_model() -> Tuple[str, str]:
    """获取当前激活的 provider 和 model"""
    config = load_config()
    return config.get("active_provider", "deepseek"), config.get("active_model", "deepseek-chat")


def update_preference(key: str, value):
    """更新用户偏好"""
    config = load_config()
    config["user_preferences"][key] = value
    save_config(config)


def get_preferences() -> dict:
    """获取用户偏好"""
    return load_config().get("user_preferences", {})


def increment_stats(key: str, amount: int = 1):
    """更新使用统计"""
    config = load_config()
    config["usage_stats"][key] = config["usage_stats"].get(key, 0) + amount
    save_config(config)


def reset_stats():
    """重置使用统计为初始值"""
    config = load_config()
    config["usage_stats"] = dict(DEFAULT_CONFIG["usage_stats"])
    save_config(config)
