import os

from services.config import get_llm_config


def test_get_llm_config_uses_defaults(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = get_llm_config()

    assert config.model == "gpt-5.5"
    assert config.base_url == "https://newapi.lxhei.xyz/v1"
    assert config.api_key is None
    assert config.enabled is False


def test_get_llm_config_reads_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "custom-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    config = get_llm_config()

    assert config.model == "custom-model"
    assert config.base_url == "https://example.test/v1"
    assert config.api_key == "test-key"
    assert config.enabled is True
