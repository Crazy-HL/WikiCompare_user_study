import os

from services.config import get_llm_config


def test_get_llm_config_uses_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = get_llm_config(tmp_path / "missing.env")

    assert config.model == "gpt-5.5"
    assert config.base_url == "https://newapi.lxhei.xyz/v1"
    assert config.api_key is None
    assert config.timeout_seconds == 20.0
    assert config.enabled is False


def test_get_llm_config_reads_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "custom-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "7.5")

    config = get_llm_config()

    assert config.model == "custom-model"
    assert config.base_url == "https://example.test/v1"
    assert config.api_key == "test-key"
    assert config.timeout_seconds == 7.5
    assert config.enabled is True


def test_get_llm_config_reads_env_file_when_environment_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                'OPENAI_MODEL="env-file-model"',
                "OPENAI_BASE_URL=https://env-file.example/v1",
                "OPENAI_API_KEY=env-file-key",
                "OPENAI_TIMEOUT_SECONDS=9",
            ]
        )
    )

    config = get_llm_config(env_file)

    assert config.model == "env-file-model"
    assert config.base_url == "https://env-file.example/v1"
    assert config.api_key == "env-file-key"
    assert config.timeout_seconds == 9.0
    assert config.enabled is True


def test_get_llm_config_environment_overrides_env_file(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "shell-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://shell.example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "shell-key")
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "OPENAI_MODEL=env-file-model",
                "OPENAI_BASE_URL=https://env-file.example/v1",
                "OPENAI_API_KEY=env-file-key",
            ]
        )
    )

    config = get_llm_config(env_file)

    assert config.model == "shell-model"
    assert config.base_url == "https://shell.example/v1"
    assert config.api_key == "shell-key"
    assert config.enabled is True
