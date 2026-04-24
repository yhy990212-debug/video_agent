"""
测试 config.py
- API Key 加密存储/读取
- 模型切换
- 用户偏好持久化
- 统计计数
"""
import pytest
from config import (
    load_config, save_config,
    set_api_key, get_api_key,
    set_active_model, get_active_model,
    update_preference, get_preferences,
    increment_stats, SUPPORTED_MODELS,
)


class TestLoadConfig:
    def test_returns_default_on_first_run(self):
        cfg = load_config()
        assert "active_provider" in cfg
        assert "api_keys" in cfg
        assert "user_preferences" in cfg
        assert "usage_stats" in cfg

    def test_config_file_created(self, tmp_path):
        import config as cfg_module
        load_config()  # 触发文件创建
        assert cfg_module.CONFIG_FILE.exists()

    def test_missing_keys_are_merged(self, tmp_path):
        import config as cfg_module
        # 写入一个缺字段的配置
        import json
        cfg_module.CONFIG_FILE.write_text(
            json.dumps({"active_provider": "deepseek"}), encoding="utf-8"
        )
        cfg = load_config()
        # 缺失字段应被默认值补全
        assert "api_keys" in cfg
        assert "usage_stats" in cfg


class TestApiKey:
    def test_set_and_get_api_key(self):
        set_api_key("deepseek", "sk-test-1234567890")
        result = get_api_key("deepseek")
        assert result == "sk-test-1234567890"

    def test_key_is_encrypted_on_disk(self, tmp_path):
        import config as cfg_module, json
        set_api_key("deepseek", "sk-plaintext")
        raw = json.loads(cfg_module.CONFIG_FILE.read_text())
        # 磁盘上不应有明文
        assert "sk-plaintext" not in str(raw["api_keys"])

    def test_missing_key_returns_none(self):
        assert get_api_key("kimi") is None

    def test_multiple_providers(self):
        set_api_key("deepseek", "ds-key-aaa")
        set_api_key("kimi", "kimi-key-bbb")
        assert get_api_key("deepseek") == "ds-key-aaa"
        assert get_api_key("kimi") == "kimi-key-bbb"


class TestActiveModel:
    def test_default_model(self):
        provider, model = get_active_model()
        assert provider in SUPPORTED_MODELS
        assert model != ""

    def test_set_and_get_active_model(self):
        set_active_model("kimi", "moonshot-v1-32k")
        provider, model = get_active_model()
        assert provider == "kimi"
        assert model == "moonshot-v1-32k"

    def test_switch_between_providers(self):
        set_active_model("deepseek", "deepseek-chat")
        assert get_active_model() == ("deepseek", "deepseek-chat")
        set_active_model("qwen", "qwen-turbo")
        assert get_active_model() == ("qwen", "qwen-turbo")


class TestPreferences:
    def test_update_and_get_preference(self):
        update_preference("default_word_count", 1500)
        prefs = get_preferences()
        assert prefs["default_word_count"] == 1500

    def test_update_output_dir(self):
        update_preference("output_dir", "/tmp/test-output")
        assert get_preferences()["output_dir"] == "/tmp/test-output"


class TestStats:
    def test_increment_stats(self):
        increment_stats("total_sessions")
        cfg = load_config()
        assert cfg["usage_stats"]["total_sessions"] == 1

    def test_increment_multiple(self):
        increment_stats("scripts_generated")
        increment_stats("scripts_generated")
        increment_stats("scripts_generated")
        cfg = load_config()
        assert cfg["usage_stats"]["scripts_generated"] == 3
